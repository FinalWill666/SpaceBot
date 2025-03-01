import requests
import time
from flask import Flask, request
from threading import Thread

app = Flask(__name__)

@app.route('/', methods=['GET', 'HEAD'])
def home():
    if request.method == 'HEAD':
        return '', 200  # Empty response for UptimeRobot
    return "Bot is running!", 200  # Normal response for GET requests

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def ping_self():
    while True:
        try:
            requests.get("https://4e358631-416b-4c96-90e8-9aca725d1fc5-00-1uoknwyv8n8g6.janeway.replit.dev/")  
        except:
            pass
        time.sleep(60)  # Wait 1 minute before sending another request

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
    Thread(target=ping_self, daemon=True).start()

