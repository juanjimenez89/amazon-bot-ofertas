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
# 2. CONFIGURACIÓN Y LÓGICA (VERSIÓN DEFINITIVA)
# ==========================================
sent = set()
prices = {}

# URLs directas a lo más vendido de cada sección
CATEGORIAS = [
    "https://www.amazon.com.mx/gp/bestsellers/electronics/",
    "https://www.amazon.com.mx/gp/bestsellers/toys/",
    "https://www.amazon.com.mx/gp/bestsellers/beauty/",
    "https://www.amazon.com.mx/gp/bestsellers/fashion/",
    "https://www.amazon.com.mx/gp/bestsellers/home/",
    "https://www.amazon.com.mx/gp/bestsellers/videogames/"
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
        # ACTIVAMOS browser=true para que ScrapingAnt use un navegador real
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}&browser=true"
        r = requests.get(api_url, timeout=60)
        if r.status_code == 200:
            return r.text
        print(f"⚠️ Amazon nos bloqueó ({r.status_code}) en: {url_objetivo}", flush=True)
    except Exception as e:
        print(f"❌ Error conexión: {e}", flush=True)
    return None

def extract_price(html):
    if not html: return 0
    clean_html = html.replace('\n', '').replace('\r', '')
    try:
        # Buscamos patrones de precio en Amazon MX
        patterns = [
            r'priceAmount":(\d+\.?\d*)',
            r'priceToPay.*?(\d+\.?\d*)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'price" content="(\d+\.?\d*)'
        ]
        for p in patterns:
            m = re.search(p, clean_html)
            if m:
                val = m.group(1).replace(",", "")
                return float(val)
    except: pass
    return 0

def monitor():
    print(f"\n--- 🔎 INICIANDO RONDA DE MONITOREO ---", flush=True)
    
    for url in CATEGORIAS:
        nombre = url.split('/')[-2]
        print(f"📂 Revisando sección: {nombre}...", flush=True)
        
        html = get_html(url)
        if not html: continue

        # Buscamos códigos de producto ASIN
        asins = list(set(re.findall(r'B[A-Z0-9]{9}', html)))
        print(f"📦 Encontré {len(asins)} productos en {nombre}.", flush=True)
        
        for asin in asins[:5]:
            prod_url = f"https://www.amazon.com.mx/dp/{asin}"
            p_html = get_html(prod_url)
            price = extract_price(p_html)

            if price > 0:
                print(f"💰 {asin}: ${price}", flush=True)
                if asin in prices:
                    old = prices[asin]
                    # Alerta si baja un 30% o más
                    if price <= (old * 0.7):
                        if asin not in sent:
                            sent.add(asin)
                            msg = f"🚨 ¡OFERTA EN {nombre.upper()}! 🚨\nAntes: ${old}\nAhora: ${price}\nLink: {prod_url}"
                            send_telegram(msg)
                prices[asin] = price
            time.sleep(2)
            
    print("--- ✅ Ronda terminada. Esperando 15 min ---", flush=True)

def run_server():
    server = HTTPServer(('', 10000), Handler)
    print("✅ Servidor Render escuchando puerto 10000", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    print("🎬 BOT INICIADO...", flush=True)
    send_telegram("🚀 Bot de Ofertas Totalmente Activo.")
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"❌ Error: {e}", flush=True)
        time.sleep(900)
