import requests

url = (
    "http://127.0.0.1:5000/generate_reports_by_dept_sse"
    "?department=23"
    "&min_parcelle_area_ha=10.0"
    "&max_bt_dist_m=500"
    "&max_ht_dist_m=5000"
    "&has_eleveurs=true"
    "&exclude_nature=true"
    "&exclude_historic=true"
    "&culture_codes=PPH,J6S"
)

with requests.get(url, stream=True) as resp:
    resp.raise_for_status()
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        # chaque "raw" ressemble à "event: progress" ou "data: {...}"
        print(raw)
