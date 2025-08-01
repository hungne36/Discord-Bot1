import discord
from discord.ext import commands
from discord import app_commands
from cogs.taixiu import TaiXiuModal, EndTaiXiuButton
from cogs.chanle import ChanLeModal
from cogs.xocdia import KetThucButton

# Giao diện chính chọn game
class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="🎲 Tài Xỉu", style=discord.ButtonStyle.primary, custom_id="taixiu_menu"))
        self.add_item(discord.ui.Button(label="⚪ Chẵn Lẻ", style=discord.ButtonStyle.primary, custom_id="chanle_menu"))
        self.add_item(discord.ui.Button(label="🪙 Xóc Đĩa", style=discord.ButtonStyle.primary, custom_id="xocdia_menu"))

# Giao diện chọn cược Tài Xỉu
class TaiXiuSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.create_sum_buttons()
        self.add_item(discord.ui.Button(label="⬅️ Quay lại", style=discord.ButtonStyle.gray, custom_id="back_to_main_taixiu"))
        self.add_item(EndTaiXiuButton())

    def create_sum_buttons(self):
        for i in range(3, 18):
            btn = discord.ui.Button(label=str(i), style=discord.ButtonStyle.secondary, custom_id=f"tx_{i}")
            btn.callback = self.make_callback(i)
            self.add_item(btn)

        self.add_item(discord.ui.Button(label="🎲 Tài", style=discord.ButtonStyle.success, custom_id="tx_tai"))
        self.add_item(discord.ui.Button(label="🎲 Xỉu", style=discord.ButtonStyle.danger, custom_id="tx_xiu"))

    def make_callback(self, value):
        async def callback(interaction: discord.Interaction):
            await interaction.response.send_modal(TaiXiuModal(f"tx_{value}"))
        return callback

# Giao diện chọn cược Chẵn Lẻ
class ChanLeSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="⚪ Chẵn", style=discord.ButtonStyle.success, custom_id="cl_chan"))
        self.add_item(discord.ui.Button(label="🔴 Lẻ", style=discord.ButtonStyle.danger, custom_id="cl_le"))
        self.add_item(discord.ui.Button(label="⬅️ Quay lại", style=discord.ButtonStyle.gray, custom_id="back_to_main_chanle"))
        self.add_item(KetThucButton("chanle"))

# Lệnh /menu
class Menu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="menu", description="🎮 Mở giao diện chọn trò chơi")
    async def menu(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("🎮 Chọn trò chơi", view=MenuView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Menu(bot))