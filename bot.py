import time
import requests
from bs4 import BeautifulSoup
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

URL = "https://www.amazon.com.mx/gp/goldbox"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(('',10000), Handler).serve_forever()

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

def check():
    try:
        r = requests.get(URL, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
        asins = re.findall(r'data-asin="([A-Z0-9]{10})"', r.text)

        send(f"Encontrados {len(asins)} productos")

    except Exception as e:
        send("Error en bot")

threading.Thread(target=run_server).start()

send("Bot prueba activo")

while True:
    check()
    time.sleep(180)
