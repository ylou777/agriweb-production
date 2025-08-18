#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

# Test simple et rapide de l'endpoint
print("🧪 [TEST SIMPLE] Test endpoint département")

test_data = {
    "rapports": [
        {
            "nom": "Test Commune",
            "data": {
                "parcelles": [
                    {"id": "rpg1", "surface": 5.0},
                    {"id": "rpg2", "surface": 3.0}
                ],
                "eleveurs": [
                    {"nom": "Eleveur 1"},
                    {"nom": "Eleveur 2"}
                ]
            },
            "nb_eleveurs": 2
        }
    ]
}

try:
    response = requests.post(
        "http://localhost:5000/rapport_departement", 
        json=test_data,
        timeout=10
    )
    
    print(f"✅ [TEST] Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ [TEST] Réponse HTML reçue avec succès")
        print(f"📊 [TEST] Taille réponse: {len(response.text)} caractères")
        
        # Vérifier si les valeurs synthèse sont dans le HTML
        if "Agriculteurs : 2" in response.text:
            print("✅ [TEST] Synthèse agriculteurs affichée correctement")
        else:
            print("❌ [TEST] Synthèse agriculteurs manquante")
            
        if "Parcelles : 2" in response.text:
            print("✅ [TEST] Synthèse parcelles affichée correctement")
        else:
            print("❌ [TEST] Synthèse parcelles manquante")
    else:
        print(f"❌ [TEST] Erreur: {response.status_code}")
        print(f"❌ [TEST] Réponse: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ [TEST] Exception: {e}")

print("🧪 [TEST SIMPLE] Fin du test")
