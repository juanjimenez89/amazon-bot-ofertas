import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

MIN_DISCOUNT = 70
MIN_PRICE = 20
MAX_PRICE = 10000

URLS = [
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/deals",
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_server():
    port = 10000
    server = HTTPServer(('', port), Handler)
    server.serve_forever()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, data=data)
    except:
        pass

def check_deals():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            for item in soup.select("div[data-asin]"):
                text = item.get_text(" ", strip=True)

                if "%" in text:
                    send_telegram("🔥 Oferta detectada\n" + text[:200])
                    print("Oferta enviada")

        except Exception as e:
            print("Error:", e)

threading.Thread(target=run_server).start()

print("Amazon bot iniciado")
send_telegram("🤖 Bot activo y monitoreando ofertas...")

while True:
    check_deals()
    time.sleep(300)
