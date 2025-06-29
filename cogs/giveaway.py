    @app_commands.command(name="giveaway", description="🎉 Admin tạo giveaway thủ công")
    async def giveaway(self, interaction: discord.Interaction):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message("❌ Bạn không có quyền.", ephemeral=True)
        channel = interaction.channel
        embed = discord.Embed(
            title="🎉 GIVEAWAY 10 TỶ XU 🎉",
            description="Tham gia giveaway và đợi admin đóng để biết kết quả!\n"
                        "🥇 Giải nhất: 10 tỷ xu\n"
                        "🥈 Giải nhì: 5 tỷ xu\n"
                        "🥉 Giải ba: 1 tỷ xu\n\n"
                        "Nhấn 🎉 để tham gia!",
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc)
        )
        msg = await channel.send(embed=embed)
        await msg.add_reaction("🎉")

        # Lưu lại để sử dụng cho /donggiveaway
        with open("data/giveaway_temp.json", "w") as f:
            import json
            json.dump({"channel_id": channel.id, "msg_id": msg.id}, f)

        await interaction.response.send_message("✅ Giveaway đã được tạo!", ephemeral=True)
@app_commands.command(name="donggiveaway", description="✅ Đóng giveaway và trao thưởng")
async def donggiveaway(self, interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("❌ Bạn không có quyền.", ephemeral=True)

    import json
    try:
        with open("data/giveaway_temp.json", "r") as f:
            data = json.load(f)
    except:
        return await interaction.response.send_message("❌ Không có giveaway nào đang diễn ra!", ephemeral=True)

    channel = self.bot.get_channel(data["channel_id"])
    msg = await channel.fetch_message(data["msg_id"])
    users = await msg.reactions[0].users().flatten()
    users = [u for u in users if not u.bot]

    if len(users) == 0:
        await channel.send("❌ Không có ai tham gia giveaway.")
        return

    winners = random.sample(users, k=min(3, len(users)))
    reward_text = ""
    for i, winner in enumerate(winners):
        reward = REWARDS[i]
        new_balance = update_balance(winner.id, reward)
        medal = "🥇" if i == 0 else ("🥈" if i == 1 else "🥉")
        reward_text += (
            f"{medal} <@{winner.id}> nhận **{reward:,} xu**\n"
            f"🆔 UID: `{winner.id}` | 🕒 {datetime.utcnow().isoformat()} UTC\n\n"
        )

    await channel.send(f"🎉 **Kết quả Giveaway** 🎉\n{reward_text}")

    # Xoá file trạng thái
    import os
    os.remove("data/giveaway_temp.json")

    await interaction.response.send_message("✅ Giveaway đã được đóng và trả thưởng!", ephemeral=True)