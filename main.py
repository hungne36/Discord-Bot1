import discord
from discord.ext import commands
from discord import app_commands
import os
from utils import data_manager
import random

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 730436357838602301

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

    # Load all cogs
async def load_cogs():
        for cog in ["menu", "info", "nap", "lichsu", "daily", "phucloi"]:
            await bot.load_extension(f"cogs.{cog}")

@bot.event
async def on_ready():
        await load_cogs()
        await tree.sync()
        print(f"✅ Bot đã online: {bot.user}")

    # /ping
@tree.command(name="ping", description="Kiểm tra trạng thái bot")
async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

    # /resetdaily (Admin)
@tree.command(name="resetdaily", description="Reset quà khởi đầu cho người dùng (admin)")
@app_commands.describe(user="Người dùng cần reset")
async def resetdaily(interaction: discord.Interaction, user: discord.User):
        if interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
            return

        data = data_manager.read_json("data/user_data.json")
        uid = str(user.id)

        if uid in data:
            del data[uid]
            data_manager.write_json("data/user_data.json", data)
            await interaction.response.send_message(f"✅ Đã reset /daily cho {user.mention}", ephemeral=True)
        else:
            await interaction.response.send_message(f"ℹ️ Người dùng này chưa từng nhận /daily", ephemeral=True)

    # Game functions
async def play_taixiu(interaction, amount, choice):
    uid = interaction.user.id
    balance = data_manager.get_balance(uid)
    
    if amount > balance:
        await interaction.response.send_message("❌ Không đủ xu để đặt cược!", ephemeral=True)
        return
    
    # Roll 3 dice
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    
    # Determine result
    is_tai = total >= 11
    result = "tài" if is_tai else "xỉu"
    
    # Check if player won
    won = (choice == "tai" and is_tai) or (choice == "xiu" and not is_tai)
    
    if won:
        winnings = amount * 2
        new_balance = data_manager.update_balance(uid, winnings)
        data_manager.add_history(uid, f"taixiu_thắng_{choice}", winnings, new_balance)
        
        embed = discord.Embed(title="🎲 Tài Xỉu", color=0x00ff00)
        embed.add_field(name="Kết quả", value=f"🎲 {dice[0]} - {dice[1]} - {dice[2]} (Tổng: {total})\n🎯 **{result.upper()}**", inline=False)
        embed.add_field(name="🏆 Thắng!", value=f"Bạn nhận được: **{winnings:,} xu**\nSố dư mới: **{new_balance:,} xu**", inline=False)
    else:
        new_balance = data_manager.update_balance(uid, -amount)
        data_manager.add_history(uid, f"taixiu_thua_{choice}", -amount, new_balance)
        
        embed = discord.Embed(title="🎲 Tài Xỉu", color=0xff0000)
        embed.add_field(name="Kết quả", value=f"🎲 {dice[0]} - {dice[1]} - {dice[2]} (Tổng: {total})\n🎯 **{result.upper()}**", inline=False)
        embed.add_field(name="💥 Thua!", value=f"Bạn mất: **{amount:,} xu**\nSố dư mới: **{new_balance:,} xu**", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def play_chanle(interaction, amount, choice):
    uid = interaction.user.id
    balance = data_manager.get_balance(uid)
    
    if amount > balance:
        await interaction.response.send_message("❌ Không đủ xu để đặt cược!", ephemeral=True)
        return
    
    # Roll a single die
    dice_result = random.randint(1, 6)
    is_chan = dice_result % 2 == 0
    result = "chẵn" if is_chan else "lẻ"
    
    # Check if player won
    won = (choice == "chan" and is_chan) or (choice == "le" and not is_chan)
    
    if won:
        winnings = amount * 2
        new_balance = data_manager.update_balance(uid, winnings)
        data_manager.add_history(uid, f"chanle_thắng_{choice}", winnings, new_balance)
        
        embed = discord.Embed(title="🎲 Chẵn Lẻ", color=0x00ff00)
        embed.add_field(name="Kết quả", value=f"🎲 **{dice_result}** ({result})", inline=False)
        embed.add_field(name="🏆 Thắng!", value=f"Bạn nhận được: **{winnings:,} xu**\nSố dư mới: **{new_balance:,} xu**", inline=False)
    else:
        new_balance = data_manager.update_balance(uid, -amount)
        data_manager.add_history(uid, f"chanle_thua_{choice}", -amount, new_balance)
        
        embed = discord.Embed(title="🎲 Chẵn Lẻ", color=0xff0000)
        embed.add_field(name="Kết quả", value=f"🎲 **{dice_result}** ({result})", inline=False)
        embed.add_field(name="💥 Thua!", value=f"Bạn mất: **{amount:,} xu**\nSố dư mới: **{new_balance:,} xu**", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

    # Run bot
if __name__ == "__main__":
        if TOKEN:
            bot.run(TOKEN)
        else:
            print("❌ Thiếu biến môi trường TOKEN")