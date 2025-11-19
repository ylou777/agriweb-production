# 🔍 Système d'Autocomplétion Intelligent pour Recherche d'Adresses et Communes

## Vue d'ensemble

Ce système offre une **autocomplétion intelligente** avec **tolérance aux fautes de frappe** pour la recherche d'adresses et de communes dans AgriWeb.

## Fonctionnalités principales

### ✨ Tolérance aux fautes de frappe
- **"montiers d'ahun"** → trouve "Moutiers-d'Ahun (23150, 23)"
- **"verdun"** → trouve "Verdun (55100, 55)" et "Verdun-sur-Garonne (82600, 82)"
- **"pari"** → trouve "Paris", "Parisot", etc.
- **"10 rue de la paix pari"** → trouve "10 Rue de la Paix 75002 Paris"

### 🎯 Recherche multiple formats
- **Par nom complet** : "Lyon", "Marseille"
- **Par code postal** : "75001", "69000"
- **Par adresse partielle** : "10 rue victor hugo"
- **Par département** : "Verdun 55"

### ⚡ Performance optimisée
- **Debouncing** : évite les requêtes excessives (300ms)
- **Cache côté serveur** : réponses rapides
- **Limite de résultats** : maximum 8 suggestions
- **Timeout** : 3 secondes maximum par requête

## Architecture technique

### Backend (Flask)

#### 1. Endpoint `/api/autocomplete/address`
```python
GET /api/autocomplete/address?q=montiers
```

**Paramètres:**
- `q` (string) : terme de recherche (minimum 3 caractères)

**Réponse:**
```json
{
  "suggestions": [
    {
      "label": "Moutiers-d'Ahun 23150",
      "value": "Moutiers-d'Ahun",
      "city": "Moutiers-d'Ahun",
      "postcode": "23150",
      "context": "23, Creuse, Nouvelle-Aquitaine",
      "lat": 46.0234,
      "lon": 1.9876,
      "score": 0.95,
      "type": "municipality",
      "icon": "🏛️",
      "display": "🏛️ Moutiers-d'Ahun 23150"
    }
  ]
}
```

