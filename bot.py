import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import re

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent_items = set()

URLS = [
    "https://www.amazon.com.mx/gp/goldbox",
    "https://www.amazon.com.mx/deals",
    "https://www.amazon.com.mx/gp/goldbox?ref_=nav_cs_gb",
    "https://www.amazon.com.mx/deals?ref_=nav_cs_deals",
    "https://www.amazon.com.mx/s?i=electronics&rh=p_n_deal_type%3A23566065011",
    "https://www.amazon.com.mx/s?i=home&rh=p_n_deal_type%3A23566065011",
    "https://www.amazon.com.mx/s?i=fashion&rh=p_n_deal_type%3A23566065011",
    "https://www.amazon.com.mx/s?i=toys&rh=p_n_deal_type%3A23566065011",
    "https://www.amazon.com.mx/s?k=cupon",
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
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

def extract_price(text):
    match = re.findall(r"\$[\d,]+\.?\d*", text)
    if len(match) >= 2:
        try:
            old_price = float(match[0].replace("$","").replace(",",""))
            new_price = float(match[1].replace("$","").replace(",",""))
            return old_price, new_price
        except:
            return None, None
    return None, None

def extract_coupon(text):
    percent = re.search(r"(\d+)%", text)
    if percent:
        return int(percent.group(1))
    return 0

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

                text = item.get_text(" ", strip=True).lower()

                if "amazon" not in text:
                    continue

                old_price, new_price = extract_price(text)

                if not old_price or not new_price:
                    continue

                base_discount = int((old_price - new_price) / old_price * 100)
                coupon = extract_coupon(text)
                total_discount = base_discount + coupon

                if not (
                    total_discount >= 60
                    or base_discount >= 50
                    or coupon >= 20
                ):
                    continue

                sent_items.add(asin)

                link = f"https://www.amazon.com.mx/dp/{asin}"

                msg = (
                    f"🔥 {total_discount}% OFF\n"
                    f"💰 ${new_price} antes ${old_price}\n"
                    f"🎟️ Cupón: {coupon}%\n\n"
                    f"🔗 {link}"
                )

                send_telegram(msg)
                print("Oferta enviada:", asin)

        except Exception as e:
            print("Error:", e)

threading.Thread(target=run_server).start()

print("Amazon bot PRO iniciado")
send_telegram("🚀 Bot PRO MAX activo: más fuentes + 60% + cupones + enviado por Amazon")

while True:
    check_deals()
    time.sleep(300)
