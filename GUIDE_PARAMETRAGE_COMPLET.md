# 📋 Guide Complet - Système de Paramétrage AgriWeb

## ✅ Fonctionnalités Implémentées

### 1. Interface de Paramétrage
Accessible via : **`/api/crm/parametrage`**

#### 📍 Onglet 1 : Entreprise
- **Logo entreprise** : Upload avec prévisualisation (max 5 MB, formats PNG/JPG/SVG)
- **Informations société** : Nom, adresse complète, téléphone, email, site web
- **Identifiants légaux** : SIRET, RCS
- **Certifications** : 
  - RGE : numéro + dates validité
  - Qualibat : numéro + dates validité
- **Sauvegarde automatique** dans `parametrage_entreprise`

#### 💶 Onglet 2 : Prix des Organes
- **Table dynamique** avec filtres par catégorie
- **Catégories disponibles** :
  - Modules photovoltaïques (€/Wc)
  - Onduleurs (€/kW)
  - Structures de fixation (€/kW ou €/m²)
  - Câbles (€/ml)
  - Protections électriques (€/unité)

- **Champs par organe** :
  - Nom de l'organe
  - Marque / Modèle
  - Prix unitaire HT
  - Unité (€/Wc, €/kW, €/m², etc.)
  - Marge commerciale (%)
  - Puissance (Wc ou kW selon catégorie)
  
- **Actions** : Ajouter / Modifier / Supprimer (soft delete)

#### 🎨 Onglet 3 : Graphique & Design
- **3 couleurs personnalisables** :
  - Couleur primaire (sections, titres)
  - Couleur secondaire (sous-titres, accents)
  - Couleur accent (graphs, highlights)
- **Prévisualisation en direct** du rendu PDF

---

## 🗄️ Structure Base de Données

