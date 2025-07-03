# cogs/chanle.py
import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_balance, update_balance, add_history, get_pet_buff
from utils.cooldown import can_play
import random, asyncio

class ChanLeModal(discord.ui.Modal):
    def __init__(self, choice: str):
        super().__init__(title=f"Cược {'Chẵn' if choice=='chan' else 'Lẻ'}")
        self.choice = choice
        self.add_item(discord.ui.TextInput(
            label="Số xu cược", placeholder="Nhập ≥1,000", max_length=18
        ))

    async def on_submit(self, interaction: discord.Interaction):
        amt = int(self.children[0].value)
        ok, wait = can_play(interaction.user.id)
        if not ok:
            return await interaction.response.send_message(f"⏳ Đợi {int(wait)}s", ephemeral=True)

        bal = get_balance(interaction.user.id)
        if amt < 1000 or amt > bal:
            return await interaction.response.send_message("❌ Cược không hợp lệ!", ephemeral=True)

        await interaction.response.send_message("⚖️ Đang chờ kết quả...", ephemeral=True)
        await asyncio.sleep(2)

        sec = random.randint(0,59)
        total = (sec // 10) + (sec % 10)
        kq = "chan" if total % 2 == 0 else "le"
        win = (kq == self.choice)

        if win:
            profit = round(amt * 0.95)
            buff   = get_pet_buff(interaction.user.id)
            bonus  = round(profit * buff/100) if buff else 0
            delta  = amt + profit + bonus
        else:
            delta = -amt
            profit, bonus = 0, 0

        newb = update_balance(interaction.user.id, delta)
        add_history(interaction.user.id,
                    f"chanle_{'win' if win else 'lose'}",
                    delta, newb)

        txt = (
            f"🔢 Số {sec:02d} → **{total}** ({'CHẴN' if kq=='chan' else 'LẺ'})\n"
            + (f"🎉 Thắng! +{profit:,} + pet bonus {bonus:,}\n" if win else "💸 Thua mất stake\n")
            + f"💰 Số dư: {newb:,} xu"
        )
        await interaction.followup.send(txt)

class ChanLe(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="chanle", description="⚖️ Cược Chẵn/Lẻ (qua /menu)")
    async def chanle(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ChanLeModal("chan"))  # mặc định chỉ modal

async def setup(bot):
    await bot.add_cog(ChanLe(bot))