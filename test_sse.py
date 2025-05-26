# test_sse.py
import requests, json

# Chargez vos critères depuis le JSON
with open("body.json","r", encoding="utf-8-sig") as f:
    payload = json.load(f)

# Ouvrir le flux SSE
resp = requests.post(
    "http://127.0.0.1:5000/generate_reports_sse",
    json=payload,
    headers={"Accept": "text/event-stream"},
    stream=True
)
from agriweb_source import app

with app.test_request_context():
    print(app.url_map)
    
for line in resp.iter_lines(decode_unicode=True):
    if line:
        print(line)
