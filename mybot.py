from flask import Flask
from threading import Thread

app = Flask('') # 小さなWebサーバーを作る

@app.route('/') # ホームページ（/）にアクセスが来たら...
def home():
    return "Bot is running!" # 「動いてるよ！」と返事をする

def run_web():
    app.run(host='0.0.0.0', port=8080) # サーバーを起動する

def keep_alive():
    t = Thread(target=run_web) # Botと同時に動くようにセットする
    t.start()
