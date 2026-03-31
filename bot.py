import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import re
import json
import os

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

DB_FILE = "prices.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE,"r") as f:
        prices_db = json.load(f)
else:
    prices_db = {}

sent = set()

PAGES = range(1,11)

SEARCHES = [
    "a",
    "electronica",
    "hogar",
    "herramientas",
    "juguetes",
    "computadora",
    "oficina"
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

def extract_price(text):
    prices = re.findall(r"\$[\d,]+\.?\d*", text)
    if prices:
        try:
            return float(prices[0].replace("$","").replace(",",""))
        except:
            return None
    return None

def check():
    headers = {"User-Agent": "Mozilla/5.0"}

    for search in SEARCHES:
        for page in PAGES:
            url = f"https://www.amazon.com.mx/s?k={search}&page={page}"

            try:
                r = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")

                items = soup.select("[data-asin]")

                for item in items:
                    asin = item.get("data-asin")
                    text = item.get_text(" ", strip=True)

                    price = extract_price(text)

                    if not price:
                        continue

                    if asin in prices_db:
                        old_price = prices_db[asin]

                        if old_price <= 0:
                            continue

                        discount = int((old_price - price) / old_price * 100)

                        if discount >= 60 and asin not in sent:
                            sent.add(asin)

                            send(
                                f"🔥 {discount}% OFF detectado\n"
                                f"💰 ${price} antes ${old_price}\n\n"
                                f"🔗 https://www.amazon.com.mx/dp/{asin}"
                            )

                    prices_db[asin] = price

            except:
                pass

    save_db()

threading.Thread(target=run_server).start()

send("🚀 Bot FINAL monitoreando todo Amazon")

while True:
    check()
    time.sleep(180)
