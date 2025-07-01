import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json
from datetime import datetime, timedelta

TOP_FILE = "data/top_rewards.json"
HISTORY_FILE = "data/lichsu.json"

class Top(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="top", description="🏆 Xem BXH Tiêu Xu hôm nay")
        async def top(self, interaction: discord.Interaction):
            hist = read_json(HISTORY_FILE)
            today = datetime.utcnow().date()
            spent = {}
            for h in hist:
                if h["amount"] < 0:
                    d = datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date()
                    if d == today:
                        uid = h["user_id"]
                        spent[uid] = spent.get(uid, 0) - h["amount"]

            if not spent:
                return await interaction.response.send_message("📊 Chưa có ai tiêu xu hôm nay.", ephemeral=True)

            # sort giảm dần, lấy top 10
            top5 = sorted(spent.items(), key=lambda x: x[1], reverse=True)[:5]
            embed = discord.Embed(title="🏆 BXH Tiêu Xu Hôm Nay", color=discord.Color.purple())
            for rank, (uid, amt) in enumerate(top5, start=1):
                member = interaction.guild.get_member(uid)
                name = member.display_name if member else f"user {uid}"
                embed.add_field(name=f"{rank}. {name}", value=f"{amt:,} xu", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
        await bot.add_cog(Top(bot))
