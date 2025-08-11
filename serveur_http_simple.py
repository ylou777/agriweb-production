#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serveur HTTP simple sans Flask pour test
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

class ToitureHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Surcharge pour éviter WinError 233 dans les logs"""
        try:
            super().log_message(format, *args)
        except OSError:
            pass

    def do_GET(self):
        """Gestion des requêtes GET"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            params = parse_qs(parsed_url.query)
            
            if path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Serveur HTTP simple fonctionnel')
                
            elif path == '/test_toiture':
                commune = params.get('commune', ['Test'])[0]
                recherche_type = params.get('recherche_type', ['toiture'])[0]
                
                response = {
                    "status": "success",
                    "commune": commune,
                    "recherche_type": recherche_type,
                    "message": "Test toiture avec serveur HTTP simple"
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())

if __name__ == '__main__':
    try:
        print("🌐 [HTTP] Démarrage serveur HTTP simple sur port 5002...")
        server = HTTPServer(('127.0.0.1', 5002), ToitureHandler)
        print("🌐 [HTTP] Serveur actif sur http://127.0.0.1:5002")
        server.serve_forever()
    except KeyboardInterrupt:
        print("🛑 [HTTP] Arrêt du serveur")
        server.server_close()
    except Exception as e:
        print(f"❌ [HTTP] Erreur: {e}")
        import traceback
        traceback.print_exc()
