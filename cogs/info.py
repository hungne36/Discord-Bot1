import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, get_balance
from datetime import datetime

HISTORY_FILE = "data/lichsu.json"

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Xem thông tin cá nhân")
    async def info(self, interaction: discord.Interaction):
        uid = interaction.user.id
        bal = get_balance(uid)
        hist = read_json(HISTORY_FILE)
        today = datetime.utcnow().date()

        spent_today = sum(
            abs(h["amount"]) for h in hist
            if h["user_id"] == uid and h["amount"] < 0 and
            datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date() == today
        )

        reward_cap = min(spent_today, 500_000_000_000_000)
        pending = (reward_cap // 10_000_000_000_000) * 500_000_000_000

        wins = sum(1 for h in hist if h["user_id"]==uid and "thắng" in h["action"])
        losses = sum(1 for h in hist if h["user_id"]==uid and "thua" in h["action"])

        msg = (
            f"👤 **Thông tin của bạn**\n"
            f"💰 Số xu hiện có: {bal:,}\n"
            f"📉 Xu đã tiêu hôm nay: {spent_today:,}\n"
            f"🎁 Xu chờ nhận (dựa trên tiêu hôm nay): {pending:,}\n"
            f"🏆 Thắng: {wins} trận\n"
            f"💥 Thua: {losses} trận"
        )
        await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Info(bot))