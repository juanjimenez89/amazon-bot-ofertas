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
# 2. CONFIGURACIÓN Y LÓGICA (VERSIÓN REFORZADA)
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
        # Usamos ScrapingAnt con un tiempo de espera de 30 seg
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}&browser=false"
        r = requests.get(api_url, timeout=35)
        if r.status_code == 200:
            return r.text
        print(f"⚠️ Error ScrapingAnt ({r.status_code}) en: {url_objetivo}", flush=True)
    except Exception as e:
        print(f"❌ Error conexión: {e}", flush=True)
    return None

def extract_price(html):
    if not html: return 0
    # Limpieza rápida del código para facilitar la búsqueda
    clean_html = html.replace('\n', '').replace('\r', '')
    try:
        # Método 1: JSON Interno de Amazon
        m = re.search(r'priceAmount":(\d+\.?\d*)', clean_html)
        if m: return float(m.group(1))
        
        # Método 2: Etiqueta de precio final (apexPrice)
        m = re.search(r'priceToPay.*?(\d+\.?\d*)', clean_html)
        if m: return float(m.group(1))
        
        # Método 3: Símbolo de pesos directo
        m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', clean_html)
        if m: return float(m.group(1).replace(",", ""))
        
        # Método 4: Meta tag de precio
        m = re.search(r'price" content="(\d+\.?\d*)', clean_html)
        if m: return float(m.group(1))
    except: pass
    return 0

def monitor():
    print(f"\n--- 🔎 INICIANDO RONDA MULTI-CATEGORIA ---", flush=True)
    
    for url in CATEGORIAS:
        nombre = url.split('/')[-2]
        print(f"📂 Revisando: {nombre}...", flush=True)
        
        html = get_html(url)
        if not html: continue

        # Buscamos códigos de producto (/dp/ASIN)
        asins = list(set(re.findall(r'/dp/([A-Z0-9]{10})', html)))
        print(f"📦 Encontré {len(asins)} productos posibles.", flush=True)
        
        # Revisamos los primeros 5 productos de cada categoría
        for asin in asins[:5]:
            prod_url = f"https://www.amazon.com.mx/dp/{asin}"
            p_html = get_html(prod_url)
            price = extract_price(p_html)

            if price > 0:
                print(f"💰 {asin}: ${price}", flush=True)
                
                # Si ya conocíamos el producto, comparamos
                if asin in prices:
                    old = prices[asin]
                    # Si baja un 40% o más (Ajusta el 0.6 si quieres que sea más o menos sensible)
                    if price <= (old * 0.6):
                        if asin not in sent:
                            sent.add(asin)
                            msg = f"🚨 ¡OFERTA DETECTADA EN {nombre.upper()}! 🚨\nAntes: ${old}\nAhora: ${price}\nLink: {prod_url}"
                            send_telegram(msg)
                            print(f"🔔 ALERTA ENVIADA: {asin}", flush=True)
                
                # Guardamos el precio para la siguiente vuelta
                prices[asin] = price
            else:
                print(f"❓ {asin}: No se pudo leer el precio todavía", flush=True)
            
            time.sleep(2) # Pausa para no ser bloqueados
            
    print("--- ✅ Ronda terminada. Esperando 15 min ---", flush=True)

def run_server():
    try:
        server = HTTPServer(('', 10000), Handler)
        print("✅ Servidor Render escuchando puerto 10000", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"❌ Error servidor web: {e}", flush=True)

# ==========================================
# 3. ARRANQUE DEL SISTEMA
# ==========================================
if __name__ == "__main__":
    print("🎬 BOT REFORZADO ARRANCANDO...", flush=True)
    
    # Confirmación inicial
    send_telegram("🚀 Bot Activo y Reforzado. Monitoreando todas las categorías...")
    
    # Servidor en segundo plano para que Render no se apague
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # Bucle infinito de revisión
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"❌ Error crítico en el loop: {e}", flush=True)
        
        # Espera 15 minutos (900 segundos) para la siguiente vuelta
        time.sleep(900)
