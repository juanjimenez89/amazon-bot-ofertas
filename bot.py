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
    "a","b","c","d","e","oferta","descuento","cupon"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
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
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "es-MX,es;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.amazon.com.mx/",
    }

def get_price(asin):
    try:
        url = f"https://www.amazon.com.mx/dp/{asin}"
        r = session.get(url, headers=headers(), timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        selectors = [
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            "#corePriceDisplay_desktop_feature_div .a-offscreen"
        ]

        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                m = re.search(r"\$[\d,]+\.?\d*", el.text)
                if m:
                    return float(m.group().replace("$","").replace(",",""))

    except:
        pass

    return None

def check():
    for search in SEARCHES:
        try:
            r = session.get(SEARCH_URL + search, headers=headers(), timeout=20)
            asins = re.findall(r'data-asin="([A-Z0-9]{10})"', r.text)

            for asin in asins[:10]:
                price = get_price(asin)
                if not price:
                    continue

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

                time.sleep(random.uniform(3,5))

        except:
            pass

    save_db()
    send(f"📊 Comparados {len(prices_db)}")

threading.Thread(target=run_server).start()

send("🚀 BOT FINAL REAL activo")

while True:
    check()
    time.sleep(180)
