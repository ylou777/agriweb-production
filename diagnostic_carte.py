#!/usr/bin/env python3
"""
Diagnostic détaillé de la carte HTML
"""

import requests

def diagnostic_carte_html():
    """Diagnostic détaillé du contenu HTML de la carte"""
    print("🧪 [DIAGNOSTIC] Analyse détaillée de la carte HTML")
    
    try:
        response = requests.get("http://localhost:5000/generated_map", timeout=30)
        
        if response.status_code == 200:
            html_content = response.text
            print(f"📄 [HTML] Taille: {len(html_content)} caractères")
            
            # Analyse des balises de structure
            html_checks = {
                "<!DOCTYPE": html_content.count("<!DOCTYPE"),
                "<html": html_content.count("<html"),
                "</html>": html_content.count("</html>"),
                "<head": html_content.count("<head"),
                "</head>": html_content.count("</head>"),
                "<body": html_content.count("<body"),
                "</body>": html_content.count("</body>"),
            }
            
            print("📊 [STRUCTURE] Comptage des balises principales:")
            for tag, count in html_checks.items():
                status = "✅" if count == 1 else "❌" if count == 0 else f"⚠️ ({count})"
                print(f"    {status} {tag}: {count}")
            
            # Vérification de l'intégrité
            has_doctype = html_content.startswith("<!DOCTYPE") or "<!DOCTYPE" in html_content[:100]
            has_complete_structure = (
                html_checks["<html"] >= 1 and 
                html_checks["</html>"] >= 1 and
                html_checks["<head"] >= 1 and
                html_checks["</head>"] >= 1 and
                html_checks["<body"] >= 1 and
                html_checks["</body>"] >= 1
            )
            
            print(f"\n🔍 [ANALYSE]:")
            print(f"    DOCTYPE présent: {has_doctype}")
            print(f"    Structure complète: {has_complete_structure}")
            
            # Début et fin du document
            print(f"\n📄 [DÉBUT] Premiers 200 caractères:")
            print(repr(html_content[:200]))
            
            print(f"\n📄 [FIN] Derniers 200 caractères:")
            print(repr(html_content[-200:]))
            
            # Recherche d'erreurs courantes
            if "javascript error" in html_content.lower():
                print("⚠️ [ERREUR] Erreur JavaScript détectée")
            
            if "python error" in html_content.lower():
                print("⚠️ [ERREUR] Erreur Python détectée")
                
            # Vérification des données de toitures
            toiture_refs = html_content.lower().count("toiture")
            building_refs = html_content.lower().count("building")
            parcelle_refs = html_content.lower().count("parcelle")
            
            print(f"\n📊 [DONNÉES] Occurrences:")
            print(f"    'toiture': {toiture_refs}")
            print(f"    'building': {building_refs}")
            print(f"    'parcelle': {parcelle_refs}")
            
            return has_complete_structure
            
        else:
            print(f"❌ [ERREUR] Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ [EXCEPTION] {e}")
        return False

if __name__ == "__main__":
    diagnostic_carte_html()
