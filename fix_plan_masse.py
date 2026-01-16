with open('plan_masse_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Désactiver screenshot
content = content.replace(
    "screenshot_data = self.calpinage.get('screenshot_map') if self.calpinage else None",
    "screenshot_data = None  # Désactivation screenshot (éviter doublon modules)"
)

# 2. Ajouter gps_bounds avant satellite_img
old_code = """if not self.screenshot_used:
                satellite_img = self._fetch_satellite_image_bbox(lat, lon, bbox_meters, width=1600, height=1400)"""

new_code = """if not self.screenshot_used:
                # Définir gps_bounds AVANT
                meters_to_lat = bbox_meters / 111000
                meters_to_lon = bbox_meters / (111000 * 0.7)
                self.gps_bounds = {
                    'min_lat': lat - meters_to_lat,
                    'max_lat': lat + meters_to_lat,
                    'min_lon': lon - meters_to_lon,
                    'max_lon': lon + meters_to_lon
                }
                
                satellite_img = self._fetch_satellite_image_bbox(lat, lon, bbox_meters, width=1600, height=1400)"""

content = content.replace(old_code, new_code)

with open('plan_masse_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)
    
print('✅ Fichier modifié avec succès')
