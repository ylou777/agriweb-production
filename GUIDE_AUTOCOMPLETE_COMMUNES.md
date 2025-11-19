# 🏛️ Guide d'utilisation - Autocomplétion Communes

## Vue d'ensemble

L'autocomplétion pour la recherche par commune est maintenant active et fonctionne **exactement comme** celle des adresses, avec tolérance aux fautes de frappe.

## Comment l'utiliser

### 1. Accéder à la recherche par commune

Dans votre interface AgriWeb:
```
┌─────────────────────────────────────┐
│ 🗺️ Mon App Géo                     │
├─────────────────────────────────────┤
│ ▼ Adresse • Coordonnées • GeoJSON  │
│ ▶ Commune                           │  ← Cliquez ici
│ ▶ Département                       │
└─────────────────────────────────────┘
```

### 2. Commencer à taper

Tapez au moins **2 caractères** dans le champ "Commune":

```
┌─────────────────────────────────────┐
│ Commune:                            │
│ ┌─────────────────────────────────┐ │
│ │ montiers█                       │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 3. Voir les suggestions

Après 300ms, les suggestions apparaissent automatiquement:

```
┌─────────────────────────────────────┐
│ Commune:                            │
│ ┌─────────────────────────────────┐ │
│ │ montiers                        │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🏛️ Moutiers-d'Ahun (23150, 23) │ │ ← Suggestion 1
│ │    - 688 hab.                   │ │
│ ├─────────────────────────────────┤ │
│ │ 🏛️ Moutiers (45260, 45)        │ │ ← Suggestion 2
│ │    - 470 hab.                   │ │
│ ├─────────────────────────────────┤ │
│ │ 🏛️ Moutiers (73600, 73)        │ │ ← Suggestion 3
│ │    - 3 905 hab.                 │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 4. Sélectionner une commune

**Méthode 1: Souris**
- Survolez une suggestion (elle se met en surbrillance)
- Cliquez pour sélectionner

**Méthode 2: Clavier**
- Utilisez `↓` et `↑` pour naviguer
- Appuyez sur `Entrée` pour sélectionner
- Appuyez sur `Escape` pour fermer

```
┌─────────────────────────────────────┐
│ Commune:                            │
│ ┌─────────────────────────────────┐ │
│ │ Moutiers-d'Ahun                 │ │ ← Valeur remplie
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Exemples de recherches

### ✅ Recherche avec faute de frappe

| Vous tapez | Trouve |
|------------|--------|
| `montiers d'ahun` | **Moutiers-d'Ahun** (23150, 23) |
| `verdun` | **Verdun** (55100, 55) + autres Verdun |
| `saint etienne` | **Saint-Étienne** (42000, 42) |
| `sainte genevieve` | **Sainte-Geneviève-...** |

### 🔢 Recherche par code postal

| Vous tapez | Trouve |
|------------|--------|
| `23150` | **Moutiers-d'Ahun** (23150, 23) |
| `75001` | **Paris 1er Arrondissement** |
| `69000` | **Lyon** (69000, 69) |

### 🔍 Recherche partielle

| Vous tapez | Trouve |
|------------|--------|
| `moutier` | Moutiers-d'Ahun, Moutiers (45), Moutiers (73)... |
| `ver` | Verdun, Vers, Vertou, Vernou... |
| `lyon` | Lyon, Lyon-...  |

### 🏙️ Grandes villes

| Vous tapez | Trouve |
|------------|--------|
| `paris` | Paris 1er, Paris 2e, ... Paris 20e |
| `marseille` | Marseille (13000, 13) |
| `lyon` | Lyon (69000, 69) |
| `toulouse` | Toulouse (31000, 31) |

## Fonctionnalités avancées

### 📊 Informations affichées

