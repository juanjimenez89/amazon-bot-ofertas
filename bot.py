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
# 2. CONFIGURACIÓN DEL BOT
# ==========================================
sent = set()
prices = {}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BOT MONITOR ACTIVO")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"Error Telegram: {e}", flush=True)

def get_html(url_objetivo):
    try:
        # Usamos ScrapingAnt para saltar el bloqueo de Amazon
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}&browser=false"
        r = requests.get(api_url, timeout=30)
        if r.status_code == 200:
            return r.text
        print(f"Error ScrapingAnt: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Error conexión: {e}", flush=True)
    return None

def extract_price(html):
    if not html: return 0
    try:
        # Buscamos el precio en el código de Amazon MX
        m = re.search(r'priceAmount":(\d+\.?\d*)', html)
        if m: return float(m.group(1))
        # Intento secundario con símbolo de pesos
        m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', html)
        if m: return float(m.group(1).replace(",", ""))
    except: pass
    return 0

def monitor():
    url_ofertas = "https://www.amazon.com.mx/gp/goldbox"
    print("--- Revisando ofertas en Amazon MX ---", flush=True)
    
    html = get_html(url_ofertas)
    if not html: return

    # Buscamos códigos de productos (ASINs)
    asins = list(set(re.findall(r'data-asin="([A-Z0-9]{10})"', html)))
    
    # Revisamos los primeros 10 para ahorrar créditos de la API
    for asin in asins[:10]:
        prod_url = f"https://www.amazon.com.mx/dp/{asin}"
        p_html = get_html(prod_url)
        price = extract_price(p_html)

        if price > 10:
            print(f"Producto {asin}: ${price}", flush=True)
            
            if asin in prices:
                old = prices[asin]
                # Si baja más del 40%, avisamos
                if price <= (old * 0.6):
                    if asin not in sent:
                        sent.add(asin)
                        msg = f"🚨 ¡OFERTA DETECTADA! 🚨\nAntes: ${old}\nAhora: ${price}\nLink: {prod_url}"
                        send_telegram(msg)
            
            prices[asin] = price
        time.sleep(2)

def loop():
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"Error en loop: {e}", flush=True)
        # Espera 15 minutos entre revisiones
        time.sleep(900)

def run_server():
    server = HTTPServer(('', 10000), Handler)
    print("✅ Servidor web listo (Puerto 10000)", flush=True)
    server.serve_forever()

# ==========================================
# 3. ARRANQUE DEL BOT
# ==========================================
if __name__ == "__main__":
    print("🎬 Iniciando bot...", flush=True)
    
    # Prueba de Telegram
    send_telegram("🚀 Bot de Amazon Conectado. Buscando errores...")
    
    # Hilo del servidor para Render
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # Iniciamos el monitor
    print("🕵️ Monitor arrancado...", flush=True)
    loop()
