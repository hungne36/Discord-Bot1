
from flask import Flask
from threading import Thread
import waitress

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return '', 204

@app.route('/apple-touch-icon-precomposed.png')
def apple_touch_icon_precomposed():
    return '', 204

def run():
    waitress.serve(app, host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
