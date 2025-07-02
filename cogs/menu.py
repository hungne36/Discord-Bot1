    # cogs/menu.py
import discord
from discord.ext import commands
from discord import app_commands

    # import đúng các class từ cogs khác
from .taixiu_plus import SumSelect
from .chanle      import ChanLeModal
    from .xocdia      import XocDiaView

    class MenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="🎲 Tài Plus", style=discord.ButtonStyle.success, custom_id="menu_taixiu_plus")
        async def btn_txp(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("🔢 Chọn sum (3–18)…", view=SumSelect(), ephemeral=True)

        @discord.ui.button(label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="menu_chan")
        async def btn_chan(self, interaction: discord.Interaction, button: discord.ui.Button):
            # gọi modal Chẵn/Lẻ, truyền "chan"
            await interaction.response.send_modal(ChanLeModal("chan"))

        @discord.ui.button(label="🔢 Lẻ", style=discord.ButtonStyle.primary, custom_id="menu_le")
        async def btn_le(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(ChanLeModal("le"))

        @discord.ui.button(label="🎲 Xóc Đĩa", style=discord.ButtonStyle.secondary, custom_id="menu_xocdia")
        async def btn_xd(self, interaction: discord.Interaction, button: discord.ui.Button):
            # XocDiaView là View cho xóc đĩa multi-player
            await interaction.response.send_message("🔘 Chọn cửa Xóc Đĩa…", view=XocDiaView(), ephemeral=True)

    class Menu(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(name="menu", description="🎮 Hiển thị menu chọn trò chơi")
        async def menu(self, interaction: discord.Interaction):
            await interaction.response.send_message("🎮 Chọn trò chơi:", view=MenuView(), ephemeral=True)

    async def setup(bot):
        await bot.add_cog(Menu(bot))