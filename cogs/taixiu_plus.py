# cogs/taixiu_plus.py
import discord, random
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_balance, update_balance, add_history, get_pet_buff
from datetime import datetime, timezone

# ――― Bảng tỉ lệ trả thưởng cho mỗi sum (3–18) ―――
payout_rates = {
    3: 60.0, 18: 60.0,
    4: 45.0, 17: 45.0,
    5: 30.0, 16: 30.0,
    6: 15.0, 15: 15.0,
    7:  5.0, 14:  5.0,
    # 8–13 đều x2.5
    8:  2.5, 9:  2.5, 10: 2.5, 11: 2.5, 12: 2.5, 13: 2.5,
}

class SumBetModal(discord.ui.Modal):
    def __init__(self, choices: list[int]):
        super().__init__(title=f"Cược sum: {', '.join(map(str,choices))}")
        self.choices = choices
        self.amount = discord.ui.TextInput(
            label="Số xu cược",
            placeholder="Nhập số (tối thiểu 1.000)",
            max_length=18
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            stake = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Nhập số hợp lệ!", ephemeral=True)
        bal = get_balance(interaction.user.id)
        if stake < 1000 or stake > bal:
            return await interaction.response.send_message("❌ Số xu cược không hợp lệ!", ephemeral=True)

        # Lắc xúc xắc
        dice = [random.randint(1,6) for _ in range(3)]
        total = sum(dice)
        win = total in self.choices

        if win:
            base_rate = payout_rates[total]
            profit    = round(stake * base_rate)
            pet_buff  = get_pet_buff(interaction.user.id)  # % buff
            bonus     = round(profit * pet_buff / 100) if pet_buff else 0
            thaydoi   = stake + profit + bonus
        else:
            profit  = 0
            bonus   = 0
            thaydoi = -stake

        new_bal = update_balance(interaction.user.id, thaydoi)
        add_history(
            interaction.user.id,
            f"taixiu_sum_{'win' if win else 'lose'}",
            thaydoi,
            new_bal
        )

        desc = (
            f"🎲 Kết quả: `{dice}` → **{total}**\n"
            + (f"🎉 Bạn thắng! Profit={profit:,} xu, pet bonus={bonus:,} xu\n"
               f"  • stake={stake:,} + profit + bonus = {thaydoi:,}\n"
             if win else "💸 Bạn thua và mất toàn bộ stake.\n")
            + f"💰 Số dư hiện tại: **{new_bal:,} xu**"
        )
        await interaction.response.send_message(desc, ephemeral=False)

class SumSelect(discord.ui.View):
    def __init__(self, allow_only=None):
        super().__init__(timeout=60)
        if allow_only:
            # Flatten ranges if provided
            allowed_numbers = []
            for item in allow_only:
                if isinstance(item, range):
                    allowed_numbers.extend(list(item))
                else:
                    allowed_numbers.append(item)
            options = [discord.SelectOption(label=str(i), value=str(i)) for i in allowed_numbers]
            placeholder_text = f"Chọn tối đa 4 số ({min(allowed_numbers)}–{max(allowed_numbers)})…"
        else:
            options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(3,19)]
            placeholder_text = "Chọn tối đa 4 số (3–18)…"
        
        self.add_item(discord.ui.Select(
            placeholder=placeholder_text,
            min_values=1, max_values=4,
            options=options,
            custom_id="sum_select"
        ))

    @discord.ui.select(custom_id="sum_select")
    async def on_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        choices = list(map(int, select.values))
        await interaction.response.send_modal(SumBetModal(choices))

class TaiXiuPlus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="taixiu_plus", description="🎲 Cược sum (3–18), tối đa 4 lựa chọn")
    async def taixiu_plus(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🔢 Chọn tối đa 4 số để cược:", view=SumSelect(), ephemeral=True
        )

async def play_taixiu_plus_tai(interaction: discord.Interaction):
    """Mở modal hoặc View để đặt cược cửa TÀI."""
    view = SumSelect(allow_only=[range(11,19)])  # Sum 11-18 cho Tài
    await interaction.response.send_message("🔢 Chọn số để cược TÀI:", view=view, ephemeral=True)

async def play_taixiu_plus_xiu(interaction: discord.Interaction):
    """Mở modal hoặc View để đặt cược cửa XỈU."""
    view = SumSelect(allow_only=[range(3,11)])  # Sum 3-10 cho Xỉu
    await interaction.response.send_message("🔢 Chọn số để cược XỈU:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TaiXiuPlus(bot))