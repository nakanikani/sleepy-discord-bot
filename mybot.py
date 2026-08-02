import asyncio
import json
import os
from threading import Thread
import discord
from discord.ext import commands
from flask import Flask

# --- Renderスリープ防止用Webサーバー ---
app = Flask('')


@app.route('/')
def home():
  return 'Bot is running!'


def run_web():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = Thread(target=run_web, daemon=True)
  t.start()


# ------------------------------------

CONFIG_FILE = 'bot_config.json'

# デフォルト設定
DEFAULT_CONFIG = {
    'target_channels': ['おひるね', '睡眠厨', '保健室'],
    'cut_off_minutes': 120,  # デフォルト 120分（2時間）
}


# 設定ファイルの読み込み
def load_config():
  if os.path.exists(CONFIG_FILE):
    try:
      with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # 必要なキーが含まれているか補完
        for key, val in DEFAULT_CONFIG.items():
          if key not in data:
            data[key] = val
        return data
    except Exception as e:
      print(f'設定ファイル読み込みエラー: {e}')
  return DEFAULT_CONFIG.copy()


# 設定ファイルの保存
def save_config(config):
  try:
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
      json.dump(config, f, ensure_ascii=False, indent=2)
  except Exception as e:
    print(f'設定ファイル保存エラー: {e}')


# グローバル設定オブジェクト
config = load_config()

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
  print(f'Bot起動完了: {bot.user.name}')
  print(f"現在の対象VC: {config['target_channels']}")
  print(f"現在の切断時間: {config['cut_off_minutes']}分")


# --- 💬 Discordから設定確認・変更するコマンド ---


# 1. 現在の設定（チャンネル＆切断時間）を確認 (!status または !config)
@bot.command(name='status', aliases=['config'])
async def show_status(ctx):
  channels = config['target_channels']
  minutes = config['cut_off_minutes']

  channels_str = (
      '\n'.join([f'・{c}' for c in channels])
      if channels
      else '（対象チャンネルなし）'
  )

  hours = minutes / 60
  time_str = (
      f'{minutes}分 ({hours:.1f}時間)' if minutes % 60 != 0 else f'{minutes}分'
  )

  embed_msg = (
      f'⚙️ **現在のBot設定一覧**\n'
      f'⏱️ **自動切断までの時間:** `{time_str}`\n\n'
      f'📋 **対象ボイスチャンネル:**\n{channels_str}'
  )
  await ctx.send(embed_msg)


# 2. 切断時間を変更 (!set_time 分数)
@bot.command(name='set_time')
@commands.has_permissions(administrator=True)
async def set_time(ctx, minutes: int):
  if minutes <= 0:
    await ctx.send('⚠️ 待機時間は1分以上を指定してください。')
    return

  config['cut_off_minutes'] = minutes
  save_config(config)

  hours = minutes / 60
  await ctx.send(
      f'✅ 自動切断までの時間を **{minutes}分** ({hours:.1f}時間) に変更しました！'
  )


# 3. チャンネルを追加 (!add_channel チャンネル名)
@bot.command(name='add_channel')
@commands.has_permissions(administrator=True)
async def add_channel(ctx, *, channel_name: str):
  if channel_name in config['target_channels']:
    await ctx.send(f'⚠️ `{channel_name}` は既に対象チャンネルに含まれています。')
  else:
    config['target_channels'].append(channel_name)
    save_config(config)
    await ctx.send(
        f'✅ `{channel_name}` を自動切断対象チャンネルに追加しました！'
    )


# 4. チャンネルを削除 (!remove_channel チャンネル名)
@bot.command(name='remove_channel')
@commands.has_permissions(administrator=True)
async def remove_channel(ctx, *, channel_name: str):
  if channel_name in config['target_channels']:
    config['target_channels'].remove(channel_name)
    save_config(config)
    await ctx.send(
        f'🗑️ `{channel_name}` を自動切断対象チャンネルから削除しました。'
    )
  else:
    await ctx.send(f'⚠️ `{channel_name}` は対象チャンネルに見つかりませんでした。')


# エラーハンドリング（入力ミスや権限不足）
@set_time.error
@add_channel.error
@remove_channel.error
async def cmd_error(ctx, error):
  if isinstance(error, commands.MissingPermissions):
    await ctx.send('❌ このコマンドを実行するには「管理者権限」が必要です。')
  elif isinstance(error, commands.BadArgument):
    await ctx.send(
        '⚠️ 数字の指定が正しくありません。（例: `!set_time 60` で60分に設定）'
    )


# --- VC自動切断ロジック ---
@bot.event
async def on_voice_state_update(member, before, after):
  if member.bot:
    return

  channel_name = after.channel.name if after.channel else None

  # 対象のVCに入室した場合
  if (
      channel_name in config['target_channels']
      and before.channel != after.channel
  ):
    # 設定されている分数を秒数に換算して待機
    wait_seconds = config['cut_off_minutes'] * 60
    await asyncio.sleep(wait_seconds)

    # 待機時間経過後もまだ対象VCに居続けていたら切断
    if (
        member.voice
        and member.voice.channel
        and member.voice.channel.name in config['target_channels']
    ):
      try:
        await member.move_to(None)
        print(
            f"{member.display_name} を{config['cut_off_minutes']}分経過のためVC[{channel_name}]から切断しました。"
        )
      except Exception as e:
        print(f'切断失敗: {e}')


keep_alive()

if TOKEN:
  bot.run(TOKEN)
else:
  print('エラー: DISCORD_TOKEN が設定されていません。')
