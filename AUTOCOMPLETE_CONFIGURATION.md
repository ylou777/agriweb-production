# 🎯 Configuration de l'Autocomplétion - Adresses et Communes

## 📋 Vue d'ensemble

L'autocomplétion est maintenant active sur **deux champs** :

| Champ | Type | API | Seuil | Fonctionnalité |
|-------|------|-----|-------|----------------|
| **Adresse** (`#search_input`) | `address` | BAN (Base Adresse Nationale) | 3 caractères | Recherche d'adresses avec tolérance typo |
| **Commune** (`#commune`) | `commune` | Geo API (INSEE) | 2 caractères | Recherche de communes avec tolérance typo |

---

## 🏠 Autocomplete pour les Adresses

### Champ concerné

```html
<input id="search_input" class="form-control mb-2" 
       placeholder='48.85,2.35 ou {"type":"Point",...}'>
```

### Configuration JavaScript

```javascript
new Autocomplete(searchInput, {
  type: 'address',           // Type de recherche
  minChars: 3,              // Minimum 3 caractères
  onSelect: function(suggestion) {
    // Remplir les coordonnées
    lonInput.value = suggestion.geometry.coordinates[0];
    latInput.value = suggestion.geometry.coordinates[1];
    addressInput.value = suggestion.properties.label;
  }
});
```

### Exemples de recherche

| Saisie | Suggestions affichées |
|--------|----------------------|
| `moutier` | • Moutiers-d'Ahun (23150) <br> • Moutiers-sur-Boëme (16440) <br> • Moutiers-au-Perche (61110) |
| `verdu` | • Verdun (55100) <br> • Verdun-sur-Garonne (82600) <br> • Verdun-sur-le-Doubs (71350) |
| `23150` | • Moutiers-d'Ahun (23150) <br> • Ahun (23150) <br> • Parsac (23150) |
| `5 rue de la` | • 5 Rue de la République, Paris <br> • 5 Rue de la Mairie, Lyon <br> • 5 Rue de la Liberté, Marseille |

### Données retournées

```javascript
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [1.8583333, 45.9] // [longitude, latitude]
  },
  "properties": {
    "label": "Moutiers-d'Ahun, 23150, Creuse",
    "name": "Moutiers-d'Ahun",
    "postcode": "23150",
    "city": "Moutiers-d'Ahun",
    "context": "23, Creuse, Nouvelle-Aquitaine",
    "type": "municipality",
    "importance": 0.57623
  }
}
```

---

## 🏘️ Autocomplete pour les Communes

### Champ concerné

```html
<input id="commune" name="commune" class="form-control mb-2" 
       placeholder="Lyon">
```

### Configuration JavaScript

```javascript
new Autocomplete(communeInput, {
  type: 'commune',          // Type de recherche
  minChars: 2,             // Minimum 2 caractères
  onSelect: function(suggestion) {
    console.log('🏘️ Commune sélectionnée:', suggestion);
    // La valeur est automatiquement définie dans l'input
  }
});
```

### Exemples de recherche

| Saisie | Suggestions affichées |
|--------|----------------------|
| `limo` | • Limoges (87000) <br> • Limoux (11300) <br> • Limonest (69760) |
| `pari` | • Paris (75000) <br> • Parigné-l'Évêque (72250) <br> • Parigny (50600) |
| `87` | • Limoges (87000) <br> • Saint-Junien (87200) <br> • Bellac (87300) |
| `ahun` | • Ahun (23150) <br> • Moutiers-d'Ahun (23150) |

### Données retournées

```javascript
{
  "nom": "Limoges",
  "code": "87085",
  "codeDepartement": "87",
  "codeRegion": "75",
  "codesPostaux": ["87000", "87100", "87280"],
  "population": 133627
}
```

---

## ⚙️ Architecture technique

### Structure des fichiers

```
AgW3b/
├── static/
│   ├── autocomplete.js          ← Classe Autocomplete (logique)
│   └── autocomplete.css         ← Styles des suggestions
├── templates/
│   ├── index.html              ← Initialisation des autocompletes
│   └── search_panel.html       ← Champs de formulaire
└── agriweb_hebergement_gratuit.py ← Endpoints API
```

### Endpoints API

#### 1️⃣ Autocomplete Adresse

**Endpoint :** `GET /api/autocomplete/address?q=<query>`

**Exemple :**
```bash
curl "http://localhost:5000/api/autocomplete/address?q=moutiers"
```

**Réponse :**
```json
{
  "success": true,
  "suggestions": [
    {
      "type": "Feature",
      "geometry": {"coordinates": [1.8583333, 45.9]},
      "properties": {
        "label": "Moutiers-d'Ahun, 23150, Creuse",
        "name": "Moutiers-d'Ahun",
        "postcode": "23150"
      }
    }
  ],
  "count": 5
}
```

#### 2️⃣ Autocomplete Commune

**Endpoint :** `GET /api/autocomplete/commune?q=<query>`

**Exemple :**
```bash
curl "http://localhost:5000/api/autocomplete/commune?q=limo"
```

**Réponse :**
```json
{
  "success": true,
  "suggestions": [
    {
      "nom": "Limoges",
      "code": "87085",
      "codeDepartement": "87",
      "codesPostaux": ["87000", "87100"],
      "population": 133627
    }
  ],
  "count": 5
}
```

---

## 🎨 Personnalisation

### Modifier le nombre minimum de caractères

