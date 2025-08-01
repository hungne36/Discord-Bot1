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
            return await interaction.response.send_message(
                "❌ Số không hợp lệ", ephemeral=True
            )
        bal = get_balance(interaction.user.id)
        if amt < 1000 or amt > bal:
            return await interaction.response.send_message(
                "❌ Cược phải từ 1.000 đến số dư của bạn", ephemeral=True
            )

        # 3) Roll
        await interaction.response.send_message("🎲 Đang lắc xúc xắc...")
        await asyncio.sleep(2)
        dice = [random.randint(1,6) for _ in range(3)]
        total = sum(dice)
        result = "tai" if total >= 11 else "xiu"
        win = (result == self.choice)

        # 4) Tính thưởng
        if win:
            profit = round(amt * 0.9)
            buff = get_pet_buff(interaction.user.id)
            bonus = round(profit * buff / 100)
            delta = amt + profit + bonus
        else:
            delta = -amt

        newb = update_balance(interaction.user.id, delta)
        add_history(
            interaction.user.id,
            f"taixiu_{'win' if win else 'lose'}",
            delta, newb
        )

        # 5) Trả kết quả
        emoji = "".join("⚀⚁⚂⚃⚄⚅"[d-1] for d in dice)
        tlabel = "TÀI" if result=="tai" else "XỈU"
        text = (
            f"🎲 {emoji} → **{total}** ({tlabel})\n"
            + (f"🎉 Thắng! stake +{profit:,} + pet bonus {bonus:,}\n"
               if win else "💸 Thua mất stake\n")
            + f"💰 Số dư hiện tại: **{newb:,}** xu"
        )
        await interaction.edit_original_response(content=text)

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

async def setup(bot):
    await bot.add_cog(TaiXiuCog(bot))