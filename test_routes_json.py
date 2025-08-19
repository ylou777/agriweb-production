#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des routes JSON AgriWeb
"""

import requests
import json

def test_route(url, description):
    print(f"\n🔍 Test: {description}")
    print(f"URL: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Non défini')}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            content = response.text[:200]
            print(f"HTML début: {content}...")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🌾 Test des routes AgriWeb")
    
    # Test routes principales
    test_route("http://localhost:5001/api/status", "Status API")
    test_route("http://localhost:5001/search_by_commune", "Recherche commune (GET)")
    test_route("http://localhost:5001/altitude_point?lat=47.2184&lon=-1.5536", "Altitude point")
    test_route("http://localhost:5001/debug", "Debug routes")
    
    # Test avec session
    print("\n🔐 Test avec session...")
    session = requests.Session()
    
    # Login
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_response = session.post("http://localhost:5001/login", data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    # Test route protégée
    protected_response = session.get("http://localhost:5001/search_by_commune")
    print(f"Route protégée status: {protected_response.status_code}")
    print(f"Content-Type: {protected_response.headers.get('content-type', 'Non défini')}")
