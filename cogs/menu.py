
# cogs/menu.py
import discord
from discord.ext import commands
from discord import app_commands

from main import play_taixiu, play_chanle          # Hàm chơi Tài Xỉu + Chẵn Lẻ
from cogs.taixiu_plus import SumSelect            # View chọn số cho taixiu_plus
from utils.xocdia_ui import CuocView               # View Xóc Đĩa chung

class MenuView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎲 Tài Xỉu", style=discord.ButtonStyle.success, custom_id="menu_taixiu")
    async def btn_taixiu(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Modal nhập amount + chọn Tai/Xiu
        class TaiXiuModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Cược Tài/Xỉu")
                self.amount = discord.ui.TextInput(label="Số xu cược", placeholder="Ví dụ: 10000", max_length=18)
                self.choice = discord.ui.TextInput(label="Chọn 'tai' hoặc 'xiu'", placeholder="tai hoặc xiu")
                self.add_item(self.amount)
                self.add_item(self.choice)

            async def on_submit(self, modal_inter: discord.Interaction):
                amt = int(self.amount.value)
                choice = self.choice.value.lower()
                await play_taixiu(modal_inter, amt, choice)

        await interaction.response.send_modal(TaiXiuModal())

    @discord.ui.button(label="🔢 Cược sum", style=discord.ButtonStyle.primary, custom_id="menu_sum")
    async def btn_sum(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Gọi/view SumSelect của taixiu_plus
        await interaction.response.send_message(
            "🔢 Chọn tối đa 4 số (3–18) để cược sum:", 
            view=SumSelect(), 
            ephemeral=True
        )

    @discord.ui.button(label="⚖️ Chẵn/Lẻ", style=discord.ButtonStyle.secondary, custom_id="menu_chanle")
    async def btn_chanle(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Modal nhập amount + chọn Chan/Le
        class ChanLeModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Cược Chẵn/Lẻ")
                self.amount = discord.ui.TextInput(label="Số xu cược", placeholder="Ví dụ: 10000", max_length=18)
                self.choice = discord.ui.TextInput(label="Chọn 'chan' hoặc 'le'", placeholder="chan hoặc le")
                self.add_item(self.amount)
                self.add_item(self.choice)

            async def on_submit(self, modal_inter: discord.Interaction):
                amt = int(self.amount.value)
                choice = self.choice.value.lower()
                await play_chanle(modal_inter, amt, choice)

        await interaction.response.send_modal(ChanLeModal())

    @discord.ui.button(label="🎲 Xóc Đĩa", style=discord.ButtonStyle.danger, custom_id="menu_xocdia")
    async def btn_xocdia(self, interaction: discord.Interaction, button: discord.ui.Button):
        # View Xóc Đĩa nhiều người
        await interaction.response.send_message(
            "🔘 Chọn các cửa muốn cược:", 
            view=CuocView(interaction.user), 
            ephemeral=True
        )

class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="menu", description="Hiển thị menu chọn trò chơi")
    async def menu(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎮 Chọn trò chơi:", view=MenuView(self.bot), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Menu(bot))