```javascript
// Adresse : 3 caractères (actuel)
new Autocomplete(searchInput, {
  minChars: 3  // ← Modifier ici
});

// Commune : 2 caractères (actuel)
new Autocomplete(communeInput, {
  minChars: 2  // ← Modifier ici
});
```

### Modifier le délai de debounce

Dans `static/autocomplete.js` :

```javascript
this.debounceDelay = 300;  // ← 300ms actuellement (bon équilibre)
```

**Recommandations :**
- ⚡ **100-200ms** : Réactif mais plus de requêtes API
- ✅ **300ms** : Équilibre optimal (défaut)
- 🐢 **500ms+** : Moins de requêtes mais moins fluide

### Modifier le nombre de suggestions

Dans `agriweb_hebergement_gratuit.py` :

```python
# Pour les adresses
response = requests.get(
    'https://api-adresse.data.gouv.fr/search/',
    params={'q': query, 'limit': 5}  # ← 5 suggestions (défaut)
)

# Pour les communes
response = requests.get(
    'https://geo.api.gouv.fr/communes',
    params={'nom': query, 'limit': 5}  # ← 5 suggestions (défaut)
)
```

---

## 🔧 Désactiver l'autocomplétion

### Désactiver pour le champ adresse

Dans `templates/index.html`, commentez :

```javascript
// Désactiver autocomplete adresse
/*
new Autocomplete(searchInput, {
  type: 'address',
  ...
});
*/
```

### Désactiver pour le champ commune

```javascript
// Désactiver autocomplete commune
/*
new Autocomplete(communeInput, {
  type: 'commune',
  ...
});
*/
```

---

## 🐛 Dépannage

### L'autocomplete ne s'affiche pas

**1. Vérifier que les fichiers sont chargés**

Ouvrez la console (F12) et tapez :

```javascript
console.log(typeof Autocomplete);  // Doit afficher "function"
```

**2. Vérifier que les champs existent**

```javascript
console.log(document.getElementById('search_input'));  // Adresse
console.log(document.getElementById('commune'));       // Commune
```

**3. Vérifier les logs de console**

Vous devriez voir au chargement :
```
🎯 Autocomplete initialisé sur #search_input (type: address)
🎯 Autocomplete initialisé sur #commune (type: commune)
```

### Les suggestions ne s'affichent pas

**1. Vérifier les requêtes API**

Ouvrez l'onglet **Network** (F12) et tapez dans un champ. Vous devriez voir :
- Pour adresse : `api/autocomplete/address?q=...`
- Pour commune : `api/autocomplete/commune?q=...`

**2. Vérifier la réponse API**

Cliquez sur la requête dans Network → Response. Doit retourner :
```json
{
  "success": true,
  "suggestions": [...]
}
```

**3. Tester les endpoints directement**

```bash
# Test adresse
curl "http://localhost:5000/api/autocomplete/address?q=paris"

# Test commune
curl "http://localhost:5000/api/autocomplete/commune?q=lyon"
```

### Le style est incorrect

**1. Vérifier que le CSS est chargé**

Dans la console :
```javascript
console.log(document.styleSheets);
// Doit contenir autocomplete.css
```

**2. Forcer le rechargement**

```
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

---

## 📊 Performance

### Temps de réponse

| API | Temps moyen | Cache | Débit max |
|-----|-------------|-------|-----------|
| **BAN (adresse)** | ~150ms | OUI | 10 req/s |
| **Geo API (commune)** | ~100ms | OUI | 50 req/s |

### Optimisations appliquées

✅ **Debouncing** : 300ms entre les requêtes  
✅ **Minimum de caractères** : Évite les requêtes inutiles  
✅ **Limite de résultats** : 5 suggestions maximum  
✅ **Cache navigateur** : Les requêtes identiques sont mises en cache

---

## 🎯 Tests

### Test manuel rapide

**1. Test adresse :**
```
1. Allez sur http://localhost:5000
2. Ouvrez l'accordéon "Adresse • Coordonnées • GeoJSON"
3. Tapez "moutier" dans le champ
4. ✅ Vous devez voir des suggestions après 300ms
5. Sélectionnez "Moutiers-d'Ahun"
6. ✅ Le champ doit se remplir automatiquement
```

**2. Test commune :**
```
1. Ouvrez l'accordéon "Commune"
2. Tapez "limo" dans le champ Commune
3. ✅ Vous devez voir des suggestions après 300ms
4. Sélectionnez "Limoges"
5. ✅ Le champ doit se remplir avec "Limoges"
```

### Test avec typos

| Saisie incorrecte | Suggestion correcte |
|-------------------|---------------------|
| `montiers` | ✅ Moutiers-d'Ahun |
| `verdon` | ✅ Verdun |
| `limmoge` | ✅ Limoges |
| `pariz` | ✅ Paris |

---

## 🚀 Commandes de démarrage

```powershell
# Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# Démarrer Flask
python agriweb_hebergement_gratuit.py

# Ouvrir dans le navigateur
start http://localhost:5000
```

---

## 📚 Documentation complémentaire

- **Guide d'utilisation** : `GUIDE_AUTOCOMPLETE_COMMUNES.md`
- **API BAN** : https://adresse.data.gouv.fr/api-doc/adresse
- **API Geo** : https://geo.api.gouv.fr/decoupage-administratif/communes

---

**Version :** 2.0.0  
**Date :** Octobre 2025  
**Status :** ✅ PRODUCTION READY

🎉 **L'autocomplétion fonctionne maintenant sur les adresses ET les communes !**
