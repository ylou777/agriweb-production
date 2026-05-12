"""
test_send_3mairies.py
Envoie 3 emails de test (un par dept 23/19/15) vers une adresse unique.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

# Import du script de test unitaire
from test_send_mairie import send_test

COMMUNES = [
    # commune, insee, lat, lon, pop
    ('Puy-Malsignat',            '23058', 46.037277, 2.218005,  102),
    ('Albussac',                 '19004', 45.137329, 1.836103,  725),
    ('Mandailles-Saint-Julien',  '15096', 45.069398, 2.657803,  260),
]

to_email = sys.argv[1] if len(sys.argv) > 1 else 'ylaurent.perso@gmail.com'

for i, (commune, insee, lat, lon, pop) in enumerate(COMMUNES, 1):
    print(f"\n{'='*60}")
    print(f"[{i}/3] {commune} ({insee})")
    print('='*60)
    try:
        send_test(to_email, commune, insee, lat, lon, pop)
    except Exception as e:
        print(f"  ERREUR : {e}")

print("\nTerminé — 3 emails envoyés à", to_email)
