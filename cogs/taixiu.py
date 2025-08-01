    # cogs/taixiu.py
import discord, random, asyncio, json
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Select, Button
from datetime import datetime

from utils.cooldown import can_play
from utils.data_manager import (
    get_balance, update_balance, add_history, get_pet_buff
)

# ――― Tiền thưởng theo tổng ―――
PAYOUT = {
    3:60, 18:60, 4:45, 17:45, 5:30, 16:30,
    6:15, 15:15, 7:5, 14:5,
    **{i:2.5 for i in range(8,14)}
}

def format_number(n): return f"{n:,}".replace(",", ".")

# ――― MODAL: Tài/Xỉu cơ bản ―――
class TaiXiuModal(Modal):
        def __init__(self, choice: str):
            title = f"Cược {'Tài' if choice=='tai' else 'Xỉu' if choice=='xiu' else choice}"
            super().__init__(title=title)
            self.choice = choice
            self.amount = TextInput(
                label="Số xu cược (≥1.000)",
                placeholder="Ví dụ: 10000",
                max_length=18
            )
            self.add_item(self.amount)

        async def on_submit(self, interaction: discord.Interaction):
            # 1. Cooldown
            ok, wait = can_play(interaction.user.id)
            if not ok:
                return await interaction.response.send_message(
                    f"⏳ Vui lòng chờ {int(wait)} giây", ephemeral=True
                )

            # 2. Parse & check balance
            try:
                amt = int(self.amount.value)
            except:
                return await interaction.response.send_message("❌ Số không hợp lệ", ephemeral=True)

            bal = get_balance(interaction.user.id)
            if amt < 1000 or amt > bal:
                return await interaction.response.send_message("❌ Cược phải từ 1.000 đến số dư của bạn", ephemeral=True)

            # 3. Trừ xu và ghi lịch sử
            update_balance(interaction.user.id, -amt)
            with open("data/lichsu.json", "r") as f:
                history = json.load(f)

            game_type = "taixiu_sum" if self.choice.startswith("tx_") else "taixiu"
            choice_val = self.choice.replace("tx_", "")

            entry = {
                "user_id": interaction.user.id,
                "game": game_type,
                "resolved": False,
                "amount": amt,
                "timestamp": datetime.utcnow().isoformat()
            }

            if game_type == "taixiu_sum":
                entry["choices"] = [int(choice_val)]
            else:
                entry["choice"] = choice_val

            history.append(entry)

            with open("data/lichsu.json", "w") as f:
                json.dump(history, f, indent=4)

            label = f"**{choice_val.upper()}**" if game_type == "taixiu" else f"**{choice_val} điểm**"
            await interaction.response.send_message(
                f"✅ Bạn đã đặt cược {label} với **{format_number(amt)} xu**.\n⏳ Vui lòng chờ kết thúc trò chơi.",
                ephemeral=True
            )

    # ――― MODAL: Đặt nhiều tổng (3–18) ―――
class SumBetModal(Modal):
        def __init__(self, choices: list[int]):
            super().__init__(title=f"Cược tổng: {', '.join(map(str,choices))}")
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

            update_balance(interaction.user.id, -stake)

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

            labels = [f"[{c}]{'Tài' if c >= 11 else 'Xỉu'}" for c in self.choices]
            await interaction.response.send_message(
                f"✅ Bạn đã đặt cược {', '.join(labels)} với **{format_number(stake)} xu**.\n⏳ Vui lòng chờ kết thúc trò chơi.",
                ephemeral=True
            )

    # ――― UI: Chọn tổng (Select hoặc Button) ―――
class SumSelect(View):
        def __init__(self):
            super().__init__(timeout=60)
            options = [discord.SelectOption(label=str(i), value=str(i)) for i in range(3, 19)]
            self.add_item(Select(placeholder="Chọn 4–5 tổng muốn cược", options=options, min_values=4, max_values=5))

        @discord.ui.select()
        async def on_select(self, interaction: discord.Interaction, select: Select):
            choices = list(map(int, select.values))
            await interaction.response.send_modal(SumBetModal(choices))

