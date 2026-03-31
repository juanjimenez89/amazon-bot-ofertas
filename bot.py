import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()

URL = "https://www.amazon.com.mx/s?k=ofertas"

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

def check():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        for item in soup.select("[data-asin]"):
            asin = item.get("data-asin")

            if not asin or asin in sent:
                continue

            text = item.get_text(" ", strip=True).lower()

            if "%" not in text and "cupón" not in text:
                continue

            sent.add(asin)

            link = f"https://www.amazon.com.mx/dp/{asin}"

            send(
                "🔥 Oferta detectada\n\n"
                f"🔗 {link}"
            )

    except:
        pass

threading.Thread(target=run_server).start()

send("🚀 Bot productos específicos activo")

while True:
    check()
    time.sleep(180)
