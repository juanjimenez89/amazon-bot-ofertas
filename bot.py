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
    "https://www.amazon.com.mx/s?k=ofertas",
    "https://www.amazon.com.mx/s?k=descuentos",
    "https://www.amazon.com.mx/s?k=cupon",
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/deals"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
    "Mozilla/5.0 (X11; Linux x86_64)",
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_server():
    HTTPServer(('', 10000), Handler).serve_forever()

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def check_deals():
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    for url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")

            for item in soup.select("div.s-result-item"):
                asin = item.get("data-asin")

                if not asin or asin in sent_items:
                    continue

                text = item.get_text(" ", strip=True)

                if "%" not in text and "cupón" not in text.lower():
                    continue

                sent_items.add(asin)

                link = f"https://www.amazon.com.mx/dp/{asin}"

                send_telegram(
                    "🔥 Oferta detectada\n\n"
                    f"{text[:120]}...\n\n"
                    f"🔗 {link}"
                )

                print("Enviado:", asin)

        except Exception as e:
            print("Error:", e)

threading.Thread(target=run_server).start()

send_telegram("🚀 Bot estable anti-bloqueo activo")

while True:
    check_deals()
    time.sleep(random.randint(120,240))
