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

    if not hasattr(bot, "active_vcs"):
        bot.active_vcs = set()

    if not hasattr(bot, "vc_views"):
        bot.vc_views = {}

    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# ============================
# VC自動削除イベント（通知付き）
# ============================
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        if before.channel.id in bot.active_vcs:

            channel = before.channel

            if len(channel.members) == 0:
                try:
                    await channel.delete()
                    print(f"Deleted VC: {channel.name}")
                except discord.NotFound:
                    print("VC already deleted (NotFound).")

                # VC削除通知
                msg = bot.vc_views.get(channel.id)
                if msg:
                    try:
                        await msg.reply("🔔 VCが削除されました（無人になったため）")
                    except:
                        pass

                bot.active_vcs.remove(channel.id)
                bot.vc_views.pop(channel.id, None)


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
