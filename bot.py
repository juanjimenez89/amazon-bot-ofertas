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
# 2. GENERADOR DE LISTADOS (VERSIÓN AGRESIVA)
# ==========================================
productos_encontrados = []

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Estructura de la tabla mejorada para scannear rápido
        html_out = f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: -apple-system, sans-serif; margin: 0; padding: 15px; background: #f0f2f5; }}
                h1 {{ color: #1a1a1a; font-size: 20px; }}
                .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; min-width: 500px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
                th {{ background: #232f3e; color: white; position: sticky; top: 0; }}
                .precio {{ color: #b12704; font-weight: bold; font-size: 1.1em; }}
                .btn {{ background: #ffd814; padding: 8px 12px; border-radius: 5px; text-decoration: none; color: black; font-size: 13px; font-weight: bold; display: inline-block; }}
            </style>
        </head>
        <body>
            <h1>🔎 Sabueso: {len(productos_encontrados)} Productos Detectados</h1>
            <div class="card">
                <table>
                    <tr>
                        <th>ASIN</th>
                        <th>Precio actual</th>
                        <th>Acción</th>
                    </tr>
        """
        for p in productos_encontrados:
            html_out += f"""
                <tr>
                    <td><code>{p['asin']}</code></td>
                    <td class="precio">${p['precio']}</td>
                    <td><a href="{p['url']}" class="btn" target="_blank">🛒 Abrir</a></td>
                </tr>
            """
        html_out += "</table></div><p style='color:gray; font-size:12px;'>Actualizado: " + time.strftime("%H:%M:%S") + "</p></body></html>"
        self.wfile.write(html_out.encode('utf-8'))

def get_html(url_objetivo):
    try:
        # Forzamos proxy residencial para evitar el "Encontré 0 productos"
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}&proxy_type=residential"
        r = requests.get(api_url, timeout=45)
        return r.text if r.status_code == 200 else None
    except: return None

def monitor():
    global productos_encontrados
    print("🚀 Iniciando barrido profundo...", flush=True)
    lista_temp = []
    
    # Buscamos en las URLs que más productos arrojan de golpe
    fuentes = [
        "https://www.amazon.com.mx/gp/movers-and-shakers/electronics",
        "https://www.amazon.com.mx/gp/movers-and-shakers/toys",
        "https://www.amazon.com.mx/gp/movers-and-shakers/beauty",
        "https://www.amazon.com.mx/gp/movers-and-shakers/fashion"
    ]

    for url in fuentes:
        html = get_html(url)
        if not html: continue
        
        # Buscador de códigos ASIN ultra-amplio
        asins = list(set(re.findall(r'B0[A-Z0-9]{8}', html)))
        print(f"📦 Detectados {len(asins)} posibles productos en {url.split('/')[-1]}", flush=True)
        
        for asin in asins[:15]: # Procesamos 15 de cada categoría para llenar la tabla
            p_url = f"https://www.amazon.com.mx/dp/{asin}"
            p_html = get_html(p_url)
            if p_html:
                # Extractor de precio multizona
                match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', p_html)
                if match:
                    precio = match.group(1)
                    lista_temp.append({'asin': asin, 'precio': precio, 'url': p_url})
                    print(f"💰 Guardado: {asin} a ${precio}", flush=True)
            time.sleep(1) # Pausa mínima para fluidez
            
    productos_encontrados = lista_temp
    # Aviso discreto a Telegram
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": f"📊 Tabla lista: {len(productos_encontrados)} productos nuevos encontrados."})

def run_server():
    server = HTTPServer(('', 10000), Handler)
    server.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    while True:
        try:
            monitor()
        except Exception as e:
            print(f"❌ Error: {e}", flush=True)
        time.sleep(900)
