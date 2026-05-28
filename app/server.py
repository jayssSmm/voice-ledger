import threading, os, logging
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)

class _PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def log_message(self, *args): pass

def start_ping_server(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), _PingHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info(f"Ping server on port {port}")