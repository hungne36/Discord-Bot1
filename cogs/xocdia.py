import discord
import random
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, write_json, add_history
from datetime import datetime

BALANCE_FILE = "data/sodu.json"
HISTORY_FILE = "data/lichsu.json"
SESSION_FILE = "data/xocdia_session.json"
PETS_FILE = "data/pets.json"

CACH_CUA = ["4 Đỏ", "4 Trắng", "3 Đỏ 1 Trắng", "3 Trắng 1 Đỏ", "Chẵn", "Lẻ"]

def tung_xoc_dia():
    return [random.choice(["Đỏ", "Trắng"]) for _ in range(4)]

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
            return await interaction.response.send_message("❌ Vui lòng nhập số hợp lệ!", ephemeral=True)
        if amount < 1000:
            return await interaction.response.send_message("❌ Tối thiểu 1,000 xu!", ephemeral=True)

        user_id = str(interaction.user.id)
        balances = read_json(BALANCE_FILE)
        if user_id not in balances or balances[user_id] < amount:
            return await interaction.response.send_message("❌ Bạn không đủ xu!", ephemeral=True)

        session = read_json(SESSION_FILE)
        if not session.get("active", False):
            return await interaction.response.send_message("❌ Phiên đã kết thúc!", ephemeral=True)

        user_bets = session["bets"].get(user_id, {})

        if self.choice in ["4 Đỏ", "4 Trắng"] and ("4 Trắng" if self.choice == "4 Đỏ" else "4 Đỏ") in user_bets:
            return await interaction.response.send_message("❌ Cược mâu thuẫn với cửa đối lập!", ephemeral=True)
        if self.choice in ["Chẵn", "Lẻ"] and ("Lẻ" if self.choice == "Chẵn" else "Chẵn") in user_bets:
            return await interaction.response.send_message("❌ Cược mâu thuẫn với cửa đối lập!", ephemeral=True)

        balances[user_id] -= amount
        write_json(BALANCE_FILE, balances)

        session["bets"].setdefault(user_id, {})
        session["bets"][user_id][self.choice] = session["bets"][user_id].get(self.choice, 0) + amount
        write_json(SESSION_FILE, session)

        total_bet = sum(session["bets"][user_id].values())
        await interaction.channel.send(
            f"📥 {interaction.user.mention} đã cược **{amount:,} xu** vào **{self.choice}** lúc `{datetime.now().strftime('%H:%M:%S')}`"
        )
        await interaction.response.send_message(
            f"✅ Cược thành công!\n💰 Tổng đã cược: **{total_bet:,} xu**\n💼 Số dư: **{balances[user_id]:,} xu**",
            ephemeral=True
        )

class CuaButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(label=label, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(BetModal(self.label))

class StartButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔒 Bắt đầu chơi", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        session = read_json(SESSION_FILE)
        if str(interaction.user.id) != session.get("host_id"):
            return await interaction.response.send_message("❌ Chỉ chủ phòng được bắt đầu chơi!", ephemeral=True)
        await ket_thuc_phien(interaction.channel, self.view.msg)

class XocDiaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.msg = None
        for label in CACH_CUA:
            self.add_item(CuaButton(label))
        self.add_item(StartButton())

    async def on_timeout(self):
        if self.msg:
            await ket_thuc_phien(self.msg.channel, self.msg)

async def ket_thuc_phien(channel, original_message=None):
    session = read_json(SESSION_FILE)
    if not session.get("active", False):
        return

    session["active"] = False
    write_json(SESSION_FILE, session)

    if not session.get("bets"):
        await channel.send("🎲 Phiên kết thúc! Không ai đặt cược.")
        if original_message:
            try: await original_message.delete()
            except: pass
        return

    result = tung_xoc_dia()
    do = result.count("Đỏ")
    trang = result.count("Trắng")

    cua_thang = []
    if do == 4: cua_thang.append("4 Đỏ")
    elif trang == 4: cua_thang.append("4 Trắng")
    elif do == 3: cua_thang.append("3 Đỏ 1 Trắng")
    elif trang == 3: cua_thang.append("3 Trắng 1 Đỏ")
    cua_thang.append("Chẵn" if do % 2 == 0 else "Lẻ")

    balances = read_json(BALANCE_FILE)
    emoji_map = {"Đỏ": "🔴", "Trắng": "⚪"}
    ketqua = ' '.join(emoji_map[i] for i in result)

    embed = discord.Embed(
        title="🎲 Kết quả Xóc Đĩa", 
        description=f"🎯 {ketqua} ({do} Đỏ – {trang} Trắng)",
        color=0x3498db
    )

    thuong_info = []
    tong_cuoc_map = {}

    for user_id, user_bets in session["bets"].items():
        user = channel.guild.get_member(int(user_id))
        name = user.mention if user else f"User {user_id}"
        tong_cuoc = sum(user_bets.values())
        tong_thuong = 0

        for cua, tien in user_bets.items():
            if cua in cua_thang:
                if cua in ["4 Đỏ", "4 Trắng"]:
                    tong_thuong += tien + round(tien * 11)  # 11x profit
                elif cua in ["3 Đỏ 1 Trắng", "3 Trắng 1 Đỏ"]:
                    tong_thuong += tien + round(tien * 1.6)  # 1.6x profit
                elif cua in ["Chẵn", "Lẻ"]:
                    tong_thuong += tien + round(tien * -0.1)  # -0.1x profit (house edge)
            else:
                tong_thuong += -tien  # Loss

        # Apply pet buff if player won
        if tong_thuong > 0:  # Player won something
            from utils.data_manager import get_pet_buff
            buff_pct = get_pet_buff(int(user_id))
            if buff_pct > 0:
                profit = tong_thuong - tong_cuoc  # Calculate net profit
                if profit > 0:
                    bonus = round(profit * buff_pct / 100)
                    tong_thuong += bonus

        lai_lo = int(tong_thuong)
        balances[user_id] = balances.get(user_id, 0) + int(tong_thuong)
        add_history(int(user_id), "Xóc Đĩa", lai_lo, balances[user_id], name)
        tong_cuoc_map[name] = tong_cuoc
        icon = "🏆" if lai_lo > 0 else "💸" if lai_lo < 0 else "🤝"
        thuong_info.append(f"{icon} {name}: {lai_lo:+,} xu")

    write_json(BALANCE_FILE, balances)

    embed.add_field(name="📊 Kết quả người chơi", value="\n".join(thuong_info), inline=False)

    if tong_cuoc_map:
        tong_txt = "\n".join(f"{k}: {v:,} xu" for k, v in tong_cuoc_map.items())
        embed.add_field(name="📊 Tổng cược", value=tong_txt, inline=False)

    await channel.send(embed=embed)
    if original_message:
        try: await original_message.delete()
        except: pass
    write_json(SESSION_FILE, {"active": False, "bets": {}, "host_id": None})

class XocDia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="xocdia", description="Bắt đầu phiên Xóc Đĩa chơi chung")
    async def xocdia(self, interaction: discord.Interaction):
        session = {"active": True, "bets": {}, "host_id": str(interaction.user.id)}
        write_json(SESSION_FILE, session)

        view = XocDiaView()
        await interaction.response.send_message(
            f"🎮 **{interaction.user.mention}** đã mở phiên Xóc Đĩa! Chọn cửa để cược:",
            view=view
        )
        msg = await interaction.original_response()
        view.msg = msg

async def setup(bot):
    await bot.add_cog(XocDia(bot))
