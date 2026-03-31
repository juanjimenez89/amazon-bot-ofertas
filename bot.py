import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent_items = set()

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
    headers = {"User-Agent": "Mozilla/5.0"}

    for url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            for item in soup.select("div[data-asin]"):
                asin = item.get("data-asin")

                if not asin or asin in sent_items:
                    continue

                text = item.get_text(" ", strip=True)

                if "%" in text:
                    sent_items.add(asin)

                    link = f"https://www.amazon.com.mx/dp/{asin}"

                    msg = (
                        "🔥 Oferta detectada\n\n"
                        f"{text[:150]}\n\n"
                        f"🔗 {link}"
                    )

                    send_telegram(msg)
                    print("Oferta enviada:", asin)

        except Exception as e:
            print("Error:", e)

threading.Thread(target=run_server).start()

print("Amazon bot iniciado")
send_telegram("🤖 Bot activo sin duplicados...")

while True:
    check_deals()
    time.sleep(300)
