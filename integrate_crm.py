"""
Script de test pour intégrer le CRM dans votre application AgriWeb existante
Modifie agriweb_hebergement_gratuit.py pour ajouter les fonctionnalités CRM
"""

import os
import sys

def integrate_crm_into_agriweb():
    """Intègre le CRM dans l'application AgriWeb principale"""
    
    agriweb_file = 'agriweb_hebergement_gratuit.py'
    
    if not os.path.exists(agriweb_file):
        print(f"❌ Fichier {agriweb_file} non trouvé")
        return False
    
    print(f"🔧 Intégration du CRM dans {agriweb_file}...")
    
    # Lire le contenu actuel
    with open(agriweb_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si l'intégration CRM est déjà présente
    if 'CRM_INTEGRATION_MARKER' in content:
        print("✅ CRM déjà intégré dans l'application")
        return True
    
    # Rechercher les points d'injection
    import_section = None
    routes_section = None
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Trouver la section des imports Flask
        if 'from flask import' in line and import_section is None:
            import_section = i
        
        # Trouver la fin des routes (avant if __name__ == '__main__')
        if 'if __name__' in line and '__main__' in line:
            routes_section = i - 1
            break
    
    if import_section is None or routes_section is None:
        print("❌ Impossible de trouver les points d'injection dans le fichier")
        return False
    
    # Injections CRM
    crm_imports = [
        "",
        "# === CRM_INTEGRATION_MARKER ===",
        "# Import des modules CRM",
        "try:",
        "    from agriweb_crm_routes import add_crm_routes, get_crm_widget_html, CRM_INTEGRATION_JS",
        "    from agriweb_crm_bridge import integrate_agriweb_search_to_crm, is_crm_available",
        "    CRM_AVAILABLE = True",
        "    print('✅ CRM: Modules importés avec succès')",
        "except ImportError as e:",
        "    print(f'⚠️ CRM: Modules non disponibles - {e}')",
        "    CRM_AVAILABLE = False",
        "",
    ]
    
    crm_routes = [
        "",
        "# === CRM ROUTES ===",
        "if CRM_AVAILABLE:",
        "    try:",
        "        add_crm_routes(app)",
        "        print('✅ CRM: Routes ajoutées')",
        "    except Exception as e:",
        "        print(f'⚠️ CRM: Erreur ajout routes - {e}')",
        "",
        "# Route pour inclure le widget CRM",
        "@app.route('/crm/widget')",
        "def crm_widget():",
        "    if CRM_AVAILABLE:",
        "        return get_crm_widget_html(session)",
        "    else:",
        "        return '<div>CRM non disponible</div>'",
        "",
    ]
    
    # Injecter les imports après la section d'imports Flask
    lines[import_section:import_section] = crm_imports
    
    # Ajuster l'index pour les routes
    routes_section += len(crm_imports)
    
    # Injecter les routes avant if __name__ == '__main__'
    lines[routes_section:routes_section] = crm_routes
    
    # Écrire le fichier modifié
    modified_content = '\n'.join(lines)
    
    # Backup de l'original
    backup_file = f"{agriweb_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Backup créé: {backup_file}")
    
    # Écrire le fichier modifié
    with open(agriweb_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✅ CRM intégré avec succès dans l'application AgriWeb")
    return True

def create_crm_integration_guide():
    """Crée un guide d'intégration"""
    guide_content = """
# 🎯 Guide d'Intégration CRM dans AgriWeb

## État Actuel
Votre application AgriWeb principale (`agriweb_hebergement_gratuit.py`) fonctionne avec:
- Recherches par commune
- Données géographiques (parcelles, bâtiments, réseaux)
- Interface web complète

## Intégration CRM

### 1. Modules Créés
- `crm_integration.py` - Logique d'intégration CRM
- `agriweb_crm_bridge.py` - Pont entre AgriWeb et CRM
- `agriweb_crm_routes.py` - Routes web pour le CRM
- `agriweb_crm_standalone.py` - Application CRM complète

### 2. Comment Tester l'Intégration

#### Option A: Application CRM Séparée (ACTUELLE)
```bash
# Terminal 1: Application AgriWeb principale
python run_app.py

# Terminal 2: Application CRM
python agriweb_crm_standalone.py
```
- AgriWeb: http://localhost:5000
- CRM: http://localhost:5000 (changer le port en 5001)

#### Option B: Intégration Complète (RECOMMANDÉE)
1. Modifier votre application principale pour inclure le CRM
2. Ajouter des boutons dans l'interface de recherche
3. Intégration automatique des résultats

### 3. Fonctionnement de l'Intégration

#### Quand vous effectuez une recherche AgriWeb:
1. **Extraction automatique** des prospects depuis:
   - Données SIRENE (entreprises)
   - Bâtiments commerciaux/agricoles
   - Parcelles RPG importantes
   - Zones d'activité

2. **Création de prospects** avec:
   - Nom de l'entreprise
   - Adresse complète
   - Catégorie d'activité
   - Coordonnées géographiques

3. **Assignation hiérarchique**:
   - Admin → Directeur commercial
   - Directeur → Commercial avec moins de prospects
   - Commercial → Auto-assigné

### 4. Interface Utilisateur

#### Avant intégration:
```
[Recherche AgriWeb] → [Résultats cartographiques]
```

#### Après intégration:
```
[Recherche AgriWeb] → [Résultats + Widget CRM]
                   → [Bouton "Créer Prospects"]
                   → [Dashboard CRM intégré]
```

### 5. Workflow Commercial

1. **Recherche géographique** (existant)
2. **Détection automatique** d'entreprises potentielles
3. **Création prospects CRM** en un clic
4. **Suivi commercial** dans le dashboard
5. **Reporting** par équipe

### 6. Prochaines Étapes

1. **Tester** l'application CRM standalone
2. **Modifier** votre interface de recherche
3. **Ajouter** les boutons d'intégration
4. **Former** les utilisateurs

### 7. Comptes de Test CRM
- Admin: admin@agriweb.com / admin123
- Directeur: directeur@agriweb.com / director123
- Commercial: commercial@agriweb.com / commercial123

### 8. Support
En cas de problème:
1. Vérifier que les modules CRM sont importés
2. Contrôler la base de données SQLite
3. Vérifier les logs d'erreur
"""
    
    with open('INTEGRATION_CRM_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("📋 Guide créé: INTEGRATION_CRM_GUIDE.md")

if __name__ == "__main__":
    from datetime import datetime
    
    print("🚀 Script d'Intégration CRM AgriWeb")
    print("=" * 50)
    
    # Créer le guide
    create_crm_integration_guide()
    
    # Option d'intégration automatique
    choice = input("\n🤔 Voulez-vous intégrer automatiquement le CRM dans votre application ? (y/N): ")
    
    if choice.lower() in ['y', 'yes', 'oui']:
        success = integrate_crm_into_agriweb()
        if success:
            print("\n🎉 Intégration terminée !")
            print("📍 Redémarrez votre application avec: python run_app.py")
            print("🔗 Nouvelles routes disponibles:")
            print("   • /crm/login - Connexion CRM")
            print("   • /crm/dashboard - Dashboard CRM")
            print("   • /api/crm/integrate_search - API d'intégration")
        else:
            print("\n❌ Intégration échouée")
    else:
        print("\n📋 Intégration manuelle:")
        print("1. Utilisez les modules CRM créés")
        print("2. Ajoutez les routes dans votre application")
        print("3. Modifiez l'interface de recherche")
        print("4. Consultez le guide: INTEGRATION_CRM_GUIDE.md")
    
    print("\n✅ Pour tester immédiatement:")
    print("   python agriweb_crm_standalone.py")
    print("   → http://localhost:5000")