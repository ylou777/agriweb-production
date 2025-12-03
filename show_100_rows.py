import sqlite3

conn = sqlite3.connect('C:/Users/Utilisateur/Desktop/AG32.1/proprietaires_parcelles.db')
cur = conn.cursor()

cur.execute('''
    SELECT departement, code_insee, section, numero, siren, forme_juridique, denomination, contenance 
    FROM proprietaires_parcelles 
    LIMIT 100
''')

rows = cur.fetchall()

print('=' * 150)
print(f"{'Dept':<6}{'Code INSEE':<12}{'Section':<10}{'Numéro':<10}{'SIREN':<15}{'Forme Jur.':<12}{'Dénomination':<50}{'Contenance'}")
print('=' * 150)

for r in rows:
    dept = str(r[0])
    insee = str(r[1])
    section = str(r[2])
    numero = str(r[3])
    siren = str(r[4] or "")
    forme = str(r[5] or "")
    denom = str(r[6] or "")[:48]
    contenance = r[7] or 0
    
    print(f"{dept:<6}{insee:<12}{section:<10}{numero:<10}{siren:<15}{forme:<12}{denom:<50}{contenance} m²")

print('=' * 150)
print(f"\nTotal affiché: {len(rows)} parcelles")
print(f"Note: La base contient 18,740,957 parcelles au total")

conn.close()
