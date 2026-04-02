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
        print(f"❌ Error Telegram: {e}", flush=True)

def get_html(url_objetivo):
    try:
        # Usamos ScrapingAnt para saltar el bloqueo de Amazon
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}&browser=false"
        r = requests.get(api_url, timeout=30)
        if r.status_code == 200:
            return r.text
        print(f"⚠️ Error ScrapingAnt: {r.status_code}", flush=True)
    except Exception as e:
        print(f"❌ Error conexión: {e}", flush=True)
    return None

def extract_price(html):
    if not html: return 0
    try:
        # Intento 1: Buscar en el JSON de Amazon
        m = re.search(r'priceAmount":(\d+\.?\d*)', html)
        if m: return float(m.group(1))
        
        # Intento 2: Buscar con símbolo de pesos y decimales
        m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', html)
        if m: return float(m.group(1).replace(",", ""))
        
        # Intento 3: Buscar en etiquetas de oferta
        m = re.search(r'priceToPay.*?(\d+\.?\d*)', html)
        if m: return float(m.group(1))
    except: pass
    return 0

def monitor():
    url_ofertas = "https://www.amazon.com.mx/gp/goldbox"
    print("\n--- 🔎 Iniciando nueva revisión en Amazon MX ---", flush=True)
    
    html = get_html(url_ofertas)
    if not html: 
        print("❌ No pude entrar a la página de ofertas hoy.", flush=True)
        return

    # Extraer códigos de productos (ASINs)
    asins = list(set(re.findall(r'data-asin="([A-Z0-9]{10})"', html)))
    print(f"📦 Encontré {len(asins)} productos en la lista.", flush=True)
    
    # Revisamos los primeros 10 para no gastar todos los créditos de golpe
    for asin in asins[:10]:
        prod_url = f"https://www.amazon.com.mx/dp/{asin}"
        p_html = get_html(prod_url)
        price = extract_price(p_html)

        if price > 0:
            print(f"💰 {asin}: ${price}", flush=True)
            
            if asin in prices:
                old = prices[asin]
                # Si el precio baja un 40% o más, avisamos
                if price <= (old * 0.6):
                    if asin not in sent:
                        sent.add(asin)
                        msg = f"🚨 ¡ERROR DE PRECIO O BAJÓN! 🚨\nAntes: ${old}\nAhora: ${price}\nLink: {prod_url}"
                        send_telegram(msg)
                        print(f"🔔 ¡ALERTA ENVIADA PARA {asin}!", flush=True)
            
            prices[asin] = price
        else:
            print(f"❓ {asin}: No se pudo leer el precio", flush=True)
        
        # Pequeña pausa para no saturar
        time.sleep(2)
    print("--- ✅ Revisión terminada. Esperando 15 min ---", flush=True)

def run_server():
    try:
        server = HTTPServer(('', 10000), Handler)
        print("✅ Servidor Render escuchando en puerto 10000", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"❌ Error en servidor web: {e}", flush=True)

# ==========================================
# 3. ARRANQUE DEL SISTEMA
# ==========================================
if __name__ == "__main__":
    print("🎬 BOT ARRANCANDO...", flush=True)
    
    # Mensaje de confirmación a Telegram
    send_telegram("🚀 Bot Activo: A partir de ahora te avisaré si detecto errores de precio en Amazon MX.")
    
    # Arrancar servidor web en segundo plano
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    
    # Entrar al bucle de monitoreo
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"❌ Error crítico en el loop: {e}", flush=True)
        time.sleep(900) # 15 minutos entre vueltas
