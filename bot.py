import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import re
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()

URLS = [
    "https://www.amazon.com.mx/s?k=ofertas",
    "https://www.amazon.com.mx/s?k=descuentos",
    "https://www.amazon.com.mx/s?k=cupon",
    "https://www.amazon.com.mx/s?k=rebaja",
    "https://www.amazon.com.mx/gp/goldbox"
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

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def extract_prices(text):
    prices = re.findall(r"\$[\d,]+\.?\d*", text)
    values = []

    for p in prices:
        try:
            values.append(float(p.replace("$","").replace(",","")))
        except:
            pass

    if len(values) >= 2:
        return max(values), min(values)

    return None

def check():
    total = 0

    for url in URLS:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "es-MX,es;q=0.9"
        }

        try:
            r = requests.get(url, headers=headers, timeout=20)
            text = r.text

            blocks = text.split("data-asin")

            for block in blocks:
                asin_match = re.search(r'([A-Z0-9]{10})', block)
                if not asin_match:
                    continue

                asin = asin_match.group(1)

                price = extract_prices(block)

                total += 1

                if price:
                    old_price, new_price = price
                    discount = int((old_price - new_price) / old_price * 100)

                    if discount >= 55 and asin not in sent:
                        sent.add(asin)

                        send(
                            f"🔥 {discount}% OFF\n"
                            f"💰 ${new_price} antes ${old_price}\n\n"
                            f"https://www.amazon.com.mx/dp/{asin}"
                        )

            time.sleep(random.uniform(2,4))

        except:
            pass

    send(f"📊 Revisados {total} productos")

threading.Thread(target=run_server).start()

send("🚀 Bot estable final activo")

while True:
    check()
    time.sleep(180)
