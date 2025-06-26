import discord
from discord.ext import commands
from discord import app_commands
import os
from utils import data_manager

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 730436357838602301

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

    # Load all cogs
async def load_cogs():
        for cog in ["menu", "info", "nap", "lichsu", "daily", "phucloi"]:
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

    # Run bot
if __name__ == "__main__":
        if TOKEN:
            bot.run(TOKEN)
        else:
            print("❌ Thiếu biến môi trường TOKEN")