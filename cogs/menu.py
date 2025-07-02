
import discord
from discord.ext import commands
from discord import app_commands
from main import play_taixiu, play_chanle
from utils.xocdia_ui import CuocView

class MenuModal(discord.ui.Modal):
    def __init__(self, game_type, choice):
        super().__init__(title=f"Cược {choice.upper()}")
        self.game_type = game_type
        self.choice = choice
        self.add_item(discord.ui.TextInput(label="Số xu cược", placeholder="Ví dụ: 10000", max_length=18))

    async def on_submit(self, interaction):
        amount = int(self.children[0].value)
        if self.game_type == "taixiu":
            await play_taixiu(interaction, amount, self.choice)
        elif self.game_type == "chanle":
            await play_chanle(interaction, amount, self.choice)

class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="menu", description="Chọn trò chơi")
    async def menu(self, interaction):
        view = discord.ui.View(timeout=None)
        
        # Create buttons
        tai_btn = discord.ui.Button(label="🎲 Tài", style=discord.ButtonStyle.success, custom_id="m_tai")
        xiu_btn = discord.ui.Button(label="❌ Xỉu", style=discord.ButtonStyle.danger, custom_id="m_xiu")
        chan_btn = discord.ui.Button(label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="m_chan")
        le_btn = discord.ui.Button(label="🔢 Lẻ", style=discord.ButtonStyle.primary, custom_id="m_le")
        xocdia_btn = discord.ui.Button(label="🎲 Xóc Đĩa", style=discord.ButtonStyle.secondary, custom_id="m_xocdia")

        # Define callbacks
        async def tai_callback(inter):
            await inter.response.send_modal(MenuModal("taixiu", "tai"))
        
        async def xiu_callback(inter):
            await inter.response.send_modal(MenuModal("taixiu", "xiu"))
            
        async def chan_callback(inter):
            await inter.response.send_modal(MenuModal("chanle", "chan"))
            
        async def le_callback(inter):
            await inter.response.send_modal(MenuModal("chanle", "le"))
            
        async def xocdia_callback(inter):
            await inter.response.send_message("🔘 Chọn cửa xóc đĩa:", view=CuocView(inter.user), ephemeral=True)

        # Assign callbacks
        tai_btn.callback = tai_callback
        xiu_btn.callback = xiu_callback
        chan_btn.callback = chan_callback
        le_btn.callback = le_callback
        xocdia_btn.callback = xocdia_callback

        # Add buttons to view
        view.add_item(tai_btn)
        view.add_item(xiu_btn)
        view.add_item(chan_btn)
        view.add_item(le_btn)
        view.add_item(xocdia_btn)

        await interaction.response.send_message("🎮 Chọn trò:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Menu(bot))
