from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

SERVICE_NAME = os.environ.get("MOCK_SERVICE_NAME", "unknown")
PORT = int(os.environ.get("MOCK_SERVICE_PORT", 8080))

class Handler(BaseHTTPRequestHandler):
    def _send(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(content).encode())

    def do_GET(self):
        self._send({"service": SERVICE_NAME, "method": "GET", "path": self.path})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        self._send({"service": SERVICE_NAME, "method": "POST", "path": self.path, "body": body})

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
