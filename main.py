import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import traceback
import sys
import random
from datetime import datetime

from keep_alive import keep_alive  # Giữ bot online trên Replit
from utils import data_manager
from utils.data_manager import get_balance, update_balance, add_history

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 730436357838602301

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

    # --- Global error handler cho slash commands ---
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
        print("🔴 App command error:", "".join(traceback.format_exception(type(error), error, error.__traceback__)))
        try:
            await interaction.response.send_message("❌ Đã có lỗi xảy ra, thử lại sau.", ephemeral=True)
        except:
            pass

    # --- Load tất cả cogs ---
async def load_extensions():
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_ready():
    await load_extensions()
    await bot.tree.sync()
    if bot.user:
        print(f"✅ Bot đã online: {bot.user} (ID: {bot.user.id})")
    else:
        print("⚠️ Bot đã online, nhưng không lấy được thông tin bot.user")

    # --- Sample commands ---
@tree.command(name="ping", description="Kiểm tra trạng thái bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

@tree.command(name="resetdaily", description="Reset /daily cho user (Admin only)")
@app_commands.describe(user="Người dùng cần reset")
async def resetdaily(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
    
    data = data_manager.read_json("data/user_data.json")
    uid = str(user.id)
    if uid in data:
        del data[uid]
        data_manager.write_json("data/user_data.json", data)
        await interaction.response.send_message(f"✅ Đã reset /daily cho {user.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ️ Người này chưa nhận /daily.", ephemeral=True)

    # --- Cooldown stub ---
def can_play(uid):
        return True, 10

    # --- Game: Tài Xỉu ---
async def play_taixiu(interaction: discord.Interaction, amount: int, choice: str):
        uid = interaction.user.id
        ok, wait = can_play(uid)
        if not ok:
            return await interaction.response.send_message(f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True)
        bal = get_balance(uid)
        if amount < 1000 or amount > bal:
            return await interaction.response.send_message("❌ Số xu cược không hợp lệ!", ephemeral=True)

        # Hiệu ứng hồi hộp
        await interaction.response.send_message("🎲 **Đang lắc số phận của bạn...**")
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

        txt = (
            f"🎲 Kết quả: {dice} → {tong} → **{kq.upper()}**\n"
            + ("🎉 Húp thì xin tý!\n" if win else "💸 Đưa đít đây anh bơm thêm!\n")
            + f"💰 Thay đổi: {thaydoi:+,} xu | Số dư mới: {newb:,} xu"
        )
        await interaction.edit_original_response(content=txt)

    # --- Game: Chẵn Lẻ ---
async def play_chanle(interaction: discord.Interaction, amount: int, choice: str):
        uid = interaction.user.id
        ok, wait = can_play(uid)
        if not ok:
            return await interaction.response.send_message(f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True)
        bal = get_balance(uid)
        if amount < 1000 or amount > bal:
            return await interaction.response.send_message("❌ Số xu cược không hợp lệ!", ephemeral=True)

        # Hiệu ứng chờ
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

        msg = (
            f"🕓 Kết quả: {giay} → {so1}+{so2}={tong} → **{kq.upper()}**\n"
            + ("🎉 Ôi bạn thắng gớm!\n" if win else "💸 Eo bạn đần vãi lợn!\n")
            + f"💰 Thay đổi: {thaydoi:+,} xu | Số dư mới: {newb:,} xu"
        )
        await interaction.edit_original_response(content=msg)

    # --- Safe main: tự restart khi crash ---
async def safe_main():
        keep_alive()  # Giữ Flask luôn chạy
        while True:
            try:
                if TOKEN:
                    await bot.start(TOKEN)
                else:
                    print("❌ Thiếu biến môi trường TOKEN")
                    return
            except Exception:
                print("🚨 Bot crashed, restarting in 5s...", file=sys.stderr)
                traceback.print_exc()
                await asyncio.sleep(5)

    # --- Chạy bot ---
if __name__ == "__main__":
        asyncio.run(safe_main())