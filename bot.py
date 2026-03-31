import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import re
import json
import os
import random

TELEGRAM_TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

DB_FILE = "prices.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE,"r") as f:
        prices_db = json.load(f)
else:
    prices_db = {}

sent = set()

URLS = [
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/gp/bestsellers",
    "https://www.amazon.com.mx/gp/new-releases",
    "https://www.amazon.com.mx/gp/most-wished-for"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

session = requests.Session()

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

def get_price(asin):
    try:
        r = session.get(
            f"https://www.amazon.com.mx/dp/{asin}",
            headers={"User-Agent": random.choice(USER_AGENTS)},
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

        el = soup.select_one(".a-price .a-offscreen")
        if el:
            m = re.search(r"\$[\d,]+\.?\d*", el.text)
            if m:
                return float(m.group().replace("$","").replace(",",""))

    except:
        pass

    return None

def check():
    compared = 0

    for url in URLS:
        try:
            r = session.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=10)
            asins = re.findall(r'data-asin="([A-Z0-9]{10})"', r.text)

            for asin in asins[:15]:
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
                time.sleep(random.uniform(2,4))

        except:
            pass

    with open(DB_FILE,"w") as f:
        json.dump(prices_db,f)
        
send(f"📊 Comparados {compared} | Bot vivo")

threading.Thread(target=run_server).start()

send("🚀 BOT AMAZON FUENTES REALES activo")

while True:
    check()
    time.sleep(180)
