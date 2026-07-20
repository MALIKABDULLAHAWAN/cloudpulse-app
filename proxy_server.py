import http.server
import socketserver
import urllib.request
import os

PORT = 3000
BACKEND_URL = 'http://localhost:8000'

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='frontend', **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/'):
            # Proxy to backend
            target_url = BACKEND_URL + self.path.replace('/api/', '/')
            try:
                req = urllib.request.Request(target_url)
                with urllib.request.urlopen(req) as response:
                    self.send_response(response.status)
                    for k, v in response.headers.items():
                        if k.lower() not in ['transfer-encoding', 'connection']:
                            self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(response.read())
            except Exception as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(f"502 Bad Gateway: {e}".encode())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            target_url = BACKEND_URL + self.path.replace('/api/', '/')
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                req = urllib.request.Request(target_url, data=post_data, headers={'Content-Type': 'application/json'}, method='POST')
                with urllib.request.urlopen(req) as response:
                    self.send_response(response.status)
                    for k, v in response.headers.items():
                        if k.lower() not in ['transfer-encoding', 'connection']:
                            self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(response.read())
            except Exception as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(f"502 Bad Gateway: {e}".encode())

Handler = ProxyHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving frontend with API proxy at http://localhost:{PORT}")
    httpd.serve_forever()
