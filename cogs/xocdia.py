import discord
import random
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, write_json
from datetime import datetime

# File dữ liệu
BALANCE_FILE = "data/sodu.json"
HISTORY_FILE = "data/lichsu.json"

# Hàm ghi lịch sử
def add_history(user_id: int, username: str, action: str, amount: int, balance_after: int):
    hist = read_json(HISTORY_FILE)
    hist.append({
        "user_id": user_id,
        "username": username,
        "action": action,
        "amount": amount,
        "balance_after": balance_after,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    write_json(HISTORY_FILE, hist)

# Hàm tung 4 đồng xu
def tung_xoc_dia():
    result = [random.choice(["Đỏ", "Trắng"]) for _ in range(4)]
    return result

# Giao diện chọn cửa
class CuocView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.selected = []

        options = [
            discord.SelectOption(label="4 Đỏ", description="Tỷ lệ 1:12"),
            discord.SelectOption(label="4 Trắng", description="Tỷ lệ 1:12"),
            discord.SelectOption(label="3 Trắng 1 Đỏ", description="Tỷ lệ 1:2.6"),
            discord.SelectOption(label="3 Đỏ 1 Trắng", description="Tỷ lệ 1:2.6"),
            discord.SelectOption(label="Chẵn", description="2 Đỏ 2 Trắng (1:0.9)"),
            discord.SelectOption(label="Lẻ", description="3-1 hoặc 1-3 (1:0.9)")
        ]

        self.select = discord.ui.Select(
            placeholder="Chọn ít nhất 1 cửa",
            min_values=1,
            max_values=len(options),
            options=options
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

        self.confirm = discord.ui.Button(label="Chọn xong", style=discord.ButtonStyle.green)
        self.confirm.callback = self.confirm_callback
        self.add_item(self.confirm)

    async def select_callback(self, interaction: discord.Interaction):
        self.selected = self.select.values

    async def confirm_callback(self, interaction: discord.Interaction):
        self.stop()

# Giao diện nhập số tiền cược
class TienCuocModal(discord.ui.Modal, title="💰 Nhập số xu muốn cược"):
    def __init__(self, selected_choices, callback):
        super().__init__()
        self.selected_choices = selected_choices
        self.callback_function = callback

        self.tiencuoc = discord.ui.TextInput(
            label="Nhập số xu cược cho mỗi cửa",
            placeholder="Ví dụ: 10000",
            required=True
        )
        self.add_item(self.tiencuoc)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback_function(interaction, self.selected_choices, int(self.tiencuoc.value))

# Lệnh slash chính
class XocDia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="xocdia", description="🎲 Chơi Xóc Đĩa (chọn nhiều cửa)")
    async def xocdia(self, interaction: discord.Interaction):
        sodu = read_json(BALANCE_FILE)
        user_id = str(interaction.user.id)

        if user_id not in sodu or sodu[user_id] <= 0:
            await interaction.response.send_message("❌ Bạn không có đủ xu để chơi.", ephemeral=True)
            return

        view = CuocView()
        await interaction.response.send_message("🔘 Chọn các cửa muốn cược:", view=view, ephemeral=True)
        await view.wait()

        if not view.selected:
            await interaction.followup.send("❌ Bạn chưa chọn cửa nào!", ephemeral=True)
            return

        # Sau khi chọn xong cửa -> hiện modal nhập tiền cược
        await interaction.followup.send_modal(
            TienCuocModal(view.selected, self.process_game)
        )

    # Xử lý kết quả sau khi nhập tiền
    async def process_game(self, interaction: discord.Interaction, choices, amount: int):
        user = interaction.user
        user_id = str(user.id)
        sodu = read_json(BALANCE_FILE)

        total_bet = amount * len(choices)
        if user_id not in sodu or sodu[user_id] < total_bet:
            await interaction.response.send_message("❌ Bạn không đủ xu để đặt cược!", ephemeral=True)
            return

        result = tung_xoc_dia()
        count_do = result.count("Đỏ")
        count_trang = result.count("Trắng")

        # Xác định kết quả thắng
        ketqua = []
        if count_do == 4:
            ketqua.append("4 Đỏ")
        elif count_trang == 4:
            ketqua.append("4 Trắng")
        elif count_trang == 3:
            ketqua.append("3 Trắng 1 Đỏ")
        elif count_do == 3:
            ketqua.append("3 Đỏ 1 Trắng")

        if count_do % 2 == 0:
            ketqua.append("Chẵn")
        else:
            ketqua.append("Lẻ")

        # Tính tiền thưởng
        thuong = 0
        for choice in choices:
            if choice in ketqua:
                if choice in ["4 Đỏ", "4 Trắng"]:
                    thuong += amount * 12
                elif choice in ["3 Trắng 1 Đỏ", "3 Đỏ 1 Trắng"]:
                    thuong += amount * 2.6
                elif choice in ["Chẵn", "Lẻ"]:
                    thuong += amount * 0.9

        # Trừ tiền, cộng thưởng
        sodu[user_id] -= total_bet
        sodu[user_id] += int(thuong)
        write_json(BALANCE_FILE, sodu)

        # Ghi lịch sử
        add_history(user.id, user.name, "Xóc Đĩa", total_bet, sodu[user_id])

        # Gửi kết quả
        desc = f"🎯 Kết quả: {' | '.join(result)} ({count_do} Đỏ - {count_trang} Trắng)\n"
        desc += f"🧾 Bạn đã chọn: {', '.join(choices)}\n"
        desc += f"💸 Tổng cược: {total_bet:,} xu\n"
        desc += f"🏆 Thắng: {int(thuong):,} xu\n"
        desc += f"💰 Số dư: {sodu[user_id]:,} xu"

        embed = discord.Embed(title="🎲 Kết quả Xóc Đĩa", description=desc, color=0x3498db)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(XocDia(bot))