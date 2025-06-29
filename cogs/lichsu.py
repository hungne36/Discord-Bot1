import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json

HISTORY_FILE = "data/lichsu.json"

class LichSu(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="lichsu", description="📜 Xem lịch sử giao dịch")
        async def lichsu(self, interaction: discord.Interaction):
            hist = read_json(HISTORY_FILE)
            user_hist = [h for h in hist if h["user_id"] == interaction.user.id]

            if not user_hist:
                await interaction.response.send_message("📜 Không có giao dịch.", ephemeral=True)
                return

            embed = discord.Embed(title="📜 Lịch sử giao dịch gần đây", color=0x00ff00)
            for h in user_hist[-10:]:
                game = h["action"]
                amount = h["amount"]
                balance = h["balance_after"]
                time = h["timestamp"][:19]
                username = h.get("username", "Không rõ")

                embed.add_field(
                    name=f"🎮 {game} - {amount:,} xu",
                    value=f"👤 {username} | 💰 Sau: {balance:,} xu\n🕒 {time}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LichSu(bot))