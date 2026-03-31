import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()

FEEDS = [
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/deals",
    "https://www.amazon.com.mx/s?k=ofertas",
    "https://www.amazon.com.mx/s?k=cupon",
    "https://www.amazon.com.mx/s?k=rebajas",
    "https://www.amazon.com.mx/s?k=liquidacion",
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(('',10000), Handler).serve_forever()

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def check():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in FEEDS:
        try:
            r = requests.get(url, headers=headers, timeout=15)

            if "%" in r.text.lower() or "cupón" in r.text.lower():
                key = url + str(random.randint(1,1000))

                if key in sent:
                    continue

                sent.add(key)

                send(
                    "🔥 Posible oferta detectada\n\n"
                    "Incluye:\n"
                    "• cupón\n"
                    "• oferta relámpago\n"
                    "• posible error de precio\n\n"
                    f"🔗 {url}"
                )

        except:
            pass

threading.Thread(target=run_server).start()

send("🚀 Bot Amazon México PRO activo")

while True:
    check()
    time.sleep(random.randint(120,240))
