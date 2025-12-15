# 🎨 Plans de Strings Détaillés - Documentation

## Vue d'ensemble

Les **Plans de Strings** sont des plans techniques détaillés générés automatiquement pour chaque zone d'installation photovoltaïque. Ces documents sont destinés aux techniciens d'installation pour visualiser précisément l'agencement des modules et le câblage DC.

## Fonctionnalités

### Format du document
- **Format**: A3 paysage (420 x 297 mm)
- **Structure**: Page de garde + une page par zone
- **Norme**: Respect des conventions de plans électriques

### Page de garde
Contient un résumé de l'installation:
- Nom du projet et adresse
- Date de génération
- Nombre total de zones
- Puissance totale installée
- Nombre total de modules
- Liste des zones avec leurs caractéristiques

### Plans par zone

Chaque zone dispose d'une page dédiée avec:

#### 1. Cartouche technique (en-tête)
- Nom du projet
- Adresse d'installation
- Nom de la zone (ex: "Zone 1 - Hangar Nord")
- Nombre de modules dans la zone
- Puissance de la zone
- Orientation et inclinaison
- Date et échelle

#### 2. Grille de modules
- **Dessin à l'échelle** de tous les modules
- **Numérotation**: Chaque module est identifié (M1, M2, M3...)
- **Couleurs par string**: Chaque string a une couleur distinctive
  - String 1: Rouge
  - String 2: Bleu  
  - String 3: Vert
  - String 4+: Rotation des couleurs
- **Dimensions**: Rectangles proportionnels aux dimensions réelles des modules

#### 3. Câblage DC
- **Flèches de connexion** entre les modules d'un même string
- **Sens du câblage**: Visualisation du cheminement des câbles DC
- **Points de connexion**: Indique clairement comment les modules sont reliés en série

#### 4. Légende des strings
Tableau récapitulatif pour chaque string:
- **Numéro du string** (S1, S2, S3...)
- **Nombre de modules** en série
- **Tension à vide (Voc)**: Tension maximale du string
- **Tension MPPT (Vmpp)**: Tension au point de puissance maximale
- **Courant de court-circuit (Isc)**: Courant maximal
- **Courant MPPT (Impp)**: Courant au point de puissance maximale

## Algorithme de calcul des strings

### Objectifs
1. **Optimisation électrique**: Maximiser la production
2. **Sécurité**: Respecter Voc max < 1000V (NF C 15-712)
3. **Compatibilité onduleur**: Respecter les plages MPPT

### Paramètres de calcul
```python
MODULES_MIN_PAR_STRING = 10  # Minimum pour limiter les pertes
MODULES_MAX_PAR_STRING = 20  # Maximum pour faciliter l'installation
TENSION_MAX_SECURITE = 1000  # Voc max selon NF C 15-712 (V)
```

### Logique
1. **Calcul Voc max autorisé** par string:
   ```
   nb_max_serie = floor(1000V / Voc_module)
   nb_serie = min(nb_max_serie, MODULES_MAX_PAR_STRING)
   nb_serie = max(nb_serie, MODULES_MIN_PAR_STRING)
   ```

2. **Répartition des modules**:
   ```
   nb_strings_complets = floor(nb_modules_zone / nb_serie)
   modules_restants = nb_modules_zone % nb_serie
   ```

3. **Gestion des modules restants**:
   - Si restants >= 50% d'un string → créer un string additionnel
   - Sinon → répartir équitablement sur les strings existants

## Utilisation

### Dans l'interface de calepinage

1. **Créer les zones** avec placement des modules
2. **Configurer les équipements** électriques (onduleurs, TGBT...)
3. **Cliquer sur "🎨 Plans de strings détaillés"**
4. **Sauvegarde automatique** du calepinage
5. **Génération du PDF** qui s'ouvre dans un nouvel onglet

### Via API REST

```http
GET /api/crm/prospects/{prospect_id}/plans-strings
```

**Prérequis**:
- Le prospect doit avoir un calepinage sauvegardé
- Au moins une zone avec des modules doit être définie
- Les informations du module doivent être complètes

