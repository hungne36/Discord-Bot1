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
                -h["amount"]
                for h in hist
                if h["user_id"] == uid
                   and h["amount"] < 0
                   and datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date() == today
            )

            # Tính phúc lợi chờ nhận: 50 tỷ cho mỗi 1 nghìn tỷ đã tiêu (max 50 tỷ)
            reward_cap = min(spent_today, 1_000_000_000_000)  # tiêu tối đa 1 nghìn tỷ
            pending = (reward_cap // 1_000_000_000_000) * 50_000_000_000

            wins = sum(1 for h in hist if h["user_id"] == uid and "thắng" in h["action"])
            losses = sum(1 for h in hist if h["user_id"] == uid and "thua" in h["action"])

            embed = discord.Embed(title="👤 Thông tin của bạn", color=discord.Color.blue())
            embed.add_field(name="💰 Số dư hiện tại", value=f"{bal:,} xu")
            embed.add_field(name="📉 Xu đã tiêu hôm nay", value=f"{spent_today:,} xu")
            embed.add_field(name="🎁 Xu chờ nhận", value=f"{pending:,} xu")
            embed.add_field(name="🏆 Thắng", value=str(wins))
            embed.add_field(name="💥 Thua", value=str(losses))
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
        await bot.add_cog(Info(bot))