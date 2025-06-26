import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, write_json, update_balance, add_history
import os

DATA_FILE = "data/user_data.json"

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Nhận quà khởi đầu (chỉ 1 lần duy nhất)")
    async def daily(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        data = read_json(DATA_FILE)
        if uid in data and data[uid].get("claimed", False):
            await interaction.response.send_message("❌ Bạn đã nhận quà khởi đầu rồi!", ephemeral=True)
            return

        # Cập nhật dữ liệu
        data[uid] = {"claimed": True}
        write_json(DATA_FILE, data)

        amount = 500_000
        newb = update_balance(uid, amount)
        add_history(uid=int(uid), action="daily", amount=amount, balance=newb)

        embed = discord.Embed(
            title="🎁 Quà khởi đầu",
            description=f"Chúc mừng bạn đã nhận **{amount:,} xu**!",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Daily(bot))