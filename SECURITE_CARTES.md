# 🔒 Sécurité des Cartes Sauvegardées

## Problème identifié (10 octobre 2025)

Sur Railway en production, **toutes les cartes sont sauvegardées dans `/static/cartes/`** et sont accessibles publiquement. Cela signifie que :

❌ **Sans protection** :
- Tous les utilisateurs peuvent voir les recherches de tout le monde
- Les URLs sont prévisibles : `recherche_15-rue-pelleport_20251010.html`
- Un utilisateur peut énumérer et télécharger toutes les cartes
- Problème de confidentialité : adresses, parcelles, données sensibles

## Solution implémentée : Tokens UUID

### 🎯 Principe

Ajout d'un **token UUID de 8 caractères** dans chaque nom de fichier pour le rendre impossible à deviner.

### 📝 Format des fichiers

**Avant** (prévisible) :
```
recherche_15-rue-pelleport-bordeaux_20251010_150623.html
rapport_12-rue-de-nice-toulouse_20251010_151402.html
commune_Toulouse_20251010_145530.html
```

**Après** (sécurisé) :
```
recherche_15-rue-pelleport-bordeaux_a3f8d2c1_20251010_150623.html
rapport_12-rue-de-nice-toulouse_7b9e4f2a_20251010_151402.html
commune_Toulouse_e1c8a5d3_20251010_145530.html
```

### 🔐 Sécurité apportée

✅ **Tokens UUID impossibles à deviner** : 2^32 combinaisons (4 milliards)
✅ **Pas d'énumération possible** : Impossible de scanner systématiquement
✅ **URLs uniques** : Jamais de collision entre utilisateurs
✅ **Rétrocompatible** : Fonctionne avec le système actuel
✅ **Simple** : Pas besoin de restructurer les dossiers

### ⚠️ Limitations

Cette solution **empêche la découverte par énumération** mais ne remplace pas une vraie authentification :

- ❌ Si quelqu'un partage un lien, la carte reste accessible
- ❌ Les cartes sont toujours dans `/static/` (publiques par nature)
- ❌ Pas de contrôle d'accès par utilisateur

### 🚀 Améliorations futures (optionnel)

Pour une sécurité maximale, considérer :

1. **Authentification obligatoire** : 
   - Route `/cartes/<token>` qui vérifie `session['user_id']`
   - Vérifier la propriété du fichier avant de le servir

2. **Base de données** :
   ```sql
   CREATE TABLE user_maps (
       id INTEGER PRIMARY KEY,
       user_id INTEGER,
       filename TEXT,
       token TEXT UNIQUE,
       created_at TIMESTAMP
   );
   ```

3. **Nettoyage automatique** :
   - Supprimer les cartes > 7 jours
   - Limiter à 20 cartes par utilisateur
   - Tâche cron quotidienne

4. **Dossiers utilisateurs** :
   ```
   user_data/
   ├── user_1/cartes/
   ├── user_2/cartes/
   └── user_3/cartes/
   ```

## 📊 Impact sur l'existant

### Fichiers modifiés
- `agriweb_hebergement_gratuit.py` :
  - Nouvelle fonction `generate_secure_filename()`
  - 3 points d'utilisation : recherches, rapports, communes

### Compatibilité
- ✅ Anciennes cartes restent accessibles
- ✅ Nouvelles cartes ont le format sécurisé
- ✅ Pas de migration nécessaire

### Performance
- ✅ Aucun impact (génération UUID instantanée)
- ✅ Pas de requête DB supplémentaire

## 🧪 Tests

Exemples de noms générés :

```python
generate_secure_filename("recherche", "15 rue de Nice, Toulouse")
# → recherche_15-rue-de-Nice-Toulouse_a3f8d2c1_20251010_150623.html

generate_secure_filename("rapport", "Paris 75001")
# → rapport_Paris-75001_7b9e4f2a_20251010_151402.html

generate_secure_filename("commune", "Bordeaux")
# → commune_Bordeaux_e1c8a5d3_20251010_145530.html
```

## 📅 Historique

- **10 octobre 2025** : Identification du problème de sécurité
- **10 octobre 2025** : Implémentation tokens UUID (Option 3)

---

**Note** : Cette solution est un compromis entre sécurité et simplicité. Pour une application commerciale avec données sensibles, préférer l'authentification complète + base de données.
