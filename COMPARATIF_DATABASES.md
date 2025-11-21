# 🔍 COMPARATIF BASE DE DONNÉES LOCAL vs RAILWAY

**Date d'analyse**: 21 novembre 2025

---

## 📊 BASE DE DONNÉES LOCALE (SQLite)

### Emplacement
```
c:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\KPI\kpi_sunstice.db
```

### 📁 Tables (9)
1. ✅ `agriweb_prospects` - **61 prospects**
2. ✅ `contacts_energaia`
3. ✅ `prospect_actions`
4. ✅ `prospect_appointments`
5. ✅ `prospect_proposals`
6. ✅ `project_fiches`
7. ✅ `project_steps`
8. ✅ `project_documents`
9. `sqlite_sequence` (auto-incrémentation)

### 🎯 Table `agriweb_prospects` (Détails)

**Total**: 61 prospects

**Répartition par type**:
- Parkings: 56
- Toitures: 5

**Répartition par statut**:
- Nouveau: 59
- Qualifié: 2

**Structure**: 35 colonnes
- ✅ `contact_telephone` (TEXT) - **Nom correct**
- ✅ `contact_nom` (TEXT)
- ✅ `contact_email` (TEXT)
- ✅ `dirigeant_nom`, `dirigeant_email`, `dirigeant_tel`
- ✅ `nom_prospect`, `siret`, `siren`
- ✅ Données géographiques (lat, lon, commune, etc.)
- ✅ Données métier (surface, postes électriques, etc.)

**Qualité des données** (analyse échantillon):
- 1 prospect sur 5 premiers a un téléphone renseigné (ID 3: `0621165585`)
- 1 prospect sur 5 premiers a un contact_nom renseigné (ID 3: `test`)
- Beaucoup de champs NULL (données à enrichir)

---

## 🚀 BASE DE DONNÉES RAILWAY (PostgreSQL)

### État actuel
⚠️ **Non accessible en local** - Nécessite connexion Railway

### Pour analyser Railway:

**Option 1: Via Railway Shell**
```bash
# Sur railway.app
railway shell
python check_railway_db.py
```

**Option 2: Via variable d'environnement locale**
```powershell
# Récupérer DATABASE_URL depuis Railway Dashboard
$env:DATABASE_URL = "postgresql://..."
python compare_databases.py
```

**Option 3: Via Railway CLI**
```bash
railway run python compare_databases.py
```

---

## 🔄 MIGRATION PRÉVUE

### Script de migration disponible
`migrate_data.py` - Migre les 61 prospects depuis SQLite → PostgreSQL

### Tables à créer sur Railway
✅ Déjà définies dans `database_adapter.py`:
1. `agriweb_prospects` (35 colonnes PostgreSQL)
2. `project_fiches` (22 colonnes)
3. `project_etapes` (avec CASCADE DELETE)
4. `project_documents` (avec CASCADE DELETE)

### Différences SQLite → PostgreSQL
- ✅ `INTEGER PRIMARY KEY` → `SERIAL PRIMARY KEY`
- ✅ `TIMESTAMP` → `TIMESTAMP` (compatible)
- ✅ `REAL` → `REAL` (compatible)
- ✅ `TEXT` → `TEXT` (compatible)
- ✅ Ajout `ON DELETE CASCADE` pour intégrité référentielle

---

## 🐛 CORRECTIF APPLIQUÉ

### Problème identifié
Le champ `contact_telephone` (BDD) n'était pas mappé vers `contact_tel` (Frontend)

### Solution
✅ Mapping automatique dans `crm_routes.py` ligne 220:
```python
# Mapper contact_telephone -> contact_tel pour compatibilité frontend
if prospects:
    for prospect in prospects:
        if 'contact_telephone' in prospect:
            prospect['contact_tel'] = prospect['contact_telephone']
```

✅ Mapping aussi appliqué dans `agriweb_hebergement_gratuit.py` (version locale)

---

## 📋 ACTIONS RECOMMANDÉES

### 1️⃣ Analyser la base Railway
```bash
# Depuis Railway Dashboard → Shell
python check_railway_db.py
```

### 2️⃣ Comparer les données
- Vérifier le nombre de prospects sur Railway
- Comparer avec les 61 prospects locaux
- Identifier les différences

### 3️⃣ Migration si nécessaire
Si Railway est vide ou incomplet:
```bash
railway run python migrate_data.py
```

### 4️⃣ Tester le correctif téléphone
- Éditer un prospect sur Railway
- Saisir un téléphone
- Vérifier qu'il s'enregistre correctement
- Vérifier qu'il s'affiche au rechargement

---

## 🔧 STRUCTURE DES DONNÉES

### Champs critiques à vérifier
- ✅ `contact_telephone` - Mapping OK
- ⚠️ `contact_nom` - À vérifier sur Railway
- ⚠️ `contact_email` - À vérifier sur Railway
- ⚠️ `dirigeant_*` - À vérifier sur Railway
- ⚠️ `nom_prospect` - À vérifier sur Railway

### Intégrité référentielle
```
agriweb_prospects (parent)
    ↓
project_fiches (enfant - prospect_id)
    ↓
project_etapes (petit-enfant - project_id ON DELETE CASCADE)
project_documents (petit-enfant - project_id ON DELETE CASCADE)
```

---

## 📊 RÉSUMÉ

| Critère | Local (SQLite) | Railway (PostgreSQL) |
|---------|----------------|----------------------|
| **Prospects** | 61 | ❓ À vérifier |
| **Tables CRM** | 8 | ❓ À vérifier |
| **Colonnes agriweb_prospects** | 35 | 41 (avec colonnes manquantes ajoutées) |
| **Statut** | ✅ Opérationnel | ⚠️ À vérifier |
| **Mapping téléphone** | ✅ Corrigé | ✅ Corrigé |

---

## 🎯 PROCHAINES ÉTAPES

1. Exécuter `check_railway_db.py` sur Railway Shell
2. Comparer les résultats avec cette analyse locale
3. Migrer si nécessaire (61 prospects + projets associés)
4. Tester le CRUD complet (Create, Read, Update, Delete)
5. Vérifier que tous les champs s'enregistrent correctement
