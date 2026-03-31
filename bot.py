import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()
prices = {}

MONITOR = [
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/gp/bestsellers",
    "https://www.amazon.com.mx/gp/new-releases"
]

EXTERNAL = [
    "https://www.promodescuentos.com",
    "https://www.ofertitas.com.mx"
]

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
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except:
        pass

def extract_discount(text):
    m = re.search(r'(\d{1,3})\s?%', text)
    return int(m.group(1)) if m else 0

def extract_price(text):
    m = re.search(r'\$ ?([\d,]+)', text)
    return int(m.group(1).replace(",","")) if m else 0

def monitor_amazon():
    for url in MONITOR:
        try:
            r = requests.get(url, timeout=10)
            asins = re.findall(r'data-asin="([A-Z0-9]{10})"', r.text)

            for asin in asins[:20]:
                product_url = f"https://www.amazon.com.mx/dp/{asin}"
                try:
                    pr = requests.get(product_url, timeout=10)
                    price = extract_price(pr.text)

                    if not price:
                        continue

                    if asin in prices:
                        old = prices[asin]
                        discount = int((old-price)/old*100)

                        if discount >= 55 and asin not in sent:
                            sent.add(asin)
                            send(
                                f"💥 Bajada detectada {discount}%\n"
                                f"Antes: ${old}\n"
                                f"Ahora: ${price}\n"
                                f"{product_url}"
                            )

                    prices[asin] = price

                except:
                    pass

        except:
            pass

def check_external():
    for url in EXTERNAL:
        try:
            r = requests.get(url, timeout=10)
            html = r.text.lower()

            links = re.findall(r'https://www\.amazon\.com\.mx[^\s"]+', html)

            for link in links:
                if link in sent:
                    continue

                pos = html.find(link)
                snippet = html[max(0,pos-200):pos+200]

                discount = extract_discount(snippet)
                coupon = extract_price(snippet)

                if discount >= 55 or coupon >= 100:
                    sent.add(link)
                    send(
                        f"🔥 Oferta detectada\n"
                        f"Descuento: {discount}%\n"
                        f"Cupón: ${coupon}\n"
                        f"{link}"
                    )

        except:
            pass

def loop():
    while True:
        try:
            monitor_amazon()
            check_external()
            send("📊 Bot monitoreando...")
        except:
            send("⚠️ error reinicio")
        time.sleep(300)

threading.Thread(target=run_server).start()
threading.Thread(target=loop).start()

send("🚀 BOT HÍBRIDO ACTIVO")
