import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import traceback
import sys
import random
from datetime import datetime

from keep_alive import keep_alive
from utils import data_manager
from utils.data_manager import get_balance, update_balance, add_history, read_json
from utils.cooldown import can_play

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 730436357838602301
PETS_FILE = "data/pets.json"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

    # —————————————————————————
    # Global error handler cho slash command
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
        print("🔴 App command error:", "".join(traceback.format_exception(type(error), error, error.__traceback__)))
        try:
            await interaction.response.send_message("❌ Đã có lỗi xảy ra, thử lại sau.", ephemeral=True)
        except:
            pass

    # —————————————————————————
    # Load tất cả cogs
async def load_extensions():
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print(f"✅ Loaded cog: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

    # —————————————————————————
@bot.event
async def on_ready():
        await load_extensions()
        try:
            synced = await tree.sync(guild=None)  # Toàn bộ global (có thể sửa lại thành `guild=interaction.guild` nếu cần)
            print(f"✅ Synced {len(synced)} commands")
        except Exception as e:
            print(f"❌ Sync commands failed: {e}")

        if bot.user:
            print(f"✅ Bot online as {bot.user} (ID: {bot.user.id})")
        else:
            print("⚠️ Bot online but bot.user is None")

    # —————————————————————————
@tree.command(name="ping", description="Kiểm tra trạng thái bot")
async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

    # —————————————————————————
@tree.command(name="resetdaily", description="Reset /daily cho user (Admin only)")
@app_commands.describe(user="Người dùng cần reset")
async def resetdaily(interaction: discord.Interaction, user: discord.User):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Không có quyền!", ephemeral=True)

        data = data_manager.read_json("data/user_data.json")
        uid = str(user.id)
        if uid in data:
            del data[uid]
            data_manager.write_json("data/user_data.json", data)
            await interaction.response.send_message(f"✅ Đã reset /daily cho {user.mention}", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ Người này chưa nhận /daily.", ephemeral=True)

    # —————————————————————————
@tree.command(name="sync", description="Đồng bộ lệnh slash (Admin only)")
async def sync(interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)

        try:
            synced = await tree.sync(guild=interaction.guild)
            await interaction.response.send_message(f"✅ Đã đồng bộ {len(synced)} lệnh cho server này.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("❌ Lỗi khi đồng bộ lệnh!", ephemeral=True)
            print(f"Sync error: {e}")

    # —————————————————————————
    # Game: Tài Xỉu
async def play_taixiu(interaction: discord.Interaction, amount: int, choice: str):
        uid = interaction.user.id
        ok, wait = can_play(uid)
        if not ok:
            return await interaction.response.send_message(f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True)

        bal = get_balance(uid)
        if amount < 1000 or amount > bal:
            return await interaction.response.send_message("❌ Số xu cược không hợp lệ!", ephemeral=True)

        await interaction.response.send_message("🎲 Đang lắc cuộc đời bạn...")
        await asyncio.sleep(2)

        dice = [random.randint(1, 6) for _ in range(3)]
        total = sum(dice)
        kq = "tai" if total >= 11 else "xiu"
        win = (choice == kq)

        if win:
            profit = round(amount * 0.97)
            thaydoi = amount + profit
        else:
            thaydoi = -amount

        # Apply pet buff if player wins
        pets_data = read_json(PETS_FILE).get(str(uid))
        if pets_data and win and "last" in pets_data:
            buff_pct = pets_data["last"][2]  # Get buff percentage from last pet
            buff = buff_pct / 100
            base_profit = profit  # Original profit before buff
            extra = round(base_profit * buff)
            thaydoi = amount + profit + extra

        newb = update_balance(uid, thaydoi)
        add_history(uid, f"taixiu_{'thắng' if win else 'thua'}", thaydoi, newb)

        await interaction.edit_original_response(
            content=(
                f"🎲 Kết quả: {dice} → {total} → **{kq.upper()}**\n"
                f"{'🎉 Ôi bạn đỉnh vãi ò!' if win else '💸 Ôi bạn đần vãi chưởng!'}\n"
                f"💰 Thay đổi: {thaydoi:+,} xu | Số dư: {newb:,} xu"
            )
        )

    # —————————————————————————
    # Game: Chẵn Lẻ
async def play_chanle(interaction: discord.Interaction, amount: int, choice: str):
        uid = interaction.user.id
        ok, wait = can_play(uid)
        if not ok:
            return await interaction.response.send_message(f"⏳ Vui lòng đợi {int(wait)} giây nữa!", ephemeral=True)

        bal = get_balance(uid)
        if amount < 1000 or amount > bal:
            return await interaction.response.send_message("❌ Số xu cược không hợp lệ!", ephemeral=True)

        await interaction.response.send_message("⚖️ Ăn cơm hay ăn cứt do bạn chọn...")
        await asyncio.sleep(2)

        sec = datetime.utcnow().second
        so1, so2 = divmod(sec, 10)
        total = so1 + so2
        kq = "chan" if total % 2 == 0 else "le"
        win = (choice == kq)

        if win:
            profit = round(amount * 0.95)
            thaydoi = amount + profit
        else:
            thaydoi = -amount

        # Apply pet buff if player wins
        pets_data = read_json(PETS_FILE).get(str(uid))
        if pets_data and win and "last" in pets_data:
            buff_pct = pets_data["last"][2]  # Get buff percentage from last pet
            buff = buff_pct / 100
            base_profit = profit  # Original profit before buff
            extra = round(base_profit * buff)
            thaydoi = amount + profit + extra

        newb = update_balance(uid, thaydoi)
        add_history(uid, f"chanle_{'thắng' if win else 'thua'}", thaydoi, newb)

        await interaction.edit_original_response(
            content=(
                f"🕓 Kết quả: giây={sec} → {so1}+{so2}={total} → **{kq.upper()}**\n"
                f"{'🎉 Chúc mừng bạn có cơm ăn!' if win else '💸 Chia buồn với bạn vì còn cứt thôi nhá!'}\n"
                f"💰 Thay đổi: {thaydoi:+,} xu | Số dư: {newb:,} xu"
            )
        )

    # —————————————————————————
    # Safe main loop: auto restart nếu bot crash
async def safe_main():
        while True:
            try:
                if not TOKEN:
                    print("❌ Thiếu TOKEN")
                    return
                await bot.start(TOKEN)
            except Exception:
                print("🚨 Bot crashed, restarting in 5s...", file=sys.stderr)
                traceback.print_exc()
                await asyncio.sleep(5)

if __name__ == "__main__":
        keep_alive()
        asyncio.run(safe_main())