#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

print("🧪 [PING] Test de connexion simple")

try:
    response = requests.get("http://localhost:5000/", timeout=5)
    print(f"✅ [PING] Connexion OK: {response.status_code}")
except Exception as e:
    print(f"❌ [PING] Connexion échouée: {e}")
    
print("🧪 [PING] Fin du test")
