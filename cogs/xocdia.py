
import discord
import random
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, write_json
from datetime import datetime
import asyncio

# File dữ liệu
BALANCE_FILE = "data/sodu.json"
HISTORY_FILE = "data/lichsu.json"
SESSION_FILE = "data/xocdia_session.json"

# Các cửa cược
CACH_CUA = ["4 Đỏ", "4 Trắng", "3 Đỏ 1 Trắng", "3 Trắng 1 Đỏ", "Chẵn", "Lẻ"]

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

class BetModal(discord.ui.Modal):
    def __init__(self, choice):
        super().__init__(title=f"Cược {choice}")
        self.choice = choice
        self.amount = discord.ui.TextInput(
            label="Số xu cược", 
            placeholder="Nhập số xu", 
            required=True,
            max_length=18
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount.value)
        except ValueError:
            await interaction.response.send_message("❌ Vui lòng nhập số hợp lệ!", ephemeral=True)
            return

        if amount < 1000:
            await interaction.response.send_message("❌ Số xu cược tối thiểu là 1,000!", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        balances = read_json(BALANCE_FILE)
        
        if user_id not in balances or balances[user_id] < amount:
            await interaction.response.send_message("❌ Bạn không đủ xu để đặt cược!", ephemeral=True)
            return

        # Kiểm tra session còn hoạt động không
        session_data = read_json(SESSION_FILE)
        if not session_data.get("active", False):
            await interaction.response.send_message("❌ Phiên cược đã kết thúc!", ephemeral=True)
            return

        # Kiểm tra mâu thuẫn cược
        user_bets = session_data["bets"].get(user_id, {})
        
        # Kiểm tra mâu thuẫn 4 Đỏ vs 4 Trắng
        if self.choice == "4 Đỏ" and "4 Trắng" in user_bets:
            await interaction.response.send_message("❌ Bạn đã cược 4 Trắng, không thể cược 4 Đỏ!", ephemeral=True)
            return
        if self.choice == "4 Trắng" and "4 Đỏ" in user_bets:
            await interaction.response.send_message("❌ Bạn đã cược 4 Đỏ, không thể cược 4 Trắng!", ephemeral=True)
            return
        
        # Kiểm tra mâu thuẫn Chẵn vs Lẻ
        if self.choice == "Chẵn" and "Lẻ" in user_bets:
            await interaction.response.send_message("❌ Bạn đã cược Lẻ, không thể cược Chẵn!", ephemeral=True)
            return
        if self.choice == "Lẻ" and "Chẵn" in user_bets:
            await interaction.response.send_message("❌ Bạn đã cược Chẵn, không thể cược Lẻ!", ephemeral=True)
            return

        # Trừ xu
        balances[user_id] -= amount
        write_json(BALANCE_FILE, balances)

        # Lưu cược vào session
        if user_id not in session_data["bets"]:
            session_data["bets"][user_id] = {}
        
        session_data["bets"][user_id][self.choice] = session_data["bets"][user_id].get(self.choice, 0) + amount
        write_json(SESSION_FILE, session_data)

        await interaction.response.send_message(
            f"✅ Đã cược **{amount:,} xu** vào **{self.choice}**!\n💰 Số dư còn lại: **{balances[user_id]:,} xu**", 
            ephemeral=True
        )

class CuaButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(label=label, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BetModal(self.label))

class XocDiaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.msg = None
        for label in CACH_CUA:
            self.add_item(CuaButton(label))

    async def on_timeout(self):
        if self.msg:
            await ket_thuc_phien(self.msg.channel)

async def ket_thuc_phien(channel):
    session_data = read_json(SESSION_FILE)
    if not session_data.get("active", False):
        return

    # Đánh dấu session kết thúc
    session_data["active"] = False
    write_json(SESSION_FILE, session_data)

    if not session_data.get("bets"):
        await channel.send("🎲 Phiên Xóc Đĩa kết thúc! Không có ai cược.")
        return

    # Random kết quả
    result = tung_xoc_dia()
    count_do = result.count("Đỏ")
    count_trang = result.count("Trắng")

    # Xác định cửa thắng
    cua_thang = []
    if count_do == 4:
        cua_thang.append("4 Đỏ")
    elif count_trang == 4:
        cua_thang.append("4 Trắng")
    elif count_do == 3:
        cua_thang.append("3 Đỏ 1 Trắng")
    elif count_trang == 3:
        cua_thang.append("3 Trắng 1 Đỏ")

    if count_do % 2 == 0:
        cua_thang.append("Chẵn")
    else:
        cua_thang.append("Lẻ")

    # Tính thưởng cho từng người
    balances = read_json(BALANCE_FILE)
    emoji_map = {"Đỏ": "🔴", "Trắng": "⚪"}
    ketqua_emoji = ' '.join(emoji_map[i] for i in result)

    embed = discord.Embed(
        title="🎲 Kết quả Xóc Đĩa", 
        description=f"🎯 Kết quả: {ketqua_emoji} ({count_do} Đỏ – {count_trang} Trắng)",
        color=0x3498db
    )

    thuong_info = []
    
    for user_id, user_bets in session_data["bets"].items():
        user = channel.guild.get_member(int(user_id))
        username = user.display_name if user else f"User {user_id}"
        
        tong_cuoc = sum(user_bets.values())
        tong_thuong = 0

        for cua, so_cuoc in user_bets.items():
            if cua in cua_thang:
                if cua in ["4 Đỏ", "4 Trắng"]:
                    tong_thuong += so_cuoc * 12
                elif cua in ["3 Đỏ 1 Trắng", "3 Trắng 1 Đỏ"]:
                    tong_thuong += so_cuoc * 2.6
                elif cua in ["Chẵn", "Lẻ"]:
                    tong_thuong += so_cuoc * 0.9

        # Cộng thưởng vào số dư
        balances[user_id] = balances.get(user_id, 0) + int(tong_thuong)
        
        # Ghi lịch sử
        add_history(int(user_id), username, "Xóc Đĩa", tong_cuoc, balances[user_id])
        
        # Thông tin người chơi
        lai_lo = int(tong_thuong) - tong_cuoc
        status = "🏆" if lai_lo > 0 else "💸" if lai_lo < 0 else "🤝"
        
        thuong_info.append(f"{status} **{username}**: {lai_lo:+,} xu")

    write_json(BALANCE_FILE, balances)

    # Hiển thị kết quả
    if thuong_info:
        embed.add_field(name="📊 Kết quả người chơi", value="\n".join(thuong_info), inline=False)
    else:
        embed.add_field(name="📊 Kết quả", value="Không có ai thắng", inline=False)

    await channel.send(embed=embed)

    # Reset session
    write_json(SESSION_FILE, {"active": False, "bets": {}})

class XocDia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="xocdia", description="Bắt đầu phiên chơi Xóc Đĩa (chơi chung)")
    async def xocdia(self, interaction: discord.Interaction):
        # Kiểm tra phiên hiện tại
        session_data = read_json(SESSION_FILE)
        if session_data.get("active", False):
            await interaction.response.send_message("❌ Đã có phiên Xóc Đĩa đang diễn ra!", ephemeral=True)
            return

        # Tạo phiên mới
        data = {"active": True, "bets": {}}
        write_json(SESSION_FILE, data)
        
        view = XocDiaView()
        await interaction.response.send_message(
            "🎮 Phiên Xóc Đĩa bắt đầu! Chọn cửa bên dưới để cược:",
            view=view
        )
        message = await interaction.original_response()
        view.msg = message  # view.msg sẽ dùng lại để kết thúc phiên

async def setup(bot):
    await bot.add_cog(XocDia(bot))
