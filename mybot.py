import discord
from discord.ext import commands
import asyncio
from flask import Flask
from threading import Thread

# --- Renderのスリープ防止用サーバー ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()
# ------------------------------------

TARGET_CHANNELS = ["おひるね", "睡眠厨","保健室"]
CUT_OFF_SECONDS = 2 * 60 * 60 
TOKEN = 'MTQ1OTEyNjI2NTUzMjM4NzM1OA.GQKcXk.YBB6oDkMLJdrRplR2Rne2NTBGJdvt19kNdEz-I'

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot起動完了: {bot.user.name}')

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot: return
    channel_name = after.channel.name if after.channel else None
    if channel_name in TARGET_CHANNELS and before.channel != after.channel:
        await asyncio.sleep(CUT_OFF_SECONDS)
        if member.voice and member.voice.channel and member.voice.channel.name in TARGET_CHANNELS:
            try:
                await member.move_to(None)
            except:
                pass

# Webサーバーを起動してからBotを動かす
keep_alive()
bot.run('MTQ1OTEyNjI2NTUzMjM4NzM1OA.GQKcXk.YBB6oDkMLJdrRplR2Rne2NTBGJdvt19kNdEz-I')
