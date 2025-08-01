import discord
from discord.ext import commands
from discord import app_commands
from .taixiu import TaiXiuModal
from .chanle import ChanLeModal
from .xocdia import XocDiaView

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎲 Tài", style=discord.ButtonStyle.success, custom_id="menu_tai")
    async def tai_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TaiXiuModal("tai"))

    @discord.ui.button(label="❌ Xỉu", style=discord.ButtonStyle.danger, custom_id="menu_xiu")
    async def xiu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TaiXiuModal("xiu"))

    @discord.ui.button(label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="menu_chan")
    async def chan_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChanLeModal("chan"))

    @discord.ui.button(label="🔢 Lẻ", style=discord.ButtonStyle.secondary, custom_id="menu_le")
    async def le_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChanLeModal("le"))

    @discord.ui.button(label="🥢 Xóc Đĩa", style=discord.ButtonStyle.secondary, custom_id="menu_xocdia")
    async def xocdia_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from .xocdia import start_xocdia_game
        await start_xocdia_game(interaction)

class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="menu", description="🎮 Mở giao diện chọn trò chơi")
    async def menu(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            "🎮 Chọn trò chơi",
            view=MenuView(),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Menu(bot))
