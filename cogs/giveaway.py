
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
import random

from utils.data_manager import update_balance

GIVEAWAY_CHANNEL_ID = 1388725889591939263  # Kênh #giveaway
ADMIN_ID = 730436357838602301  # UID admin
REWARDS = [10_000_000_000, 5_000_000_000, 1_000_000_000]
INTERVAL_HOURS = 3

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_giveaway = None
        self.auto_giveaway.start()

    def cog_unload(self):
        self.auto_giveaway.cancel()

    @tasks.loop(hours=INTERVAL_HOURS)
    async def auto_giveaway(self):
        channel = self.bot.get_channel(GIVEAWAY_CHANNEL_ID)
        if channel:
            await self.start_giveaway(channel)

    @app_commands.command(name="giveaway", description="🎉 Admin tạo giveaway thủ công")
    async def giveaway(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True)
        await self.start_giveaway(interaction.channel)
        await interaction.response.send_message("✅ Giveaway đã được tạo!", ephemeral=True)

    @app_commands.command(name="dong_giveaway", description="🚫 Đóng giveaway và trao thưởng")
    async def dong_giveaway(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Bạn không có quyền dùng lệnh này.", ephemeral=True)

        if not self.current_giveaway:
            return await interaction.response.send_message("❌ Không có giveaway nào đang mở.", ephemeral=True)

        channel = self.bot.get_channel(GIVEAWAY_CHANNEL_ID)
        msg_id = self.current_giveaway["message_id"]
        msg = await channel.fetch_message(msg_id)
        await self.tra_thuong(channel, msg)
        await interaction.response.send_message("✅ Đã đóng giveaway và trao thưởng!", ephemeral=True)

    async def start_giveaway(self, channel):
        embed = discord.Embed(
            title="🎉 GIVEAWAY 10 TỶ XU 🎉",
            description=(
                "Tham gia giveaway và chờ 5 phút để biết kết quả!\n"
                "🥇 Giải nhất: 10 tỷ xu\n"
                "🥈 Giải nhì: 5 tỷ xu\n"
                "🥉 Giải ba: 1 tỷ xu\n\n"
                "Nhấn 🎉 để tham gia!"
            ),
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🎉")

        self.current_giveaway = {
            "message_id": msg.id,
            "start_time": datetime.now(timezone.utc)
        }

        await discord.utils.sleep_until(datetime.now(timezone.utc) + timedelta(minutes=5))
        if self.current_giveaway and self.current_giveaway["message_id"] == msg.id:
            await self.tra_thuong(channel, msg)

    async def tra_thuong(self, channel, msg):
        users = await msg.reactions[0].users().flatten()
        users = [u for u in users if not u.bot]

        if not users:
            await channel.send("❌ Không có ai tham gia giveaway lần này.")
            self.current_giveaway = None
            return

        winners = random.sample(users, min(3, len(users)))
        reward_text = ""

        for i, winner in enumerate(winners):
            reward = REWARDS[i]
            newb = update_balance(winner.id, reward)
            reward_text += f"{['🥇', '🥈', '🥉'][i]} <@{winner.id}> nhận **{reward:,} xu**\n"
            reward_text += f"🆔 UID: `{winner.id}` | 🕒 {datetime.utcnow().isoformat()} UTC\n\n"

        await channel.send(f"🎉 **KẾT QUẢ GIVEAWAY** 🎉\n{reward_text}")
        self.current_giveaway = None

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
