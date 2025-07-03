    # cogs/xocdia.py
import random, discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, write_json, add_history, get_pet_buff
from datetime import datetime

BALANCE_FILE = "data/sodu.json"
SESSION_FILE = "data/xocdia_session.json"
CACH_CUA = ["4 Đỏ", "4 Trắng", "3 Đỏ 1 Trắng", "3 Trắng 1 Đỏ", "Chẵn", "Lẻ"]

def tung_xoc_dia():
        return [random.choice(["Đỏ","Trắng"]) for _ in range(4)]

class BetModal(discord.ui.Modal):
        def __init__(self, choice):
            super().__init__(title=f"Cược {choice}")
            self.choice = choice
            self.amount = discord.ui.TextInput(label="Số xu cược", placeholder="≥1.000", max_length=18)
            self.add_item(self.amount)

        async def on_submit(self, interaction: discord.Interaction):
            amt = int(self.amount.value)
            data = read_json(BALANCE_FILE)
            uid = str(interaction.user.id)
            if amt < 1000 or data.get(uid,0) < amt:
                return await interaction.response.send_message("❌ Không đủ xu!", ephemeral=True)

            sess = read_json(SESSION_FILE)
            if not sess.get("active"):
                return await interaction.response.send_message("❌ Phiên kết thúc!", ephemeral=True)

            # kiểm mâu thuẫn
            bets = sess["bets"].setdefault(uid, {})
            if self.choice in ["4 Đỏ","4 Trắng"] and ("4 Trắng" if self.choice=="4 Đỏ" else "4 Đỏ") in bets:
                return await interaction.response.send_message("❌ Mâu thuẫn cửa!", ephemeral=True)
            if self.choice in ["Chẵn","Lẻ"] and ("Lẻ" if self.choice=="Chẵn" else "Chẵn") in bets:
                return await interaction.response.send_message("❌ Mâu thuẫn cửa!", ephemeral=True)

            data[uid] -= amt
            write_json(BALANCE_FILE, data)
            bets[self.choice] = bets.get(self.choice,0) + amt
            write_json(SESSION_FILE, sess)

            total = sum(bets.values())
            await interaction.response.defer(ephemeral=True)
            await interaction.channel.send(f"📥 {interaction.user.mention} cược **{amt:,} xu** → **{self.choice}**")
            await interaction.followup.send(f"✅ Đã cược | Tổng cược: {total:,} xu | Dư: {data[uid]:,}", ephemeral=True)

class CuaButton(discord.ui.Button):
        def __init__(self,label): super().__init__(label=label,style=discord.ButtonStyle.primary)
        async def callback(self, i:discord.Interaction): await i.response.send_modal(BetModal(self.label))

class StartButton(discord.ui.Button):
        def __init__(self): super().__init__(label="🔒 Kết thúc",style=discord.ButtonStyle.danger)
        async def callback(self, i:discord.Interaction):
            sess = read_json(SESSION_FILE)
            if str(i.user.id)!=sess.get("host_id"):
                return await i.response.send_message("❌ Chỉ host!", ephemeral=True)
            await ket_thuc_phien(i.channel, self.view.msg)

class XocDiaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.msg=None
            for c in CACH_CUA: self.add_item(CuaButton(c))
            self.add_item(StartButton())
        async def on_timeout(self):
            if self.msg: await ket_thuc_phien(self.msg.channel, self.msg)

async def ket_thuc_phien(channel, orig=None):
        sess = read_json(SESSION_FILE)
        if not sess.get("active"): return
        sess["active"]=False; write_json(SESSION_FILE, sess)
        if not sess["bets"]:
            await channel.send("🎲 Không ai cược!"); return
        res = tung_xoc_dia(); d=res.count("Đỏ"); t=res.count("Trắng")
        winners=[]
        data=read_json(BALANCE_FILE)
        for uid,bets in sess["bets"].items():
            profit=0
            for c,m in bets.items():
                if c in (["4 Đỏ","4 Trắng"] if d==4 else ["3 Đỏ 1 Trắng"] if d==3 else []):
                    rate=12
                elif c in (["3 Trắng 1 Đỏ"] if t==3 else []): rate=1.6
                elif c in ["Chẵn","Lẻ"]: rate=0.9
                else: rate=0
                profit += round(m*rate) if rate>0 else -m
            if profit>0:
                buff=get_pet_buff(int(uid))
                bonus=round(profit*buff/100) if buff else 0
                profit+=bonus
            data[uid]=data.get(uid,0)+profit
            add_history(int(uid),"xocdia",profit,data[uid])
            winners.append(f"<@{uid}>: {profit:+,}")
        write_json(BALANCE_FILE, data)
        em = discord.Embed(title="🎲 Kết quả Xóc Đĩa", description=f"{' '.join('🔴' if x=='Đỏ' else '⚪' for x in res)} ({d}Đ–{t}T)")
        em.add_field(name="Kết quả", value="\n".join(winners), inline=False)
        await channel.send(embed=em)
        if orig: await orig.delete()
        write_json(SESSION_FILE, {"active":False,"bets":{},"host_id":None})

class XocDia(commands.Cog):
        def __init__(self, bot): self.bot=bot

        @app_commands.command(name="xocdia", description="❌ Dùng /menu để chơi Xóc Đĩa!")
        async def xd(self, interaction: discord.Interaction):
            await interaction.response.send_message("❌ Dùng /menu!", ephemeral=True)

async def setup(bot):
        await bot.add_cog(XocDia(bot))