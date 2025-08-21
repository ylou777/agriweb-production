#!/usr/bin/env python3
"""
Serveur de test simple pour vérifier ngrok
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

class TestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        response = f"""
        <html>
        <head><title>Test Server</title></head>
        <body>
            <h1>✅ Serveur de test ngrok fonctionne !</h1>
            <p>Heure: {self.date_time_string()}</p>
            <p>Path: {self.path}</p>
            <p>Headers: {dict(self.headers)}</p>
        </body>
        </html>
        """
        self.wfile.write(response.encode())

if __name__ == "__main__":
    PORT = 8088  # Port différent de GeoServer
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        print(f"🚀 Serveur de test démarré sur http://localhost:{PORT}")
        print(f"🔗 Test avec ngrok: ngrok http {PORT}")
        httpd.serve_forever()
