import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
import random
from utils.data_manager import update_balance

GIVEAWAY_CHANNEL_ID = 1388725889591939263
ADMIN_ID = 730436357838602301
REWARDS = [10_000_000_000, 5_000_000_000, 1_000_000_000]
INTERVAL_HOURS = 3

class Giveaway(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
            self.current = None
            self.auto.start()

        def cog_unload(self):
            self.auto.cancel()

        @tasks.loop(hours=INTERVAL_HOURS)
        async def auto(self):
            ch = self.bot.get_channel(GIVEAWAY_CHANNEL_ID)
            if ch: await self.start_giveaway(ch)

        @app_commands.command(name="giveaway", description="Admin mở Giveaway ngay")
        async def giveaway(self, interaction: discord.Interaction):
            if interaction.user.id != ADMIN_ID:
                return await interaction.response.send_message("❌ Chỉ admin!", ephemeral=True)
            await self.start_giveaway(interaction.channel)
            await interaction.response.send_message("✅ Tạo giveaway!", ephemeral=True)

        @app_commands.command(name="dong_giveaway", description="Admin đóng và trả thưởng")
        async def dong_giveaway(self, interaction: discord.Interaction):
            if interaction.user.id != ADMIN_ID:
                return await interaction.response.send_message("❌ Chỉ admin!", ephemeral=True)
            if not self.current:
                return await interaction.response.send_message("❌ Không có giveaway mở.", ephemeral=True)
            ch = self.bot.get_channel(GIVEAWAY_CHANNEL_ID)
            msg = await ch.fetch_message(self.current["msg_id"])
            await self._payout(ch, msg)
            await interaction.response.send_message("✅ Đã đóng giveaway!", ephemeral=True)

        async def start_giveaway(self, channel):
            embed = discord.Embed(
                title="🎉 GIVEAWAY 10 TỶ XU 🎉",
                description="React 🎉 trong 5 phút!",
                color=discord.Color.gold(),
                timestamp=datetime.now(timezone.utc)
            )
            for i, amt in enumerate(REWARDS,1):
                embed.add_field(name=f"🥇🥈🥉"[i-1], value=f"Top{i}: {amt:,} xu", inline=True)
            msg = await channel.send(embed=embed)
            await msg.add_reaction("🎉")
            self.current = {"msg_id": msg.id, "time": datetime.now(timezone.utc)}
            await asyncio.sleep(5*60)
            if self.current and self.current["msg_id"]==msg.id:
                await self._payout(channel, msg)

        async def _payout(self, channel, msg):
            users = []
            async for u in msg.reactions[0].users():
                if not u.bot:
                    users.append(u)
            if not users:
                await channel.send("❌ Không ai tham gia.")
            else:
                winners = random.sample(users, min(3,len(users)))
                text=""
                for idx,u in enumerate(winners):
                    amt=REWARDS[idx]
                    newb=update_balance(u.id,amt)
                    text+=(
                        f"{['🥇','🥈','🥉'][idx]} <@{u.id}> +{amt:,} xu | "
                        f"UID:`{u.id}` | 🕒{datetime.utcnow().isoformat()} UTC\n"
                    )
                await channel.send(f"🎉 **KẾT QUẢ GIVEAWAY** 🎉\n{text}")
            self.current=None

async def setup(bot):
        await bot.add_cog(Giveaway(bot))
