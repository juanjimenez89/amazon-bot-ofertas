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

SEARCHES = ["a","b","c","oferta","descuento","cupon"]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121 Safari/537.36",
]

session = requests.Session()

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
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except:
        pass

def headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "es-MX,es;q=0.9",
        "Referer": "https://www.amazon.com.mx/"
    }

def get_price(asin):
    try:
        r = session.get(
            f"https://www.amazon.com.mx/dp/{asin}",
            headers=headers(),
            timeout=8
        )
        soup = BeautifulSoup(r.text, "html.parser")

        for sel in [
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            ".a-price .a-offscreen"
        ]:
            el = soup.select_one(sel)
            if el:
                m = re.search(r"\$[\d,]+\.?\d*", el.text)
                if m:
                    return float(m.group().replace("$","").replace(",",""))

    except:
        pass

    return None

def check():
    compared = 0

    for search in SEARCHES:
        try:
            r = session.get(
                SEARCH_URL + search,
                headers=headers(),
                timeout=8
            )

            asins = re.findall(r'data-asin="([A-Z0-9]{10})"', r.text)

            for asin in asins[:8]:
                price = get_price(asin)
                if not price:
                    continue

                compared += 1

                if asin in prices_db:
                    old = prices_db[asin]
                    discount = int((old - price) / old * 100)

                    if discount >= 55 and asin not in sent:
                        sent.add(asin)
                        send(
                            f"🔥 {discount}% OFF\n"
                            f"💰 ${price}\n"
                            f"https://www.amazon.com.mx/dp/{asin}"
                        )

                prices_db[asin] = price
                time.sleep(random.uniform(1.5,3))

        except:
            continue

    save_db()
    send(f"📊 Comparados {compared}")

threading.Thread(target=run_server).start()

send("🚀 BOT ESTABLE REAL activo")

while True:
    try:
        check()
    except:
        send("⚠️ reinicio automático")
    time.sleep(180)
