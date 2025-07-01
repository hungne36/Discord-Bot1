import json
import discord
from discord import app_commands
from discord.ext import commands
import os

# Use the same data structure as main.py
DATA_FILE = "data/sodu.json"
USER_DATA_FILE = "data/user_data.json"

def read_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        if "user_data" in path:
            return {}
        return {}

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        os.fsync(f.fileno())

def get_balance(uid):
    return read_json(DATA_FILE).get(str(uid), 1000)

def update_balance(uid, amount):
    data = read_json(DATA_FILE)
    uid = str(uid)
    data[uid] = data.get(uid, 0) + amount
    write_json(DATA_FILE, data)
    return data[uid]

def has_claimed_daily(uid):
    data = read_json(USER_DATA_FILE)
    return str(uid) in data

def mark_daily_claimed(uid):
    data = read_json(USER_DATA_FILE)
    data[str(uid)] = {"daily_claimed": True}
    write_json(USER_DATA_FILE, data)

class DailyView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = str(user_id)

    @discord.ui.button(label="🎁 Nhận khởi đầu", style=discord.ButtonStyle.success, custom_id="daily_claim")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has already claimed using user_data.json
        if has_claimed_daily(int(self.user_id)):
            await interaction.response.send_message("❌ Bạn đã nhận quà khởi đầu rồi!", ephemeral=True)
        else:
            new_balance = update_balance(int(self.user_id), 25_000_000_000)
            mark_daily_claimed(int(self.user_id))
            await interaction.response.send_message(f"✅ Bạn đã nhận **25 tỷ xu khởi đầu**!\n💰 Số dư mới: {new_balance:,} xu", ephemeral=True)

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Nhận quà khởi đầu")
    async def daily(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎉 Quà Khởi Đầu!",
            description="Chào mừng bạn đến với bot! Hãy nhận **25 tỷ xu** để bắt đầu chơi.\n\nẤn nút bên dưới để nhận.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=DailyView(interaction.user.id), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Daily(bot))