Pour chaque suggestion, vous voyez:
- 🏛️ **Nom complet** de la commune
- 📮 **Code postal** principal
- 📍 **Numéro de département**
- 👥 **Population** (nombre d'habitants)

### 🎯 Données stockées

Quand vous sélectionnez une commune, le système stocke automatiquement:
- `data-lat`: Latitude du centre de la commune
- `data-lon`: Longitude du centre de la commune
- `data-code-insee`: Code INSEE officiel
- `data-code-postal`: Code postal principal

Ces données peuvent être utilisées pour des recherches avancées.

### ⚡ Performance

- **Minimum 2 caractères** requis
- **Debouncing de 300ms** (attend que vous finissiez de taper)
- **Maximum 10 suggestions** affichées
- **Timeout de 3 secondes** par requête
- **Cache navigateur** pour réponses rapides

## Différences avec la recherche d'adresses

| Caractéristique | Adresses | Communes |
|-----------------|----------|----------|
| **Minimum caractères** | 3 | 2 |
| **Max suggestions** | 8 | 10 |
| **Source API** | BAN (Base Adresse Nationale) | Geo API (INSEE) |
| **Recherche par** | Rue, n°, ville, CP | Nom, CP, code INSEE |
| **Affichage** | Adresse complète | Nom + CP + Dept + Pop |

## Cas d'usage typiques

### 🎯 Cas 1: Recherche simple
```
Objectif: Trouver Lyon
Action: Tapez "lyon"
Résultat: Lyon (69000, 69) - 522 969 hab.
```

### 🎯 Cas 2: Commune mal orthographiée
```
Objectif: Trouver Moutiers-d'Ahun
Action: Tapez "montiers d'ahun" (faute)
Résultat: Moutiers-d'Ahun (23150, 23) - 688 hab.
```

### 🎯 Cas 3: Plusieurs communes homonymes
```
Objectif: Trouver la bonne Verdun
Action: Tapez "verdun"
Résultat: 
  1. Verdun (55100, 55) - 17 904 hab.
  2. Verdun-sur-Garonne (82600, 82) - 4 689 hab.
  3. Verdun-en-Lauragais (11400, 11) - 429 hab.
Sélection: Choisir selon le département
```

### 🎯 Cas 4: Code postal inconnu
```
Objectif: Quelle commune a le CP 23150 ?
Action: Tapez "23150"
Résultat: Moutiers-d'Ahun (23150, 23)
```

## Intégration avec la recherche

Une fois la commune sélectionnée:

1. **Valeur remplie** dans le champ
2. **Données stockées** (lat, lon, codes)
3. **Prêt à rechercher** - cliquez sur "Rechercher"
4. **Filtres appliqués** selon vos choix (RPG, Parkings, etc.)

```
┌──────────────────────────────────────────┐
│ Commune: Moutiers-d'Ahun                 │
│ ─────────────────────────────────────    │
│ [×] RPG (Cultures)                       │
│ [×] Parkings                             │
│ [×] Bâtiments                            │
│ [ ] Lignes Enedis                        │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │    [🔍 Rechercher]                 │  │
│ └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

## Dépannage

### ❓ Pas de suggestions

**Problème**: Les suggestions n'apparaissent pas

**Solutions**:
1. Vérifiez que vous avez tapé au moins **2 caractères**
2. Attendez **300ms** après avoir fini de taper
3. Vérifiez que le serveur est démarré
4. Ouvrez la console navigateur (F12) pour voir les erreurs

### ❓ Suggestions incorrectes

**Problème**: Les suggestions ne correspondent pas

**Solutions**:
1. L'API recherche par **début de nom** ET par **contenu**
2. Tapez plus de caractères pour affiner
3. Ajoutez le département: "verdun 55"
4. Utilisez le code postal pour une recherche exacte

### ❓ Recherche lente

**Problème**: Les suggestions mettent du temps

**Solutions**:
1. Normal: timeout après 3 secondes
2. Vérifiez votre connexion internet
3. L'API externe peut être lente parfois
4. Réessayez quelques instants plus tard

## Raccourcis clavier

| Touche | Action |
|--------|--------|
| `↓` | Suggestion suivante |
| `↑` | Suggestion précédente |
| `Entrée` | Sélectionner la suggestion |
| `Escape` | Fermer les suggestions |
| `Tab` | Passer au champ suivant |

## API utilisée

**Source**: [API Geo - Gouvernement français](https://geo.api.gouv.fr)

**Caractéristiques**:
- ✅ Gratuite
- ✅ Sans clé API
- ✅ Données officielles INSEE
- ✅ Mise à jour régulière
- ✅ Tolérance aux fautes intégrée

**Endpoint**:
```
GET https://geo.api.gouv.fr/communes
?nom={recherche}
&fields=nom,code,codesPostaux,codeDepartement,population,centre
&limit=10
```

## Conseils d'utilisation

### ✅ Bonnes pratiques

1. **Tapez naturellement** - l'API tolère les fautes
2. **Laissez le temps** - debouncing de 300ms
3. **Soyez précis si besoin** - ajoutez le département ou CP
4. **Utilisez le clavier** - plus rapide que la souris
5. **Vérifiez le département** - pour les homonymes

### ❌ À éviter

1. ❌ Taper trop vite et cliquer avant la fin
2. ❌ Taper 1 seul caractère (minimum = 2)
3. ❌ Ignorer le département pour les communes courantes
4. ❌ Fermer les suggestions avant de lire toutes les options

## Support

### 📚 Documentation complète
Voir: `AUTOCOMPLETE_DOCUMENTATION.md`

### 🧪 Tests
Lancer: `python test_commune_autocomplete.py`

### 🐛 Bugs
- Vérifier la console navigateur (F12)
- Vérifier les logs serveur
- Tester l'API directement: `/api/autocomplete/commune?q=test`

---

**Version**: 1.0.0  
**Date**: Octobre 2025  
**Status**: ✅ Production Ready
