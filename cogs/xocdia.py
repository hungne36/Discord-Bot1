    # cogs/xocdia.py
import discord, random
from discord.ext import commands
from discord import app_commands
from utils.data_manager import read_json, write_json, add_history, get_pet_buff
from datetime import datetime, timezone

BALANCE_FILE = "data/sodu.json"
SESSION_FILE = "data/xocdia_session.json"
CACH_CUA = ["4 Đỏ", "4 Trắng", "3 Đỏ 1 Trắng", "3 Trắng 1 Đỏ", "Chẵn", "Lẻ"]

def tung_xoc_dia():
        return [random.choice(["Đỏ","Trắng"]) for _ in range(4)]

class BetModal(discord.ui.Modal):
        def __init__(self, choice):
            super().__init__(title=f"Cược {choice}")
            self.choice = choice
            self.amount = discord.ui.TextInput(label="Số xu cược", placeholder="Nhập số xu", max_length=18)
            self.add_item(self.amount)

        async def on_submit(self, interaction):
            amt = int(self.amount.value)
            user_id = str(interaction.user.id)
            data = read_json(BALANCE_FILE)
            if data.get(user_id,0) < amt or amt<1000:
                return await interaction.response.send_message("❌ Số cược không hợp lệ",ephemeral=True)

            session = read_json(SESSION_FILE)
            if not session.get("active"):
                return await interaction.response.send_message("❌ Phiên đã kết thúc",ephemeral=True)

            # chống cược mâu thuẫn
            user_bets = session["bets"].setdefault(user_id,{})
            if self.choice in ["4 Đỏ","4 Trắng"] and ("4 Trắng" if self.choice=="4 Đỏ" else "4 Đỏ") in user_bets:
                return await interaction.response.send_message("❌ Mâu thuẫn cửa",ephemeral=True)
            if self.choice in ["Chẵn","Lẻ"] and ("Lẻ" if self.choice=="Chẵn" else "Chẵn") in user_bets:
                return await interaction.response.send_message("❌ Mâu thuẫn cửa",ephemeral=True)

            # trừ tạm
            data[user_id] -= amt
            write_json(BALANCE_FILE,data)
            user_bets[self.choice] = user_bets.get(self.choice,0)+amt
            write_json(SESSION_FILE, session)

            total = sum(user_bets.values())
            await interaction.response.defer(ephemeral=True)
            await interaction.channel.send(f"📥 {interaction.user.mention} cược **{amt:,} xu** cửa **{self.choice}**")
            await interaction.followup.send(f"✅ Cược OK | Tổng cược: {total:,} xu | Dư: {data[user_id]:,} xu")

class CuaButton(discord.ui.Button):
        def __init__(self,label): super().__init__(label=label,style=discord.ButtonStyle.primary)
        async def callback(self,i): await i.response.send_modal(BetModal(self.label))

class StartButton(discord.ui.Button):
        def __init__(self): super().__init__(label="🔒 Bắt đầu",style=discord.ButtonStyle.danger)
        async def callback(self,i):
            session=read_json(SESSION_FILE)
            if str(i.user.id)!=session.get("host_id"):
                return await i.response.send_message("❌ Chỉ host được đóng",ephemeral=True)
            await ket_thuc_phien(i.channel,self.view.msg)

class XocDiaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.msg=None
            for c in CACH_CUA: self.add_item(CuaButton(c))
            self.add_item(StartButton())
        async def on_timeout(self):
            if self.msg: await ket_thuc_phien(self.msg.channel,self.msg)

async def ket_thuc_phien(channel,orig=None):
        session=read_json(SESSION_FILE)
        if not session.get("active"): return
        session["active"]=False; write_json(SESSION_FILE,session)
        if not session["bets"]:
            await channel.send("🎲 Không ai cược."); return
        res = tung_xoc_dia()
        do=res.count("Đỏ"); tr=res.count("Trắng")
        win_c = []
        if do==4: win_c.append("4 Đỏ")
        elif tr==4: win_c.append("4 Trắng")
        elif do==3: win_c.append("3 Đỏ 1 Trắng")
        elif tr==3: win_c.append("3 Trắng 1 Đỏ")
        win_c.append("Chẵn" if do%2==0 else "Lẻ")

        data=read_json(BALANCE_FILE); out=[]
        for uid,bets in session["bets"].items():
            total_bet=sum(bets.values()); profit=0
            for c,m in bets.items():
                if c in win_c:
                    rate=12 if c in ["4 Đỏ","4 Trắng"] else 2.6 if "3" in c else 0.9
                    profit += round(m*rate)
                else: profit -= m
            # pet buff
            if profit>0:
                buff=get_pet_buff(int(uid))
                bonus=round(profit*buff/100) if buff>0 else 0
                profit+=bonus
            data[uid]=data.get(uid,0)+profit
            add_history(int(uid),"xocdia",profit,data[uid])
            out.append(f"{uid}: {profit:+,} xu")
        write_json(BALANCE_FILE,data)
        await channel.send(f"🎲 KQ: {' '.join('🔴' if x=='Đỏ' else '⚪' for x in res)} ({do}Đ–{tr}T)\n"+"\n".join(out))
        write_json(SESSION_FILE,{"active":False,"bets":{},"host_id":None})

class XocDia(commands.Cog):
        def __init__(self,bot): self.bot=bot
        @app_commands.command(name="xocdia",description="Xóc Đĩa chơi chung")
        async def xocdia(self,interaction):
            await interaction.response.defer()
            write_json(SESSION_FILE,{"active":True,"bets":{},"host_id":str(interaction.user.id)})
            view=XocDiaView()
            await interaction.followup.send(f"🎮 {interaction.user.mention} mở phiên Xóc Đĩa!",view=view)
            view.msg=await interaction.original_response()

async def setup(bot):
        await bot.add_cog(XocDia(bot))