### Table `parametrage_entreprise`
```sql
CREATE TABLE parametrage_entreprise (
    id SERIAL PRIMARY KEY,
    nom_entreprise VARCHAR(255),
    adresse_ligne1 VARCHAR(255),
    adresse_ligne2 VARCHAR(255),
    code_postal VARCHAR(10),
    ville VARCHAR(100),
    telephone VARCHAR(20),
    email VARCHAR(255),
    site_web VARCHAR(255),
    siret VARCHAR(14),
    rcs VARCHAR(100),
    numero_rge VARCHAR(50),
    date_debut_rge DATE,
    date_fin_rge DATE,
    numero_qualibat VARCHAR(50),
    date_debut_qualibat DATE,
    date_fin_qualibat DATE,
    logo_base64 TEXT,
    couleur_primaire VARCHAR(7) DEFAULT '#003d7a',
    couleur_secondaire VARCHAR(7) DEFAULT '#0066cc',
    couleur_accent VARCHAR(7) DEFAULT '#4caf50',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Table `parametrage_prix_organes`
```sql
CREATE TABLE parametrage_prix_organes (
    id SERIAL PRIMARY KEY,
    nom_organe VARCHAR(255) NOT NULL,
    categorie VARCHAR(50) NOT NULL,
    marque VARCHAR(100),
    modele VARCHAR(100),
    prix_unitaire_ht DECIMAL(10,2) NOT NULL,
    unite VARCHAR(20) NOT NULL,
    marge_commerciale_pct DECIMAL(5,2) DEFAULT 20.00,
    puissance_wc INTEGER,
    puissance_kw DECIMAL(10,2),
    description TEXT,
    actif BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(nom_organe, categorie, marque, modele)
);
```

### Table `parametrage_main_oeuvre`
```sql
CREATE TABLE parametrage_main_oeuvre (
    id SERIAL PRIMARY KEY,
    type_prestation VARCHAR(100) NOT NULL,
    tarif_horaire_ht DECIMAL(10,2) NOT NULL,
    nb_heures_unitaire DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 Intégration dans Générateur PDF

### Fichier : `proposition_professionnelle.py`

#### Méthodes de Chargement BDD
```python
def _charger_parametrage_entreprise(self):
    """Charge les infos entreprise depuis BDD avec fallback"""
    query = "SELECT * FROM parametrage_entreprise ORDER BY id DESC LIMIT 1"
    result = execute_query(query, fetch_one=True)
    
    if result:
        self.entreprise = {
            'nom_entreprise': result.get('nom_entreprise'),
            'logo_base64': result.get('logo_base64'),
            'couleur_primaire': result.get('couleur_primaire', '#003d7a'),
            # ... tous les champs
        }
    else:
        # Valeurs par défaut si BDD vide
        self.entreprise = {
            'nom_entreprise': 'AgriWeb Photovoltaïque',
            # ...
        }

def _charger_prix_organes(self):
    """Charge les prix depuis parametrage_prix_organes"""
    query = """
        SELECT * FROM parametrage_prix_organes 
        WHERE actif = TRUE
        ORDER BY categorie, marque, modele
    """
    results = execute_query(query, fetch_all=True)
    
    for row in results:
        key = f"{row['categorie']}_{row['marque']}_{row.get('puissance_wc', '')}_"
        key = key.lower().replace(' ', '_')
        self.prix_organes[key] = row
```

#### Utilisation dans PDF

##### 1. Logo sur Page de Couverture
```python
def _page_couverture(self):
    if self.entreprise.get('logo_base64'):
        logo_data = self.entreprise['logo_base64'].split(',')[1]
        logo_bytes = base64.b64decode(logo_data)
        logo_buffer = BytesIO(logo_bytes)
        logo_img = RLImage(
            ImageReader(logo_buffer), 
            width=8*cm, 
            height=3*cm, 
            kind='proportional'
        )
```

##### 2. Couleurs Personnalisées
```python
def _create_custom_styles(self):
    primary = HexColor(self.entreprise.get('couleur_primaire', '#003d7a'))
    secondary = HexColor(self.entreprise.get('couleur_secondaire', '#0066cc'))
    
    self.styles.add(ParagraphStyle(
        'TitrePrincipal',
        textColor=primary,
        # ...
    ))
```

##### 3. Prix Dynamiques dans Devis
```python
def _devis_detaille(self):
    # Chercher prix module dans BDD
    prix_module_data = None
    for key, val in self.prix_organes.items():
        if 'module' in key:
            prix_module_data = val
            break
    
    if prix_module_data and prix_module_data.get('unite') == '€/Wc':
        prix_module_unit = prix_module_data['prix_unitaire_ht'] * self.module_puissance
        cout_modules = nb_modules_total * prix_module_unit
    else:
        # Fallback si BDD vide
        prix_module_unit = (investissement_total * 0.30) / nb_modules_total
```

##### 4. Étude Financière
```python
def _etude_financiere(self):
    # Modules
    if prix_module_data and prix_module_data.get('unite') == '€/Wc':
        prix_modules_total = prix_module_data['prix_unitaire_ht'] * (puissance * 1000)
        prix_unitaire_module_kwc = prix_module_data['prix_unitaire_ht'] * 1000
    else:
        prix_modules_total = investissement_ht * 0.30
        prix_unitaire_module_kwc = 250
```

---

## 📝 Routes API Disponibles

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/crm/parametrage` | Affiche l'interface de paramétrage |
| GET | `/api/crm/parametrage/check-init` | Vérifie si les tables existent |
| POST | `/api/crm/parametrage/init-database` | Initialise les tables SQL |
| GET | `/api/crm/parametrage/entreprise` | Récupère les infos entreprise |
| POST | `/api/crm/parametrage/entreprise` | Sauvegarde les infos entreprise |
| GET | `/api/crm/parametrage/prix` | Liste tous les prix (avec filtres) |
| POST | `/api/crm/parametrage/prix` | Ajoute un nouveau prix |
| DELETE | `/api/crm/parametrage/prix/<id>` | Supprime un prix (soft delete) |
| GET | `/api/crm/parametrage/graphique` | Récupère les couleurs |
| POST | `/api/crm/parametrage/graphique` | Sauvegarde les couleurs |

---

## 🛠️ Workflow d'Utilisation

### Première Utilisation (Initialisation)

1. **Accéder à l'interface** : Aller sur `/api/crm/parametrage`
2. **Initialiser la BDD** : Cliquer sur "Initialiser la base de données" (bouton bleu)
   - Crée automatiquement les 3 tables
   - Insère les données par défaut :
     - Entreprise : AgriWeb Photovoltaïque
     - Modules : JA Solar 550W/600W, Longi 665W
     - Onduleurs : Huawei 25/50/100 kW, SMA
     - Structure, câbles, protections

3. **Configurer l'entreprise** (Onglet 1)
   - Uploader votre logo
   - Remplir vos coordonnées
   - Ajouter vos certifications RGE/Qualibat

4. **Adapter les prix** (Onglet 2)
   - Modifier les prix par défaut selon vos tarifs fournisseurs
   - Ajouter vos propres organes
   - Ajuster les marges commerciales

5. **Personnaliser les couleurs** (Onglet 3)
   - Choisir vos couleurs corporate
   - Prévisualiser le rendu PDF

### Utilisation Quotidienne

1. **Générer une proposition** :
   - Les données sont automatiquement chargées depuis BDD
   - Logo affiché sur couverture
   - Couleurs appliquées à tous les styles
   - Prix calculés dynamiquement

2. **Mettre à jour les prix** :
   - Onglet "Prix des Organes"
   - Modifier le prix unitaire HT
   - La prochaine proposition utilisera le nouveau prix

3. **Changer le logo** :
   - Onglet "Entreprise"
   - Uploader nouveau fichier
   - Sauvegarde automatique en base64

---

## 🔍 Fonctionnement Technique

### Fallback Automatique
Si les tables BDD n'existent pas ou sont vides :
- ✅ **Logo** : Affiche nom entreprise en texte si pas de logo
- ✅ **Couleurs** : Utilise couleurs par défaut (#003d7a, #0066cc, #4caf50)
- ✅ **Prix** : Calcule proportionnellement au prix total (30% modules, 18% onduleurs, etc.)

### Clés de Lookup Prix
Format : `categorie_marque_puissance_`
Exemples :
- `module_jasolar_550_` → JA Solar 550W
- `onduleur_huawei_50_` → Huawei 50 kW
- `structure_aluminium__` → Structure aluminium

### Unités Supportées
- **€/Wc** : Modules (prix × puissance_wc)
- **€/kW** : Onduleurs (prix × puissance_kw)
- **€/m²** : Structures (prix × surface)
- **€/ml** : Câbles (prix × longueur)
- **€/unité** : Protections, coffrets

---

## 📊 Données par Défaut Insérées

### Modules
| Marque | Modèle | Puissance | Prix €/Wc | Marge |
|--------|--------|-----------|-----------|-------|
| JA Solar | JAM72S30 | 550 Wc | 0.32 | 25% |
| JA Solar | JAM72S30 | 600 Wc | 0.30 | 25% |
| Longi Solar | Hi-MO 5 | 665 Wc | 0.28 | 25% |

### Onduleurs
| Marque | Modèle | Puissance | Prix €/kW | Marge |
|--------|--------|-----------|-----------|-------|
| Huawei | SUN2000-25KTL | 25 kW | 90 | 20% |
| Huawei | SUN2000-50KTL | 50 kW | 85 | 20% |
| Huawei | SUN2000-100KTL | 100 kW | 80 | 20% |
| SMA | Sunny Tripower | 50 kW | 95 | 20% |

### Autres Composants
| Catégorie | Prix | Unité |
|-----------|------|-------|
| Structure aluminium | 45 | €/kW |
| Câbles DC 6mm² | 3.50 | €/ml |
| Protections AC/DC | 850 | €/unité |

---

## 🐛 Dépannage

### Les tables n'existent pas
**Symptôme** : Message "La base de données n'a pas encore été initialisée"  
**Solution** : Cliquer sur "Initialiser la base de données"

### Le logo ne s'affiche pas
**Symptôme** : Nom entreprise en texte au lieu du logo  
**Vérifications** :
- Fichier < 5 MB
- Format PNG, JPG ou SVG
- Upload terminé (barre 100%)
- Cliquer "Sauvegarder les modifications"

### Les prix sont incorrects
**Symptôme** : PDF affiche prix par défaut au lieu des prix BDD  
**Vérifications** :
- Prix enregistrés dans onglet "Prix"
- Champ `actif` = TRUE
- Unité correcte (€/Wc, €/kW, etc.)
- Catégorie bien orthographiée (module, onduleur, structure, cable, protection)

### Les couleurs ne changent pas
**Symptôme** : PDF garde les couleurs bleues par défaut  
**Vérifications** :
- Couleurs sauvegardées dans onglet "Graphique"
- Format hexadécimal valide (#RRGGBB)
- Régénérer le PDF après modification

---

## 📈 Améliorations Futures Possibles

- [ ] Ajout main d'œuvre dans paramétrage (tarifs horaires)
- [ ] Gestion multi-entreprises (agences)
- [ ] Historique des modifications de prix
- [ ] Import/Export Excel des prix
- [ ] Templates de propositions multiples
- [ ] Footer personnalisé sur toutes les pages
- [ ] Gestion des remises commerciales

---

## 📞 Support Technique

**Repository** : `github.com/ylou777/agriweb-production` (branche `main`)  
**Auto-deploy** : Railway (chaque push déclenche déploiement)  
**SQL Init File** : `create_tables_parametrage.sql` (194 lignes)  
**Interface HTML** : `templates/parametrage.html` (774 lignes)  
**PDF Generator** : `proposition_professionnelle.py` (2681 lignes)

---

*Document généré le 2025-01-XX | Version 1.0*
