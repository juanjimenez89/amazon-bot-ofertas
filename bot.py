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
# 2. GENERADOR DE LISTADOS MASIVOS (WEB)
# ==========================================
productos_encontrados = [] # Aquí guardaremos la lista para mostrarla

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Creamos una página web simple para que veas la lista
        html_out = f"""
        <html>
        <head>
            <title>Panel de Caza-Ofertas</title>
            <style>
                body {{ font-family: sans-serif; background: #f4f4f9; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; background: white; }}
                th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
                th {{ background: #232f3e; color: white; }}
                tr:nth-child(even) {{ background: #f2f2f2; }}
                .precio {{ font-weight: bold; color: #b12704; }}
                .descuento {{ background: #ffd814; padding: 5px; border-radius: 4px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>📦 Listado de Productos Detectados</h1>
            <p>Se actualiza automáticamente cada 15 minutos.</p>
            <table>
                <tr>
                    <th>Producto (ASIN)</th>
                    <th>Precio Detectado</th>
                    <th>Link Directo</th>
                </tr>
        """
        for p in productos_encontrados:
            html_out += f"""
                <tr>
                    <td>{p['asin']}</td>
                    <td class="precio">${p['precio']}</td>
                    <td><a href="{p['url']}" target="_blank">Ver en Amazon</a></td>
                </tr>
            """
        html_out += "</table></body></html>"
        self.wfile.write(html_out.encode('utf-8'))

def get_html(url_objetivo):
    try:
        api_url = f"https://api.scrapingant.com/v2/general?url={url_objetivo}&x-api-key={SCRAPER_API_KEY}"
        r = requests.get(api_url, timeout=40)
        return r.text if r.status_code == 200 else None
    except: return None

def monitor():
    global productos_encontrados
    print("🔎 Iniciando escaneo masivo...", flush=True)
    nuevos_productos = []
    
    # Buscamos en secciones de mucho movimiento
    urls = [
        "https://www.amazon.com.mx/gp/movers-and-shakers/electronics",
        "https://www.amazon.com.mx/gp/movers-and-shakers/toys",
        "https://www.amazon.com.mx/gp/goldbox"
    ]

    for url in urls:
        html = get_html(url)
        if not html: continue
        asins = list(set(re.findall(r'B0[A-Z0-9]{8}', html)))
        
        for asin in asins[:10]: # Sacamos 10 de cada categoría
            p_url = f"https://www.amazon.com.mx/dp/{asin}"
            p_html = get_html(p_url)
            if p_html:
                # Extraer precio
                m = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', p_html)
                precio = m.group(1) if m else "No visible"
                nuevos_productos.append({'asin': asin, 'precio': precio, 'url': p_url})
                print(f"✅ Registrado: {asin} - ${precio}", flush=True)
            time.sleep(1)
            
    productos_encontrados = nuevos_productos
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": "📊 ¡Lista actualizada! Entra a tu link de Render para verla."})

def run_server():
    server = HTTPServer(('', 10000), Handler)
    server.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
    while True:
        monitor()
        time.sleep(900)


