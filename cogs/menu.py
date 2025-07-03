
# cogs/menu.py
import discord
from discord.ext import commands
from discord import app_commands

from cogs.taixiu_plus import SumSelect     # view chọn sum 3–18
from cogs.chanle import ChanLeModal         # modal cược Chẵn/Lẻ
from cogs.xocdia import XocDiaView          # view Xóc Đĩa multiplayer

class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="menu",
        description="🎮 Mở menu: Tài Xỉu Plus, Chẵn/Lẻ, Xóc Đĩa mp"
    )
    async def menu(self, interaction: discord.Interaction):
        view = MenuView()
        await interaction.response.send_message(
            "🎮 **Chọn trò chơi**", view=view, ephemeral=True
        )

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="🔢 Tài Xỉu Plus", style=discord.ButtonStyle.success,
            custom_id="menu_taixiu_plus"
        ))
        self.add_item(discord.ui.Button(
            label="⚖️ Chẵn", style=discord.ButtonStyle.primary,
            custom_id="menu_chan"
        ))
        self.add_item(discord.ui.Button(
            label="🔢 Lẻ", style=discord.ButtonStyle.danger,
            custom_id="menu_le"
        ))
        self.add_item(discord.ui.Button(
            label="🥢 Xóc Đĩa (mp)", style=discord.ButtonStyle.secondary,
            custom_id="menu_xocdia_mp"
        ))

    @discord.ui.button(custom_id="menu_taixiu_plus")
    async def _taixiu_plus(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "🔢 Chọn tối đa 4 số (3–18) để cược:", view=SumSelect(), ephemeral=True
        )

    @discord.ui.button(custom_id="menu_chan")
    async def _chan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChanLeModal("chan"))

    @discord.ui.button(custom_id="menu_le")
    async def _le(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChanLeModal("le"))

    @discord.ui.button(custom_id="menu_xocdia_mp")
    async def _xocdia_mp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        view = XocDiaView()
        await interaction.followup.send(
            f"🎲 **{interaction.user.mention}** đã mở Xóc Đĩa Multiplayer! Chọn cửa:",
            view=view
        )

async def setup(bot):
    await bot.add_cog(Menu(bot))
