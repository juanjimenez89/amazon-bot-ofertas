import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re

# ==========================================
# 1. TUS DATOS (CAMBIA ESTO)
# ==========================================
TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQSA"
CHAT_ID = "-1003785044780" # Recuerda el "-" si es grupo (ej: -100123456)
SCRAPER_API_KEY = "0f356e3516784877bcf481cc9b6fdac0" 

# ==========================================
# 2. LÓGICA DE MONITOREO (VERSIÓN COMPATIBLE)
# ==========================================
sent = set()
prices = {}

CATEGORIAS = [
    "https://www.amazon.com.mx/gp/bestsellers/electronics",
    "https://www.amazon.com.mx/gp/bestsellers/toys",
    "https://www.amazon.com.mx/gp/bestsellers/beauty",
    "https://www.amazon.com.mx/gp/bestsellers/home"
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BOT TRABAJANDO")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"❌ Error Telegram: {e}", flush=True)

def get_html(url_objetivo):
    try:
        # Quitamos browser=true para evitar el error 422 si la cuenta es Free
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}"
        r = requests.get(api_url, timeout=30)
        if r.status_code == 200:
            return r.text
        print(f"⚠️ Error ScrapingAnt {r.status_code} en URL: {url_objetivo}", flush=True)
    except Exception as e:
        print(f"❌ Error conexión: {e}", flush=True)
    return None

def extract_price(html):
    if not html: return 0
    try:
        # Buscador de precio simplificado
        m = re.search(r'priceAmount":(\d+\.?\d*)', html)
        if m: return float(m.group(1))
        
        m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', html)
        if m: return float(m.group(1).replace(",", ""))
    except: pass
    return 0

def monitor():
    print(f"\n--- 🔎 NUEVA RONDA ---", flush=True)
    for url in CATEGORIAS:
        nombre = url.split('/')[-1]
        print(f"📂 Revisando: {nombre}...", flush=True)
        
        html = get_html(url)
        if not html: continue

        # Buscamos códigos ASIN
        asins = list(set(re.findall(r'B[A-Z0-9]{9}', html)))
        print(f"📦 Productos encontrados: {len(asins)}", flush=True)
        
        for asin in asins[:3]: # Revisamos 3 de cada una
            prod_url = f"https://www.amazon.com.mx/dp/{asin}"
            p_html = get_html(prod_url)
            price = extract_price(p_html)

            if price > 0:
                print(f"💰 {asin}: ${price}", flush=True)
                if asin in prices:
                    old = prices[asin]
                    if price <= (old * 0.7): # 30% de descuento
                        if asin not in sent:
                            sent.add(asin)
                            send_telegram(f"🚨 OFERTA: {asin}\nAntes: ${old}\nAhora: ${price}\n{prod_url}")
                prices[asin] = price
            time.sleep(2)
    print("--- ✅ Fin de ronda. Esperando 15 min ---", flush=True)

def run_server():
    server = HTTPServer(('', 10000), Handler)
    print("✅ Puerto 10000 listo", flush=True)
    server.serve_forever()

# ==========================================
# 3. ARRANQUE
# ==========================================
if __name__ == "__main__":
    print("🎬 INICIANDO...", flush=True)
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"❌ Error: {e}", flush=True)
        time.sleep(900)
