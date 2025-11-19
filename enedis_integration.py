import requests
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

"""
Intégration simplifiée Enedis HTA (réseau aérien et souterrain) pour AgriWeb.
Datasets utilisés:
 - Lignes HTA aériennes: reseau-hta
 - Lignes HTA souterraines: reseau-souterrain-hta

Fonctionnalités:
 - Récupération par département (code_departement)
 - Récupération par bbox (west,south,east,north)
 - Fusion logique de paramètres: department prioritaire sur bbox
 - Cache mémoire léger (TTL 300s) pour limiter les appels
 - Retour structuré: deux FeatureCollections séparées + résumé

Note: l'API supporte des paramètres `where`, `limit`, `offset`.
Ici on implémente un usage direct via l'export GeoJSON simplifié.
"""

BASE_URL = "https://data.enedis.fr/api/explore/v2.1/catalog/datasets"
DATASET_AERIEN = "reseau-hta"
DATASET_SOUTERRAIN = "reseau-souterrain-hta"

logger = logging.getLogger("enedis_integration")
logger.setLevel(logging.INFO)

# Cache simple: clé -> (timestamp, data)
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_CACHE_TTL = 300  # secondes


def _cache_key(dataset: str, department: Optional[str], bbox: Optional[List[float]], limit: int) -> str:
    if department:
        return f"{dataset}::dep::{department}::{limit}"
    if bbox:
        return f"{dataset}::bbox::{','.join(map(str,bbox))}::{limit}"
    return f"{dataset}::all::{limit}"

def _get_cached(key: str) -> Optional[Dict[str, Any]]:
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, data = entry
    if time.time() - ts > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    return data

def _set_cache(key: str, data: Dict[str, Any]):
    _CACHE[key] = (time.time(), data)


def _build_where_department(department: str) -> str:
    return f'code_departement="{department}"'


def _build_where_bbox(bbox: List[float]) -> str:
    west, south, east, north = bbox
    # Utilisation de intersects sur geo_shape
    return (
        "intersects(geo_shape, geom'POLYGON(("
        f"{west} {south}, {east} {south}, {east} {north}, {west} {north}, {west} {south}"  ") )')"
    )


def _fetch_dataset(dataset: str, department: Optional[str], bbox: Optional[List[float]], limit: int) -> Dict[str, Any]:
    """Récupère un dataset Enedis (GeoJSON export)."""
    key = _cache_key(dataset, department, bbox, limit)
    cached = _get_cached(key)
    if cached:
        logger.info(f"♻️ [ENEDIS] Cache hit {dataset} ({'dep '+department if department else 'bbox' if bbox else 'all'})")
        return cached

    url = f"{BASE_URL}/{dataset}/exports/geojson"
    params = {"limit": limit, "timezone": "UTC"}

    where_clauses = []
    if department:
        where_clauses.append(_build_where_department(department))
    elif bbox:
        where_clauses.append(_build_where_bbox(bbox))

    if where_clauses:
        # Si plusieurs éventuels futurs filtres: AND join
        params["where"] = " AND ".join(where_clauses)

    logger.info(f"🔌 [ENEDIS] Requête dataset={dataset} params={params}")

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        feats = data.get("features", [])
        logger.info(f"✅ [ENEDIS] {len(feats)} features récupérées ({dataset})")
        _set_cache(key, data)
        return data
    except Exception as e:
        logger.error(f"❌ [ENEDIS] Erreur fetch {dataset}: {e}")
        return {"type": "FeatureCollection", "features": [], "error": str(e)}


def get_lignes_hta(
    department: Optional[str] = None,
    bbox: Optional[List[float]] = None,
    include_aerienne: bool = True,
    include_souterraine: bool = True,
    limit: int = 1000,
) -> Dict[str, Any]:
    """
    Récupère les lignes HTA aériennes et souterraines.
    Le paramètre limit est pour le total -> réparti entre les deux types.
    """
    if limit < 2:
        limit = 2
    limit_per_type = max(1, limit // 2)

    aerienne_fc = {"type": "FeatureCollection", "features": []}
    souterraine_fc = {"type": "FeatureCollection", "features": []}

    if include_aerienne:
        raw_a = _fetch_dataset(DATASET_AERIEN, department, bbox, limit_per_type)
        feats_a = raw_a.get("features", [])
        for f in feats_a:
            props = f.setdefault("properties", {})
            props["type_ligne"] = "aerienne"
            props["source"] = "enedis"
        aerienne_fc = {"type": "FeatureCollection", "features": feats_a}

    if include_souterraine:
        raw_s = _fetch_dataset(DATASET_SOUTERRAIN, department, bbox, limit_per_type)
        feats_s = raw_s.get("features", [])
        for f in feats_s:
            props = f.setdefault("properties", {})
            props["type_ligne"] = "souterraine"
            props["source"] = "enedis"
        souterraine_fc = {"type": "FeatureCollection", "features": feats_s}

    summary = {
        "aerienne_count": len(aerienne_fc.get("features", [])),
        "souterraine_count": len(souterraine_fc.get("features", [])),
        "total": len(aerienne_fc.get("features", [])) + len(souterraine_fc.get("features", [])),
        "params": {
            "department": department,
            "bbox": bbox,
            "include_aerienne": include_aerienne,
            "include_souterraine": include_souterraine,
            "limit_total": limit,
            "limit_per_type": limit_per_type,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    logger.info(
        f"🔎 [ENEDIS_HTA] Récap aérienne={summary['aerienne_count']} souterraine={summary['souterraine_count']} total={summary['total']}"
    )

    return {
        "aerienne": aerienne_fc,
        "souterraine": souterraine_fc,
        "summary": summary,
    }

__all__ = ["get_lignes_hta"]
