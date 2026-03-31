import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import random
import re

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()

FEEDS = [
    "https://www.amazon.com.mx/s?k=ofertas",
    "https://www.amazon.com.mx/s?k=cupon",
    "https://www.amazon.com.mx/s?k=rebaja",
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/deals"
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

def extract_prices(text):
    prices = re.findall(r"\$[\d,]+\.?\d*", text)
    if len(prices) >= 2:
        try:
            old_price = float(prices[0].replace("$","").replace(",",""))
            new_price = float(prices[1].replace("$","").replace(",",""))
            return old_price, new_price
        except:
            return None, None
    return None, None

def check():
    headers = {"User-Agent": "Mozilla/5.0"}

    for url in FEEDS:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            text = r.text.lower()

            old_price, new_price = extract_prices(text)

            if not old_price or not new_price:
                continue

            discount = int((old_price - new_price) / old_price * 100)

            if discount < 60:
                continue

            key = str(old_price) + str(new_price)

            if key in sent:
                continue

            sent.add(key)

            send(
                f"🔥 {discount}% OFF\n"
                f"💰 ${new_price} antes ${old_price}\n\n"
                f"🔗 {url}"
            )

        except:
            pass

threading.Thread(target=run_server).start()

send("🚀 Bot filtrando solo ≥60% OFF")

while True:
    check()
    time.sleep(random.randint(120,240))
