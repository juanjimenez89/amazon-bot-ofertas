import time
import requests
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import random
import re

TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780"

sent = set()

PAGES = [1,2,3,4,5]

BASE_URL = "https://www.amazon.com.mx/s?k=a&page="

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

def extract_coupon(text):
    match = re.search(r"(\d+)%", text)
    if match:
        return int(match.group(1))
    return 0

def check():
    headers = {"User-Agent": "Mozilla/5.0"}

    for page in PAGES:
        url = BASE_URL + str(page)

        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            items = soup.select("[data-asin]")

            for item in items:
                text = item.get_text(" ", strip=True)

                prices = re.findall(r"\$[\d,]+\.?\d*", text)

                if len(prices) < 2:
                    continue

                try:
                    old_price = float(prices[0].replace("$","").replace(",",""))
                    new_price = float(prices[1].replace("$","").replace(",",""))
                except:
                    continue

                coupon = extract_coupon(text)

                discount = int((old_price - new_price) / old_price * 100)
                total_discount = discount + coupon

                if total_discount < 60:
                    continue

                key = str(old_price) + str(new_price)

                if key in sent:
                    continue

                sent.add(key)

                send(
                    f"🔥 {total_discount}% OFF\n"
                    f"💰 ${new_price} antes ${old_price}\n"
                    f"🎟️ Cupón: {coupon}%\n\n"
                    f"🔗 https://www.amazon.com.mx"
                )

        except:
            pass

threading.Thread(target=run_server).start()

send("🚀 Bot comparando precios en todo Amazon")

while True:
    check()
    time.sleep(random.randint(90,180))
