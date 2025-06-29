import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
from datetime import datetime, timezone

from utils.data_manager import update_balance

GIVEAWAY_CHANNEL_ID =1388725889591939263
YOUR_ACTUAL_CHANNEL_ID  # 👈 Replace with your real giveaway channel ID
ADMIN_ID = 730436357838602301  # 👈 UID admin

REWARDS = [10_000_000_000, 5_000_000_000, 1_000_000_000]
INTERVAL_HOURS = 3

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_giveaway.start()

    def cog_unload(self):
        self.auto_giveaway.cancel()

    @tasks.loop(hours=INTERVAL_HOURS)
    async def auto_giveaway(self):
        channel = self.bot.get_channel(GIVEAWAY_CHANNEL_ID)
        if not channel:
            return
        await self.start_giveaway(channel)

    @app_commands.command(name="giveaway", description="🎉 Admin tạo giveaway thủ công")
    async def giveaway(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Chỉ admin được dùng lệnh này.", ephemeral=True)
            return
        await self.start_giveaway(interaction.channel)
        await interaction.response.send_message("✅ Đã tạo giveaway!", ephemeral=True)

    async def start_giveaway(self, channel):
        embed = discord.Embed(
            title="🎉 GIVEAWAY 10 TỶ XU 🎉",
            description="Tham gia giveaway và chờ 5 phút để biết kết quả!\n"
                        "🥇 Giải nhất: 10 tỷ xu\n"
                        "🥈 Giải nhì: 5 tỷ xu\n"
                        "🥉 Giải ba: 1 tỷ xu\n\n"
                        "Nhấn 🎉 để tham gia!",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🎉")

        await discord.utils.sleep_until(datetime.now(timezone.utc) + discord.utils.timedelta(minutes=5))

        new_msg = await channel.fetch_message(msg.id)
        users = await new_msg.reactions[0].users().flatten()
        users = [u for u in users if not u.bot]

        if len(users) == 0:
            await channel.send("❌ Không có ai tham gia giveaway lần này.")
            return

        winners = random.sample(users, k=min(3, len(users)))
        reward_text = ""
        for i, winner in enumerate(winners):
            reward = REWARDS[i]
            new_balance = update_balance(winner.id, reward)
            reward_text += f"🥇" if i == 0 else ("🥈" if i == 1 else "🥉")
            reward_text += f" <@{winner.id}> nhận **{reward:,} xu**\n"
            reward_text += f"🆔 UID: `{winner.id}` | 🕒 {datetime.utcnow().isoformat()} UTC\n\n"

        await channel.send(f"🎉 **Kết quả Giveaway** 🎉\n{reward_text}")

async def setup(bot):
    await bot.add_cog(Giveaway(bot))