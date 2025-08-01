import discord
from discord.ext import commands
from discord import app_commands
from cogs.taixiu import TaiXiuView   # ← Import đúng view, không phải BetModal
from cogs.chanle import ChanLeSelectView
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

    # Giao diện chọn cược Tài Xỉu: không cần để test embed ở đây, sử dụng TaiXiuView từ taixiu.py
class TaiXiuSelectView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            # Các nút đã được định nghĩa trong TaiXiuView, bạn không cần view này nữa.
            # Chỉ giữ lại nếu bạn muốn view đặc biệt khác.

    # Lệnh /menu và listener xử lý nút
class Menu(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_interaction(self, interaction: discord.Interaction):
            # Bắt sự kiện component click
            if interaction.type == discord.InteractionType.component:
                cid = interaction.data.get("custom_id")
                if cid == "taixiu_menu":
                    # Mở giao diện Tài Xỉu thực sự
                    await interaction.response.send_message(
                        "🎲 Tài Xỉu - chọn cược:", view=TaiXiuView(), ephemeral=True
                    )
                elif cid == "chanle_menu":
                    await interaction.response.send_message(
                        "⚪ Chẵn Lẻ - chọn cược:", view=ChanLeSelectView(), ephemeral=True
                    )
                elif cid == "xocdia_menu":
                    await interaction.response.send_message(
                        "🪙 Xóc Đĩa - bắt đầu:", view=KetThucButton("xocdia"), ephemeral=True
                    )

        @app_commands.command(name="menu", description="🎮 Mở giao diện chọn trò chơi")
        async def menu(self, interaction: discord.Interaction):
            # Check global menu lock
            if datetime.now() < menu_lock_time:
                remaining = int((menu_lock_time - datetime.now()).total_seconds())
                return await interaction.response.send_message(
                    f"🚫 Vui lòng đợi **{remaining} giây** trước khi sử dụng lại /menu.",
                    ephemeral=True
                )

            # Check cooldown theo kênh
            cooldown_data = read_json("data/menu_cooldown.json")
            channel_id = str(interaction.channel.id)
            now = datetime.now(timezone.utc)
            last_time_str = cooldown_data.get(channel_id)

            if last_time_str:
                try:
                    last_time = datetime.fromisoformat(last_time_str)
                    diff = (now - last_time).total_seconds()
                    if diff < 30:
                        remaining = int(30 - diff)
                        return await interaction.response.send_message(
                            f"⚠️ Vui lòng đợi **{remaining} giây** trước khi mở lại menu.",
                            ephemeral=True
                        )
                except:
                    pass

            # Cập nhật cooldown
            cooldown_data[channel_id] = now.isoformat()
            write_json("data/menu_cooldown.json", cooldown_data)

            # Gửi giao diện chính
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("🎮 Chọn trò chơi", view=MenuView(), ephemeral=True)

async def setup(bot):
        await bot.add_cog(Menu(bot))
        # Đăng ký listener
        bot.add_listener(Menu.on_interaction)