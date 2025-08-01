import discord
from discord.ext import commands
import random
import asyncio
from utils.data_manager import get_balance, update_balance, log_history, get_pet_bonus
from datetime import datetime, timedelta
from main import menu_lock_time

class TaiXiuView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(TaiXiuButton("Tài", 11, 17))
                self.add_item(TaiXiuButton("Xỉu", 4, 10))
                for i in range(3, 19):
                    self.add_item(TaiXiuButton(f"{i}", i, i))
                self.add_item(KetThucTaiXiuButton())

        # Nút đặt cược
class TaiXiuButton(discord.ui.Button):
            def __init__(self, label, min_sum, max_sum):
                super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=f"taixiu_{label}")
                self.min_sum = min_sum
                self.max_sum = max_sum

            async def callback(self, interaction: discord.Interaction):
                await interaction.response.send_modal(TaiXiuModal(self.label, self.min_sum, self.max_sum))

        # Modal nhập số tiền cược
class TaiXiuModal(discord.ui.Modal, title="💰 Nhập số tiền cược"):
            def __init__(self, choice, min_sum, max_sum):
                super().__init__()
                self.choice = choice
                self.min_sum = min_sum
                self.max_sum = max_sum

                self.tien_cuoc = discord.ui.TextInput(
                    label="Nhập số tiền cược",
                    placeholder="Ví dụ: 1000000",
                    required=True,
                    style=discord.TextStyle.short
                )
                self.add_item(self.tien_cuoc)

            async def on_submit(self, interaction: discord.Interaction):
                user_id = str(interaction.user.id)
                try:
                    amount = int(self.tien_cuoc.value.replace(",", ""))
                    if amount <= 0:
                        raise ValueError
                except:
                    return await interaction.response.send_message("⚠️ Số tiền không hợp lệ.", ephemeral=True)

                balance = get_balance(user_id)
                if amount > balance:
                    return await interaction.response.send_message("⚠️ Bạn không đủ xu.", ephemeral=True)

                # Ghi lại dữ liệu cược vào bộ nhớ tạm
                if not hasattr(interaction.client, "taixiu_data"):
                    interaction.client.taixiu_data = {}
                if user_id not in interaction.client.taixiu_data:
                    interaction.client.taixiu_data[user_id] = []
                interaction.client.taixiu_data[user_id].append({
                    "choice": self.choice,
                    "min_sum": self.min_sum,
                    "max_sum": self.max_sum,
                    "amount": amount
                })

                await interaction.response.send_message(
                    f"✅ Đặt cược {self.choice} với {amount:,} xu thành công.\nHãy nhấn **Kết thúc trò chơi** khi sẵn sàng.",
                    ephemeral=True
                )

        # Nút kết thúc trò chơi
class KetThucTaiXiuButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="🎯 Kết thúc trò chơi", style=discord.ButtonStyle.danger, custom_id="taixiu_ketthuc")

            async def callback(self, interaction: discord.Interaction):
                client = interaction.client
                user_id = str(interaction.user.id)

                if not hasattr(client, "taixiu_data") or user_id not in client.taixiu_data:
                    return await interaction.response.send_message("⚠️ Bạn chưa đặt cược.", ephemeral=True)

                bets = client.taixiu_data[user_id]
                dice = [random.randint(1, 6) for _ in range(3)]
                total = sum(dice)
                result_text = f"🎲 Kết quả: {dice} → Tổng: **{total}**\n"

                win_total = 0
                lose_total = 0
                pet_bonus_total = 0

                for bet in bets:
                    amount = bet["amount"]
                    if bet["min_sum"] <= total <= bet["max_sum"]:
                        bonus = get_pet_bonus(user_id, amount)
                        win_total += amount + bonus
                        pet_bonus_total += bonus
                        result_text += f"✅ Thắng cược {bet['choice']} (+{amount:,} xu, bonus {bonus:,})\n"
                    else:
                        lose_total += amount
                        result_text += f"❌ Thua cược {bet['choice']} (-{amount:,} xu)\n"

                net = win_total - lose_total
                update_balance(user_id, net)
                log_history(user_id, "Tài Xỉu", net)

                result_text += f"\n📌 Tổng lời/lỗ: {'+' if net >= 0 else ''}{net:,} xu"
                if pet_bonus_total > 0:
                    result_text += f"\n🐾 Pet bonus cộng thêm: {pet_bonus_total:,} xu"

                # Xoá dữ liệu
                del client.taixiu_data[user_id]

                # Khoá menu toàn server 30 giây
                global menu_lock_time
                menu_lock_time = datetime.now() + timedelta(seconds=30)

                # Vô hiệu hoá nút
                for child in self.view.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                await interaction.response.edit_message(content=result_text, view=self.view)

async def setup(bot):
    pass  # View-only cog, no commands to register