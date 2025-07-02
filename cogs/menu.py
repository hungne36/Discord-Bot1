# cogs/menu.py
import discord
from discord.ext import commands
from discord import app_commands
from cogs.taixiu_plus import play_taixiu_plus_tai, play_taixiu_plus_xiu
from cogs.chanle import play_chanle
from cogs.xocdia import start_xocdia_mp

class MenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="🎲 Tài Plus", style=discord.ButtonStyle.success, custom_id="menu_txp_tai")
        async def btn_tai_plus(self, interaction: discord.Interaction, button: discord.ui.Button):
            await play_taixiu_plus_tai(interaction)

        @discord.ui.button(label="❌ Xỉu Plus", style=discord.ButtonStyle.danger, custom_id="menu_txp_xiu")
        async def btn_xiu_plus(self, interaction: discord.Interaction, button: discord.ui.Button):
            await play_taixiu_plus_xiu(interaction)

        @discord.ui.button(label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="menu_chan")
        async def btn_chan(self, interaction: discord.Interaction, button: discord.ui.Button):
            await play_chanle(interaction, choice="chan")

        @discord.ui.button(label="🔢 Lẻ", style=discord.ButtonStyle.primary, custom_id="menu_le")
        async def btn_le(self, interaction: discord.Interaction, button: discord.ui.Button):
            await play_chanle(interaction, choice="le")

        @discord.ui.button(label="🎲 Xóc Đĩa MP", style=discord.ButtonStyle.secondary, custom_id="menu_xdmp")
        async def btn_xocdia(self, interaction: discord.Interaction, button: discord.ui.Button):
            await start_xocdia_mp(interaction)

class Menu(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="menu", description="🎮 Hiển thị menu chọn trò chơi")
        async def menu(self, interaction: discord.Interaction):
            await interaction.response.send_message("🎮 Chọn trò chơi:", view=MenuView(), ephemeral=True)

async def setup(bot):
        await bot.add_cog(Menu(bot))