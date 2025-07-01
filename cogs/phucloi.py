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

            spent = sum(
                -h["amount"] for h in hist
                if h["user_id"] == uid and h["amount"] < 0
                and datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date() == yesterday
            )

            # 25% hoàn tối đa 50 tỷ
            reward = min(spent * 0.25, 50_000_000_000)
            reward = int(reward // 1)  # lấy phần nguyên
            if reward <= 0:
                return await interaction.response.send_message("❌ Bạn không đủ điều kiện nhận phúc lợi.", ephemeral=True)

            claimed = any(
                h["user_id"] == uid and h["action"] == "nhan_phucloi"
                and datetime.fromisoformat(h["timestamp"].replace("Z", "+00:00")).date() == today
                for h in hist
            )
            if claimed:
                return await interaction.response.send_message("❌ Bạn đã nhận phúc lợi hôm nay rồi.", ephemeral=True)

            newb = update_balance(uid, reward)
            add_history(uid, "nhan_phucloi", reward, newb, interaction.user.name)
            await interaction.response.send_message(
                f"🎁 Bạn nhận **{reward:,} xu** phúc lợi!\n💰 Số dư mới: {newb:,} xu",
                ephemeral=True
            )

async def setup(bot):
        await bot.add_cog(PhucLoi(bot))