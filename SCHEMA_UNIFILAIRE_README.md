# 📐 Schéma Unifilaire NF C 15-712 - AgriWeb Pro

## 🎯 Vue d'ensemble

Module de génération automatique de **schémas unifilaires conformes à la norme NF C 15-712-1** (Installations photovoltaïques raccordées au réseau) à partir des données de calepinage AgriWeb.

## ✨ Fonctionnalités

### **Génération automatique depuis le calepinage**
- Analyse des zones PV dessinées
- Calcul optimal de la configuration électrique
- Sélection intelligente de l'onduleur
- Dimensionnement des câbles et protections
- Export PDF professionnel 2 pages

### **Calculs électriques conformes**
- **Configuration strings** : Optimisation tension/courant selon onduleur
- **Dimensionnement câbles** : Sections DC/AC avec chutes de tension < 3%
- **Protections** : Sectionneurs, parafoudres, différentiels, fusibles
- **Vérifications** : Conformité complète NF C 15-712 + NF C 15-100

### **Base de données onduleurs**
Onduleurs pré-configurés avec caractéristiques techniques :
- **Huawei** : SUN2000 (3kW à 20kW) - Leader France
- **Fronius** : Primo/Symo (3kW à 10kW) - Premium Autriche
- **SMA** : Sunny Boy/Tripower (3kW à 10kW) - Leader Allemagne
- **Enphase** : Micro-onduleurs IQ8+

Sélection automatique selon :
- Puissance DC totale
- Ratio DC/AC optimal (1.2-1.3)
- Plages de tension MPPT

## 📋 Structure du PDF généré

### **Page 1 : Schéma unifilaire**
```
┌─────────────────┐       ┌──────────────┐       ┌───────────┐       ┌─────────┐
│ CHAMP PV (DC)   │  ───> │ BOÎTE DC     │  ───> │ ONDULEUR  │  ───> │ RÉSEAU  │
│ Zones + Strings │       │ Protections  │       │ DC → AC   │       │ AC      │
└─────────────────┘       └──────────────┘       └───────────┘       └─────────┘
```

**Éléments affichés :**
- Zones PV avec orientation/inclinaison
- Strings (configuration modules série/parallèle)
- Câblage DC avec sections (mm²)
- Boîte de jonction DC (sectionneurs, parafoudres, fusibles)
- Onduleur (marque, modèle, puissances)
- Câblage AC avec sections
- Protections AC (disjoncteur, différentiel, parafoudre)
- Cartouche normalisé (projet, adresse, puissance, date)

### **Page 2 : Notes de calculs**

**Tableaux détaillés :**

1. **Configuration électrique**
   - Puissance totale, nombre modules/strings
   - Caractéristiques onduleur
   - Ratio DC/AC

2. **Dimensionnement câbles**
   - Sections calculées (strings DC, principal DC, AC)
   - Courants max, chutes de tension
   - Références normes

3. **Protections électriques**
   - Sectionneurs, parafoudres, fusibles
   - Disjoncteurs, différentiels
   - Mise à la terre

4. **Vérifications conformité**
   - ✅ Checklist complète NF C 15-712
   - ✅ Validation automatique

## 🔧 Utilisation

### **Dans l'interface AgriWeb**

1. Ouvrir un prospect dans le CRM
2. Créer le calepinage (dessiner zones PV)
3. Configurer modules et orientation
4. Cliquer sur **"⚡ Schéma unifilaire NF C 15-712"**
5. Le PDF se télécharge automatiquement

### **Via API**

```python
GET /api/crm/prospects/<prospect_id>/schema-unifilaire
```

**Prérequis :** Calepinage sauvegardé avec au moins 1 zone PV

**Réponse :** PDF téléchargeable (`schema_unifilaire_<prospect>_<date>.pdf`)

### **Programmation (Python)**

