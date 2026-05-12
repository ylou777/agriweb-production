# Campagne email solaire mairies — État au 30/03/2026

## Objectif
Pipeline automatisé : données MAJIC cadastrales → diagnostic solaire → email personnalisé par mairie.
Cible : ~36 000 communes françaises. Obligation légale de solarisation (Loi APER).

---

## Fichiers clés

| Fichier | Rôle |
|---|---|
| `mairies_diagnostic.py` | Pipeline MAJIC + OSM Overpass + PVGIS + Nominatim + staticmap |
| `mairies_campaign.py` | Génération email HTML (`build_email_html`, `build_diagnostic`, `_build_obligations`) |
| `test_email_gueret.py` | Test unitaire Guéret (23096) — 41 parkings, 637 parcelles, 4 924 kWc |
| `test_batch_mairies.py` | Test batch 10 communes variées (toutes OK) |

---

## Architecture données

| Source | Usage | Notes |
|---|---|---|
| **MAJIC** PostgreSQL Railway | Parcelles communales | filtre `forme_juridique='30'` ou `denomination LIKE 'COMMUNE DE %'` |
| **IGN Apicarto** | Géométries parcelles | par section, 0.25s entre requêtes |
| **OSM Overpass** | Parkings bbox | timeout=60s, retry ×3 avec backoff 15s/30s, cache `_parkings_cache` |
| **Nominatim** | bbox commune polygon | `featuretype=city&polygon_geojson=1` — PAS `geo.api.gouv.fr` (retourne Point) |
| **PVGIS** | Irradiance annuelle | cache par `round(lat,2)/round(lon,2)` |
| **staticmap + Pillow** | Miniature carte dans email | zoom centré sur assets, base64 PNG |

---

## Caches module-level dans mairies_diagnostic.py

```python
_pvgis_cache: dict = {}
_commune_bbox_cache: dict = {}
_parkings_cache: dict = {}   # évite double appel Overpass
```

---

## Points critiques à retenir

### 1. Ne jamais appeler build_diagnostic() séparément dans les tests
```python
# CORRECT — une seule requête Overpass
diag_full = build_commune_diagnostic(...)
diag_email = diagnostic_summary(diag_full)
diag_email['obligations'] = _build_obligations(pop)

# INCORRECT — provoque un 2ème appel Overpass → rate-limit → 0 parkings
diag_email = build_diagnostic(COMMUNE)
```

### 2. Structure get_parkings_osm_bbox — cache APRÈS le try/except
```python
parkings = []
try:
    r = requests.post(...)
    ...
    parkings = [...]
except Exception as e:
    logger.warning(...)

_parkings_cache[cache_key] = parkings   # ← APRÈS le try/except, pas dedans
return parkings
```

### 3. Retries Overpass (504 Gateway Timeout fréquent)
```python
for attempt in range(3):
    if attempt > 0:
        time.sleep(15 * attempt)   # 15s puis 30s
    try:
        r = requests.post(_OVERPASS, ...)
        ...
        break
    except Exception as e:
        ...
```

### 4. Folium — CartoDB Light par défaut
Ajouter CartoDB Light **en dernier** dans la carte Folium = couche active par défaut.
Satellite + Dark ajoutés en premier avec `show=False`.

---

## Texte email reformulé (mairies_campaign.py ~ligne 421)

```
Nous avons analysé le patrimoine foncier de la commune de {nom}
à partir des données cadastrales officielles (MAJIC).

Sur les {nb_parc} parcelles analysées :
{nb_park} parking(s) et {nb_bat} bâtiment(s) public(s)
ont été identifiés comme prioritairement solarisables.
```

**Civilité** : `'Madame la Maire'` si `mme/madame` dans `nom_maire`, sinon `'Monsieur le Maire'`

---

## Résultats batch validés (30/03/2026)

| Commune | Parcelles | Parkings | Bâtiments | kWc | Durée |
|---|---|---|---|---|---|
| Guéret (23096) | 637 | 41 | 10 | 4 924 | ~90s |
| Aurillac (15014) | 521 | 17 | 2 | 2 208 | 113s |
| Rodez (12202) | 482 | 32 | 5 | 3 300 | 70s |
| Mende (48095) | 579 | 19 | 2 | 2 316 | 130s* |
| Digne-les-Bains (04070) | 657 | 42 | 10 | 3 540 | 99s |
| Gap (05061) | 1 037 | 42 | 0 | 3 940 | 146s |
| Alençon (61001) | 526 | 32 | 7 | 2 890 | 102s |
| Châteauroux (36044) | 1 023 | 89 | 1 | 5 741 | 132s* |
| Privas (07186) | 409 | 12 | 8 | 1 023 | 77s |

*retry Overpass déclenché automatiquement

---

## Bugs résolus

| Problème | Cause | Solution |
|---|---|---|
| `geo.api.gouv.fr` retourne Point | Format incompatible | Remplacé par Nominatim avec `polygon_geojson=1` |
| CartoDB Dark comme fond par défaut | Ordre couches Folium | CartoDB Light ajouté en dernier |
| Couleur parking invisible | `#1e40af` sur fond clair | Remplacé par `#0ea5e9` |
| Cache `_parkings_cache` inopérant | `return` avant l'écriture cache | Restructuré : `parkings=[]` + try/except + cache après |
| 0 parkings dans email | Double appel Overpass | `test_email_gueret.py` utilise `diagnostic_summary(diag_full)` |
| Overpass 504 | Rate-limiting serveur | Retry ×3 avec backoff 15s/30s |

---

## Pistes de monétisation

1. **CPL leads → installateurs PV** : 50–300 €/lead × ~1 000 leads/mois = revenus rapides
2. **SaaS diagnostic** pour installateurs : 200–3 000 €/mois/région, données MAJIC exclusives
3. **Commission AMO** mise en relation mairie/installateur : 1–3% du projet (ex. 5–15 k€/projet ~630 kWc)
4. **Licence marque blanche** bureaux d'études / SDE : 5 000 € setup + 500–2 000 €/mois

**Prochaine étape recommandée** : lancer campagne réelle sur 2–3 départements (ex. 23/19/15),
tracker les clics → pipeline CRM, puis contacter 2–3 installateurs régionaux.

---

## Connexion PostgreSQL Railway

```
postgresql://postgres:WbjgkcXDKvbbYJhWprDDQQobbpnggYJc@yamanote.proxy.rlwy.net:42931/railway
Table : proprietaires_parcelles
Colonnes clés : code_insee, section, numero, contenance, denomination, forme_juridique, siren
```
