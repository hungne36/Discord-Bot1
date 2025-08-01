    # cogs/chanle.py
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from discord import Interaction
from utils.data_manager import get_balance, update_balance, add_history, get_pet_buff
from utils.cooldown import can_play, set_cooldown
import random
import asyncio

    # Biến lưu trữ cược đang chờ
pending_chanle = {}

class ChanLeSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Chẵn", style=discord.ButtonStyle.primary, custom_id="chan"))
        self.add_item(Button(label="Lẻ", style=discord.ButtonStyle.primary, custom_id="le"))
        self.add_item(Button(label="Kết thúc trò chơi", style=discord.ButtonStyle.danger, custom_id="chanle_ketthuc"))

    async def interaction_check(self, interaction: Interaction) -> bool:
        return True

class ChanLeModal(discord.ui.Modal):
        def __init__(self, choice: str):
            super().__init__(title=f"Cược {'Chẵn' if choice=='chan' else 'Lẻ'}")
            self.choice = choice
            self.add_item(discord.ui.TextInput(
                label="Số xu cược", placeholder="Nhập ≥1.000", max_length=18
            ))

        async def on_submit(self, interaction: discord.Interaction):
            try:
                amt = int(self.children[0].value)
            except ValueError:
                return await interaction.response.send_message(
                    "❌ Vui lòng nhập một số hợp lệ!", ephemeral=True
                )

            ok, wait = can_play(interaction.user.id)
            if not ok:
                return await interaction.response.send_message(
                    f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True
                )

            bal = get_balance(interaction.user.id)
            if amt < 1000 or amt > bal:
                return await interaction.response.send_message(
                    "❌ Số xu cược không hợp lệ!", ephemeral=True
                )

            # Lưu cược vào pending
            pending_chanle[interaction.user.id] = {
                "choice": self.choice,
                "amount": amt,
                "user": interaction.user
            }

            await interaction.response.send_message(
                f"✅ Đã đặt cược **{'Chẵn' if self.choice=='chan' else 'Lẻ'}** với **{amt:,} xu**!\n"
                "👉 Nhấn **Kết thúc trò chơi** để xem kết quả!", ephemeral=True
            )

class ChanLeView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Chẵn", style=discord.ButtonStyle.primary, custom_id="chanle_chan")
        async def chan_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(ChanLeModal("chan"))

        @discord.ui.button(label="Lẻ", style=discord.ButtonStyle.success, custom_id="chanle_le")
        async def le_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(ChanLeModal("le"))

        @discord.ui.button(label="Kết thúc trò chơi", style=discord.ButtonStyle.danger, custom_id="chanle_end")
        async def end_game(self, interaction: discord.Interaction, button: discord.ui.Button):
            data = pending_chanle.pop(interaction.user.id, None)
            if not data:
                return await interaction.response.send_message("❌ Bạn chưa đặt cược!", ephemeral=True)

            await interaction.response.defer()

            await asyncio.sleep(2)
            sec = random.randint(0, 59)
            total = (sec // 10) + (sec % 10)
            kq = "chan" if total % 2 == 0 else "le"
            win = (kq == data["choice"])
            amt = data["amount"]

            if win:
                profit = round(amt * 0.8)
                buff = get_pet_buff(interaction.user.id)
                bonus = round(profit * buff / 100) if buff else 0
                delta = amt + profit + bonus
            else:
                profit, bonus = 0, 0
                delta = -amt

            newb = update_balance(interaction.user.id, delta)
            add_history(
                interaction.user.id,
                f"chanle_{'win' if win else 'lose'}",
                delta,
                newb
            )

            txt = (
                f"🔢 Số {sec:02d} → **{total}** ({'CHẴN' if kq=='chan' else 'LẺ'})\n"
                + (f"🎉 Thắng! +{profit:,} + pet bonus {bonus:,}\n" if win else "💸 Bạn thua và mất stake\n")
                + f"💰 Số dư hiện tại: **{newb:,} xu**"
            )

            await interaction.followup.send(txt, view=None)

            # Đóng các nút lại
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)

            # Cấm chơi lại trong 30s
            set_cooldown(interaction.user.id, 30)

class ChanLe(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.command(name="chanle_testmenu")
        async def chanle_test(self, ctx):
            await ctx.send("🎮 **Chẵn Lẻ** - chọn một tùy chọn:", view=ChanLeView())

async def setup(bot):
    await bot.add_cog(ChanLe(bot))