```python
from schema_unifilaire import SchemaUnifilaire

# Données calepinage
calpinage_data = {
    'module': {
        'puissance': 550,      # Wc
        'voc': 49.5,           # V (circuit ouvert)
        'vmpp': 41.8,          # V (MPP)
        'isc': 13.9,           # A (court-circuit)
        'impp': 13.2,          # A (MPP)
        'longueur': 2278,      # mm
        'largeur': 1134        # mm
    },
    'zones': [
        {
            'numero': 1,
            'nbModules': 24,
            'orientation': 180,  # Sud
            'inclinaison': 30,   # °
            'puissanceKw': 13.2,
            'surfaceM2': 61.8
        }
    ]
}

# Données prospect
prospect_data = {
    'nom': 'MARTIN',
    'prenom': 'Jean',
    'adresse': '15 Rue de la République, 44000 Nantes'
}

# Générer le schéma
schema = SchemaUnifilaire(calpinage_data, prospect_data)
pdf_path = schema.generer_schema_pdf('schema_unifilaire.pdf')

# Accès aux calculs
print(f"Onduleur: {schema.onduleur['marque']} {schema.onduleur['modele']}")
print(f"Strings: {len(schema.configuration_strings)}")
print(f"Section DC: {schema.section_cable_dc}mm²")
print(f"Section AC: {schema.section_cable_ac}mm²")
```

## 📊 Calculs automatiques

### **1. Configuration strings**

```python
# Contraintes MPPT onduleur
V_min_onduleur ≤ V_mpp_string ≤ V_max_onduleur
V_oc_string < V_max_onduleur (facteur température -10°C)

# Optimisation
nb_modules_série = Optimal(V_mpp, plage MPPT)
nb_strings_parallèle = Total_modules / nb_modules_série
```

### **2. Sections câbles**

**NF C 15-712 article 7.12.1.1 : Chute tension ≤ 3%**

```python
# Câbles DC
S_dc = (2 × ρ_Cu × L × I_max) / (0.03 × V_mpp)
I_max = I_sc_total × 1.25  # Facteur sécurité

# Câbles AC
S_ac = (k × ρ_Cu × L × I_max) / (0.03 × V_réseau)
k = 2 (monophasé) ou √3 (triphasé)
```

**Vérification courant admissible (NF C 15-100)**

### **3. Protections**

**Sectionneurs DC :**
```python
Calibre = 1.25 × I_sc_total
Tension nominale > V_oc_max × 1.25 (température)
```

**Disjoncteurs AC :**
```python
Calibre = 1.45 × I_nominale_onduleur
Courbe C ou D selon onduleur
```

**Différentiels AC :**
- Type A (minimum) : Onduleurs standard
- Type B : Onduleurs + batteries
- Sensibilité : 30mA

**Parafoudres :**
- DC : Type 2, tension > V_oc_max
- AC : Type 2, 275V AC, 20kA

## 🎯 Conformité normative

### **Normes appliquées**

- ✅ **NF C 15-712-1** : Installations photovoltaïques raccordées au réseau
- ✅ **NF C 15-100** : Installations électriques basse tension
- ✅ **UTE C 15-712-1** : Guide pratique photovoltaïque

### **Articles clés**

| Article | Description | Implémentation |
|---------|-------------|----------------|
| 7.12.1.1 | Chutes de tension DC/AC < 3% | ✅ Calcul automatique |
| 7.12.3.1 | Sectionneurs DC coupure visible | ✅ Dimensionnement |
| 7.12.3.4 | Parafoudres DC/AC obligatoires | ✅ Type 2 minimum |
| 7.13 | Mise à la terre < 100Ω | ✅ Spécifié |
| 7.2.1 | Configuration strings compatible onduleur | ✅ Vérification MPPT |

## 🛠️ Architecture technique

### **Fichiers**

```
AgW3b/
├── schema_unifilaire.py          # Module principal
├── crm_routes.py                 # Route API
└── templates/
    └── calpinage_pv.html         # Bouton interface
```

