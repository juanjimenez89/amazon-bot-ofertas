import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import re

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = "8730063920:AAGT5H5firb-8JC-NpypA1GFKa-N2tTbQS"
CHAT_ID = "-1003785044780"
SCRAPER_API_KEY = "0f356e3516784877bcf481cc9b6fdac0" 

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
    except: pass

def get_html(url):
    try:
        # Usamos ScrapingAnt para saltar el bloqueo
        api_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={SCRAPER_API_KEY}&browser=false"
        r = requests.get(api_url, timeout=25)
        return r.text if r.status_code == 200 else None
    except: return None

def extract_price(html):
    if not html: return 0
    # Buscamos el precio en el formato de Amazon MX
    m = re.search(r'priceAmount":(\d+\.?\d*)', html)
    if not m:
        # Intento secundario por si cambian el JSON
        m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', html)
    return float(m.group(1).replace(",", "")) if m else 0

def monitor():
    # Sección de Ofertas del Día
    url_ofertas = "https://www.amazon.com.mx/gp/goldbox"
    html = get_html(url_ofertas)
    if not html: return

    # Extraer ASINs (identificadores de producto)
    asins = list(set(re.findall(r'data-asin="([A-Z0-9]{10})"', html)))
    
    # Revisamos los primeros 12 para no agotar créditos rápido
    for asin in asins[:12]:
        prod_url = f"https://www.amazon.com.mx/dp/{asin}"
        p_html = get_html(prod_url)
        price = extract_price(p_html)

        if price > 10:
            if asin in prices:
                old = prices[asin]
                # Si el precio baja más del 50%, es un posible error
                if price < (old * 0.5):
                    if asin not in sent:
                        sent.add(asin)
                        send_telegram(f"🚨 ¡ERROR DE PRECIO! 🚨\nAntes: ${old}\nAhora: ${price}\n{prod_url}")
            
            prices[asin] = price
            print(f"Producto {asin}: ${price}")
        time.sleep(2)

def loop():
    while True:
        try: monitor()
        except: pass
        time.sleep(900) # Revisa cada 15 minutos
def run_server():
    try:
        server = HTTPServer(('', 10000), Handler)
        print("✅ Servidor web iniciado en puerto 10000")
        server.serve_forever()
    except Exception as e:
        print(f"Error en servidor: {e}")

if __name__ == "__main__":
    print("🎬 Iniciando bot...")
    
    # 1. Intentamos enviar el mensaje a Telegram primero
    send_telegram("🚀 ¡Bot conectado! Buscando errores de precio...")
    
    # 2. Arrancamos el servidor en segundo plano
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # 3. Arrancamos el buscador de ofertas (el loop infinito)
    print("🕵️ Monitor de Amazon arrancado...")
    loop()

