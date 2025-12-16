from equipements_database import ONDULEURS_DATABASE, get_onduleur_optimal

print("=" * 70)
print("TEST ONDULEURS HAUTE PUISSANCE")
print("=" * 70)
print()

# Compter les onduleurs
print(f"Total onduleurs dans la base: {len(ONDULEURS_DATABASE)}")
print()

# Lister les onduleurs >50kW
print("ONDULEURS HAUTE PUISSANCE (>50kW):")
haute_puissance = {ref: data for ref, data in ONDULEURS_DATABASE.items() 
                   if data['p_ac_nominale'] >= 50000}
for ref, data in sorted(haute_puissance.items(), key=lambda x: x[1]['p_ac_nominale']):
    print(f"  {ref:25s} | {data['p_ac_nominale']/1000:>6.0f}kW AC | "
          f"DC_max:{data['p_dc_max']/1000:>6.0f}kW | "
          f"rend:{data['rendement_max']:>4.1f}% | {data['prix_indicatif']:>7,}EUR")
print()

# Test sélection pour grandes installations
print("TEST SELECTION POUR GRANDES INSTALLATIONS:")
test_installations = [
    {'kwc': 50.0, 'desc': 'Toiture PME'},
    {'kwc': 100.0, 'desc': 'Hangar agricole'},
    {'kwc': 150.0, 'desc': 'Ombriere parking'},
    {'kwc': 250.0, 'desc': 'Centrale au sol'},
    {'kwc': 500.0, 'desc': 'Ferme solaire'}
]

for install in test_installations:
    result = get_onduleur_optimal(install['kwc'])
    if result:
        ref, ond = result
        ratio = (install['kwc'] * 1000) / ond['p_ac_nominale']
        print(f"[OK] {install['kwc']:>6.1f}kWc ({install['desc']})")
        print(f"     -> {ref}: {ond['fabricant']} {ond['modele']}")
        print(f"     -> {ond['p_ac_nominale']/1000:.0f}kW AC | "
              f"rend:{ond['rendement_max']:.1f}% | "
              f"ratio DC/AC:{ratio:.2f} | "
              f"{ond['prix_indicatif']:,}EUR")
    else:
        print(f"[WARN] {install['kwc']:>6.1f}kWc ({install['desc']}) -> Aucun onduleur compatible")
    print()

print("=" * 70)
print("TEST TERMINE")
print("=" * 70)
