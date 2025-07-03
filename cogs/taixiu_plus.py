
# cogs/taixiu_plus.py
import random
import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_balance, update_balance, add_history, get_pet_buff

PAYOUT = {
    3:60, 18:60, 4:45,17:45,5:30,16:30,6:15,15:15,7:5,14:5,
    **{i:2.5 for i in range(8,14)}
}

class SumBetModal(discord.ui.Modal):
    def __init__(self, choices: list[int]):
        title = f"Cược sum: {', '.join(map(str, choices))}"
        super().__init__(title=title)
        self.choices = choices
        self.amount = discord.ui.TextInput(label="Số xu cược", placeholder="≥1.000", max_length=18)
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        stake = int(self.amount.value)
        bal = get_balance(interaction.user.id)
        if stake < 1000 or stake > bal:
            return await interaction.response.send_message("❌ Cược không hợp lệ!", ephemeral=True)

        dice = [random.randint(1,6) for _ in range(3)]
        total = sum(dice)
        win = total in self.choices

        if win:
            rate = PAYOUT[total]
            profit = round(stake * rate)
            buff = get_pet_buff(interaction.user.id)
            bonus = round(profit * buff / 100) if buff else 0
            delta = stake + profit + bonus
        else:
            delta = -stake

        newb = update_balance(interaction.user.id, delta)
        add_history(interaction.user.id, f"taixiu_sum_{'win' if win else 'lose'}", delta, newb)

        lines = [
            f"🎲 `{dice}` → **{total}**",
            ("🎉 Thắng! +" + f"{profit:,} + pet bonus {bonus:,}" if win else "💸 Thua mất stake"),
            f"💰 Số dư: {newb:,}"
        ]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

class SumSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        opts = [discord.SelectOption(label=str(i), value=str(i)) for i in range(3,19)]
        self.add_item(discord.ui.Select(placeholder="Chọn 1–4 số", min_values=1, max_values=4, options=opts))

    @discord.ui.select()
    async def on_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        choices = list(map(int, select.values))
        await interaction.response.send_modal(SumBetModal(choices))

class TaiXiuPlus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="taixiu_plus", description="🎲 Cược sum (3–18), tối đa 4 lựa chọn")
    async def txp(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔢 Chọn số để cược:", view=SumSelect(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(TaiXiuPlus(bot))
