#!/usr/bin/env python3
"""
Script de test pour vérifier que les fichiers 3D WebGL sont correctement intégrés
"""

import os
import sys

def test_3d_files():
    """Vérifier que tous les fichiers nécessaires existent"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        'AgW3b/static/js/calpinage_3d.js',
        'AgW3b/static/css/calpinage_3d.css',
        'AgW3b/templates/calpinage_pv.html',
        'DOCS_3D_WEBGL.md'
    ]
    
    print("🔍 Vérification des fichiers 3D WebGL...")
    print("-" * 60)
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        exists = os.path.exists(full_path)
        
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        
        if exists:
            # Afficher la taille
            size = os.path.getsize(full_path)
            size_kb = size / 1024
            print(f"   Taille: {size_kb:.2f} KB")
        else:
            all_exist = False
    
    print("-" * 60)
    
    if all_exist:
        print("✅ Tous les fichiers 3D WebGL sont présents !")
        print("\n📋 Prochaines étapes:")
        print("1. Redémarrer l'application Flask")
        print("2. Ouvrir le calpinage d'un prospect")
        print("3. Cliquer sur '🌐 Vue 3D' dans l'interface")
        print("4. Profiter de la visualisation 3D immersive !")
        return True
    else:
        print("❌ Certains fichiers sont manquants")
        return False

def check_template_integration():
    """Vérifier que le template contient les éléments 3D"""
    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'AgW3b/templates/calpinage_pv.html'
    )
    
    if not os.path.exists(template_path):
        print("❌ Template non trouvé")
        return False
    
    print("\n🔍 Vérification de l'intégration dans le template...")
    print("-" * 60)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'Three.js CDN': 'three@0.160.0' in content,
        'OrbitControls': 'OrbitControls.js' in content,
        'Module 3D JS': 'calpinage_3d.js' in content,
        'CSS 3D': 'calpinage_3d.css' in content,
        'Bouton Vue 3D': 'toggle3DView' in content,
        'Container 3D': 'viewer3DContainer' in content,
        'Fonction toggle': 'function toggle3DView' in content or 'onclick="toggle3DView()"' in content,
        'Mise à jour 3D': 'update3DFromZones' in content
    }
    
    all_ok = True
    for check_name, check_result in checks.items():
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        if not check_result:
            all_ok = False
    
    print("-" * 60)
    
    if all_ok:
        print("✅ Template correctement configuré pour la 3D !")
    else:
        print("⚠️ Certaines intégrations sont manquantes")
    
    return all_ok

def check_js_module():
    """Vérifier le contenu du module JavaScript 3D"""
    js_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'AgW3b/static/js/calpinage_3d.js'
    )
    
    if not os.path.exists(js_path):
        print("❌ Module JS 3D non trouvé")
        return False
    
    print("\n🔍 Analyse du module JavaScript 3D...")
    print("-" * 60)
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.count('\n')
    
    # Compter les fonctions principales
    functions = {
        'Classe Calpinage3DViewer': 'class Calpinage3DViewer' in content,
        'init()': 'init()' in content,
        'createBuildingFromZones()': 'createBuildingFromZones' in content,
        'addModules3D()': 'addModules3D' in content,
        'updateSunPosition()': 'updateSunPosition' in content,
        'toggle()': 'toggle()' in content,
        'animate()': 'animate()' in content
    }
    
    print(f"📄 Lignes de code: {lines}")
    print(f"📦 Taille: {os.path.getsize(js_path) / 1024:.2f} KB")
    print()
    
    for func_name, exists in functions.items():
        status = "✅" if exists else "❌"
        print(f"{status} {func_name}")
    
    print("-" * 60)
    
    return all(functions.values())

if __name__ == '__main__':
    print("=" * 60)
    print("   TEST D'INTÉGRATION 3D WEBGL - AGRIWEB")
    print("=" * 60)
    print()
    
    files_ok = test_3d_files()
    template_ok = check_template_integration()
    js_ok = check_js_module()
    
    print("\n" + "=" * 60)
    if files_ok and template_ok and js_ok:
        print("✅✅✅ TOUS LES TESTS PASSÉS ! ✅✅✅")
        print("=" * 60)
        print("\n🚀 La fonctionnalité 3D WebGL est prête à l'emploi !")
        print("\n💡 Avantages de la vue 3D:")
        print("   • Visualisation réaliste des installations")
        print("   • Meilleure compréhension pour les clients")
        print("   • Simulation d'ombrage en temps réel")
        print("   • Navigation intuitive (rotation, zoom, pan)")
        print("   • Rendu accéléré par GPU (WebGL)")
        sys.exit(0)
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("=" * 60)
        print("\n⚠️ Veuillez vérifier les erreurs ci-dessus")
        sys.exit(1)
