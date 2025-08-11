import requests
import json

url = (
    "http://127.0.0.1:5000/generate_reports_by_dept_sse"
    "?department=23"
    "&min_area_ha=10.0"
    "&bt_max_distance=500"
    "&ht_max_distance=5000"
    "&want_eleveurs=true"
    "&exclude_nature=true"
    "&exclude_historic=true"
    "&culture=PPH,J6S"
)

with requests.get(url, stream=True) as resp:
    resp.raise_for_status()
    event = None
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        if raw.startswith("event:"):
            event = raw.split(":", 1)[1].strip()
        elif raw.startswith("data:"):
            data = raw.split(":", 1)[1].strip()
            # Essaie d'afficher le JSON de façon lisible
            try:
                obj = json.loads(data)
                print(json.dumps(obj, indent=2, ensure_ascii=False))
            except Exception:
                print(data)