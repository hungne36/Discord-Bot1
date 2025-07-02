import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_balance, get_today_spent, get_today_net, get_pending_reward
import os
from utils.data_manager import read_json

PETS_FILE = "data/pets.json"
class Info(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="info", description="📊 Xem thông tin tài khoản")
        async def info(self, interaction: discord.Interaction):
            uid = interaction.user.id
            balance = get_balance(uid)
            spent_today = get_today_spent(uid)
            net_today = get_today_net(uid)
            pending = get_pending_reward(uid)

            # Đọc pet đang sở hữu
            pets_data = read_json(PETS_FILE)
            user_data = pets_data.get(str(uid), {})
            owned_pets = user_data.get("collected", [])
            last_pet = user_data.get("last", None)

            # Tính buff
            total_buff = 0
            buff_lines = []
            for name, emoji, pct in [
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
            ]:
                if name in owned_pets:
                    total_buff += pct
                    buff_lines.append(f"{emoji} {name} (+{pct}%)")

            embed = discord.Embed(
                title=f"👤 Thông tin của {interaction.user.name}",
                description=(
                    f"💰 Số dư: **{balance:,} xu**\n"
                    f"🔥 Xu tiêu hôm nay: **{spent_today:,} xu**\n"
                    f"📈 Thắng/Thua hôm nay: **{net_today:+,} xu**\n"
                    f"🎁 Xu chờ nhận: **{pending:,} xu**\n"
                    f"🐾 Buff Pet: **+{total_buff}%**\n" +
                    (f"> " + "\n> ".join(buff_lines) if buff_lines else "Bạn chưa sở hữu pet nào.")
                ),
                color=discord.Color.gold()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
        await bot.add_cog(Info(bot))