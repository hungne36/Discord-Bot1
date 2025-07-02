
# main.py
import os
import sys
import asyncio
import traceback

import discord
from discord.ext import commands
from discord import app_commands

from keep_alive import keep_alive  # Giữ bot online qua Flask

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 730436357838602301  # Thay bằng ID admin của bạn

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# —————————————————————————————————————————
# Global error handler cho slash commands
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    print("🔴 App command error:", "".join(traceback.format_exception(type(error), error, error.__traceback__)))
    try:
        await interaction.response.send_message("❌ Đã có lỗi xảy ra, thử lại sau.", ephemeral=True)
    except:
        pass

# —————————————————————————————————————————
# Load tất cả cogs trong thư mục cogs/
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")

# —————————————————————————————————————————
@bot.event
async def on_ready():
    await load_extensions()
    try:
        synced = await tree.sync()  # sync global commands
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync commands failed: {e}")

    if bot.user:
        print(f"✅ Bot online as {bot.user} (ID: {bot.user.id})")
    else:
        print("⚠️ Bot online but bot.user is None")

# —————————————————————————————————————————
# /ping
@tree.command(name="ping", description="Kiểm tra trạng thái bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

# —————————————————————————————————————————
# /resetdaily (admin only)
@tree.command(name="resetdaily", description="Reset /daily cho user (Admin only)")
@app_commands.describe(user="Người dùng cần reset")
async def resetdaily(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)

    from utils.data_manager import read_json, write_json

    data = read_json("data/user_data.json")
    uid = str(user.id)
    if uid in data:
        del data[uid]
        write_json("data/user_data.json", data)
        await interaction.response.send_message(f"✅ Đã reset /daily cho {user.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ️ Người này chưa nhận /daily.", ephemeral=True)

# —————————————————————————————————————————
# /sync (admin only)
@tree.command(name="sync", description="Đồng bộ slash commands (Admin only)")
async def sync(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
    try:
        synced = await tree.sync(guild=interaction.guild)
        await interaction.response.send_message(f"✅ Đã đồng bộ {len(synced)} lệnh cho server này.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message("❌ Lỗi khi đồng bộ lệnh!", ephemeral=True)
        print(f"Sync error: {e}")

# —————————————————————————————————————————
# Safe main: tự restart khi crash
async def safe_main():
    keep_alive()  # Khởi chạy Flask server giữ bot online
    while True:
        try:
            if not TOKEN:
                print("❌ Thiếu biến môi trường TOKEN")
                return
            await bot.start(TOKEN)
        except Exception:
            print("🚨 Bot crashed, restarting in 5s...", file=sys.stderr)
            traceback.print_exc()
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(safe_main())
