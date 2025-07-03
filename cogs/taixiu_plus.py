
# cogs/taixiu_plus.py
import random, discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_balance, update_balance, add_history, get_pet_buff
from datetime import datetime

# ― Tỉ lệ trả thưởng sum (3–18)
PAYOUT = {
    3:60, 18:60, 4:45,17:45,5:30,16:30,6:15,15:15,7:5,14:5,
    **{i:2.5 for i in range(8,14)}
}

class SumBetModal(discord.ui.Modal):
    def __init__(self, choices: list[int]):
        super().__init__(title=f"Cược sum: {', '.join(map(str,choices))}")
        self.choices = choices
        self.amount = discord.ui.TextInput(
            label="Số xu cược", placeholder="Nhập ≥1,000", max_length=18
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        stake = int(self.amount.value)
        bal   = get_balance(interaction.user.id)
        if stake < 1000 or stake > bal:
            return await interaction.response.send_message("❌ Số cược không hợp lệ!", ephemeral=True)

        dice  = [random.randint(1,6) for _ in range(3)]
        total = sum(dice)
        win   = total in self.choices

        if win:
            rate   = PAYOUT[total]
            profit = round(stake * rate)
            buff   = get_pet_buff(interaction.user.id)
            bonus  = round(profit * buff/100) if buff else 0
            delta  = stake + profit + bonus
        else:
            delta = -stake
            profit, bonus = 0, 0

        newb = update_balance(interaction.user.id, delta)
        add_history(interaction.user.id,
                    f"taixiu_sum_{'win' if win else 'lose'}",
                    delta, newb)

        msg = (
            f"🎲 `{dice}` → **{total}**\n"
            + (f"🎉 Thắng! +{profit:,} + pet bonus {bonus:,}\n" if win else "💸 Thua mất stake\n")
            + f"💰 Số dư: {newb:,} xu"
        )
        await interaction.response.send_message(msg, ephemeral=False)

class SumSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        opts = [discord.SelectOption(label=str(i), value=str(i)) for i in range(3,19)]
        self.add_item(discord.ui.Select(
            placeholder="Chọn 1–4 số", min_values=1, max_values=4, options=opts
        ))

    @discord.ui.select()
    async def on_sel(self, interaction: discord.Interaction, select: discord.ui.Select):
        choices = list(map(int, select.values))
        await interaction.response.send_modal(SumBetModal(choices))

class TaiXiuPlus(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="taixiu_plus", description="🎲 Cược sum (3–18)")
    async def txp(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔢 Chọn 1–4 số:", view=SumSelect(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(TaiXiuPlus(bot))
