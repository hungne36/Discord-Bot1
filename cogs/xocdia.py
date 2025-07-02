import random, discord
from discord.ext import commands, tasks
from discord import app_commands
from utils.data_manager import read_json, write_json, add_history, get_pet_buff
from datetime import datetime, timedelta, timezone

BAL   = "data/sodu.json"
HIST  = "data/lichsu.json"
SESS  = "data/xocdia_session.json"
CHOICES = ["4 Đỏ","4 Trắng","3 Đỏ 1 Trắng","3 Trắng 1 Đỏ","Chẵn","Lẻ"]

def spin(): return [random.choice(["Đỏ","Trắng"]) for _ in range(4)]

class XocDia(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
            self.auto.start()

        def cog_unload(self):
            self.auto.cancel()

        @tasks.loop(hours=3)
        async def auto(self):
            ch = self.bot.get_channel(GIVEAWAY_CHANNEL_ID)
            await self.start(ch)

        @app_commands.command(name="xocdia", description="🎲 Xóc Đĩa MP")
        async def xoc(self, inter: discord.Interaction):
            await inter.response.defer()
            session = {"active":True,"bets":{}, "host":str(inter.user.id)}
            write_json(SESS, session)
            msg = await inter.followup.send("🎲 Xóc Đĩa bắt đầu! Chủ nhấn Kết thúc", view=StartView())
            session["msg"] = msg.id
            write_json(SESS, session)

        @app_commands.command(name="ketthuc", description="🔒 Kết thúc Xóc Đĩa (host only)")
        async def end(self, inter: discord.Interaction):
            sess = read_json(SESS)
            if str(inter.user.id)!=sess.get("host"):
                return await inter.response.send_message("❌ Chỉ host mới kết thúc!", ephemeral=True)
            await self.payout(inter.channel, sess)

        async def payout(self, channel, sess):
            msg = await channel.fetch_message(sess["msg"])
            users = [u for u in await msg.reactions[0].users().flatten() if not u.bot]
            # ... giống trước, cộng thêm buff pet ...
            # (để ngắn gọn, bạn copy logic payout cũ rồi thêm get_pet_buff)

async def setup(bot):
        await bot.add_cog(XocDia(bot))
