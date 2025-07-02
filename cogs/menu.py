import discord
from discord.ext import commands
from discord import app_commands
from main import play_taixiu, play_chanle  # Dùng lại logic từ main
from utils.xocdia_ui import CuocView  # Import View chọn cửa từ Xóc Đĩa

class BetModal(discord.ui.Modal):
    def __init__(self, game: str, choice: str):
        title = f"Đặt cược {'Tài Xỉu' if game == 'taixiu' else 'Chẵn Lẻ'}"
        super().__init__(title=title)
        self.game = game
        self.choice = choice

        self.amount = discord.ui.TextInput(
            label="Số xu cược",
            placeholder="Nhập số (ví dụ: 10000)",
            max_length=30,
            style=discord.TextStyle.short
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.amount.value.isdigit():
            return await interaction.response.send_message("❌ Vui lòng nhập số hợp lệ!", ephemeral=True)
        amt = int(self.amount.value)
        if self.game == "taixiu":
            await play_taixiu(interaction, amt, self.choice)
        else:
            await play_chanle(interaction, amt, self.choice)
        
        # Delete the original menu message
        try:
            await interaction.message.delete()
        except:
            pass  # Ignore if message is already deleted or can't be deleted

class MenuView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎲 Tài", style=discord.ButtonStyle.success, custom_id="menu_tai")
    async def btn_tai(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetModal("taixiu", "tai"))

    @discord.ui.button(label="❌ Xỉu", style=discord.ButtonStyle.danger, custom_id="menu_xiu")
    async def btn_xiu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetModal("taixiu", "xiu"))

    @discord.ui.button(label="⚖️ Chẵn", style=discord.ButtonStyle.primary, custom_id="menu_chan")
    async def btn_chan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetModal("chanle", "chan"))

    @discord.ui.button(label="🔢 Lẻ", style=discord.ButtonStyle.primary, custom_id="menu_le")
    async def btn_le(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetModal("chanle", "le"))

    @discord.ui.button(label="🎲 Xóc Đĩa", style=discord.ButtonStyle.secondary, custom_id="menu_xocdia")
    async def btn_xocdia(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = CuocView(interaction.user)
        await interaction.response.send_message("🔘 Chọn các cửa muốn cược:", view=view, ephemeral=True)

class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="menu", description="Hiển thị menu chọn trò chơi")
    async def menu(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎮 Chọn trò chơi:", view=MenuView(self.bot), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Menu(bot))