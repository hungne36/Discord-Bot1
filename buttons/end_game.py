import discord
from discord.ui import Button
from utils.data_manager import load_json, save_json
from datetime import datetime, timezone, timedelta
from main import menu_lock_time

class EndGameButton(Button):
    def __init__(self, game_name: str, channel, cooldown_seconds=30):
        super().__init__(label="🎯 Kết thúc trò chơi", style=discord.ButtonStyle.danger, row=3)
        self.game_name = game_name
        self.channel = channel
        self.cooldown_seconds = cooldown_seconds

    async def callback(self, interaction: discord.Interaction):
        global menu_lock_time
        
        if interaction.channel != self.channel:
            await interaction.response.send_message("Bạn không thể kết thúc trò chơi này ở đây.", ephemeral=True)
            return

        # Đóng toàn bộ nút (disable view)
        for item in self.view.children:
            item.disabled = True
        await interaction.message.edit(view=self.view)

        # Lưu cooldown cho kênh
        cooldown_data = load_json("data/menu_cooldown.json")
        now = datetime.now(timezone.utc)
        cooldown_data[str(interaction.channel.id)] = now.isoformat()
        save_json("data/menu_cooldown.json", cooldown_data)

        # Set global menu lock
        menu_lock_time = datetime.now() + timedelta(seconds=30)

        await interaction.response.send_message(
            f"🛑 Đã kết thúc trò chơi **{self.game_name}**.\n"
            f"⏳ Vui lòng đợi **{self.cooldown_seconds} giây** để bắt đầu ván mới.",
            ephemeral=False
        )
        
        await interaction.followup.send("✅ Trò chơi đã kết thúc. /menu sẽ khả dụng lại sau 30 giây.", ephemeral=True)