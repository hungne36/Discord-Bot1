
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from utils.data_manager import read_json, write_json

HISTORY_FILE = "data/lichsu.json"
BALANCE_FILE = "data/sodu.json"
REWARD_FILE = "data/top_rewards.json"

# Phần thưởng theo thứ hạng
TOP_REWARDS = {
    1: 100_000_000_000,
    2: 70_000_000_000,
    3: 50_000_000_000,
    4: 10_000_000_000,
    5: 5_000_000_000,
    6: 1_000_000_000,
    7: 500_000_000,
    8: 200_000_000,
    9: 100_000_000,
    10: 50_000_000
}

def get_today_str():
    # Dùng UTC để lấy ngày hôm nay
    return datetime.utcnow().strftime("%Y-%m-%d")

def get_user_today_spent(user_id: int) -> int:
    hist = read_json(HISTORY_FILE)
    today = get_today_str()
    # Chỉ tính amount < 0 (xu tiêu), chuyển thành dương
    return sum(
        -h["amount"]
        for h in hist
        if h["user_id"] == user_id
           and h["amount"] < 0
           and h["timestamp"].startswith(today)
    )

def get_top_spenders(target_date=None):
    hist = read_json(HISTORY_FILE)
    date_str = target_date if target_date else get_today_str()
    spent_map: dict[int, int] = {}
    for h in hist:
        if h["timestamp"].startswith(date_str) and h["action"] != "nap" and h["amount"] < 0:
            uid = h["user_id"]
            spent_map[uid] = spent_map.get(uid, 0) - h["amount"]
    top_users = sorted(spent_map.items(), key=lambda x: x[1], reverse=True)
    return top_users[:10], spent_map

class TopXu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="top", description="📊 Xem bảng xếp hạng tiêu xu hôm nay")
    async def top(self, interaction: discord.Interaction):
        top10, spent_map = get_top_spenders()
        user_id = interaction.user.id
        user_spent = spent_map.get(user_id, 0)
        user_rank = next((i+1 for i, (uid, _) in enumerate(top10) if uid == user_id), None)

        embed = discord.Embed(title="🏆 BẢNG XẾP HẠNG TIÊU XU HÔM NAY", color=0xf1c40f)
        for i, (uid, amount) in enumerate(top10, start=1):
            member = await self.bot.fetch_user(uid)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"Top {i}"
            embed.add_field(name=f"{medal} – {member.name}", value=f"💸 {amount:,} xu", inline=False)

        if user_rank:
            rank_str = f"Bạn đang đứng hạng: **Top {user_rank}**"
        elif user_spent > 0:
            rank_str = f"Bạn tiêu: **{user_spent:,} xu**, chưa vào top 10"
        else:
            rank_str = "Bạn chưa tiêu xu hôm nay."

        embed.set_footer(text=rank_str)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="nhantop", description="🎁 Nhận thưởng đua top")
    async def nhantop(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

        top_yesterday, _ = get_top_spenders(target_date=yesterday)
        reward_data = read_json(REWARD_FILE)

        if reward_data.get(yesterday, {}).get(user_id):
            await interaction.response.send_message("❌ Bạn đã nhận thưởng hôm qua rồi!", ephemeral=True)
            return

        for rank, (uid, _) in enumerate(top_yesterday, start=1):
            if str(uid) == user_id:
                reward = TOP_REWARDS.get(rank)
                if not reward:
                    break

                balances = read_json(BALANCE_FILE)
                balances[user_id] = balances.get(user_id, 0) + reward
                write_json(BALANCE_FILE, balances)

                reward_data.setdefault(yesterday, {})[user_id] = True
                write_json(REWARD_FILE, reward_data)

                await interaction.response.send_message(f"🎉 Bạn nhận được **{reward:,} xu** cho Top {rank} hôm qua!", ephemeral=True)
                return

        await interaction.response.send_message("❌ Bạn không nằm trong Top 10 hôm qua!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TopXu(bot))
