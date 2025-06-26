import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import update_balance, add_history

ADMIN_ID = 730436357838602301

class Nap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="nap", description="Nạp xu (admin)")
    @app_commands.describe(soluong="Số xu", nguoidung="Người nhận")
    async def nap(self, interaction: discord.Interaction, soluong: int, nguoidung: discord.User):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Không có quyền!", ephemeral=True)
            return
        bal = update_balance(nguoidung.id, soluong)
        add_history(nguoidung.id, "nap", soluong, bal, nguoidung.name)
        await interaction.response.send_message(
            f"✅ Đã nạp {soluong:,} xu cho {nguoidung.mention}. Số dư: {bal:,} xu"
        )

async def setup(bot):
    await bot.add_cog(Nap(bot))