class NumberBetButton(discord.ui.Button):
        def __init__(self, number: int):
            style = discord.ButtonStyle.success if number >= 11 else discord.ButtonStyle.danger
            super().__init__(label=str(number), style=style, custom_id=f"tx_sum_{number}")

        async def callback(self, interaction: discord.Interaction):
            number = int(self.custom_id.split("_")[-1])
            await interaction.response.send_modal(SumBetModal([number]))

class IndividualNumberView(View):
        def __init__(self):
            super().__init__(timeout=60)
            for i in range(3, 19):
                self.add_item(NumberBetButton(i))

    # ――― Kết thúc trò chơi ―――
class EndTaiXiuButton(Button):
        def __init__(self):
            super().__init__(label="🎲 Kết thúc trò chơi", style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            await handle_taixiu_end(interaction)

async def handle_taixiu_end(interaction: discord.Interaction):
        with open("data/lichsu.json", "r") as f:
            lichsu = json.load(f)

        user_id = interaction.user.id
        user_bets = [x for x in lichsu if x["game"] in ["taixiu", "taixiu_sum"]
                     and not x.get("resolved", False)
                     and x["user_id"] == user_id]

        if not user_bets:
            return await interaction.response.send_message("❌ Không có cược nào đang hoạt động trong Tài Xỉu.", ephemeral=True)

        dice = [random.randint(1, 6) for _ in range(3)]
        total = sum(dice)
        result = "tai" if total >= 11 else "xiu"
        result_text = "Tài" if total >= 11 else "Xỉu"

        reward_msg = f"🎲 Kết quả: **{dice}** (Tổng: {total} → **{result_text}**)\n\n"

        for bet in user_bets:
            uid = bet["user_id"]
            amt = bet["amount"]
            buff = get_pet_buff(uid)

            if bet["game"] == "taixiu":
                win = bet["choice"] == result
                if win:
                    profit = round(amt * 0.9)
                    bonus = round(profit * buff / 100)
                    total_win = amt + profit + bonus
                    new_bal = update_balance(uid, total_win)
                    add_history(uid, "taixiu_win", total_win, new_bal)
                    reward_msg += f"<@{uid}> thắng {format_number(total_win)} xu ✅\n"
                else:
                    add_history(uid, "taixiu_lose", -amt, get_balance(uid))
                    reward_msg += f"<@{uid}> thua {format_number(amt)} xu ❌\n"

            elif bet["game"] == "taixiu_sum":
                win = total in bet["choices"]
                if win:
                    rate = PAYOUT[total]
                    profit = round(amt * rate)
                    bonus = round(profit * buff / 100)
                    total_win = amt + profit + bonus
                    new_bal = update_balance(uid, total_win)
                    add_history(uid, "taixiu_sum_win", total_win, new_bal)
                    reward_msg += f"<@{uid}> thắng {format_number(total_win)} xu (x{rate}) ✅\n"
                else:
                    add_history(uid, "taixiu_sum_lose", -amt, get_balance(uid))
                    reward_msg += f"<@{uid}> thua {format_number(amt)} xu ❌\n"

            bet["resolved"] = True

        with open("data/lichsu.json", "w") as f:
            json.dump(lichsu, f, indent=4)

        await interaction.response.send_message(embed=discord.Embed(
            title="🎲 Trò chơi Tài Xỉu đã kết thúc!",
            description=reward_msg,
            color=discord.Color.green()
        ))

    # ――― EndTaiXiuView ―――
class EndTaiXiuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(EndTaiXiuButton())

    # ――― COG Setup ―――
class TaiXiuCog(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_ready(self):
            self.bot.add_view(SumSelect())
            self.bot.add_view(IndividualNumberView())
            self.bot.add_view(EndTaiXiuView())

async def setup(bot):
    await bot.add_cog(TaiXiuCog(bot))