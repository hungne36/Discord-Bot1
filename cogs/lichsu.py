import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json
from datetime import datetime

HISTORY_FILE = "data/lichsu.json"

class LichSu(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="lichsu", description="📜 Xem lịch sử giao dịch")
        async def lichsu(self, interaction: discord.Interaction):
            hist = read_json(HISTORY_FILE)
            user_hist = [h for h in hist if h["user_id"] == interaction.user.id]

            if not user_hist:
                return await interaction.response.send_message("📜 Bạn chưa có lịch sử giao dịch.", ephemeral=True)

            embed = discord.Embed(title="📜 Lịch sử giao dịch gần đây", color=discord.Color.green())
            for h in user_hist[-10:]:
                action = h["action"]
                amt = h["amount"]
                bal_after = h["balance_after"]
                ts = h["timestamp"][:19].replace("T", " ")
                usern = h.get("username", interaction.user.name)
                embed.add_field(
                    name=f"{action} | {amt:+,} xu",
                    value=f"👤 {usern} | 💰 Sau: {bal_after:,} xu\n🕒 {ts}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
        await bot.add_cog(LichSu(bot))
