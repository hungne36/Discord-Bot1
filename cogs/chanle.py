    # cogs/chanle.py
import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_balance, update_balance, add_history, get_pet_buff
from utils.cooldown import can_play
import random
import asyncio

class ChanLeModal(discord.ui.Modal):
        def __init__(self, choice: str):
            super().__init__(title=f"Cược {'Chẵn' if choice=='chan' else 'Lẻ'}")
            self.choice = choice
            self.add_item(discord.ui.TextInput(
                label="Số xu cược", placeholder="Nhập ≥1.000", max_length=18
            ))

        async def on_submit(self, interaction: discord.Interaction):
            # 1. Parse và validate số nhập vào
            try:
                amt = int(self.children[0].value)
            except ValueError:
                return await interaction.response.send_message(
                    "❌ Vui lòng nhập một số hợp lệ!", ephemeral=True
                )

            # 2. Kiểm tra cooldown
            ok, wait = can_play(interaction.user.id)
            if not ok:
                return await interaction.response.send_message(
                    f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True
                )

            # 3. Kiểm tra số dư
            bal = get_balance(interaction.user.id)
            if amt < 1000 or amt > bal:
                return await interaction.response.send_message(
                    "❌ Số xu cược không hợp lệ!", ephemeral=True
                )

            # 4. Gửi tin nhắn chờ và đợi
            await interaction.response.send_message(
                "⚖️ Đang chờ kết quả...", ephemeral=True
            )
            await asyncio.sleep(2)

            # 5. Quay kết quả
            sec = random.randint(0, 59)
            total = (sec // 10) + (sec % 10)
            kq = "chan" if total % 2 == 0 else "le"
            win = (kq == self.choice)

            # 6. Tính thaydoi
            if win:
                profit = round(amt * 0.8)
                buff   = get_pet_buff(interaction.user.id)
                bonus  = round(profit * buff / 100) if buff else 0
                delta  = amt + profit + bonus
            else:
                profit, bonus = 0, 0
                delta = -amt

            # 7. Cập nhật số dư và lịch sử
            newb = update_balance(interaction.user.id, delta)
            add_history(
                interaction.user.id,
                f"chanle_{'win' if win else 'lose'}",
                delta,
                newb
            )

            # 8. Định dạng và gửi kết quả
            txt = (
                f"🔢 Số {sec:02d} → **{total}** ({'CHẴN' if kq=='chan' else 'LẺ'})\n"
                + (f"🎉 Thắng! +{profit:,} + pet bonus {bonus:,}\n" if win else "💸 Bạn thua và mất stake\n")
                + f"💰 Số dư hiện tại: **{newb:,} xu**"
            )
            await interaction.followup.send(txt)

class ChanLe(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        # Không cần lệnh slash riêng nữa, vì đã tích hợp qua menu

async def setup(bot):
        await bot.add_cog(ChanLe(bot))