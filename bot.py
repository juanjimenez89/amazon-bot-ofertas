import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot activo")

def run_server():
    port = 10000
    server = HTTPServer(('', port), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()

print("Amazon bot iniciado")

while True:
    time.sleep(60)
