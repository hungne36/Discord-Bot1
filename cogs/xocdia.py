# cogs/xocdia.py
import discord, random
from discord.ext import commands, tasks
from discord import app_commands
from utils.data_manager import read_json, write_json, add_history, get_pet_buff
from datetime import datetime, timezone

BALANCE_FILE = "data/sodu.json"
SESSION_FILE = "data/xocdia_session.json"
CACH_CUA = ["4 Đỏ","4 Trắng","3 Đỏ 1 Trắng","3 Trắng 1 Đỏ","Chẵn","Lẻ"]

def tung_xoc_dia():
    return [random.choice(["Đỏ","Trắng"]) for _ in range(4)]

class BetModal(discord.ui.Modal):
    def __init__(self, choice):
        super().__init__(title=f"Cược {choice}")
        self.choice = choice
        self.add_item(discord.ui.TextInput(label="Số xu cược", placeholder="Nhập ≥1,000"))

    async def on_submit(self, interaction: discord.Interaction):
        amt = int(self.children[0].value)
        data = read_json(BALANCE_FILE)
        uid  = str(interaction.user.id)
        session = read_json(SESSION_FILE)
        if amt<1000 or data.get(uid,0)<amt or not session.get("active"):
            return await interaction.response.send_message("❌ Không thể cược!", ephemeral=True)

        bets = session["bets"].setdefault(uid,{})
        # mâu thuẫn cửa
        opp = "4 Trắng" if self.choice=="4 Đỏ" else ("4 Đỏ" if "4" in self.choice else
              ("Lẻ" if self.choice=="Chẵn" else "Chẵn"))
        if opp in bets:
            return await interaction.response.send_message("❌ Cửa mâu thuẫn!", ephemeral=True)

        data[uid] -= amt
        write_json(BALANCE_FILE,data)
        bets[self.choice] = bets.get(self.choice,0)+amt
        write_json(SESSION_FILE, session)

        total = sum(bets.values())
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"✅ Cược **{amt:,} xu** vào **{self.choice}** | Tổng cược: {total:,} xu")

class CuaButton(discord.ui.Button):
    def __init__(self,label): super().__init__(label=label,style=discord.ButtonStyle.primary)
    async def callback(self, inter: discord.Interaction):
        await inter.response.send_modal(BetModal(self.label))

class StartButton(discord.ui.Button):
    def __init__(self): super().__init__(label="🔒 Bắt đầu",style=discord.ButtonStyle.danger)
    async def callback(self, inter: discord.Interaction):
        session = read_json(SESSION_FILE)
        if str(inter.user.id)!=session.get("host_id"):
            return await inter.response.send_message("❌ Chỉ host!",ephemeral=True)
        await ket_thuc_phien(inter.channel, self.view.msg)

class XocDiaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.msg = None
        for c in CACH_CUA: self.add_item(CuaButton(c))
        self.add_item(StartButton())

    async def on_timeout(self):
        if self.msg:
            await ket_thuc_phien(self.msg.channel, self.msg)

async def ket_thuc_phien(channel, orig_msg):
    session = read_json(SESSION_FILE)
    if not session.get("active"): return
    session["active"] = False
    write_json(SESSION_FILE, session)

    if not session["bets"]:
        await channel.send("🎲 Phiên kết thúc! Không ai cược.")
        return

    res = tung_xoc_dia()
    do, tr = res.count("Đỏ"), res.count("Trắng")
    win_c = []
    if do==4: win_c.append("4 Đỏ")
    elif tr==4: win_c.append("4 Trắng")
    elif do==3: win_c.append("3 Đỏ 1 Trắng")
    elif tr==3: win_c.append("3 Trắng 1 Đỏ")
    win_c.append("Chẵn" if do%2==0 else "Lẻ")

    data = read_json(BALANCE_FILE)
    out = []
    for uid,bets in session["bets"].items():
        total_bet = sum(bets.values()); profit=0
        for c,m in bets.items():
            if c in win_c:
                rate = 12 if "4" in c else (2.6 if "3" in c else 0.9)
                profit += round(m*rate)
            else:
                profit -= m
        # pet buff
        if profit>0:
            buff = get_pet_buff(int(uid))
            profit += round(profit*buff/100) if buff else 0
        data[uid] = data.get(uid,0) + profit
        add_history(int(uid),"xocdia",profit,data[uid])
        out.append(f"<@{uid}>: {profit:+,} xu")
    write_json(BALANCE_FILE,data)

    emoji_map = {"Đỏ":"🔴","Trắng":"⚪"}
    await channel.send(
        f"🎲 {' '.join(emoji_map[x] for x in res)} ({do}Đ–{tr}T)\n" + "\n".join(out)
    )

class XocDia(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="xocdia", description="🥢 Xóc Đĩa Multiplayer")
    async def xocdia(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        write_json(SESSION_FILE, {"active":True,"bets":{},"host_id":str(interaction.user.id)})
        view = XocDiaView()
        await interaction.followup.send(f"🎲 **{interaction.user.mention}** mở phiên Xóc Đĩa!", view=view)
        view.msg = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(XocDia(bot))