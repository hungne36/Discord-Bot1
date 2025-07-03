
# cogs/menu.py
import discord
from discord.ext import commands
from discord import app_commands

from .taixiu_plus import SumSelect
from .chanle import ChanLeModal
from .xocdia import XocDiaView

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔢 Tài Xỉu Plus", style=discord.ButtonStyle.success, custom_id="menu_taixiu_plus")
    async def taixiu_plus_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔢 Chọn tối đa 4 số (3–18):", view=SumSelect(), ephemeral=True)

    @discord.ui.button(label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="menu_chan")
    async def chan_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChanLeModal("chan"))

    @discord.ui.button(label="🔢 Lẻ", style=discord.ButtonStyle.danger, custom_id="menu_le")
    async def le_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChanLeModal("le"))

    @discord.ui.button(label="🥢 Xóc Đĩa (mp)", style=discord.ButtonStyle.secondary, custom_id="menu_xocdia_mp")
    async def xocdia_mp_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        view = XocDiaView()
        await interaction.followup.send(
            f"🎲 **{interaction.user.mention}** mở Xóc Đĩa Multiplayer:", view=view
        )

class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="menu", description="🎮 Mở giao diện chọn trò chơi")
    async def menu(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎮 **Chọn trò chơi**", view=MenuView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Menu(bot))
