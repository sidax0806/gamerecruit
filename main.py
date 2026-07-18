import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True  # VC監視に必須

bot = commands.Bot(command_prefix="!", intents=intents)


# ============================
# 起動時
# ============================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    # active_vcs が無ければ作る
    if not hasattr(bot, "active_vcs"):
        bot.active_vcs = set()

    # スラッシュコマンド同期
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# ============================
# VC自動削除イベント（完全版）
# ============================
@bot.event
async def on_voice_state_update(member, before, after):
    # VCから抜けた場合（移動も含む）
    if before.channel is not None:

        # このVCが募集で作ったVCかどうか
        if hasattr(bot, "active_vcs") and before.channel.id in bot.active_vcs:

            channel = before.channel  # 最新状態を取得

            # メンバーが0人になったら削除
            if len(channel.members) == 0:
                try:
                    await channel.delete()
                    print(f"Deleted VC: {channel.name}")
                except discord.NotFound:
                    print("VC already deleted (NotFound).")

                # active_vcs から削除
                bot.active_vcs.remove(channel.id)


# ============================
# Cog読み込み
# ============================
async def load_cogs():
    await bot.load_extension("cogs.recruit")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
