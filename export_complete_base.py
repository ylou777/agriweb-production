#!/usr/bin/env python3
"""
Export complet de la base recipients (TOUS les enregistrements, SANS déduplication)
Inclut : tous les envois, tentatives, statuts, résultats de campagne
"""

import os
import json
import csv
import zipfile
from datetime import datetime
from mairies_campaign import get_db

def export_complete(outfile: str = None):
    """Export COMPLET sans filtrage ni déduplication."""
    
    outname = outfile or f"mairies_campaign_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    tmp_dir = os.path.splitext(outname)[0]
    os.makedirs(tmp_dir, exist_ok=True)

    csv_path = os.path.join(tmp_dir, 'recipients_all.csv')
    jsonl_path = os.path.join(tmp_dir, 'diagnostics_all.jsonl')

    headers = ['id','campaign_id','email','nom_commune','code_insee','departement','population','lat','lon',
               'nb_parcelles','nb_parkings','nb_batiments','puissance_kwc','production_kwh','economie_annuelle','co2_evite_kg','irradiance',
               'status','sent_at','opened_at','clicked_at','error','pdf_unlocked']

    conn = get_db()
    try:
        # Récupérer TOUS les recipients — SANS FILTRE
        sql = "SELECT * FROM recipients ORDER BY campaign_id, departement, nom_commune, email"
        rows = conn.execute(sql).fetchall()

        total = 0
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvf, open(jsonl_path, 'w', encoding='utf-8') as jf:
            writer = csv.DictWriter(csvf, fieldnames=headers)
            writer.writeheader()

            for r in rows:
                diag = None
                try:
                    if r.get('diagnostic_json'):
                        diag = json.loads(r['diagnostic_json']) if isinstance(r['diagnostic_json'], str) else r['diagnostic_json']
                except Exception:
                    diag = None

                outrow = {
                    'id': r.get('id'),
                    'campaign_id': r.get('campaign_id'),
                    'email': r.get('email'),
                    'nom_commune': r.get('nom_commune'),
                    'code_insee': r.get('code_insee'),
                    'departement': r.get('departement'),
                    'population': r.get('population') or 0,
                    'lat': r.get('lat'),
                    'lon': r.get('lon'),
                    'nb_parcelles': diag.get('nb_parcelles', 0) if diag else '',
                    'nb_parkings': diag.get('nb_parkings', 0) if diag else '',
                    'nb_batiments': diag.get('nb_batiments', 0) if diag else '',
                    'puissance_kwc': diag.get('puissance_totale_kwc', 0) if diag else '',
                    'production_kwh': diag.get('prod_totale_kwh', 0) if diag else '',
                    'economie_annuelle': diag.get('economie_annuelle', 0) if diag else '',
                    'co2_evite_kg': diag.get('co2_evite_kg', 0) if diag else '',
                    'irradiance': diag.get('irradiance', '') if diag else '',
                    'status': r.get('status'),
                    'sent_at': r.get('sent_at'),
                    'opened_at': r.get('opened_at'),
                    'clicked_at': r.get('clicked_at'),
                    'error': r.get('error'),
                    'pdf_unlocked': r.get('pdf_unlocked'),
                }
                writer.writerow(outrow)

                # diagnostics.jsonl
                if diag is not None:
                    jf.write(json.dumps({'id': r.get('id'), 'code_insee': r.get('code_insee'), 'diagnostic': diag}, ensure_ascii=False) + '\n')

                total += 1

        # Zip
        with zipfile.ZipFile(outname, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(csv_path, arcname='recipients_all.csv')
            zf.write(jsonl_path, arcname='diagnostics_all.jsonl')

        print(f"✅ Export complet terminé: {outname}")
        print(f"   Total enregistrements: {total}")
        return outname, total

    finally:
        conn.close()


if __name__ == '__main__':
    fname, cnt = export_complete()
    print(f"\n📦 Fichier prêt: {fname}")
