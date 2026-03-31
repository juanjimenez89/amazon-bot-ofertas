import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent_items = set()

URLS = [
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/deals",
    "https://www.amazon.com.mx/s?k=ofertas",
    "https://www.amazon.com.mx/s?k=descuento",
    "https://www.amazon.com.mx/s?k=cupon",
    "https://www.amazon.com.mx/s?k=rebaja",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_server():
    server = HTTPServer(('', 10000), Handler)
    server.serve_forever()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

def check_deals():
    for url in URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")

            items = soup.select("[data-asin]")

            for item in items:
                asin = item.get("data-asin")

                if not asin or asin in sent_items:
                    continue

                text = item.get_text(" ", strip=True)

                if "%" not in text and "cupón" not in text.lower():
                    continue

                sent_items.add(asin)

                link = f"https://www.amazon.com.mx/dp/{asin}"

                msg = (
                    "🔥 Posible oferta detectada\n\n"
                    f"{text[:150]}\n\n"
                    f"🔗 {link}"
                )

                send_telegram(msg)
                print("Enviado:", asin)

        except Exception as e:
            print("Error:", e)

threading.Thread(target=run_server).start()

send_telegram("🚀 Bot reiniciado — detección ampliada")

while True:
    check_deals()
    time.sleep(random.randint(180,300))
