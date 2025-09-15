# 📋 AgriWeb CRM - Guide Utilisateur Complet

## 🚀 Système Commercial Hiérarchique pour AgriWeb

### 📖 Vue d'ensemble

AgriWeb CRM est un système de gestion commerciale conçu spécifiquement pour la commercialisation du logiciel AgriWeb auprès d'entreprises agricoles, industrielles et commerciales. Il intègre une gestion hiérarchique des utilisateurs avec création automatique de prospects depuis les recherches géographiques.

### 🏗️ Architecture du Système

#### 1. **Hiérarchie des Utilisateurs**
```
👑 Administrateur (admin)
    ├── 👔 Directeur Commercial (directeur_commercial)
    │   ├── 💼 Commercial 1 (commercial)
    │   ├── 💼 Commercial 2 (commercial)
    │   └── 💼 Commercial N (commercial)
    └── 👔 Directeur Commercial 2
        └── ...
```

#### 2. **Flux de Données**
```
🗺️ Recherche Géographique → 🔄 Extraction → 👥 Prospect → 📊 Assignation → 💼 Suivi
```

### 🔐 Connexion et Comptes

#### Comptes de Démonstration
- **Administrateur**: `admin@agriweb.com` / `admin123`
- **Directeur Commercial**: `directeur@agriweb.com` / `director123`  
- **Commercial**: `commercial@agriweb.com` / `commercial123`

#### Rôles et Permissions

| Rôle | Permissions |
|------|-------------|
| **Admin** | • Accès complet à tous les prospects<br>• Gestion des utilisateurs<br>• Configuration système<br>• Statistiques globales |
| **Directeur Commercial** | • Gestion de son équipe<br>• Prospects de son équipe<br>• Assignation des prospects<br>• Rapports d'équipe |
| **Commercial** | • Ses prospects assignés uniquement<br>• Création de prospects<br>• Suivi des interactions<br>• Recherches sauvegardées |

### 📊 Interface Principal - Dashboard CRM

#### 1. **Tableau de Bord**
```
📈 Statistiques Temps Réel
├── Total Prospects: [Nombre total selon permissions]
├── Nouveaux: [Prospects status "nouveau"]
├── Qualifiés: [Prospects status "qualifié"]
└── Auto-générés: [Prospects créés automatiquement]
```

#### 2. **Gestion des Prospects**

##### États des Prospects
- 🆕 **Nouveau**: Prospect juste créé, non contacté
- ✅ **Qualifié**: Prospect contacté et intéressé
- 💬 **Négociation**: En cours de négociation commerciale
- 🎉 **Gagné**: Vente conclue
- ❌ **Perdu**: Prospect non converti

##### Priorités
- 🔴 **Haute**: Prospect à traiter en urgence
- 🟡 **Normale**: Traitement standard
- 🟢 **Basse**: Suivi à long terme

##### Sources des Prospects
- 🗺️ **recherche_automatique**: Créé depuis la carte
- ✋ **manuel**: Créé manuellement
- 📞 **appel_entrant**: Contact entrant
- 🌐 **web**: Depuis le site web

### 🗺️ Intégration Carte Interactive

#### 1. **Fonctionnement de l'Intégration**

1. **Recherche Géographique**
   - Clic sur la carte pour simuler une recherche
   - Données GeoJSON avec propriétés des entreprises
   - Affichage des marqueurs sur la carte

2. **Extraction Automatique**
   - Nom de l'entreprise (depuis `name`, `operator`, `brand`)
   - Adresse complète (rue, ville, code postal)
   - Catégorie métier (agriculture, industrie, commercial)
   - Coordonnées géographiques

3. **Création de Prospects**
   - Génération automatique des fiches prospects
   - Assignation selon la hiérarchie
   - Sauvegarde de la recherche

#### 2. **Interface Carte - Fonctionnalités**

