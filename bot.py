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
# 2. CONFIGURACIÓN Y LÓGICA (VERSIÓN FINAL PRO)
# ==========================================
sent = set()
prices = {}

# Usamos las listas de los más vendidos directamente
CATEGORIAS = [
    "https://www.amazon.com.mx/gp/bestsellers/electronics/",
    "https://www.amazon.com.mx/gp/bestsellers/toys/",
    "https://www.amazon.com.mx/gp/bestsellers/beauty/",
    "https://www.amazon.com.mx/gp/bestsellers/home/",
    "https://www.amazon.com.mx/gp/bestsellers/videogames/"
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MONITOR DE OFERTAS TRABAJANDO")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"❌ Error Telegram: {e}", flush=True)

def get_html(url_objetivo):
    try:
        # Usamos browser=true y activamos el proxy de ScrapingAnt
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}&browser=true&proxy_type=display"
        r = requests.get(api_url, timeout=60)
        if r.status_code == 200:
            return r.text
        print(f"⚠️ Amazon respondió con error {r.status_code}", flush=True)
    except Exception as e:
        print(f"❌ Error de conexión: {e}", flush=True)
    return None

def extract_price(html):
    if not html: return 0
    try:
        # Buscamos el precio en el formato de Amazon MX
        # Primero buscamos el símbolo $ seguido de números y comas
        match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', html)
        if match:
            return float(match.group(1).replace(",", ""))
        
        # Si no, buscamos en el atributo de precio
        match = re.search(r'priceAmount":(\d+\.?\d*)', html)
        if match:
            return float(match.group(1))
    except: pass
    return 0

def monitor():
    print(f"\n--- 🔎 INICIANDO RONDA DE MONITOREO TOTAL ---", flush=True)
    
    for url in CATEGORIAS:
        nombre = url.split('/')[-2]
        print(f"📂 Revisando sección: {nombre}...", flush=True)
        
        html = get_html(url)
        if not html: continue

        # BUSCADOR MEJORADO: Busca cualquier código ASIN (B seguido de 9 letras/números)
        asins = list(set(re.findall(r'B[A-Z0-9]{9}', html)))
        
        # Filtramos para quitar códigos que no sean productos (opcional)
        valid_asins = [a for a in asins if len(a) == 10]
        print(f"📦 Encontré {len(valid_asins)} productos en {nombre}.", flush=True)
        
        # Revisamos los primeros 3 productos de cada sección
        for asin in valid_asins[:3]:
            prod_url = f"https://www.amazon.com.mx/dp/{asin}"
            p_html = get_html(prod_url)
            price = extract_price(p_html)

            if price > 0:
                print(f"💰 Producto {asin}: ${price}", flush=True)
                
                if asin in prices:
                    old = prices[asin]
                    # Alerta si el precio baja 35% o más
                    if price <= (old * 0.65):
                        if asin not in sent:
                            sent.add(asin)
                            msg = f"🚨 ¡OFERTA DETECTADA! 🚨\nSección: {nombre.upper()}\nAntes: ${old}\nAhora: ${price}\nLink: {prod_url}"
                            send_telegram(msg)
                            print(f"🔔 MENSAJE ENVIADO A TELEGRAM", flush=True)
                
                prices[asin] = price
            else:
                print(f"❓ {asin}: Precio no visible por ahora", flush=True)
            
            time.sleep(3) # Pausa de seguridad
            
    print("--- ✅ Ronda terminada. Esperando 15 min ---", flush=True)

def run_server():
    try:
        server = HTTPServer(('', 10000), Handler)
        print("✅ Servidor Render escuchando puerto 10000", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"❌ Error servidor: {e}", flush=True)

# ==========================================
# 3. ARRANQUE DEL SISTEMA
# ==========================================
if __name__ == "__main__":
    print("🎬 BOT INICIADO CON ÉXITO", flush=True)
    send_telegram("🚀 Bot Activo: Empezando a rastrear categorías...")
    
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"❌ Error crítico: {e}", flush=True)
        time.sleep(900)