### **Classe SchemaUnifilaire**

```python
class SchemaUnifilaire:
    def __init__(calpinage_data, prospect_data)
    
    # Calculs automatiques
    def _choisir_onduleur()              # Sélection onduleur optimal
    def _calculer_strings()              # Config strings par zone
    def _calculer_sections_cables()      # Sections DC/AC
    def _calculer_protections()          # Sectionneurs, parafoudres
    
    # Génération PDF
    def generer_schema_pdf(output_path)  # PDF 2 pages
    def _dessiner_cartouche()            # Cartouche normalisé
    def _dessiner_schema_principal()     # Schéma unifilaire
    def _dessiner_notes_calculs()        # Tableaux calculs
    def _dessiner_string()               # Symbole string
```

### **Dépendances**

```python
reportlab >= 4.0.0   # Génération PDF
matplotlib >= 3.7.0  # Graphiques (si extension future)
```

## 📈 Exemples de résultats

### **Installation 30kWc (54 modules 550Wc)**

**Configuration calculée :**
- Onduleur : Huawei SUN2000-20KTL-M2 (20kW AC)
- 5 strings : 2×12 modules + 2×9 modules + 1×12 modules
- Vmpp strings : 376V - 502V (dans plage MPPT 140-980V)
- Section DC : 25mm² (strings 4mm²)
- Section AC : 6mm² (triphasé 400V)
- Protections : Sectionneur 100A 1000VDC, Fusibles 25A gPV
- Ratio DC/AC : 1.49 (optimal)

### **Installation 6kWc (12 modules 550Wc)**

**Configuration calculée :**
- Onduleur : Huawei SUN2000-6KTL-M1 (6kW AC)
- 1 string : 12 modules série
- Vmpp : 501V (dans plage MPPT 140-980V)
- Section DC : 6mm²
- Section AC : 2.5mm² (monophasé 230V)
- Protections : Sectionneur 25A 1000VDC
- Ratio DC/AC : 1.10 (optimal)

## 🚀 Évolutions futures (Version 3)

### **Fonctionnalités avancées**
- [ ] Export DXF/DWG (CAO bureau d'études)
- [ ] Optimiseur de strings multi-MPPT
- [ ] Base données modules PV (API fabricants)
- [ ] Calcul pertes joules câbles
- [ ] Schéma implantation 3D
- [ ] Vérification conformité temps réel (alertes)
- [ ] Import Consuel (attestation conformité)

### **Intégration propositions commerciales**
- [ ] Schéma unifilaire dans PDF proposition
- [ ] Liste matériel électrique chiffrée
- [ ] Compatibilité batteries (Type B différentiel)

## 📝 Notes importantes

### **Valeurs par défaut modules**

Si données module non fournies, valeurs typiques 550Wc :
```python
voc = 49.5V
vmpp = 41.8V
isc = 13.9A
impp = 13.2A
longueur = 2278mm
largeur = 1134mm
```

### **Limitations**

⚠️ **Ce schéma est généré automatiquement**
- Les calculs sont conformes aux normes en vigueur
- **Doit être vérifié par un professionnel qualifié** avant mise en œuvre
- Longueurs câbles estimées (25m DC, 15m AC) → **mesure sur site requise**
- Choix matériel doit tenir compte contraintes locales (température, altitude, corrosion)

### **Responsabilité**

Ce module est un **outil d'aide à la conception**. L'installateur reste responsable de :
- La conformité finale de l'installation
- L'adaptation aux contraintes du site
- La vérification des calculs
- Le respect des DTU et normes locales

## 📞 Support

Pour toute question technique :
- 📧 Email : ylaurent.perso@gmail.com
- 🌐 Plateforme : AgriWeb Pro
- 📚 Documentation : NF C 15-712-1 (AFNOR)

---

**AgriWeb Pro** - Plateforme géospatiale photovoltaïque professionnelle
Version 2.0 - Décembre 2025
