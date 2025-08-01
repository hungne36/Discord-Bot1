# cogs/taixiu.py
import discord, random, asyncio
from discord.ext import commands
from discord import app_commands
from utils.cooldown import can_play
from utils.data_manager import (
    get_balance, update_balance, add_history, get_pet_buff
)
from discord.ui import Modal, TextInput, View, Select, Button

def format_number(n): return f"{n:,}".replace(",", ".")

async def ask_for_bet_amount(interaction):
    """Simple amount validation - you may want to implement a modal for this"""
    # For now, this is a placeholder - you'd implement a modal to ask for amount
    # or modify the button callback to include amount selection
    return None

async def save_bet(user, game_type, choice, amount):
    """Save bet to history - placeholder for now"""
    # This should integrate with your existing history saving logic
    pass

# ――― NUMBER BET BUTTON ―――
class NumberBetButton(discord.ui.Button):
    def __init__(self, number: int):
        super().__init__(label=str(number), style=discord.ButtonStyle.secondary, custom_id=f"tx_sum_{number}")

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        number = int(self.custom_id.split("_")[-1])

        # For now, let's use the existing modal system
        await interaction.response.send_modal(SumBetModal([number]))

# ――― CLASSIC TÀI XỈU ―――
class TaiXiuModal(Modal):
    def __init__(self, choice: str):
        title = f"Cược {'Tài' if choice=='tai' else 'Xỉu'}"
        super().__init__(title=title)
        self.choice = choice
        self.amount = TextInput(
            label="Số xu cược (≥1.000)",
            placeholder="Ví dụ: 10000",
            max_length=18
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        # 1) Cooldown
        ok, wait = can_play(interaction.user.id)
        if not ok:
            return await interaction.response.send_message(
                f"⏳ Vui lòng chờ {int(wait)} giây", ephemeral=True
            )

        # 2) Parse & validate
        try:
            amt = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Số không hợp lệ", ephemeral=True)

        bal = get_balance(interaction.user.id)
        if amt < 1000 or amt > bal:
            return await interaction.response.send_message("❌ Cược phải từ 1.000 đến số dư của bạn", ephemeral=True)

        # 3) Trừ tiền tạm thời
        update_balance(interaction.user.id, -amt)

        # 4) Ghi vào lịch sử cược
        import json
        from datetime import datetime
        with open("data/lichsu.json", "r") as f:
            history = json.load(f)

        history.append({
            "user_id": interaction.user.id,
            "game": "taixiu",
            "choice": self.choice,
            "amount": amt,
            "resolved": False,
            "timestamp": datetime.utcnow().isoformat()
        })

        with open("data/lichsu.json", "w") as f:
            json.dump(history, f, indent=4)

        # Xác định xem cược Tài hay Xỉu
        bet_type = "Tài" if self.choice == "tai" else "Xỉu"

        await interaction.response.send_message(
            f"✅ Bạn đã đặt cược **{bet_type}** với **{format_number(amt)} xu**.\n"
            "⏳ Vui lòng chờ kết thúc trò chơi.",
            ephemeral=True
        )

# ――― PLUS SUM (3–18) ―――
PAYOUT = {
    3:60, 18:60, 4:45,17:45,5:30,16:30,
    6:15,15:15,7:5,14:5,
    **{i:2.5 for i in range(8,14)}
}

class SumBetModal(Modal):
    def __init__(self, choices: list[int]):
        super().__init__(title=f"Cược sum: {', '.join(map(str,choices))}")
        self.choices = choices
        self.amount = TextInput(
            label="Số xu cược (≥1.000)",
            placeholder="Ví dụ: 50000",
            max_length=18
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            stake = int(self.amount.value)
        except:
            return await interaction.response.send_message("❌ Số không hợp lệ", ephemeral=True)

        bal = get_balance(interaction.user.id)
        if stake < 1000 or stake > bal:
            return await interaction.response.send_message("❌ Cược phải từ 1.000 đến số dư của bạn", ephemeral=True)

        # Trừ tiền tạm thời
        update_balance(interaction.user.id, -stake)

        # Ghi vào lịch sử cược
        import json
        from datetime import datetime
        with open("data/lichsu.json", "r") as f:
            history = json.load(f)

        history.append({
            "user_id": interaction.user.id,
            "game": "taixiu_sum",
            "choices": self.choices,
            "amount": stake,
            "resolved": False,
            "timestamp": datetime.utcnow().isoformat()
        })

        with open("data/lichsu.json", "w") as f:
            json.dump(history, f, indent=4)

        # Trong SumBetModal.on_submit, sau phần lưu:
        choice_details = []
        for number in self.choices:
            if 3 <= number <= 10:
                t = "Xỉu"
            else:
                t = "Tài"
            choice_details.append(f"[{number}]{t}")

        await interaction.response.send_message(
            f"✅ Bạn đã đặt cược **{', '.join(choice_details)}** với **{format_number(stake)} xu**.\n"
            "⏳ Vui lòng chờ kết thúc trò chơi.",
            ephemeral=True
        )

class SumSelect(View):
    def __init__(self):
        super().__init__(timeout=60)
        opts = [discord.SelectOption(label=str(i), value=str(i))
                for i in range(3,19)]
        self.add_item(Select(
            placeholder="Chọn tối đa 5 số (3–18)…",
            min_values=4, max_values=5, options=opts
        ))

    @discord.ui.select()
    async def on_select(self, interaction: discord.Interaction, select: Select):
        choices = list(map(int, select.values))
        await interaction.response.send_modal(SumBetModal(choices))

class IndividualNumberView(View):
    def __init__(self):
        super().__init__(timeout=60)
        # Add buttons for numbers 3-18
        for i in range(3, 19):
            self.add_item(NumberBetButton(i))

class NumberBetButton(discord.ui.Button):
    def __init__(self, number: int):
        # Color code buttons based on Tài/Xỉu
        if 3 <= number <= 10:
            style = discord.ButtonStyle.danger  # Red for Xỉu
            label = f"{number}(Xỉu)"
        else:
            style = discord.ButtonStyle.success  # Green for Tài
            label = f"{number}(Tài)"
            
        super().__init__(label=label, style=style, custom_id=f"tx_sum_{number}")

    async def callback(self, interaction: discord.Interaction):
        number = int(self.custom_id.split("_")[-1])
        # Use existing SumBetModal with single number
        await interaction.response.send_modal(SumBetModal([number]))

# ――― COG ĐĂNG KÝ ―――
class TaiXiuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # NOTE: Classic Tài/Xỉu chỉ chạy qua menu ⇒ không cần slash command
    @commands.Cog.listener()
    async def on_ready(self):
        # đăng ký persistent views nếu muốn giữ View sau restart
        self.bot.add_view(SumSelect())

class EndTaiXiuButton(Button):
    def __init__(self):
        super().__init__(label="🎲 Kết thúc trò chơi", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await handle_taixiu_end(interaction)

async def handle_taixiu_end(interaction: discord.Interaction):
    """Handle ending a Tài Xỉu game session"""
    import json
    
    with open("data/lichsu.json", "r") as f:
        lichsu = json.load(f)

    user_bets = [entry for entry in lichsu if entry.get("game") in ["taixiu", "taixiu_sum"] and not entry.get("resolved", False)]

    if not user_bets:
        await interaction.response.send_message("❌ Không có cược nào đang hoạt động trong Tài Xỉu.", ephemeral=True)
        return

    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "tai" if total >= 11 else "xiu"
    result_text = "Tài" if total >= 11 else "Xỉu"

    reward_message = f"🎲 Kết quả: **{dice}** (Tổng: {total} → **{result_text}**)\n\n"

    for bet in user_bets:
        user_id = bet["user_id"]
        amount = bet["amount"]
        
        if bet["game"] == "taixiu":
            # Regular Tài Xỉu bet
            choice = bet["choice"]
            win = (choice == result)
            
            if win:
                profit = round(amount * 0.9)
                buff = get_pet_buff(user_id)
                bonus = round(profit * buff / 100)
                total_win = amount + profit + bonus
                new_balance = update_balance(user_id, total_win)
                add_history(user_id, "taixiu_win", total_win, new_balance)
                reward_message += f"<@{user_id}> thắng {total_win:,} xu (stake + {profit:,} + bonus {bonus:,}) ✅\n"
            else:
                current_balance = get_balance(user_id)
                add_history(user_id, "taixiu_lose", -amount, current_balance)
                reward_message += f"<@{user_id}> thua {amount:,} xu ❌\n"
                
        elif bet["game"] == "taixiu_sum":
            # Sum bet
            choices = bet["choices"]
            win = total in choices
            
            if win:
                rate = PAYOUT[total]
                profit = round(amount * rate)
                buff = get_pet_buff(user_id)
                bonus = round(profit * buff / 100)
                total_win = amount + profit + bonus
                new_balance = update_balance(user_id, total_win)
                add_history(user_id, "taixiu_sum_win", total_win, new_balance)
                reward_message += f"<@{user_id}> thắng {total_win:,} xu (sum {total}, rate x{rate}) ✅\n"
            else:
                current_balance = get_balance(user_id)
                add_history(user_id, "taixiu_sum_lose", -amount, current_balance)
                reward_message += f"<@{user_id}> thua {amount:,} xu ❌\n"

        bet["resolved"] = True

    with open("data/lichsu.json", "w") as f:
        json.dump(lichsu, f, indent=4)

    await interaction.response.send_message(embed=discord.Embed(
        title="🎲 Trò chơi Tài Xỉu đã kết thúc!",
        description=reward_message,
        color=discord.Color.green()
    ))

async def setup(bot):
    await bot.add_cog(TaiXiuCog(bot))