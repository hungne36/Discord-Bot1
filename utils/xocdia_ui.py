import discord
import random
from discord import Interaction
from utils.data_manager import read_json, write_json
from datetime import datetime

BALANCE_FILE = "data/sodu.json"
HISTORY_FILE = "data/lichsu.json"

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

def tung_xoc_dia():
    return [random.choice(["Đỏ", "Trắng"]) for _ in range(4)]

class TienCuocModal(discord.ui.Modal, title="💰 Nhập số xu cược"):
    def __init__(self, selected_choices, user_id, callback):
        super().__init__()
        self.selected_choices = selected_choices
        self.user_id = user_id
        self.callback = callback

        self.amount = discord.ui.TextInput(
            label="Số xu cược mỗi cửa",
            placeholder="Ví dụ: 10000",
            required=True
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: Interaction):
        await self.callback(interaction, self.selected_choices, int(self.amount.value))

class CuocView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=60)
        self.user = user
        self.selected = []

        self.select = discord.ui.Select(
            placeholder="Chọn ít nhất 1 cửa",
            min_values=1,
            max_values=6,
            options=[
                discord.SelectOption(label="4 Đỏ", description="Tỷ lệ 1:12"),
                discord.SelectOption(label="4 Trắng", description="Tỷ lệ 1:12"),
                discord.SelectOption(label="3 Trắng 1 Đỏ", description="Tỷ lệ 1:2.6"),
                discord.SelectOption(label="3 Đỏ 1 Trắng", description="Tỷ lệ 1:2.6"),
                discord.SelectOption(label="Chẵn", description="2 Đỏ 2 Trắng (1:0.9)"),
                discord.SelectOption(label="Lẻ", description="3-1 hoặc 1-3 (1:0.9)")
            ]
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)

        self.confirm = discord.ui.Button(label="Tiếp tục", style=discord.ButtonStyle.green)
        self.confirm.callback = self.confirm_callback
        self.add_item(self.confirm)

    async def select_callback(self, interaction: Interaction):
        self.selected = self.select.values
        await interaction.response.defer()  # tránh lỗi tương tác hết hạn

    async def confirm_callback(self, interaction: Interaction):
        if not self.selected:
            await interaction.response.send_message("❌ Bạn chưa chọn cửa nào!", ephemeral=True)
            return
        await interaction.response.send_modal(
            TienCuocModal(self.selected, self.user.id, process_game)
        )

async def process_game(interaction: Interaction, choices, amount: int):
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

    thuong = 0
    for choice in choices:
        if choice in ketqua:
            if choice in ["4 Đỏ", "4 Trắng"]:
                thuong += amount * 12
            elif choice in ["3 Trắng 1 Đỏ", "3 Đỏ 1 Trắng"]:
                thuong += amount * 2.6
            elif choice in ["Chẵn", "Lẻ"]:
                thuong += amount * 0.9

    sodu[user_id] -= total_bet
    sodu[user_id] += int(thuong)
    write_json(BALANCE_FILE, sodu)

    add_history(user.id, user.name, "Xóc Đĩa", total_bet, sodu[user_id])

    desc = f"🎯 Kết quả: {' | '.join(result)} ({count_do} Đỏ - {count_trang} Trắng)\n"
    desc += f"🧾 Bạn đã chọn: {', '.join(choices)}\n"
    desc += f"💸 Tổng cược: {total_bet:,} xu\n"
    desc += f"🏆 Thắng: {int(thuong):,} xu\n"
    desc += f"💰 Số dư: {sodu[user_id]:,} xu"

    embed = discord.Embed(title="🎲 Kết quả Xóc Đĩa", description=desc, color=0x3498db)
    await interaction.response.send_message(embed=embed)