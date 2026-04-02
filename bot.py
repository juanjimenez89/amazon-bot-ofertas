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
# 2. CONFIGURACIÓN Y LÓGICA (MULTI-CATEGORIA)
# ==========================================
sent = set()
prices = {}

CATEGORIAS = [
    "https://www.amazon.com.mx/gp/movers-and-shakers/electronics/",
    "https://www.amazon.com.mx/gp/movers-and-shakers/toys/",
    "https://www.amazon.com.mx/gp/movers-and-shakers/beauty/",
    "https://www.amazon.com.mx/gp/movers-and-shakers/fashion/",
    "https://www.amazon.com.mx/gp/movers-and-shakers/home/",
    "https://www.amazon.com.mx/gp/movers-and-shakers/videogames/"
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BOT MONITOR MULTI-CATEGORIA ACTIVO")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"❌ Error Telegram: {e}", flush=True)

def get_html(url_objetivo):
    try:
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}&browser=false"
        r = requests.get(api_url, timeout=30)
        if r.status_code == 200:
            return r.text
        print(f"⚠️ Error ScrapingAnt: {r.status_code} en {url_objetivo}", flush=True)
    except Exception as e:
        print(f"❌ Error conexión: {e}", flush=True)
    return None

def extract_price(html):
    if not html: return 0
    try:
        m = re.search(r'priceAmount":(\d+\.?\d*)', html)
        if m: return float(m.group(1))
        m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', html)
        if m: return float(m.group(1).replace(",", ""))
        m = re.search(r'priceToPay.*?(\d+\.?\d*)', html)
        if m: return float(m.group(1))
    except: pass
    return 0

def monitor():
    print(f"\n--- 🚀 INICIANDO RONDA MULTI-CATEGORIA ({len(CATEGORIAS)} secciones) ---", flush=True)
    for url in CATEGORIAS:
        categoria_nombre = url.split('/')[-2]
        print(f"🔎 Revisando sección: {categoria_nombre}...", flush=True)
        html = get_html(url)
        if not html: continue
        asins = list(set(re.findall(r'/dp/([A-Z0-9]{10})', html)))
        print(f"📦 Encontré {len(asins)} productos en {categoria_nombre}", flush=True)
        for asin in asins[:5]:
            prod_url = f"https://www.amazon.com.mx/dp/{asin}"
            p_html = get_html(prod_url)
            price = extract_price(p_html)
            if price > 0:
                print(f"💰 {asin}: ${price}", flush=True)
                if asin in prices:
                    old = prices[asin]
                    if price <= (old * 0.6):
                        if asin not in sent:
                            sent.add(asin)
                            msg = f"🚨 ¡OFERTA EN {categoria_nombre.upper()}! 🚨\nAntes: ${old}\nAhora: ${price}\nLink: {prod_url}"
                            send_telegram(msg)
                prices[asin] = price
            time.sleep(1)
    print("--- ✅ Ronda terminada. Esperando 15 min ---", flush=True)

def run_server():
    try:
        server = HTTPServer(('', 10000), Handler)
        print("✅ Servidor Render activo", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"❌ Error servidor: {e}", flush=True)

# ==========================================
# 3. ARRANQUE FINAL
# ==========================================
if __name__ == "__main__":
    print("🎬 BOT MULTI-CATEGORIA ARRANCANDO...", flush=True)
    send_telegram("🚀 Bot de Ofertas Total Activo: Monitoreando Juguetes, Belleza, Electrónica, Hogar y Moda.")
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"❌ Error en el loop: {e}", flush=True)
        time.sleep(900)
