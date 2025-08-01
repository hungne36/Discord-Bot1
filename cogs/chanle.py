import discord
from discord.ext import commands
from utils.data_manager import read_json, write_json
from datetime import datetime, timedelta
import random
from main import menu_lock_time
from utils.pet_bonus import get_pet_bonus_multiplier  # ← Pet bonus

    # Dữ liệu cược theo kênh
chanle_bets = {}

    # Giao diện chọn cược chẵn/lẻ
class ChanLeSelectView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(ChanLeButton("Chẵn"))
            self.add_item(ChanLeButton("Lẻ"))
            self.add_item(KetThucButton("chanle"))

class ChanLeButton(discord.ui.Button):
        def __init__(self, label):
            super().__init__(label=label, style=discord.ButtonStyle.primary, custom_id=f"chanle_{label}")

        async def callback(self, interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            channel_id = str(interaction.channel.id)

            await interaction.response.send_modal(BetModal(self.label, user_id, channel_id))

    # Modal nhập tiền cược
class BetModal(discord.ui.Modal, title="Nhập số tiền cược"):
        def __init__(self, choice, user_id, channel_id):
            super().__init__()
            self.choice = choice
            self.user_id = user_id
            self.channel_id = channel_id

            self.add_item(discord.ui.TextInput(label="Nhập số tiền", placeholder="VD: 1000000", custom_id="bet_amount"))

        async def on_submit(self, interaction: discord.Interaction):
            try:
                amount = int(self.children[0].value)
            except ValueError:
                await interaction.response.send_message("❌ Số tiền không hợp lệ.", ephemeral=True)
                return

            if amount <= 0:
                await interaction.response.send_message("❌ Số tiền phải lớn hơn 0.", ephemeral=True)
                return

            # Trừ tiền
            balances = read_json("data/sodu.json")
            user_balance = balances.get(self.user_id, 0)

            if user_balance < amount:
                await interaction.response.send_message("❌ Bạn không đủ tiền.", ephemeral=True)
                return

            balances[self.user_id] = user_balance - amount
            write_json("data/sodu.json", balances)

            # Lưu cược
            if self.channel_id not in chanle_bets:
                chanle_bets[self.channel_id] = []

            chanle_bets[self.channel_id].append({
                "user_id": self.user_id,
                "choice": self.choice,
                "amount": amount
            })

            await interaction.response.send_message(f"✅ Bạn đã cược **{self.choice}** với **{amount:,} xu**.", ephemeral=True)

    # Nút kết thúc trò chơi
class KetThucButton(discord.ui.Button):
        def __init__(self, game_type):
            super().__init__(label="🎯 Kết thúc trò chơi", style=discord.ButtonStyle.danger, custom_id=f"{game_type}_end")
            self.game_type = game_type

        async def callback(self, interaction: discord.Interaction):
            channel_id = str(interaction.channel.id)

            # Lấy danh sách cược
            bets = chanle_bets.get(channel_id, [])
            if not bets:
                await interaction.response.send_message("⚠️ Không có ai đặt cược.", ephemeral=True)
                return

            # Random kết quả
            result_number = random.randint(1, 100)
            result = "Chẵn" if result_number % 2 == 0 else "Lẻ"

            # Load số dư
            balances = read_json("data/sodu.json")

            # Xử lý trả thưởng
            msg_lines = [f"🎯 Kết quả: **{result_number} ({result})**"]
            for bet in bets:
                user_id = bet["user_id"]
                choice = bet["choice"]
                amount = bet["amount"]

                if choice == result:
                    pet_bonus = get_pet_bonus_multiplier(user_id)
                    reward = int(amount * (1 + pet_bonus)) * 2
                    balances[user_id] = balances.get(user_id, 0) + reward
                    msg_lines.append(f"<@{user_id}> ✅ Thắng! +{reward:,} xu (x{1 + pet_bonus:.2f} pet)")
                else:
                    msg_lines.append(f"<@{user_id}> ❌ Thua cược.")

            # Lưu lại số dư
            write_json("data/sodu.json", balances)

            # Xoá lượt cược
            chanle_bets[channel_id] = []

            # Khoá menu 30s
            global menu_lock_time
            menu_lock_time = datetime.now() + timedelta(seconds=30)

            # Đóng view
            await interaction.response.edit_message(content="\n".join(msg_lines), view=None)



    # Setup cog
async def setup(bot):
        pass  # Không cần add_cog nếu chỉ gọi view từ nơi khác