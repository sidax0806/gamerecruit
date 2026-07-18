import discord
from discord import app_commands
from discord.ext import commands

# ============================
# モーダル（募集作成）
# ============================
class RecruitModal(discord.ui.Modal, title="ゲーム募集の作成"):
    game = discord.ui.TextInput(
        label="ゲーム名",
        placeholder="例：Apex / FF14 / 原神 など",
        required=True,
        max_length=50
    )

    datetime_text = discord.ui.TextInput(
        label="日時（フリー入力）",
        placeholder="例：7/23 22時 / 揃い次第 / 今から など",
        required=True,
        max_length=50
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
        view = RecruitView(
            game=self.game.value,
            datetime_text=self.datetime_text.value,
            note=self.note.value or "なし",
            owner_id=self.owner_id
        )

        embed = view.build_embed()

        await interaction.response.send_message(
            content="@everyone",
            embed=embed,
            view=view
        )


# ============================
# モーダル（募集編集）
# ============================
class EditRecruitModal(discord.ui.Modal, title="募集内容の編集"):
    def __init__(self, view: "RecruitView"):
        super().__init__()
        self.view = view

        self.game = discord.ui.TextInput(
            label="ゲーム名",
            default=view.game,
            required=True
        )

        self.datetime_text = discord.ui.TextInput(
            label="日時（フリー入力）",
            default=view.datetime_text,
            required=True
        )

        self.note = discord.ui.TextInput(
            label="その他",
            default=view.note,
            required=False,
            style=discord.TextStyle.long
        )

        self.add_item(self.game)
        self.add_item(self.datetime_text)
        self.add_item(self.note)

    async def on_submit(self, interaction: discord.Interaction):
        self.view.game = self.game.value
        self.view.datetime_text = self.datetime_text.value
        self.view.note = self.note.value or "なし"

        # VCが既にある場合は名前を更新
        if self.view.vc_channel:
            await self.view.vc_channel.edit(name=f"{self.view.game} VC")

        await interaction.response.edit_message(
            embed=self.view.build_embed(),
            view=self.view
        )


# ============================
# 募集メッセージの View
# ============================
class RecruitView(discord.ui.View):
    def __init__(self, game, datetime_text, note, owner_id):
        super().__init__(timeout=None)
        self.game = game
        self.datetime_text = datetime_text
        self.note = note
        self.owner_id = owner_id
        self.members = set()
        self.vc_channel = None  # VC未生成

    def build_embed(self):
        member_list = "\n".join([m.mention for m in self.members]) if self.members else "なし"

        embed = discord.Embed(
            title="🎮 ゲーム募集",
            description=(
                f"**ゲーム名**：{self.game}\n"
                f"**日時**：{self.datetime_text}\n"
                f"**その他**：{self.note}\n\n"
                f"**参加者一覧（{len(self.members)}人）**\n{member_list}"
            ),
            color=discord.Color.blue()
        )

        # VC生成後のみ表示
        if self.vc_channel:
            embed.add_field(
                name="VCチャンネル",
                value=self.vc_channel.mention,
                inline=False
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

    @discord.ui.button(label="開始（VC生成）", style=discord.ButtonStyle.blurple)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc_channel:
            await interaction.response.send_message("❌ VCはすでに作成済みです。", ephemeral=True)
            return

        # 募集メッセージがあるカテゴリにVCを作る
        category = interaction.channel.category
        vc = await category.create_voice_channel(f"{self.game} VC")
        self.vc_channel = vc

        # VC監視リストに登録
        if not hasattr(interaction.client, "active_vcs"):
            interaction.client.active_vcs = set()
        interaction.client.active_vcs.add(vc.id)

        # VC削除通知用にメッセージを保存
        if not hasattr(interaction.client, "vc_views"):
            interaction.client.vc_views = {}
        interaction.client.vc_views[vc.id] = interaction.message

        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="編集", style=discord.ButtonStyle.gray)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ 編集できるのは作成者のみです。", ephemeral=True)
            return

        await interaction.response.send_modal(EditRecruitModal(self))

    @discord.ui.button(label="取り下げ", style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ この募集を取り下げできるのは作成者のみです。", ephemeral=True)
            return

        # VCがあれば削除（NotFound対策済み）
        if self.vc_channel:
            try:
                await self.vc_channel.delete()
            except discord.NotFound:
                pass

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
