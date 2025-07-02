import random, asyncio, discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_balance, update_balance, add_history, get_pet_buff
from utils.cooldown import can_play

class ChanLeModal(discord.ui.Modal):
    def __init__(self, choice):
        title = f"Cược {'Chẵn' if choice=='chan' else 'Lẻ'}"
        super().__init__(title=title)
        self.choice = choice
        self.add_item(discord.ui.TextInput(label="Số xu", placeholder="≥1.000", max_length=18))

    async def on_submit(self, inter):
        amt = int(self.children[0].value)
        ok, wait = can_play(inter.user.id)
        if not ok: return await inter.response.send_message(f"⏳ Đợi {int(wait)}s", ephemeral=True)
        bal = get_balance(inter.user.id)
        if amt<1000 or amt>bal:
            return await inter.response.send_message("❌ Cược không hợp lệ!", ephemeral=True)

        await inter.response.send_message("⚖️ Đang chờ…")
        await asyncio.sleep(2)

        s = random.choice(range(60))
        total = (s//10)+(s%10)
        kq    = "chan" if total%2==0 else "le"
        win   = (kq==self.choice)

        if win:
            profit = round(amt*0.85)
            buff   = get_pet_buff(inter.user.id)
            bonus  = round(profit*buff/100)
            delta  = amt + profit + bonus
        else:
            delta = -amt

        newb = update_balance(inter.user.id, delta)
        add_history(inter.user.id, f"chanle_{'win' if win else 'lose'}", delta, newb)

        await inter.edit_original_response(
            content=(
                f"🕓 Giây={s} → Tổng={total} → **{kq.upper()}**\n"
                + (f"🎉 Thắng! +{profit:,} +pet {bonus:,}\n" if win else "💸 Thua mất stake\n")
                + f"💰 Số dư: {newb:,}"
            )
        )

class ChanLe(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="chanle", description="⚖️ Cược Chẵn/Lẻ")
    async def cl(self, inter: discord.Interaction):
        await inter.response.send_modal(ChanLeModal("chanle"))

async def setup(bot):
    await bot.add_cog(ChanLe(bot))