import discord
from discord.ext import commands
from discord import app_commands
import random
from utils.data_manager import update_balance, add_history, get_balance, get_pet_buff

CACH_CUA = ["4 Đỏ", "4 Trắng", "3 Trắng 1 Đỏ", "3 Đỏ 1 Trắng", "Chẵn", "Lẻ"]

active_sessions = {}

class CuaButton(discord.ui.Button):
        def __init__(self, cach_cua):
            super().__init__(label=cach_cua, style=discord.ButtonStyle.primary)
            self.cach_cua = cach_cua

        async def callback(self, interaction: discord.Interaction):
            if interaction.channel.id not in active_sessions:
                await interaction.response.send_message("❌ Không có phiên Xóc Đĩa nào đang diễn ra!", ephemeral=True)
                return
            session = active_sessions[interaction.channel.id]
            if interaction.user.id in session["cuoc"]:
                await interaction.response.send_message("❌ Bạn đã đặt cược rồi!", ephemeral=True)
                return

            await interaction.response.send_modal(CuocModal(self.cach_cua))

class CuocModal(discord.ui.Modal, title="💰 Nhập số tiền cược"):
        def __init__(self, cach_cua):
            super().__init__()
            self.cach_cua = cach_cua

        tien_cuoc = discord.ui.TextInput(label="Nhập số tiền bạn muốn cược", style=discord.TextStyle.short)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                tien = int(self.tien_cuoc.value)
                if tien <= 0:
                    raise ValueError
            except ValueError:
                await interaction.response.send_message("❌ Số tiền cược không hợp lệ!", ephemeral=True)
                return

            balance = get_balance(interaction.user.id)
            if tien > balance:
                await interaction.response.send_message("❌ Bạn không đủ xu để cược số tiền này!", ephemeral=True)
                return

            session = active_sessions.get(interaction.channel.id)
            if not session:
                await interaction.response.send_message("❌ Phiên chơi đã kết thúc!", ephemeral=True)
                return

            session["cuoc"][interaction.user.id] = {
                "username": get_username(interaction.user),
                "cach": self.cach_cua,
                "tien": tien
            }
            update_today_spent(interaction.user.id, tien)
            update_balance(interaction.user.id, -tien)
            await interaction.response.send_message(f"✅ Bạn đã cược `{tien:,}` xu vào **{self.cach_cua}**!", ephemeral=True)

class StartButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="🎲 Kết thúc & Xóc", style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            if interaction.channel.id not in active_sessions:
                await interaction.response.send_message("❌ Không có phiên nào đang diễn ra!", ephemeral=True)
                return
            session = active_sessions[interaction.channel.id]
            if interaction.user.id != session["host"]:
                await interaction.response.send_message("❌ Chỉ người mở phiên mới được kết thúc!", ephemeral=True)
                return

            ket_qua = random.choices(["Đỏ", "Trắng"], k=4)
            so_do = ket_qua.count("Đỏ")
            so_trang = 4 - so_do
            text_ketqua = f"{so_do} Đỏ {so_trang} Trắng"
            chanle = "Chẵn" if so_do % 2 == 0 else "Lẻ"

            ket_qua_cuoi = {
                "4 Đỏ": so_do == 4,
                "4 Trắng": so_trang == 4,
                "3 Trắng 1 Đỏ": so_trang == 3,
                "3 Đỏ 1 Trắng": so_do == 3,
                "Chẵn": chanle == "Chẵn",
                "Lẻ": chanle == "Lẻ"
            }

            text = f"🎯 Kết quả: **{text_ketqua}** → **{chanle}**\n\n"

            for uid, thongtin in session["cuoc"].items():
                win = ket_qua_cuoi.get(thongtin["cach"], False)
                pet_bonus = get_pet_bonus_percent(uid)
                if win:
                    base_win = thongtin["tien"] * 2
                    total_win = int(base_win * (1 + pet_bonus / 100))
                    new_balance = update_balance(uid, total_win)
                    add_history(uid, "xocdia_win", total_win, new_balance)
                    text += f"✅ <@{uid}> thắng {thongtin['tien']:,} → nhận {total_win:,} (buff pet +{pet_bonus}%)\n"
                else:
                    balance = get_balance(uid)
                    add_history(uid, "xocdia_lose", -thongtin["tien"], balance)
                    text += f"❌ <@{uid}> thua {thongtin['tien']:,}\n"

            await session["view"].msg.edit(content=text, view=None)
            del active_sessions[interaction.channel.id]

class XocDiaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)  # ✅ Không timeout nữa
            self.msg = None
            for c in CACH_CUA:
                self.add_item(CuaButton(c))
            self.add_item(StartButton())

        async def on_timeout(self):  # Không làm gì cả
            pass

async def start_xocdia_game(interaction: discord.Interaction):
        if interaction.channel.id in active_sessions:
            await interaction.response.send_message("❌ Đã có phiên Xóc Đĩa đang diễn ra!", ephemeral=True)
            return

        view = XocDiaView()
        msg = await interaction.channel.send("🎮 **Phiên Xóc Đĩa đã mở!**\nẤn vào lựa chọn bên dưới để đặt cược:", view=view)
        view.msg = msg
        active_sessions[interaction.channel.id] = {
            "host": interaction.user.id,
            "cuoc": {},
            "view": view
        }
        await interaction.response.send_message("✅ Phiên Xóc Đĩa đã bắt đầu!", ephemeral=True)

class XocDia(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="xocdia", description="Mở một phiên Xóc Đĩa cho mọi người cùng chơi")
        async def xocdia(self, interaction: discord.Interaction):
            await start_xocdia_game(interaction)

async def setup(bot):
        await bot.add_cog(XocDia(bot))
