# cogs/taixiu.py
import discord, random, asyncio
from discord.ext import commands
from discord import app_commands
from utils.cooldown import can_play
from utils.data_manager import (
    get_balance, update_balance, add_history, get_pet_buff
)
from discord.ui import Modal, TextInput, View, Select, Button

# ――― CLASSIC TÀI XỈU ―――
class TaiXiuModal(Modal):
    def __init__(self, choice: str):
        title = f"Cược {'Tài' if choice=='tai' else 'Xỉu'}"
        super().__init__(title=title)
        self.choice = choice
        self.amount = TextInput(
            label="Số xu cược (≥1.000)",
            placeholder="Ví dụ: 10000",
            max_length=18
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        # 1) Cooldown
        ok, wait = can_play(interaction.user.id)
        if not ok:
            return await interaction.response.send_message(
                f"⏳ Vui lòng chờ {int(wait)} giây", ephemeral=True
            )

        # 2) Parse & validate
        try:
            amt = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Số không hợp lệ", ephemeral=True)

        bal = get_balance(interaction.user.id)
        if amt < 1000 or amt > bal:
            return await interaction.response.send_message("❌ Cược phải từ 1.000 đến số dư của bạn", ephemeral=True)

        # 3) Trừ tiền tạm thời
        update_balance(interaction.user.id, -amt)

        # 4) Ghi vào lịch sử cược
        import json
        from datetime import datetime
        with open("data/lichsu.json", "r") as f:
            history = json.load(f)

        history.append({
            "user_id": interaction.user.id,
            "game": "taixiu",
            "choice": self.choice,
            "amount": amt,
            "resolved": False,
            "timestamp": datetime.utcnow().isoformat()
        })

        with open("data/lichsu.json", "w") as f:
            json.dump(history, f, indent=4)

        await interaction.response.send_message(
            f"✅ Bạn đã đặt cược **{'Tài' if self.choice == 'tai' else 'Xỉu'}** với **{amt:,} xu**.\n"
            f"⏳ Vui lòng chờ kết thúc trò chơi.",
            ephemeral=True
        )

# ――― PLUS SUM (3–18) ―――
PAYOUT = {
    3:60, 18:60, 4:45,17:45,5:30,16:30,
    6:15,15:15,7:5,14:5,
    **{i:2.5 for i in range(8,14)}
}

class SumBetModal(Modal):
    def __init__(self, choices: list[int]):
        super().__init__(title=f"Cược sum: {', '.join(map(str,choices))}")
        self.choices = choices
        self.amount = TextInput(
            label="Số xu cược (≥1.000)",
            placeholder="Ví dụ: 50000",
            max_length=18
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        # tương tự validate
        try:
            stake = int(self.amount.value)
        except:
            return await interaction.response.send_message(
                "❌ Số không hợp lệ", ephemeral=True
            )
        bal = get_balance(interaction.user.id)
        if stake < 1000 or stake > bal:
            return await interaction.response.send_message(
                "❌ Cược phải từ 1.000 đến số dư của bạn", ephemeral=True
            )

        # roll
        dice = [random.randint(1,6) for _ in range(3)]
        total = sum(dice)
        win = total in self.choices

        if win:
            rate = PAYOUT[total]
            profit = round(stake * rate)
            buff = get_pet_buff(interaction.user.id)
            bonus = round(profit * buff / 100)
            delta = stake + profit + bonus
        else:
            delta = -stake
            profit = bonus = 0

        newb = update_balance(interaction.user.id, delta)
        add_history(
            interaction.user.id,
            f"taixiu_sum_{'win' if win else 'lose'}",
            delta, newb
        )

        text = (
            f"🎲 `{dice}` → **{total}**\n"
            + (f"🎉 Thắng! profit={profit:,}, pet bonus={bonus:,}\n"
               if win else "💸 Thua mất toàn bộ stake\n")
            + f"💰 Số dư hiện tại: **{newb:,}** xu"
        )
        await interaction.response.send_message(text, ephemeral=False)

class SumSelect(View):
    def __init__(self):
        super().__init__(timeout=60)
        opts = [discord.SelectOption(label=str(i), value=str(i))
                for i in range(3,19)]
        self.add_item(Select(
            placeholder="Chọn tối đa 5 số (3–18)…",
            min_values=4, max_values=5, options=opts
        ))

    @discord.ui.select()
    async def on_select(self, interaction: discord.Interaction, select: Select):
        choices = list(map(int, select.values))
        await interaction.response.send_modal(SumBetModal(choices))

# ――― COG ĐĂNG KÝ ―――
class TaiXiuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # NOTE: Classic Tài/Xỉu chỉ chạy qua menu ⇒ không cần slash command
    @commands.Cog.listener()
    async def on_ready(self):
        # đăng ký persistent views nếu muốn giữ View sau restart
        self.bot.add_view(SumSelect())

class EndTaiXiuButton(Button):
    def __init__(self):
        super().__init__(label="🎲 Kết thúc trò chơi", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await handle_taixiu_end(interaction)

async def handle_taixiu_end(interaction: discord.Interaction):
    """Handle ending a Tài Xỉu game session"""
    import json
    from utils.data_manager import add_balance
    
    with open("data/lichsu.json", "r") as f:
        lichsu = json.load(f)

    user_bets = [entry for entry in lichsu if entry.get("game") == "taixiu" and not entry.get("resolved", False)]

    if not user_bets:
        await interaction.response.send_message("❌ Không có cược nào đang hoạt động trong Tài Xỉu.", ephemeral=True)
        return

    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "Tài" if total >= 11 else "Xỉu"

    reward_message = f"🎲 Kết quả: **{dice}** (Tổng: {total} → **{result}**)\n\n"

    for bet in user_bets:
        user_id = bet["user_id"]
        choice = bet["choice"]
        amount = bet["amount"]
        win = (choice.lower() == result.lower())

        if win:
            add_balance(user_id, amount * 2)
            reward_message += f"<@{user_id}> thắng {amount * 2:,} xu ✅\n"
        else:
            reward_message += f"<@{user_id}> thua {amount:,} xu ❌\n"

        bet["resolved"] = True

    with open("data/lichsu.json", "w") as f:
        json.dump(lichsu, f, indent=4)

    await interaction.response.send_message(embed=discord.Embed(
        title="🎲 Trò chơi Tài Xỉu đã kết thúc!",
        description=reward_message,
        color=discord.Color.green()
    ))

async def setup(bot):
    await bot.add_cog(TaiXiuCog(bot))