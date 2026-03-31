import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()

SOURCES = [
    "https://www.promodescuentos.com",
    "https://www.ofertitas.com.mx",
    "https://www.promodescuentos.com/search?q=amazon"
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
    if m:
        return int(m.group(1))
    return 0

def extract_money(text):
    m = re.search(r'\$ ?([\d,]+)', text)
    if m:
        return int(m.group(1).replace(",",""))
    return 0

def check():
    found = 0

    for url in SOURCES:
        try:
            r = requests.get(url, timeout=15)
            html = r.text.lower()

            links = re.findall(r'https://www\.amazon\.com\.mx[^\s"]+', html)

            for link in links:
                if link in sent:
                    continue

                pos = html.find(link)
                snippet = html[max(0,pos-200):pos+200]

                discount = extract_discount(snippet)
                coupon = extract_money(snippet)

                send_flag = False

                if discount >= 55:
                    send_flag = True

                if coupon >= 100:
                    send_flag = True

                if coupon > 0 and discount > 0 and (discount + 25) >= 55:
                    send_flag = True

                if send_flag:
                    sent.add(link)
                    found += 1

                    send(
                        f"🔥 Oferta detectada\n"
                        f"Descuento: {discount}%\n"
                        f"Cupón: ${coupon}\n"
                        f"{link}"
                    )

        except:
            pass

    send(f"📊 Revisadas | nuevas {found}")

threading.Thread(target=run_server).start()

send("🚀 BOT FINAL OFERTAS activo")

while True:
    try:
        check()
    except:
        send("⚠️ reinicio automático")
    time.sleep(300)
