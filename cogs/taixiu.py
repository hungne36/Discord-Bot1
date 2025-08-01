import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
import random
import json
import asyncio

    # === CẤU HÌNH CƠ BẢN ===
with open("data/sodu.json", "r") as f:sodu_data = json.load(f)

with open("data/lichsu.json", "r") as f:
        lichsu_data = json.load(f)

user_bets = {}

def save_data():
        with open("data/sodu.json", "w") as f:
            json.dump(sodu_data, f, indent=4)
        with open("data/lichsu.json", "w") as f:
            json.dump(lichsu_data, f, indent=4)

    # === CÁC MODAL NHẬP TIỀN ===

class BetModal(Modal):
        def __init__(self, bet_type):
            super().__init__(title="Nhập số tiền cược")
            self.bet_type = bet_type
            self.amount = TextInput(label="Nhập số tiền", placeholder="Ví dụ: 1000000", style=discord.TextStyle.short)
            self.add_item(self.amount)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                amount = int(self.amount.value)
                user_id = str(interaction.user.id)
                if user_id not in sodu_data or sodu_data[user_id] < amount:
                    await interaction.response.send_message("❌ Bạn không đủ tiền cược!", ephemeral=True)
                    return
                if user_id not in user_bets:
                    user_bets[user_id] = []
                user_bets[user_id].append({"type": self.bet_type, "amount": amount})
                await interaction.response.send_message(f"✅ Đã cược {amount:,} vào **{self.bet_type}**", ephemeral=True)
            except:
                await interaction.response.send_message("❌ Số tiền không hợp lệ!", ephemeral=True)

class SumBetModal(Modal):
        def __init__(self, sums):
            super().__init__(title="Cược các tổng")
            self.sums = sums
            self.amount = TextInput(label="Nhập số tiền mỗi tổng", placeholder="Ví dụ: 100000", style=discord.TextStyle.short)
            self.add_item(self.amount)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                amount = int(self.amount.value)
                user_id = str(interaction.user.id)
                total_bet = amount * len(self.sums)
                if user_id not in sodu_data or sodu_data[user_id] < total_bet:
                    await interaction.response.send_message("❌ Bạn không đủ tiền cược!", ephemeral=True)
                    return
                if user_id not in user_bets:
                    user_bets[user_id] = []
                for s in self.sums:
                    user_bets[user_id].append({"type": str(s), "amount": amount})
                await interaction.response.send_message(
                    f"✅ Đã cược {amount:,} vào các tổng {', '.join(map(str, self.sums))}", ephemeral=True)
            except:
                await interaction.response.send_message("❌ Số tiền không hợp lệ!", ephemeral=True)

    # === VIEW SELECT VÀ BUTTON ===

class SumSelect(View):
        def __init__(self):
            super().__init__(timeout=60)
            self.select = Select(
                placeholder="Chọn 4–5 tổng muốn cược",
                options=[discord.SelectOption(label=str(i), value=str(i)) for i in range(3, 19)],
                min_values=4,
                max_values=5
            )
            self.select.callback = self.on_select
            self.add_item(self.select)

        async def on_select(self, interaction: discord.Interaction):
            choices = list(map(int, self.select.values))
            await interaction.response.send_modal(SumBetModal(choices))

class TaiXiuView(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(TaiXiuButton("Tài"))
            self.add_item(TaiXiuButton("Xỉu"))
            self.add_item(ChanLeButton("Chẵn"))
            self.add_item(ChanLeButton("Lẻ"))
            for i in range(3, 19):
                self.add_item(NumberBetButton(str(i)))
            self.add_item(SumSelect())
            self.add_item(EndTaiXiuButton())

class TaiXiuButton(Button):
        def __init__(self, label):
            super().__init__(label=label, style=discord.ButtonStyle.primary)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(BetModal(self.label))

class ChanLeButton(Button):
        def __init__(self, label):
            super().__init__(label=label, style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(BetModal(self.label))

class NumberBetButton(Button):
        def __init__(self, number):
            super().__init__(label=number, style=discord.ButtonStyle.success)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_modal(SumBetModal([int(self.label)]))

class EndTaiXiuButton(Button):
        def __init__(self):
            super().__init__(label="🎯 Kết thúc trò chơi", style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            user_id = str(interaction.user.id)
            bets = user_bets.get(user_id, [])
            if not bets:
                await interaction.followup.send("❌ Bạn chưa đặt cược!", ephemeral=True)
                return

            dice = [random.randint(1, 6) for _ in range(3)]
            total = sum(dice)
            result_text = f"🎲 Kết quả: **{dice[0]} + {dice[1]} + {dice[2]} = {total}**\n"

            result_type = "Tài" if total >= 11 else "Xỉu"
            result_text += f"➡️ {result_type}, {'Chẵn' if total % 2 == 0 else 'Lẻ'}\n\n"

            win = 0
            for bet in bets:
                match = False
                if bet["type"] == result_type or bet["type"] == ("Chẵn" if total % 2 == 0 else "Lẻ"):
                    match = True
                elif bet["type"].isdigit() and int(bet["type"]) == total:
                    match = True
                if match:
                    win += bet["amount"] * 2
                    result_text += f"✅ Thắng cược {bet['type']} (+{bet['amount']*2:,})\n"
                else:
                    result_text += f"❌ Thua cược {bet['type']} (-{bet['amount']:,})\n"

            net = win - sum(b["amount"] for b in bets)
            sodu_data[user_id] = sodu_data.get(user_id, 0) + net
            lichsu_data.setdefault(user_id, []).append({
                "game": "Tài Xỉu",
                "bets": bets,
                "result": total,
                "net": net
            })

            user_bets[user_id] = []
            save_data()
            await interaction.followup.send(result_text)

    # === COG ===

class TaiXiuCog(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.command()
        async def taixiu(self, ctx):
            await ctx.send("🎲 Tài Xỉu - chọn cược:", view=TaiXiuView())

async def setup(bot):
        await bot.add_cog(TaiXiuCog(bot))