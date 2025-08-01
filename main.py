import os, sys, asyncio, traceback
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from datetime import datetime

# Biến toàn cục để khóa /menu
menu_lock_time = datetime.min

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 730436357838602301

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    print("🔴 App command error:", "".join(traceback.format_exception(type(error), error, error.__traceback__)))
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Đã có lỗi, thử lại sau.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Đã có lỗi, thử lại sau.", ephemeral=True)
    except:
        pass

async def load_cogs():
    for fn in os.listdir("./cogs"):
        if fn.endswith(".py") and not fn.startswith("__"):
            try:
                await bot.load_extension(f"cogs.{fn[:-3]}")
                print(f"✅ Loaded cog: {fn}")
            except Exception as e:
                print(f"❌ Failed loading {fn}: {e}")

@bot.event
async def on_ready():
    await load_cogs()
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Sync failed:", e)

    # Đăng ký các View persistent
    from cogs.menu import MenuView
    from cogs.chanle import ChanLeSelectView
    from cogs.taixiu import TaiXiuView

    bot.add_view(MenuView())
    bot.add_view(TaiXiuView())
    bot.add_view(ChanLeSelectView())

    print(f"✅ Bot online as {bot.user}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id")

            if custom_id == "taixiu_menu":
                from cogs.taixiu import TaiXiuView
                await interaction.response.edit_message(content="🎲 Chọn cược Tài Xỉu", view=TaiXiuView())

            elif custom_id == "chanle_menu":
                from cogs.chanle import ChanLeSelectView
                await interaction.response.edit_message(content="⚪ Chọn cược Chẵn Lẻ", view=ChanLeSelectView())

            elif custom_id == "xocdia_menu":
                from cogs.xocdia import start_xocdia_game
                await start_xocdia_game(interaction)

            elif custom_id.startswith("tx_"):
                from cogs.taixiu import TaiXiuModal
                choice = "tai" if custom_id == "tx_tai" else "xiu" if custom_id == "tx_xiu" else custom_id
                await interaction.response.send_modal(TaiXiuModal(choice))

            elif custom_id in ["cl_chan", "cl_le"]:
                from cogs.chanle import ChanLeModal
                choice = "chan" if custom_id == "cl_chan" else "le"
                await interaction.response.send_modal(ChanLeModal(choice))

            elif custom_id.startswith("back_to_main"):
                from cogs.menu import MenuView
                await interaction.response.edit_message(content="🎮 Chọn trò chơi", view=MenuView())

    except Exception as e:
        print("🔴 Interaction error:", e)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Lỗi xử lý tương tác.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Lỗi xử lý tương tác.", ephemeral=True)
        except:
            pass

@tree.command(name="ping", description="🏓 Pong check")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

@tree.command(name="sync", description="🔄 Đồng bộ lệnh (Admin only)")
async def sync(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
    synced = await tree.sync(guild=interaction.guild)
    await interaction.response.send_message(f"✅ Đã sync {len(synced)} lệnh!", ephemeral=True)

@tree.command(name="resetdaily", description="🔄 Reset /daily (Admin only)")
@app_commands.describe(user="Người cần reset")
async def resetdaily(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("❌ Bạn không có quyền!", ephemeral=True)
    from utils.data_manager import read_json, write_json
    data = read_json("data/user_data.json")
    uid = str(user.id)
    if uid in data:
        del data[uid]
        write_json("data/user_data.json", data)
        await interaction.response.send_message(f"✅ Reset /daily cho {user.mention}", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ️ Chưa nhận /daily.", ephemeral=True)

async def safe_main():
    keep_alive()
    while True:
        try:
            if not TOKEN:
                print("❌ Chưa set TOKEN"); return
            await bot.start(TOKEN)
        except Exception:
            print("🚨 Bot crashed, restarting…", file=sys.stderr)
            traceback.print_exc()
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(safe_main())