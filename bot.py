import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import re
import json
import os
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

DB_FILE = "prices.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE,"r") as f:
        prices_db = json.load(f)
else:
    prices_db = {}

sent = set()

DEAL_URLS = [
    "https://www.amazon.com.mx/deals",
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/gp/goldbox/ref=gbps_ftr_s-5_",
    "https://www.amazon.com.mx/s?k=descuento",
    "https://www.amazon.com.mx/s?k=oferta"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(('',10000), Handler).serve_forever()

def save_db():
    with open(DB_FILE,"w") as f:
        json.dump(prices_db,f)

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def extract_prices(text):
    prices = re.findall(r"\$[\d,]+\.?\d*", text)
    nums = []

    for p in prices:
        try:
            nums.append(float(p.replace("$","").replace(",","")))
        except:
            pass

    if len(nums) >= 2:
        return max(nums), min(nums)

    return None

def check():
    scanned = 0

    for url in DEAL_URLS:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "es-MX,es;q=0.9"
        }

        try:
            r = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")

            items = soup.select("[data-asin]")

            for item in items:
                asin = item.get("data-asin")
                if not asin:
                    continue

                text = item.get_text(" ", strip=True)

                price = extract_prices(text)
                scanned += 1

                if price:
                    old_price, new_price = price
                    discount = int((old_price - new_price) / old_price * 100)

                    if discount >= 55 and asin not in sent:
                        sent.add(asin)

                        send(
                            f"🔥 {discount}% OFF\n"
                            f"💰 ${new_price} antes ${old_price}\n\n"
                            f"🔗 https://www.amazon.com.mx/dp/{asin}"
                        )

                if asin in prices_db and price:
                    old = prices_db[asin]
                    new = price[1]

                    if old > 0:
                        drop = int((old - new) / old * 100)

                        if drop >= 55 and asin not in sent:
                            sent.add(asin)

                            send(
                                f"⚡ Bajada {drop}%\n"
                                f"💰 ${new} antes ${old}\n\n"
                                f"🔗 https://www.amazon.com.mx/dp/{asin}"
                            )

                if price:
                    prices_db[asin] = price[1]

            time.sleep(random.uniform(2,4))

        except:
            pass

    save_db()

    send(f"📊 Ofertas monitoreadas {len(prices_db)} | Escaneadas {scanned}")

threading.Thread(target=run_server).start()

send("🚀 Bot modo OFERTAS Amazon activo")

while True:
    check()
    time.sleep(180)