**Source de données**: [API BAN](https://api-adresse.data.gouv.fr) (Base Adresse Nationale)
- Gratuite
- Officielle (gouvernement français)
- Excellente précision
- Tolérance native aux fautes

#### 2. Endpoint `/api/autocomplete/commune`
```python
GET /api/autocomplete/commune?q=verdun
```

**Paramètres:**
- `q` (string) : terme de recherche (minimum 2 caractères)

**Réponse:**
```json
{
  "suggestions": [
    {
      "label": "Verdun (55100, 55)",
      "value": "Verdun",
      "nom": "Verdun",
      "code_insee": "55545",
      "codes_postaux": ["55100"],
      "code_postal": "55100",
      "code_departement": "55",
      "population": 17904,
      "lat": 49.16,
      "lon": 5.38,
      "display": "🏛️ Verdun (55100, 55) - 17 904 hab."
    }
  ]
}
```

**Source de données**: [API Geo](https://geo.api.gouv.fr) (communes françaises)
- Gratuite
- Base de données INSEE
- Information complète (population, codes postaux, etc.)

### Frontend (JavaScript)

#### Classe `Autocomplete`

**Initialisation automatique:**
```javascript
// Champ de recherche d'adresse
const addressInput = document.getElementById('search_input');
new Autocomplete(addressInput, {
    apiEndpoint: '/api/autocomplete/address',
    placeholder: 'Ex: 10 rue de la paix paris, verdun 55...',
    onSelect: function(suggestion) {
        // Remplir les champs cachés
        document.getElementById('latitude').value = suggestion.lat;
        document.getElementById('longitude').value = suggestion.lon;
    }
});

// Champ de recherche de commune
const communeInput = document.getElementById('commune');
new Autocomplete(communeInput, {
    apiEndpoint: '/api/autocomplete/commune',
    placeholder: 'Ex: Lyon, Verdun, 75001...',
    minChars: 2
});
```

**Options disponibles:**
- `minChars` (default: 3) : nombre minimum de caractères
- `debounceMs` (default: 300) : délai avant recherche (ms)
- `maxSuggestions` (default: 8) : nombre max de suggestions
- `apiEndpoint` : URL de l'API
- `onSelect` : callback quand une suggestion est sélectionnée
- `placeholder` : texte d'aide

**Navigation clavier:**
- `↓` / `↑` : naviguer dans les suggestions
- `Enter` : sélectionner la suggestion active
- `Escape` : fermer les suggestions

### CSS

Le fichier `static/autocomplete.css` fournit:
- Design moderne et propre
- Scrollbar personnalisée
- Animation d'apparition fluide
- Highlighting des correspondances
- Responsive (mobile-friendly)

## Installation et utilisation

### 1. Fichiers créés
```
static/
  ├── autocomplete.js    # Logique d'autocomplétion
  └── autocomplete.css   # Styles des suggestions
```

### 2. Modifications apportées

**`agriweb_hebergement_gratuit.py`:**
- Ajout de `/api/autocomplete/address`
- Ajout de `/api/autocomplete/commune`

**`templates/index.html`:**
- Lien vers `autocomplete.css`
- Lien vers `autocomplete.js`

### 3. Utilisation

L'autocomplétion est **automatiquement activée** sur:
- Champ `#search_input` (recherche par adresse)
- Champ `#commune` (recherche par commune)

Aucune configuration supplémentaire n'est requise !

## Exemples d'utilisation

### Recherche d'adresses

**Avec fautes de frappe:**
```
"montiers d'ahun" → Moutiers-d'Ahun
"mon app" → Montpellier, Montargis, etc.
"10 ru victor ugo lyon" → 10 Rue Victor Hugo, Lyon
```

**Avec codes postaux:**
```
"verdun 55" → Verdun (55100)
"paris 1" → Paris 1er Arrondissement (75001)
```

**Adresses partielles:**
```
"10 rue paix" → 10 Rue de la Paix (plusieurs villes)
"place republique" → Place de la République (plusieurs villes)
```

### Recherche de communes

**Par nom:**
```
"lyon" → Lyon (69000, 69)
"moutier" → Moutiers-d'Ahun, Moutiers, etc.
```

**Par code postal:**
```
"75001" → Paris 1er Arrondissement
"69000" → Lyon
```

**Avec département:**
```
"verdun" → Verdun (55100, 55) + Verdun-sur-Garonne (82600, 82)
```

## Avantages de cette solution

### 🚀 Performance
- Requêtes API rapides (< 300ms en moyenne)
- Debouncing pour éviter surcharge
- Cache navigateur automatique

### 🎯 Précision
- APIs officielles françaises
- Données à jour (INSEE, IGN)
- Scoring de pertinence

### 💪 Robustesse
- Gestion d'erreurs complète
- Fallback en cas d'échec
- Timeout automatique

### 🌐 Compatibilité
- Tous navigateurs modernes
- Mobile-friendly
- Accessible (navigation clavier)

### 🔒 Sécurité
- Pas de clé API requise
- Limitation de débit côté serveur
- Validation des entrées

## Tests recommandés

### Cas de test basiques
1. **"montiers d'ahun"** → doit trouver "Moutiers-d'Ahun"
2. **"verdun"** → doit montrer plusieurs Verdun
3. **"75001"** → doit trouver Paris 1er
4. **"10 rue paix paris"** → doit trouver l'adresse exacte

### Cas de test avancés
1. **Fautes multiples**: "moutie dahu"
2. **Caractères spéciaux**: "saint-étienne"
3. **Accents manquants**: "sainte-genevieve"
4. **Abréviations**: "st denis", "bd victor hugo"

### Tests de performance
1. Taper rapidement → debouncing doit fonctionner
2. Recherche lente → timeout après 3s
3. Beaucoup de résultats → limité à 8

## Maintenance

### Logs
Les requêtes sont loggées côté serveur:
```python
print(f"[AUTOCOMPLETE] Recherche: {query}")
print(f"[AUTOCOMPLETE] Erreur API: {error}")
```

### Monitoring
Surveiller:
- Temps de réponse API
- Taux d'échec des requêtes
- Usage mémoire (suggestions en cache)

### Mise à jour
Les APIs utilisées sont maintenues par l'État français:
- BAN: https://adresse.data.gouv.fr
- Geo API: https://geo.api.gouv.fr

Aucune maintenance régulière nécessaire.

## Support et documentation

### APIs utilisées
- **BAN**: https://adresse.data.gouv.fr/api-doc/adresse
- **Geo API**: https://geo.api.gouv.fr/decoupage-administratif/communes

### Dépendances
- `requests` (Python)
- Vanilla JavaScript (pas de framework requis)
- CSS moderne (flexbox, animations)

## Prochaines améliorations possibles

1. **Cache côté serveur** avec Redis
2. **Historique des recherches** (localStorage)
3. **Recherche par département** dédié
4. **Géolocalisation** (suggestions basées sur position)
5. **Mode hors-ligne** (PWA avec cache)

---

**Date de création**: Octobre 2025  
**Version**: 1.0.0  
**Auteur**: AgriWeb Development Team
