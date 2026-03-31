import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import random

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

# Fuentes de ofertas (no bloqueadas fácilmente)
FEEDS = [
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/gp/goldbox?dealTypes=LIGHTNING_DEAL",
    "https://www.amazon.com.mx/gp/goldbox?dealTypes=BEST_DEAL"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
]

sent = set()

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

def check():
    found = 0
    for url in FEEDS:
        try:
            r = requests.get(
                url,
                headers={"User-Agent": random.choice(USER_AGENTS)},
                timeout=10
            )

            # buscar descuentos directos
            lines = r.text.split("\n")

            for line in lines:
                if "%" in line and "OFF" in line.upper():
                    try:
                        pct = int("".join([c for c in line if c.isdigit()])[:2])
                        if pct >= 60:
                            found += 1
                            if line not in sent:
                                sent.add(line)
                                send(f"🔥 Oferta detectada ~{pct}%\nVer Amazon")
                    except:
                        pass

        except:
            pass

    send(f"📊 Revisadas ofertas | detectadas {found}")

threading.Thread(target=run_server).start()

send("🚀 Bot ofertas reales activo")

while True:
    try:
        check()
    except:
        send("⚠️ reinicio automático")
    time.sleep(300)
