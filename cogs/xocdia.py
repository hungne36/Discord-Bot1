import discord
from discord.ext import commands
import random
import json
import os
from utils.data_manager import read_json, write_json
from datetime import datetime, timezone

    SESSION_FILE = "data/xocdia_session.json"

    def get_current_utc_timestamp():
        return datetime.now(timezone.utc).isoformat()

    def ket_thuc_phien(channel, msg):
        sess = read_json(SESSION_FILE)
        sess["active"] = False
        write_json(SESSION_FILE, sess)

        result = random.choice(["chan", "le"])
        result_str = "🔴 Chẵn" if result == "chan" else "⚫ Lẻ"
        embed = discord.Embed(
            title="🎲 Kết quả Xóc Đĩa",
            description=f"Kết quả là: **{result_str}**",
            color=discord.Color.gold(),
        )
        embed.set_footer(text="Phiên đã kết thúc.")
        return msg.edit(content=None, embed=embed, view=None)

class XocDiaView(discord.ui.View):
    def __init__(self, author_id, msg=None):
            super().__init__(timeout=None)  # Không giới hạn thời gian
            self.author_id = author_id
            self.msg = msg

        @discord.ui.button(label="🔴 Chẵn", style=discord.ButtonStyle.danger, custom_id="chan")
        async def bet_chan(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_bet(interaction, "chan")

        @discord.ui.button(label="⚫ Lẻ", style=discord.ButtonStyle.primary, custom_id="le")
        async def bet_le(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_bet(interaction, "le")

        @discord.ui.button(label="🔒 Kết thúc", style=discord.ButtonStyle.secondary, custom_id="end")
        async def end_session(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.author_id:
                return await interaction.response.send_message("❌ Chỉ chủ phòng mới được kết thúc phiên!", ephemeral=True)
            await ket_thuc_phien(interaction.channel, self.msg)

        async def handle_bet(self, interaction: discord.Interaction, choice: str):
            sess = read_json(SESSION_FILE)
            if not sess.get("active"):
                return await interaction.response.send_message("❌ Phiên đã kết thúc!", ephemeral=True)

            user_id = str(interaction.user.id)
            if user_id in sess["players"]:
                return await interaction.response.send_message("❌ Bạn đã tham gia rồi!", ephemeral=True)

            sess["players"][user_id] = {
                "choice": choice,
                "timestamp": get_current_utc_timestamp(),
            }
            write_json(SESSION_FILE, sess)

            await interaction.response.send_message(f"✅ Bạn đã chọn **{'Chẵn' if choice == 'chan' else 'Lẻ'}**!", ephemeral=True)

    class XocDia(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.command()
        async def resetxocdia(self, ctx):
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send("❌ Chỉ admin mới được dùng lệnh này.")
            write_json(SESSION_FILE, {"active": False, "players": {}})
            await ctx.send("✅ Đã reset phiên Xóc Đĩa.")

    async def start_xocdia_game(interaction: discord.Interaction):
        sess = read_json(SESSION_FILE)
        if sess.get("active"):
            return await interaction.response.send_message("❌ Hiện tại đang có một phiên Xóc Đĩa đang diễn ra!", ephemeral=True)

        sess["active"] = True
        sess["players"] = {}
        write_json(SESSION_FILE, sess)

        view = XocDiaView(author_id=interaction.user.id)
        msg = await interaction.channel.send("🎮 **Phiên Xóc Đĩa bắt đầu!**\nChọn cược bên dưới 👇", view=view)
        view.msg = msg
        await interaction.response.send_message("✅ Đã tạo phiên Xóc Đĩa!", ephemeral=True)

    def setup(bot):
        bot.add_cog(XocDia(bot))