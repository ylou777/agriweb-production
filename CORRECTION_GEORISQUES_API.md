# Correction API GeoRisques - 10 octobre 2025

## Problème identifié
Dans la recherche par adresse, des erreurs 404 apparaissaient pour les requêtes concernant :
- Radon
- Argiles (retrait-gonflement)
- Installations classées

## Cause
L'API GeoRisques a évolué et plusieurs endpoints ont changé :

### 1. **Radon**
- ❌ Ancien : `GET /api/v1/radon?latlon=lon,lat`
- ✅ Nouveau : `GET /api/v1/radon?code_insee=XXXXX`
- **Changement** : Nécessite maintenant le code INSEE de la commune au lieu des coordonnées

### 2. **Installations classées**
- ❌ Ancien : `GET /api/v1/installations?latlon=lon,lat&rayon=2000`
- ✅ Nouveau : `GET /api/v1/installations_classees?latlon=lon,lat&rayon=2000`
- **Changement** : L'endpoint s'appelle `installations_classees` (pas `installations`)

### 3. **Argiles (retrait-gonflement)**
- ❌ Ancien : `GET /api/v1/argiles?latlon=lon,lat`
- ✅ Nouveau : Les données sont dans `GET /api/v1/gaspar/risques?code_insee=XXXXX`
- **Changement** : Plus d'endpoint dédié, les tassements différentiels (liés aux argiles) sont dans les risques GASPAR

## Solution implémentée

### Modification dans `fetch_georisques_risks(lat, lon)`

1. **Ajout du géocodage inversé** pour récupérer le code INSEE :
```python
# Obtenir le code INSEE de la commune via géocodage inversé
code_insee = None
try:
    geo_info = get_address_from_coordinates(lat, lon)
    if geo_info and geo_info.get('citycode'):
        code_insee = geo_info['citycode']
        print(f"[GeoRisques] Code INSEE récupéré: {code_insee}")
except Exception as e:
    print(f"[GeoRisques] Impossible de récupérer le code INSEE: {e}")
```

2. **Radon** - Utilisation du code INSEE :
```python
if code_insee:
    url = "https://www.georisques.gouv.fr/api/v1/radon"
    params = {"code_insee": code_insee}
    # ...
```

3. **Argiles** - Extraction depuis gaspar/risques :
```python
if code_insee:
    url = "https://www.georisques.gouv.fr/api/v1/gaspar/risques"
    params = {"code_insee": code_insee}
    # Extraire les risques de tassements différentiels
    for item in results:
        for risk in item.get('risques_detail', []):
            if 'argile' in risk.get('libelle_risque_long', '').lower() or \
               'tassement' in risk.get('libelle_risque_long', '').lower():
                argiles_risks.append(risk)
```

4. **Installations** - Correction de l'endpoint :
```python
url = "https://www.georisques.gouv.fr/api/v1/installations_classees"
params = {"latlon": latlon, "rayon": 2000}
```

## Résultats des tests

### Nice (06088)
- ✅ Radon : 1 résultat (classe_potentiel: 1 - faible)
- ✅ Argiles : 1 résultat (Tassements différentiels)
- ✅ Installations classées : 10 résultats

### Nantes (44109)
- ✅ Radon : 1 résultat (classe_potentiel: 3 - modéré)
- ✅ Argiles : 1 résultat (Tassements différentiels)
- ✅ Installations classées : 10 résultats

## Statut
✅ **CORRIGÉ** - Les trois endpoints fonctionnent maintenant correctement

## Note
L'endpoint `installations_nucleaires` retourne une erreur 500 du côté du serveur GeoRisques, ce qui est un problème de leur API, pas de notre côté.

## Fichiers modifiés
- `agriweb_hebergement_gratuit.py` (fonction `fetch_georisques_risks`)

## Date de correction
10 octobre 2025
