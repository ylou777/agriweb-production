"""
Script de debug pour vérifier les positions GPS des modules dans le calpinage
"""
import json
import sys

# Lire le fichier calpinage (passé en argument ou par défaut)
calpinage_file = sys.argv[1] if len(sys.argv) > 1 else input("Chemin vers le fichier de calpinage JSON : ")

try:
    with open(calpinage_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n=== DEBUG POSITIONS GPS DES MODULES ===\n")
    
    if 'zones' not in data:
        print("❌ Pas de clé 'zones' dans le fichier")
        sys.exit(1)
    
    zones = data['zones']
    print(f"📊 Nombre de zones: {len(zones)}\n")
    
    for i, zone in enumerate(zones):
        print(f"--- ZONE {zone.get('numero', i+1)} ---")
        print(f"  Nombre de modules: {zone.get('nbModules', 0)}")
        print(f"  Orientation: {zone.get('moduleOrientation', 'N/A')}")
        print(f"  Largeur: {zone.get('largeurMetres', 0):.2f}m")
        print(f"  Longueur: {zone.get('longueurMetres', 0):.2f}m")
        
        # Vérifier modulesPositions
        modules_positions = zone.get('modulesPositions', [])
        print(f"  📍 modulesPositions: {len(modules_positions)} entrées")
        
        if modules_positions:
            # Afficher le premier module comme exemple
            first_module = modules_positions[0]
            print(f"    Premier module:")
            print(f"      Centre: lat={first_module.get('lat', 'N/A')}, lng={first_module.get('lng', 'N/A')}")
            
            corners = first_module.get('corners', [])
            if corners:
                print(f"      Corners ({len(corners)} coins):")
                for j, corner in enumerate(corners):
                    print(f"        Coin {j+1}: lat={corner.get('lat'):.10f}, lng={corner.get('lng'):.10f}")
            else:
                print(f"      ❌ PAS DE CORNERS!")
        else:
            print(f"    ❌ AUCUNE POSITION GPS SAUVEGARDÉE!")
        
        # Vérifier coordinates de la zone
        coordinates = zone.get('coordinates', [])
        if coordinates:
            print(f"  📐 Coordonnées de la zone: {len(coordinates)} points")
        else:
            print(f"  ❌ Pas de coordonnées GPS pour la zone")
        
        print()
    
    # Vérifier gpsConversion global
    if 'gpsConversion' in data:
        gps_conv = data['gpsConversion']
        print("🗺️ Facteurs de conversion GPS globaux:")
        print(f"  metersPerDegreeLng: {gps_conv.get('metersPerDegreeLng', 'N/A')}")
        print(f"  metersPerDegreeLat: {gps_conv.get('metersPerDegreeLat', 'N/A')}")
    else:
        print("❌ Pas de gpsConversion global")
    
    # Vérifier screenshot
    if 'screenshot_map' in data:
        screenshot_size = len(data['screenshot_map'])
        print(f"\n📸 Screenshot: {screenshot_size} caractères ({screenshot_size/1024:.0f} KB)")
    else:
        print("\n❌ Pas de screenshot")
    
    # Vérifier map_metadata
    if 'map_metadata' in data:
        metadata = data['map_metadata']
        print(f"\n🗺️ Map metadata:")
        if 'bounds' in metadata:
            bounds = metadata['bounds']
            print(f"  Bounds: N={bounds.get('north'):.6f}, S={bounds.get('south'):.6f}")
            print(f"          E={bounds.get('east'):.6f}, W={bounds.get('west'):.6f}")
        if 'dimensions' in metadata:
            dims = metadata['dimensions']
            print(f"  Dimensions: {dims.get('width')}x{dims.get('height')} px")
    else:
        print("\n❌ Pas de map_metadata")

except FileNotFoundError:
    print(f"❌ Fichier non trouvé: {calpinage_file}")
except json.JSONDecodeError as e:
    print(f"❌ Erreur de parsing JSON: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
