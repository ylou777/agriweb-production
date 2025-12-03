"""
Script de comparaison détaillée des colonnes entre base locale et Railway
"""
import requests

# Base locale
local_columns = [
    ('id', 'INTEGER', 'NOT NULL', 'PRIMARY KEY'),
    ('type', 'TEXT', 'NOT NULL', ''),
    ('commune', 'TEXT', 'NOT NULL', ''),
    ('departement', 'TEXT', 'NULL', ''),
    ('adresse', 'TEXT', 'NULL', ''),
    ('latitude', 'REAL', 'NULL', ''),
    ('longitude', 'REAL', 'NULL', ''),
    ('surface_m2', 'REAL', 'NULL', ''),
    ('surface_ha', 'REAL', 'NULL', ''),
    ('parcelles_cadastrales', 'TEXT', 'NULL', ''),
    ('poste_bt_distance_m', 'REAL', 'NULL', ''),
    ('poste_hta_distance_m', 'REAL', 'NULL', ''),
    ('lien_streetview', 'TEXT', 'NULL', ''),
    ('lien_annuaire', 'TEXT', 'NULL', ''),
    ('statut', 'TEXT', 'NULL', ''),
    ('priorite', 'TEXT', 'NULL', ''),
    ('notes', 'TEXT', 'NULL', ''),
    ('contact_nom', 'TEXT', 'NULL', ''),
    ('contact_email', 'TEXT', 'NULL', ''),
    ('contact_telephone', 'TEXT', 'NULL', ''),
    ('date_creation', 'TIMESTAMP', 'NULL', ''),
    ('date_modification', 'TIMESTAMP', 'NULL', ''),
    ('data_json', 'TEXT', 'NULL', ''),
    ('poste_bt_nom', 'TEXT', 'NULL', ''),
    ('poste_bt_puissance', 'REAL', 'NULL', ''),
    ('poste_hta_nom', 'TEXT', 'NULL', ''),
    ('nom_prospect', 'TEXT', 'NULL', ''),
    ('representant_nom', 'TEXT', 'NULL', ''),
    ('representant_tel', 'TEXT', 'NULL', ''),
    ('representant_email', 'TEXT', 'NULL', ''),
    ('siren', 'TEXT', 'NULL', ''),
    ('dirigeant_nom', 'TEXT', 'NULL', ''),
    ('dirigeant_email', 'TEXT', 'NULL', ''),
    ('dirigeant_tel', 'TEXT', 'NULL', ''),
    ('siret', 'TEXT', 'NULL', ''),
]

# Récupérer un prospect de Railway pour voir tous les champs
BASE_URL = "https://ample-manifestation-production-7b1a.up.railway.app"

print("=" * 80)
print("🔍 COMPARAISON DÉTAILLÉE DES COLONNES")
print("=" * 80)

print("\n📊 BASE LOCALE (SQLite)")
print(f"Total: {len(local_columns)} colonnes")
print("\nColonnes:")
for i, (name, type_, null, extra) in enumerate(local_columns, 1):
    print(f"{i:2d}. {name:30s} {type_:15s} {null}")

# Récupérer un prospect de Railway pour voir la structure
print("\n\n🚀 BASE RAILWAY (PostgreSQL)")
try:
    response = requests.get(f"{BASE_URL}/api/crm/prospects", timeout=10)
    if response.status_code == 200:
        data = response.json()
        prospects = data.get('prospects', [])
        
        if prospects:
            # Prendre le premier prospect qui a le plus de champs renseignés
            sample = prospects[0]
            railway_fields = list(sample.keys())
            railway_fields.sort()
            
            print(f"Total: {len(railway_fields)} champs retournés par l'API")
            print("\nChamps:")
            for i, field in enumerate(railway_fields, 1):
                value = sample.get(field)
                type_info = type(value).__name__
                print(f"{i:2d}. {field:30s} {type_info:15s} Valeur: {str(value)[:40]}")
            
            # Comparaison
            print("\n\n" + "=" * 80)
            print("🔄 COMPARAISON")
            print("=" * 80)
            
            local_set = {col[0] for col in local_columns}
            railway_set = set(railway_fields)
            
            # Colonnes présentes en local mais absentes sur Railway
            missing_in_railway = local_set - railway_set
            if missing_in_railway:
                print(f"\n⚠️ Colonnes présentes en LOCAL mais ABSENTES sur Railway ({len(missing_in_railway)}):")
                for col in sorted(missing_in_railway):
                    print(f"   - {col}")
            
            # Colonnes présentes sur Railway mais absentes en local
            missing_in_local = railway_set - local_set
            if missing_in_local:
                print(f"\n✅ Colonnes présentes sur RAILWAY mais ABSENTES en local ({len(missing_in_local)}):")
                for col in sorted(missing_in_local):
                    print(f"   - {col}")
            
            # Colonnes communes
            common = local_set & railway_set
            print(f"\n✅ Colonnes COMMUNES ({len(common)}):")
            for col in sorted(common):
                print(f"   - {col}")
            
            print("\n" + "=" * 80)
            print("📈 RÉSUMÉ")
            print("=" * 80)
            print(f"Base locale:      {len(local_columns)} colonnes")
            print(f"Base Railway:     {len(railway_fields)} champs")
            print(f"En commun:        {len(common)} champs")
            print(f"Manquant Railway: {len(missing_in_railway)} champs")
            print(f"Manquant Local:   {len(missing_in_local)} champs")
            
        else:
            print("❌ Aucun prospect trouvé sur Railway")
    else:
        print(f"❌ Erreur HTTP {response.status_code}")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 80)