```html
🗺️ Carte Interactive
├── 📍 Marqueurs des résultats
├── ⚡ Bouton "Créer Prospects"
├── 📝 Nom de recherche personnalisé
└── ☑️ Intégration automatique
```

### 🔄 Système d'Assignation Automatique

#### Logique d'Assignation
```python
# Pour un Admin
Prospect → Assigné au Directeur Commercial principal

# Pour un Directeur Commercial  
Prospect → Assigné au Commercial avec le moins de prospects

# Pour un Commercial
Prospect → Auto-assigné à lui-même
```

#### Équilibrage de Charge
Le système distribue automatiquement les prospects pour éviter la surcharge d'un commercial.

### 💾 Base de Données

#### Structure Principale
```sql
-- Utilisateurs avec hiérarchie
users (id, username, email, role, manager_id, ...)

-- Prospects avec assignation
prospects (id, company_name, assigned_to_id, source, status, ...)

-- Recherches sauvegardées
saved_searches (id, name, search_params, auto_prospect, ...)

-- Interactions commerciales
prospect_interactions (id, prospect_id, user_id, type, ...)
```

### 🔧 Configuration et Installation

#### 1. **Prérequis**
- Python 3.8+
- Flask
- SQLite3

#### 2. **Installation**
```bash
# Cloner le projet
cd AgW3b

# Installer les dépendances
pip install flask flask-sqlalchemy werkzeug

# Lancer l'application
python agriweb_crm_standalone.py
```

#### 3. **Accès**
- URL: `http://localhost:5000`
- Interface: Bootstrap 5 responsive
- Base de données: SQLite automatique

### 📱 Utilisation Mobile

L'interface est entièrement responsive et optimisée pour:
- 📱 Smartphones (iOS/Android)
- 💻 Tablettes 
- 🖥️ Ordinateurs de bureau

### 🔍 API et Intégration

#### Endpoints Principaux
```http
GET  /api/prospects              # Liste des prospects
POST /api/prospects              # Créer un prospect
POST /api/integrate_search       # Intégrer recherche
GET  /api/team                   # Équipe de l'utilisateur
```

#### Exemple d'Intégration
```javascript
// Créer des prospects depuis JavaScript
fetch('/api/integrate_search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        search_results: geoJsonResults,
        search_name: "Ma Recherche"
    })
})
```

### 📈 Workflow Commercial Type

#### 1. **Prospection Automatique**
```
🗺️ Recherche zone géographique 
→ 🔄 Création automatique prospects
→ 📋 Assignation équipe
→ 📞 Prise de contact
```

#### 2. **Suivi Commercial**
```
🆕 Nouveau prospect
→ ☎️ Premier contact
→ ✅ Qualification
→ 💬 Négociation
→ 🎉 Signature contrat
```

### 🚨 Dépannage

#### Problèmes Fréquents

1. **Base de données corrompue**
   ```bash
   # Supprimer et recréer
   rm agriweb_crm.db
   python agriweb_crm_standalone.py
   ```

2. **Erreur de connexion**
   - Vérifier username/password
   - Vérifier que l'utilisateur existe
   - Consulter les logs Flask

3. **Prospects non créés**
   - Vérifier format GeoJSON
   - Vérifier permissions utilisateur
   - Consulter les erreurs API

### 📞 Support et Contact

Pour toute question ou problème:
- 📧 Email: support@agriweb.com
- 📱 Tél: +33 1 23 45 67 89
- 🌐 Site: www.agriweb.com

### 🔄 Mises à Jour

#### Version Actuelle: 1.0.0
- ✅ Gestion hiérarchique complète
- ✅ Intégration carte automatique
- ✅ Interface responsive
- ✅ API REST complète

#### Prochaines Fonctionnalités
- 📧 Notifications email automatiques
- 📊 Rapports Excel exportables  
- 🔗 Intégration CRM externes
- 📱 Application mobile native

---

**© 2024 AgriWeb CRM - Système Commercial Hiérarchique**

*Documentation mise à jour le: {{date}}*