import os
import json
import asyncio
from datetime import datetime, timezone
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

# Flask サーバー設定（Renderのスリープ防止用）
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot設定
TOKEN = os.environ.get("DISCORD_TOKEN")
CONFIG_FILE = "bot_config.json"

# デフォルト設定（サーバー新規登録時用）
DEFAULT_GUILD_CONFIG = {
    "target_channels": ["おひるね", "睡眠厨", "保健室"],
    "cut_off_minutes": 120
}

# サーバーごとの設定を読み込む関数
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
    return {}

# サーバーごとの設定を保存する関数
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 指定されたサーバーの設定を取得（なければデフォルトを作成）
def get_guild_config(guild_id):
    config = load_config()
    str_guild_id = str(guild_id)
    if str_guild_id not in config:
        config[str_guild_id] = DEFAULT_GUILD_CONFIG.copy()
        save_config(config)
    return config[str_guild_id]

# Discord Botの初期化（デフォルトの!helpを無効化）
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ユーザーのVC入室時間を管理する辞書
join_times = {}

@bot.event
async def on_ready():
    print(f"Bot起動完了: {bot.user.name}")
    bot.loop.create_task(check_vc_timeout())

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    guild_id = member.guild.id
    guild_config = get_guild_config(guild_id)
    target_channels = guild_config.get("target_channels", [])

    # VCに入室、またはチャンネルを移動した場合
    if after.channel is not None and (before.channel != after.channel):
        if after.channel.name in target_channels:
            join_times[(guild_id, member.id)] = datetime.now(timezone.utc)
        else:
            join_times.pop((guild_id, member.id), None)

    # VCから切断（退出）した場合
    elif after.channel is None:
        join_times.pop((guild_id, member.id), None)

async def check_vc_timeout():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(10)
        now = datetime.now(timezone.utc)

        for (guild_id, user_id), join_time in list(join_times.items()):
            guild = bot.get_guild(guild_id)
            if not guild:
                continue

            guild_config = get_guild_config(guild_id)
            cut_off_minutes = guild_config.get("cut_off_minutes", 120)
            target_channels = guild_config.get("target_channels", [])

            member = guild.get_member(user_id)
            
            if not member or not member.voice or not member.voice.channel or member.voice.channel.name not in target_channels:
                join_times.pop((guild_id, user_id), None)
                continue

            elapsed_minutes = (now - join_time).total_seconds() / 60
            if elapsed_minutes >= cut_off_minutes:
                try:
                    await member.move_to(None)
                    print(f"[{guild.name}] {member.display_name} を {member.voice.channel.name} から自動切断しました（{cut_off_minutes}分経過）。")
                except Exception as e:
                    print(f"[{guild.name}] {member.display_name} の切断に失敗しました: {e}")
                
                join_times.pop((guild_id, user_id), None)

# --- コマンド処理 ---

# ヘルプコマンド（!sleepy）- 画像風のEmbed表示
@bot.command(name="sleepy")
async def sleepy_help(ctx):
    # 画像に合わせた紫色のEmbedを作成
    embed = discord.Embed(
        title="🛌 寝落ち防止Bot コマンドヘルプ",
        description="指定されたボイスチャンネルで一定時間が経過すると、自動的にVCから切断します。\n設定はサーバーごとに独立して保存されます。",
        color=0x9b59b6 # 画像に近い紫色
    )
    
    # 各コマンドをフィールドとして追加（inline=Falseで縦並びに）
    embed.add_field(
        name="`!status` (または `!config`)",
        value="現在の自動切断時間と対象チャンネルの一覧を表示します。（誰でも使用可能）",
        inline=False
    )
    embed.add_field(
        name="`!set_time <分数>`",
        value="自動切断までの時間を「分」単位で設定します。\n*(例: `!set_time 60` ➔ 60分に設定) ※管理者のみ*",
        inline=False
    )
    embed.add_field(
        name="`!add_channel <VC名>`",
        value="自動切断の対象にするボイスチャンネルを追加します。\n*(例: `!add_channel 寝落ち部屋`) ※管理者のみ*",
        inline=False
    )
    embed.add_field(
        name="`!remove_channel <VC名>`",
        value="対象チャンネルから削除します。\n*(例: `!remove_channel 寝落ち部屋`) ※管理者のみ*",
        inline=False
    )
    
    # フッターを追加（オプション）
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    
    await ctx.send(embed=embed)

# 設定確認コマンド
@bot.command(name="status", aliases=["config"])
async def show_status(ctx):
    guild_config = get_guild_config(ctx.guild.id)
    minutes = guild_config.get("cut_off_minutes", 120)
    channels = guild_config.get("target_channels", [])
    
    channels_str = "\n".join([f"・{c}" for c in channels]) if channels else "なし"
    
    embed = discord.Embed(title="⚙️ 現在のBot設定一覧", color=0x3498db)
    embed.add_field(name="⏱️ 自動切断までの時間", value=f"`{minutes}分` ({minutes / 60:.1f}時間)", inline=False)
    embed.add_field(name="📋 対象ボイスチャンネル", value=channels_str, inline=False)
    await ctx.send(embed=embed)

# 時間変更コマンド（管理者権限が必要）
@bot.command(name="set_time")
@commands.has_permissions(administrator=True)
async def set_time(ctx, minutes: int):
    if minutes <= 0:
        await ctx.send("⚠️ 1分以上の時間を指定してください。")
        return
    
    config = load_config()
    str_guild_id = str(ctx.guild.id)
    guild_config = get_guild_config(ctx.guild.id)
    
    guild_config["cut_off_minutes"] = minutes
    config[str_guild_id] = guild_config
    save_config(config)
    
    await ctx.send(f"✅ このサーバーの自動切断までの時間を **{minutes}分** ({minutes / 60:.1f}時間) に変更しました！")

# チャンネル追加コマンド（管理者権限が必要）
@bot.command(name="add_channel")
@commands.has_permissions(administrator=True)
async def add_channel(ctx, *, channel_name: str):
    config = load_config()
    str_guild_id = str(ctx.guild.id)
    guild_config = get_guild_config(ctx.guild.id)
    
    if channel_name in guild_config["target_channels"]:
        await ctx.send(f"⚠️ `{channel_name}` は既に対象チャンネルに追加されています。")
        return
    
    guild_config["target_channels"].append(channel_name)
    config[str_guild_id] = guild_config
    save_config(config)
    
    await ctx.send(f"✅ `{channel_name}` をこのサーバーの自動切断対象チャンネルに追加しました！")

# チャンネル削除コマンド（管理者権限が必要）
@bot.command(name="remove_channel")
@commands.has_permissions(administrator=True)
async def remove_channel(ctx, *, channel_name: str):
    config = load_config()
    str_guild_id = str(ctx.guild.id)
    guild_config = get_guild_config(ctx.guild.id)
    
    if channel_name not in guild_config["target_channels"]:
        await ctx.send(f"⚠️ `{channel_name}` は対象チャンネルに登録されていません。")
        return
    
    guild_config["target_channels"].remove(channel_name)
    config[str_guild_id] = guild_config
    save_config(config)
    
    await ctx.send(f"✅ `{channel_name}` をこのサーバーの自動切断対象チャンネルから削除しました！")

# エラーハンドリング
@set_time.error
@add_channel.error
@remove_channel.error
async def command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ このコマンドを実行するにはサーバーの**管理者権限**が必要です。")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ 引数が不足しています。正しい形式で入力してください。")

keep_alive()
if TOKEN:
    bot.run(TOKEN)
else:
    print("エラー: DISCORD_TOKENが設定されていません。")
