import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()

# Fuentes externas confiables
SOURCES = [
    "https://api.allorigins.win/raw?url=https://www.ofertitas.com.mx",
    "https://api.allorigins.win/raw?url=https://www.promodescuentos.com"
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
    m = re.search(r'(\d{2})\s?%', text)
    if m:
        return int(m.group(1))
    return 0

def check():
    total = 0

    for url in SOURCES:
        try:
            r = requests.get(url, timeout=15)
            html = r.text

            # buscar links Amazon
            links = re.findall(r'https://www\.amazon\.com\.mx[^\s"]+', html)

            for link in links:
                if link in sent:
                    continue

                # buscar descuento cercano
                snippet = html[max(0, html.find(link)-100):html.find(link)+100]
                discount = extract_discount(snippet)

                if discount >= 60:
                    sent.add(link)
                    total += 1

                    send(
                        f"🔥 {discount}% OFF detectado\n"
                        f"🛒 {link}"
                    )

        except:
            pass

    send(f"📊 Revisadas | nuevas {total}")

threading.Thread(target=run_server).start()

send("🚀 Bot OFERTAS AMAZON activo")

while True:
    try:
        check()
    except:
        send("⚠️ reinicio automático")
    time.sleep(300)
