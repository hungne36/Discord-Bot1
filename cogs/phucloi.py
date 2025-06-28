import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, update_balance, add_history
from datetime import datetime, timedelta

HISTORY_FILE = "data/lichsu.json"

class PhucLoi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="phucloi", description="Nhận xu chờ nhận từ hôm qua")
    async def phucloi(self, interaction: discord.Interaction):
        uid = interaction.user.id
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        hist = read_json(HISTORY_FILE)

        spent_yesterday = sum(
            abs(h["amount"]) for h in hist
            if h["user_id"] == uid
            and h["amount"] < 0
            and datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date() == yesterday
        )

        reward_cap = min(spent_yesterday, 50_000_000_000_000_000)
        pending = (reward_cap // 10_000_000_000_000_000) * 500_000_000_000_000

        if pending == 0:
            return await interaction.response.send_message(
                "❌ Bạn không đủ điều kiện nhận xu hôm nay!", ephemeral=True
            )

        da_nhan = any(
            h["user_id"] == uid and h["action"] == "nhan_phucloi" and
            datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date() == today
            for h in hist
        )
        if da_nhan:
            return await interaction.response.send_message("❌ Bạn đã nhận phúc lợi hôm nay rồi!", ephemeral=True)

        newb = update_balance(uid, pending)
        add_history(uid, "nhan_phucloi", pending, newb, interaction.user.name)

        await interaction.response.send_message(
            f"🎁 Bạn đã nhận **{pending:,} xu** từ xu chờ nhận hôm qua!\n"
            f"💰 Số dư mới: {newb:,} xu", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(PhucLoi(bot))