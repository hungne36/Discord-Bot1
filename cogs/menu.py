import discord
from discord.ext import commands
from discord import app_commands
from .taixiu import TaiXiuModal
from .chanle import ChanLeModal
from .xocdia import XocDiaView

class MenuView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(label="🎲 Tài", style=discord.ButtonStyle.success, custom_id="menu_tai"))
                self.add_item(discord.ui.Button(label="❌ Xỉu", style=discord.ButtonStyle.danger, custom_id="menu_xiu"))
                self.add_item(discord.ui.Button(label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="menu_chan"))
                self.add_item(discord.ui.Button(label="🔢 Lẻ", style=discord.ButtonStyle.secondary, custom_id="menu_le"))
                self.add_item(discord.ui.Button(label="🥢 Xóc Đĩa (mp)", style=discord.ButtonStyle.secondary, custom_id="menu_xocdia_mp"))

            @discord.ui.button(custom_id="menu_tai")
            async def tai_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(TaiXiuModal("tai"))

            @discord.ui.button(custom_id="menu_xiu")
            async def xiu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(TaiXiuModal("xiu"))

            @discord.ui.button(custom_id="menu_chan")
            async def chan_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChanLeModal("chan"))

            @discord.ui.button(custom_id="menu_le")
            async def le_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChanLeModal("le"))

            @discord.ui.button(custom_id="menu_xocdia_mp")
            async def xocdia_mp_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer(ephemeral=True)
                view = XocDiaView()
                await interaction.followup.send(
                    f"🎲 {interaction.user.mention} đã mở Xóc Đĩa Multiplayer — chọn cửa:",
                    view=view
                )

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
