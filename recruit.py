import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

WEEKDAYS = ["月", "火", "水", "木", "金", "土", "日"]


# ============================
# モーダル（入力フォーム）
# ============================
class RecruitModal(discord.ui.Modal, title="ゲーム募集の作成"):
    game = discord.ui.TextInput(
        label="ゲーム名",
        placeholder="例：Apex / FF14 / 原神 など",
        required=True,
        max_length=50
    )

    date = discord.ui.TextInput(
        label="日付（YYYY-MM-DD）",
        placeholder="例：2026-07-18",
        required=True,
        max_length=10
    )

    time = discord.ui.TextInput(
        label="開始時間（例：21:00）",
        placeholder="例：21:00",
        required=True,
        max_length=10
    )

    note = discord.ui.TextInput(
        label="その他（任意）",
        placeholder="VCあり / 初心者歓迎 など",
        required=False,
        style=discord.TextStyle.long
    )

    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    async def on_submit(self, interaction: discord.Interaction):
        # 日付の形式チェック
        try:
            parsed_date = datetime.strptime(self.date.value, "%Y-%m-%d").date()
        except ValueError:
            await interaction.response.send_message(
                "❌ 日付の形式が正しくありません。例：2026-07-18",
                ephemeral=True
            )
            return

        # View を作成
        view = RecruitView(
            game=self.game.value,
            time=self.time.value,
            note=self.note.value or "なし",
            date=parsed_date,
            owner_id=self.owner_id
        )

        embed = view.build_embed()

        await interaction.response.send_message(
            content="@everyone",
            embed=embed,
            view=view
        )


# ============================
# 募集メッセージの View
# ============================
class RecruitView(discord.ui.View):
    def __init__(self, game, time, note, date, owner_id):
        super().__init__(timeout=None)
        self.game = game
        self.time = time
        self.note = note
        self.date = date  # datetime.date 型
        self.owner_id = owner_id
        self.members = set()

    def build_embed(self):
        weekday = WEEKDAYS[self.date.weekday()]  # 曜日を自動計算

        member_list = "\n".join([m.mention for m in self.members]) if self.members else "なし"

        embed = discord.Embed(
            title="🎮 ゲーム募集",
            description=(
                f"**日付**：{self.date.strftime('%Y-%m-%d')}（{weekday}）\n"
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
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ この募集を取り下げできるのは作成者のみです。",
                ephemeral=True
            )
            return

        await interaction.message.delete()
        await interaction.response.send_message("募集を取り下げました。", ephemeral=True)


# ============================
# Cog 本体
# ============================
class Recruit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="募集", description="ゲーム募集を作成します")
    async def recruit(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RecruitModal(owner_id=interaction.user.id))


async def setup(bot):
    await bot.add_cog(Recruit(bot))
