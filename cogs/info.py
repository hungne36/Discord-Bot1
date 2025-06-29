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

            # Dùng ngày UTC để tính "hôm nay"
            today = datetime.utcnow().date()

            # Chỉ tính những giao dịch trừ xu (amount < 0), chuyển thành dương
            spent_today = sum(
                -h["amount"]
                for h in hist
                if h["user_id"] == uid
                   and h["amount"] < 0
                   and datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date() == today
            )

            # Phần thưởng chờ nhận
            reward_cap = min(spent_today, 50_000_000_000_000)
            pending = (reward_cap // 1_000_000_000_000) * 50_000_000_000

            wins = sum(1 for h in hist if h["user_id"] == uid and "thắng" in h["action"])
            losses = sum(1 for h in hist if h["user_id"] == uid and "thua" in h["action"])

            msg = (
                f"👤 **Thông tin của bạn**\n"
                f"💰 Số xu hiện có: {bal:,}\n"
                f"📉 Xu đã tiêu hôm nay: {spent_today:,}\n"
                f"🎁 Xu chờ nhận (Hẹn bạn 7h sáng nhé): {pending:,}\n"
                f"🏆 Thắng: {wins} trận\n"
                f"💥 Thua: {losses} trận"
            )
            await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Info(bot))