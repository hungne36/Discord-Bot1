import discord
from discord.ext import commands
from discord import app_commands
import os
from utils import data_manager
import random
import asyncio
from datetime import datetime
from utils.data_manager import get_balance, update_balance, add_history

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 730436357838602301

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

    # Load all cogs
async def load_cogs():
        for cog in ["menu", "info", "nap", "lichsu", "daily", "phucloi", "xocdia", "top"]:
            await bot.load_extension(f"cogs.{cog}")

@bot.event
async def on_ready():
        await load_cogs()
        await tree.sync()
        print(f"✅ Bot đã online: {bot.user}")

    # /ping
@tree.command(name="ping", description="Kiểm tra trạng thái bot")
async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

    # /resetdaily (Admin)
@tree.command(name="resetdaily", description="Reset quà khởi đầu cho người dùng (admin)")
@app_commands.describe(user="Người dùng cần reset")
async def resetdaily(interaction: discord.Interaction, user: discord.User):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
            return

        data = data_manager.read_json("data/user_data.json")
        uid = str(user.id)

        if uid in data:
            del data[uid]
            data_manager.write_json("data/user_data.json", data)
            await interaction.response.send_message(f"✅ Đã reset /daily cho {user.mention}", ephemeral=True)
        else:
            await interaction.response.send_message(f"ℹ️ Người dùng này chưa từng nhận /daily", ephemeral=True)

    # Game functions
def can_play(uid):
    # Simple cooldown implementation - you can enhance this
    return True, 0

async def play_taixiu(interaction: discord.Interaction, amount: int, choice: str):
        uid = interaction.user.id
        ok, wait = can_play(uid)
        if not ok:
            return await interaction.response.send_message(f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True)

        bal = get_balance(uid)
        if amount < 1000 or amount > bal:
            return await interaction.response.send_message("❌ Số xu cược không hợp lệ!", ephemeral=True)

        # Gửi hiệu ứng hồi hộp ban đầu
        await interaction.response.send_message("🎲 **Đang lắc xúc xắc...**")
        await asyncio.sleep(1)

        await interaction.edit_original_response(content="🎲 **Chúc con nghiện 6 3 ra 1...** 🎯")
        await asyncio.sleep(4)

        await interaction.edit_original_response(content="🎲 **Quên nữa, 1 4 ra 6...** ⏳")
        await asyncio.sleep(2)

        dice = [random.randint(1, 6) for _ in range(3)]
        tong = sum(dice)
        kq = "tai" if tong >= 11 else "xiu"
        win = (choice == kq)
        thaydoi = round(amount * 1.97) if win else -amount
        newb = update_balance(uid, thaydoi)
        add_history(uid, f"taixiu_{'thắng' if win else 'thua'}", thaydoi, newb)

        txt = f"🎲 Kết quả: {dice} → {tong} → **{kq.upper()}**\n"
        txt += "🎉 Húp thì xin tý!\n" if win else "💸 Đưa đít đây anh bơm thêm!\n"
        txt += f"💰 Thay đổi: {thaydoi:+,} xu | Số dư mới: {newb:,} xu"

        # Sửa lại tin nhắn đã gửi với kết quả cuối cùng
        await interaction.edit_original_response(content=txt)

async def play_chanle(interaction: discord.Interaction, amount: int, choice: str):
        uid = interaction.user.id
        ok, wait = can_play(uid)
        if not ok:
            return await interaction.response.send_message(f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True)

        bal = get_balance(uid)
        if amount < 1000 or amount > bal:
            return await interaction.response.send_message("❌ Số xu cược không hợp lệ!", ephemeral=True)

        # Gửi hiệu ứng chờ
        await interaction.response.send_message("🕓 **Đếm ngược thôi nào...**")
        await asyncio.sleep(5)

        await interaction.edit_original_response(content="🕓 **Ra liền đừng có hối...** ⏰")
        await asyncio.sleep(3)

        await interaction.edit_original_response(content="🕓 **Ra rồi nè...** ⏳")
        await asyncio.sleep(1)

        giay = datetime.utcnow().second
        so1, so2 = divmod(giay, 10)
        tong = so1 + so2
        kq = "chan" if tong % 2 == 0 else "le"
        win = (choice == kq)
        thaydoi = round(amount * 1.95) if win else -amount
        newb = update_balance(uid, thaydoi)
        add_history(uid, f"chanle_{'thắng' if win else 'thua'}", thaydoi, newb)

        msg = f"🕓 Kết quả: {giay} → {so1}+{so2}={tong} → **{kq.upper()}**\n"
        msg += "🎉 Ôi bạn thắng gớm!\n" if win else "💸 Eo bạn đần vãi lợn!\n"
        msg += f"💰 Thay đổi: {thaydoi:+,} xu | Số dư mới: {newb:,} xu"

        await interaction.edit_original_response(content=msg)

    # Run bot
if __name__ == "__main__":
        if TOKEN:
            bot.run(TOKEN)
        else:
            print("❌ Thiếu biến môi trường TOKEN")