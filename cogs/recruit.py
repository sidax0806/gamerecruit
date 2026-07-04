import discord
from discord import app_commands
from discord.ext import commands

class RecruitView(discord.ui.View):
    def __init__(self, game, time, note, owner_id):
        super().__init__(timeout=None)
        self.game = game
        self.time = time
        self.note = note
        self.owner_id = owner_id  # ← 追加：募集作成者のID
        self.members = set()

    def build_embed(self):
        member_list = "\n".join([m.mention for m in self.members]) if self.members else "なし"

        embed = discord.Embed(
            title="🎮 ゲーム募集",
            description=(
                f"**ゲーム名**：{self.game}\n"
                f"**開始時間**：{self.time}\n"
                f"**その他**：{self.note}\n\n"
                f"**参加者一覧（{len(self.members)}人）**\n{member_list}"
            ),
            color=discord.Color.blue()
        )
        return embed

    @discord.ui.button(label="参加", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.members.add(interaction.user)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="辞退", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.members:
            self.members.remove(interaction.user)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="取り下げ", style=discord.ButtonStyle.gray)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):

        # ← 追加：作成者以外は取り下げ禁止
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ この募集を取り下げできるのは作成者のみです。",
                ephemeral=True
            )
            return

        await interaction.message.delete()
        await interaction.response.send_message("募集を取り下げました。", ephemeral=True)


class Recruit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="recruit", description="ゲーム募集を作成します")
    @app_commands.describe(
        game="ゲーム名",
        time="開始時間（例：21:00）",
        note="その他（任意）"
    )
    async def recruit(self, interaction: discord.Interaction, game: str, time: str, note: str = "なし"):

        # ← 追加：作成者IDを渡す
        view = RecruitView(game, time, note, interaction.user.id)
        embed = view.build_embed()

        await interaction.response.send_message(
            content="@everyone",
            embed=embed,
            view=view
        )


async def setup(bot):
    await bot.add_cog(Recruit(bot))
