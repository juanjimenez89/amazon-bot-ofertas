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

SEARCH_URL = "https://www.amazon.com.mx/s?k="

SEARCHES = [
    "a",
    "oferta",
    "descuento",
    "cupon"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
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

def get_price_and_coupon(asin):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "es-MX,es;q=0.9"
    }

    try:
        url = f"https://www.amazon.com.mx/dp/{asin}"
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        price = None

        selectors = [
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            "#corePriceDisplay_desktop_feature_div .a-offscreen"
        ]

        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                match = re.search(r"\$[\d,]+\.?\d*", el.text)
                if match:
                    price = float(match.group().replace("$","").replace(",",""))
                    break

        coupon = 0
        text = soup.get_text(" ", strip=True)

        percent = re.search(r"(\d+)%", text)
        if percent:
            coupon = int(percent.group(1))

        return price, coupon

    except:
        return None, 0

def check():
    scanned = 0

    for search in SEARCHES:
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }

        try:
            r = requests.get(SEARCH_URL + search, headers=headers, timeout=15)

            asins = re.findall(r'data-asin="([A-Z0-9]{10})"', r.text)

            for asin in asins[:10]:
                price, coupon = get_price_and_coupon(asin)

                if not price:
                    continue

                scanned += 1

                discount = 0

                if asin in prices_db:
                    old = prices_db[asin]
                    discount = int((old - price) / old * 100)

                coupon_discount = coupon

                total_discount = discount + coupon_discount

                if total_discount >= 55 and asin not in sent:
                    sent.add(asin)

                    send(
                        f"🔥 {total_discount}% TOTAL\n"
                        f"💰 ${price}\n"
                        f"🎟️ Cupón {coupon}%\n\n"
                        f"https://www.amazon.com.mx/dp/{asin}"
                    )

                prices_db[asin] = price

                time.sleep(random.uniform(1,2))

        except:
            pass

    save_db()

    send(f"📊 Productos comparados {len(prices_db)}")

threading.Thread(target=run_server).start()

send("🚀 Bot PRECISIÓN FINAL activo")

while True:
    check()
    time.sleep(180)
