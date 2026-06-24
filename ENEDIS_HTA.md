# Intégration Lignes HTA Enedis

Endpoint interne: `/api/hta-lignes`

## Paramètres de requête
- `department` (string) Code département (ex: 23) – requis si `bbox` absent.
- `bbox` (string) Bounding box `minx,miny,maxx,maxy` (EPSG:4326) – requis si `department` absent.
- `include_aerienne` (bool, défaut true)
- `include_souterraine` (bool, défaut true)
- `limit` (int, défaut 1000) Limite totale souhaitée (répartie moitié / moitié).

## Réponse JSON
```json
{
  "aerienne": { "type": "FeatureCollection", "features": [...] },
  "souterraine": { "type": "FeatureCollection", "features": [...] },
  "summary": {
    "aerienne_count": 500,
    "souterraine_count": 500,
    "total": 1000,
    "params": { ... },
    "timestamp": "2025-09-18T07:08:34.106679Z"
  }
}
```
Chaque feature reçoit des propriétés enrichies:
- `type_ligne` = `aerienne` | `souterraine`
- `source` = `enedis`

## Exemples
Lignes département 23 (Creuse):
```
curl "http://localhost:5000/api/hta-lignes?department=23&limit=1000"
```
Seulement aérien sur une zone bbox:
```
curl "http://localhost:5000/api/hta-lignes?bbox=1.80,46.10,1.95,46.25&include_souterraine=false&limit=400"
```

## Implémentation
Module: `enedis_integration.py`
- Export GeoJSON: `https://opendata.enedis.fr/api/explore/v2.1/catalog/datasets/{dataset}/exports/geojson`
  (⚠️ juin 2026 : migration `data.enedis.fr` → `opendata.enedis.fr` ; l'ancienne base répond 404 en HTML)
- Datasets: `reseau-hta` (aérien), `reseau-souterrain-hta` (souterrain)
- Filtrage: `where=code_departement="23"` ou `intersects(geo_shape, geom'POLYGON((...)) )`
- Cache mémoire TTL 300s (clé incluant dataset, département ou bbox, limite)

## Notes
- Si `limit` impair, la division moitié / moitié peut perdre 1 feature; ajuster si nécessaire.
- Amélioration future: paramètre `raw_params=true` pour renvoyer les paramètres exacts envoyés à l'API Enedis.
- Pagination future possible via `offset` si besoin d'exhaustivité.
