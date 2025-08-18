#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader, TemplateError
import os

# Test du template simple
template_dir = 'templates'
env = Environment(loader=FileSystemLoader(template_dir))

print("🧪 [JINJA] Test des templates")

# Test 1: Template minimal
try:
    template = env.get_template('rapport_departement_minimal.html')
    print("✅ [JINJA] Template minimal chargé avec succès")
    
    # Test de rendu avec données factices
    test_data = {
        'synthese': {
            'nb_agriculteurs': 2,
            'nb_parcelles': 2
        },
        'reports': [
            {
                'nom': 'Test Commune',
                'nb_eleveurs': 1,
                'data': {
                    'parcelles': [{'test': 'data'}]
                }
            }
        ]
    }
    
    rendered = template.render(**test_data)
    print("✅ [JINJA] Template minimal rendu avec succès")
    print(f"📊 [JINJA] Longueur HTML: {len(rendered)} caractères")
    
except TemplateError as e:
    print(f"❌ [JINJA] Erreur template minimal: {e}")
except Exception as e:
    print(f"❌ [JINJA] Erreur générale template minimal: {e}")

# Test 2: Template complexe
try:
    template = env.get_template('rapport_departement.html')
    print("✅ [JINJA] Template complexe chargé avec succès")
    
    rendered = template.render(**test_data)
    print("✅ [JINJA] Template complexe rendu avec succès")
    print(f"📊 [JINJA] Longueur HTML: {len(rendered)} caractères")
    
except TemplateError as e:
    print(f"❌ [JINJA] Erreur template complexe: {e}")
    print(f"📍 [JINJA] Type erreur: {type(e).__name__}")
except Exception as e:
    print(f"❌ [JINJA] Erreur générale template complexe: {e}")

print("🧪 [JINJA] Fin des tests")