**Réponse**:
- Type: `application/pdf`
- Nom du fichier: `Plans_Strings_{NomProspect}_{Date}.pdf`

## Architecture technique

### Fichier principal: `plans_strings.py`

#### Classe `PlansStrings`
```python
class PlansStrings:
    def __init__(self, zones, module_info, onduleurs, nom_projet, adresse_projet, filepath):
        """Initialise le générateur de plans"""
        
    def generer_plans_pdf(self):
        """Génère le PDF complet avec page de garde + plans par zone"""
        
    def _calculer_strings_zone(self, zone):
        """Calcule la configuration optimale des strings"""
        
    def _dessiner_champ_modules(self, zone, strings_data):
        """Dessine la grille de modules avec numérotation et couleurs"""
        
    def _dessiner_cablage_strings(self, zone, strings_data):
        """Dessine les flèches de câblage DC"""
        
    def _dessiner_legende_strings(self, strings_data):
        """Génère le tableau de légende avec caractéristiques électriques"""
```

### Intégration Flask: `crm_routes.py`

Route ajoutée:
```python
@app.route('/api/crm/prospects/<int:prospect_id>/plans-strings')
def generer_plans_strings(prospect_id):
    # 1. Récupération du prospect et calepinage
    # 2. Validation des données (zones, module, onduleurs)
    # 3. Génération du PDF avec PlansStrings
    # 4. Retour du fichier PDF
```

### Interface utilisateur: `calpinage_pv.html`

Bouton ajouté:
```html
<button class="btn btn-info btn-lg" id="genererPlansStrings">
    🎨 Plans de strings détaillés
</button>
```

Event listener JavaScript:
```javascript
btnPlansStrings.addEventListener('click', async () => {
    // 1. Validation (au moins une zone)
    // 2. Sauvegarde du calepinage
    // 3. Ouverture du PDF dans nouvel onglet
});
```

## Cas d'usage

### Exemple 1: Installation simple (1 zone)
- **36 modules** de 400Wc (Voc: 49.5V)
- **Calcul**: 49.5V × 20 = 990V < 1000V → OK
- **Résultat**: 2 strings de 18 modules

### Exemple 2: Installation multi-zones
- **Zone 1 (Hangar Nord)**: 48 modules → 3 strings de 16 modules
- **Zone 2 (Hangar Sud)**: 32 modules → 2 strings de 16 modules
- **Zone 3 (Stabulation)**: 24 modules → 2 strings de 12 modules

### Exemple 3: Modules haute tension
- **Modules bifaciaux** 550Wc (Voc: 52.8V)
- **Calcul**: 52.8V × 18 = 950.4V < 1000V → OK
- **Protection**: Évite dépassement 1000V en hiver (-10°C → Voc augmente)

## Avantages

### Pour les techniciens
✅ **Visualisation claire** du câblage avant intervention  
✅ **Numérotation précise** pour éviter erreurs de connexion  
✅ **Gain de temps** sur chantier (pas de calcul manuel)  
✅ **Traçabilité** de l'installation réalisée

### Pour le bureau d'études
✅ **Automatisation** des plans techniques  
✅ **Cohérence** entre calepinage et plans  
✅ **Documentation** professionnelle pour le DOE  
✅ **Conformité** NF C 15-712 garantie

### Pour le client
✅ **Transparence** sur l'installation  
✅ **Dossier complet** pour Consuel  
✅ **Maintenance facilitée** (repérage des strings)

## Maintenance et évolutions futures

### Améliorations possibles
- [ ] Export en DWG/DXF pour AutoCAD
- [ ] Ajout des distances de câblage
- [ ] Calcul des sections de câbles par string
- [ ] Intégration des boîtes de jonction DC
- [ ] Plans 3D avec vue en perspective
- [ ] Annotations personnalisables

### Bugs connus
Aucun bug connu à ce jour.

---

**Auteur**: AgriWeb Pro Development Team  
**Version**: 1.0.0  
**Date**: Décembre 2024  
**Commit**: 9984d57
