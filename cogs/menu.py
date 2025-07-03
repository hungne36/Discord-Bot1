    # cogs/menu.py
import discord
from discord.ext import commands
from discord import app_commands
    # gọi lại các hàm core hoặc slash-handler đã có sẵn trong cog tương ứng
from cogs.taixiu_plus import SumSelect     # view để mở modal đặt sum
from cogs.chanle import ChanleBetModal, ChanleView  # tương tự
from cogs.xocdia import XocDiaView          # view multiplayer

class Menu(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @app_commands.command(
            name="menu",
            description="🎮 Mở giao diện chọn trò chơi: Tài Xỉu Plus, Chẵn/Lẻ, Xóc Đĩa (multiplayer)"
        )
        async def menu(self, interaction: discord.Interaction):
            view = MenuView()
            await interaction.response.send_message(
                "🎮 **Chọn trò chơi**", view=view, ephemeral=True
            )

class MenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            # Tài Xỉu Plus (sum)
            self.add_item(discord.ui.Button(
                label="🔢 Tài Xỉu Plus", style=discord.ButtonStyle.success, custom_id="menu_taixiu_plus"
            ))
            # Chẵn
            self.add_item(discord.ui.Button(
                label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="menu_chan"
            ))
            # Lẻ
            self.add_item(discord.ui.Button(
                label="🔢 Lẻ", style=discord.ButtonStyle.danger, custom_id="menu_le"
            ))
            # Xóc Đĩa multiplayer
            self.add_item(discord.ui.Button(
                label="🥢 Xóc Đĩa (mp)", style=discord.ButtonStyle.secondary, custom_id="menu_xocdia_mp"
            ))

        @discord.ui.button(custom_id="menu_taixiu_plus")
        async def taixiu_plus_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            # mở Select view từ cogs/taixiu_plus.py
            await interaction.response.send_message(
                "🔢 Chọn tối đa 4 số (3–18) để cược:", view=SumSelect(), ephemeral=True
            )

        @discord.ui.button(custom_id="menu_chan")
        async def chan_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            # mở form cược Chẵn (chanle view)
            await interaction.response.send_modal(ChanleBetModal("chan"))

        @discord.ui.button(custom_id="menu_le")
        async def le_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            # mở form cược Lẻ
            await interaction.response.send_modal(ChanleBetModal("le"))

        @discord.ui.button(custom_id="menu_xocdia_mp")
        async def xocdia_mp_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            # bắt đầu phiên xóc dĩa multiplayer
            # defer rồi followup để tránh interaction xóa
            await interaction.response.defer(ephemeral=True)
            view = XocDiaView()
            await interaction.followup.send(
                f"🎲 **{interaction.user.mention}** đã mở phiên Xóc Đĩa Multiplayer! Chọn cửa để cược:",
                view=view
            )

async def setup(bot):
        await bot.add_cog(Menu(bot))
