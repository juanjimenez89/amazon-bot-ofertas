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
    "oficina",
    "cocina",
    "gaming",
    "celular"
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
    if len(prices) >= 2:
        try:
            old_price = float(prices[0].replace("$","").replace(",",""))
            new_price = float(prices[1].replace("$","").replace(",",""))
            return old_price, new_price
        except:
            return None, None
    return None, None

def extract_coupon(text):
    match = re.search(r"(\d+)%", text)
    if match:
        return int(match.group(1))
    return 0

def check():
    headers = {"User-Agent": "Mozilla/5.0"}
    scanned = 0

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

                    price = extract_prices(text)
                    coupon = extract_coupon(text)

                    scanned += 1

                    # detectar descuento visible
                    if price[0] and price[1]:
                        old_price, new_price = price
                        discount = int((old_price - new_price) / old_price * 100)

                        if discount >= 55 and asin not in sent:
                            sent.add(asin)

                            send(
                                f"🔥 {discount}% OFF\n"
                                f"💰 ${new_price} antes ${old_price}\n\n"
                                f"🔗 https://www.amazon.com.mx/dp/{asin}"
                            )

                    # detectar bajada histórica
                    if asin in prices_db and price[1]:
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

                    # detectar cupon
                    if coupon >= 20 and asin not in sent:
                        sent.add(asin)

                        send(
                            f"🎟️ Cupón {coupon}% detectado\n"
                            f"🔗 https://www.amazon.com.mx/dp/{asin}"
                        )

                    # guardar precio actual
                    if price[1]:
                        prices_db[asin] = price[1]

            except:
                pass

    save_db()

    send(f"📊 Monitoreando {len(prices_db)} productos | Escaneados {scanned}")

threading.Thread(target=run_server).start()

send("🚀 Bot PRO 55% + cupones + bajadas activo")

while True:
    check()
    time.sleep(180)
