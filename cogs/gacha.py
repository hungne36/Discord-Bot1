    # cogs/gacha.py
import discord, random, os
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, write_json, get_balance, update_balance, add_history
from datetime import datetime, timezone

    # File chứa dữ liệu pets của từng user
PETS_FILE     = "data/pets.json"
COST_PER_SPIN = 1_000_000_000

    # Định nghĩa Pet: (Tên, Emoji, Buff%)
PET_LIST = [
        ("Tí",   "🐭",  5),
        ("Sửu",  "🐂", 10),
        ("Dần",  "🐯", 15),
        ("Mẹo",  "🐇", 20),
        ("Thìn", "🐉", 25),
        ("Tỵ",   "🐍", 30),
        ("Ngọ",  "🐎", 35),
        ("Mùi",  "🐐", 40),
        ("Thân", "🐒", 45),
        ("Dậu",  "🐓", 50),
        ("Tuất", "🐕", 55),
        ("Hợi",  "🐖", 60),
    ]
    # Trọng số tương ứng (càng hiếm ở đầu thì weight thấp hơn)
WEIGHTS = [1,2,3,4,5,6,5,4,3,2,1,1]

    # chắc chắn có file
os.makedirs(os.path.dirname(PETS_FILE), exist_ok=True)
if not os.path.exists(PETS_FILE):
        write_json = write_json  # khai báo để tạo file
        write_json(PETS_FILE, {})

class GachaButton(discord.ui.Button):
        def __init__(self, count: int):
            super().__init__(label=f"Quay ×{count}", style=discord.ButtonStyle.green)
            self.count = count

        async def callback(self, interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            bal = get_balance(interaction.user.id)
            cost = COST_PER_SPIN * self.count
            if bal < cost:
                return await interaction.response.send_message("❌ Bạn không đủ xu để quay!", ephemeral=True)

            # trừ xu
            newb = update_balance(interaction.user.id, -cost)
            add_history(interaction.user.id, "gacha_cost", -cost, newb)

            # load pets đã có
            pets_data = read_json(PETS_FILE)
            owned = pets_data.get(user_id, {}).get("collected", [])

            obtained = []
            available = [p for p in PET_LIST if p[0] not in owned]
            weights  = [WEIGHTS[i] for i,p in enumerate(PET_LIST) if p[0] not in owned]

            if not available:
                return await interaction.response.send_message(
                    "🎉 Bạn đã sở hữu toàn bộ Pet! Không thể quay thêm.", ephemeral=True
                )

            # spin tối đa count, nhưng không vượt quá số còn thiếu
            spins = min(self.count, len(available))
            for _ in range(spins):
                idx = random.choices(range(len(available)), weights=weights, k=1)[0]
                name, emoji, pct = available[idx]
                obtained.append((name, emoji, pct))
                # đánh dấu đã có
                owned.append(name)
                # sau khi lấy 1 pet, loại khỏi available
                del available[idx]
                del weights[idx]

            # lưu lại
            pets_data[user_id] = {
                "collected": owned,
                "last": obtained[-1],
                "updated_at": datetime.now(timezone.utc).isoformat()+"Z"
            }
            write_json(PETS_FILE, pets_data)

            # trả kết quả
            lines = "\n".join(f"{e} **{n}** (+{p}%)" for n,e,p in obtained)
            await interaction.response.edit_message(
                content=(
                    f"🎉 **Bạn đã quay ×{spins}!**\n{lines}\n\n"
                    f"💰 Số dư hiện tại: **{newb:,} xu**\n"
                    f"Pet cuối cùng bật buff **+{obtained[-1][2]}%**"
                ),
                view=None
            )

class GachaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            for c in [1,5,10,50,100,1000]:
                self.add_item(GachaButton(c))

class Gacha(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="gacha", description="🎲 Quay Pet để nhận buff mọi trò chơi")
        async def gacha(self, interaction: discord.Interaction):
            """Hiện menu các nút quay"""
            # đảm bảo file tồn tại
            if not os.path.exists(PETS_FILE):
                write_json(PETS_FILE, {})

            # load đã có
            pets_data = read_json(PETS_FILE)
            owned = pets_data.get(str(interaction.user.id), {}).get("collected", [])

            embed = discord.Embed(
                title="🎁 Gacha Pet",
                description=(
                    f"Mỗi lượt quay mất **{COST_PER_SPIN:,} xu**\n"
                    f"Bạn đã sở hữu: {', '.join(owned) or 'chưa có pet nào'}\n\n"
                    "**Danh sách Pet & Buff:**\n" +
                    "\n".join(f"{e} {n} – +{p}%" for n,e,p in PET_LIST if n not in owned)
                ),
                color=discord.Color.purple()
            )
            await interaction.response.send_message(embed=embed, view=GachaView(), ephemeral=True)

async def setup(bot):
        await bot.add_cog(Gacha(bot))