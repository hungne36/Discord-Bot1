import discord
from discord.ext import commands
from discord import app_commands
from cogs.taixiu import TaiXiuModal, EndTaiXiuButton
from cogs.chanle import ChanLeModal
from cogs.xocdia import KetThucButton
from utils.data_manager import read_json, write_json
from datetime import datetime, timezone
from main import menu_lock_time

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
        # Check global menu lock
        if datetime.now() < menu_lock_time:
            remaining = int((menu_lock_time - datetime.now()).total_seconds())
            await interaction.response.send_message(
                f"🚫 Vui lòng đợi **{remaining} giây** trước khi sử dụng lại /menu.", 
                ephemeral=True
            )
            return

        # Check cooldown theo kênh
        cooldown_data = read_json("data/menu_cooldown.json")
        channel_id = str(interaction.channel.id)
        now = datetime.now(timezone.utc)
        last_time_str = cooldown_data.get(channel_id)

        if last_time_str:
            try:
                last_time = datetime.fromisoformat(last_time_str)
                if (now - last_time).total_seconds() < 30:
                    remaining = int(30 - (now - last_time).total_seconds())
                    await interaction.response.send_message(
                        f"⚠️ Vui lòng đợi **{remaining} giây** trước khi mở lại menu.",
                        ephemeral=True
                    )
                    return
            except:
                pass  # Bỏ qua nếu lỗi định dạng thời gian

        # Cập nhật cooldown
        cooldown_data[channel_id] = now.isoformat()
        write_json("data/menu_cooldown.json", cooldown_data)

        # Gửi giao diện
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("🎮 Chọn trò chơi", view=MenuView(), ephemeral=True)

async def setup(bot):
        await bot.add_cog(Menu(bot))