import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()

class RecruitBot(commands.Bot):
    async def setup_hook(self):
        # Cog を読み込む（ここは非同期OK）
        await self.load_extension("cogs.recruit")

        # スラッシュコマンド同期
        await self.tree.sync()
        print("Slash commands synced.")

bot = RecruitBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
