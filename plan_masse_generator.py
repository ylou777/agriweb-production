"""
G├®n├®rateur de Plan de Masse Cadastral avec Calpinage PV
Version simplifi├®e et professionnelle
v2.1 - 2026-01-07: Int├®gration API Cadastre IGN pour contours parcelles r├®els
"""

from reportlab.lib.pagesizes import A3, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import requests
from PIL import Image
import json
import base64
import re
import math


class LabelManager:
    """Gestion intelligente du positionnement des ├®tiquettes pour ├®viter les superpositions"""
    
    def __init__(self, center_x=None, center_y=None):
        self.used_positions = []  # Liste des rectangles d├®j├á utilis├®s
        self.center_x = center_x  # Centre de l'image pour calculer la distance
        self.center_y = center_y
    
    def find_non_overlapping_position(self, initial_x, initial_y, width, height, max_attempts=24):
        """Trouve une position non superpos├®e pour une ├®tiquette"""
        # Positions alternatives ├á essayer (offsets relatifs) - BEAUCOUP plus de variations
        offsets = [
            (0, 0),             # Position originale
            (3*cm, 2*cm),       # Haut-droite (priorité)
            (-3*cm, 2*cm),      # Haut-gauche
            (3*cm, -2*cm),      # Bas-droite
            (-3*cm, -2*cm),     # Bas-gauche
            (5*cm, 0),          # Droite loin
            (-5*cm, 0),         # Gauche loin
            (0, 4*cm),          # Haut loin
            (0, -4*cm),         # Bas loin
            (4*cm, 3*cm),       # Diagonale haut-droite large
            (-4*cm, 3*cm),      # Diagonale haut-gauche large
            (4*cm, -3*cm),      # Diagonale bas-droite large
            (-4*cm, -3*cm),     # Diagonale bas-gauche large
            (2*cm, 4*cm),       # Haut-droite intermédiaire
            (-2*cm, 4*cm),      # Haut-gauche intermédiaire
            (2*cm, -4*cm),      # Bas-droite intermédiaire
            (-2*cm, -4*cm),     # Bas-gauche intermédiaire
            (6*cm, 1*cm),       # Très droite
            (-6*cm, 1*cm),      # Très gauche
            (1*cm, 5*cm),       # Très haut
            (1*cm, -5*cm),      # Très bas
            (5*cm, 4*cm),       # Grande diagonale haut-droite
            (-5*cm, 4*cm),      # Grande diagonale haut-gauche
            (5*cm, -4*cm),      # Grande diagonale bas-droite
        ]
        
        for offset_x, offset_y in offsets[:max_attempts]:
            test_x = initial_x + offset_x
            test_y = initial_y + offset_y
            
            if not self._overlaps_existing(test_x, test_y, width, height):
                # Position trouv├®e sans superposition
                self.used_positions.append({
                    'x': test_x,
                    'y': test_y,
                    'width': width,
                    'height': height
                })
                return test_x, test_y
        
        # Si toutes les positions se superposent, utiliser la position originale avec un d├®calage progressif
        final_x = initial_x + len(self.used_positions) * 0.3*cm
        final_y = initial_y + len(self.used_positions) * 0.3*cm
        
        self.used_positions.append({
            'x': final_x,
            'y': final_y,
            'width': width,
            'height': height
        })
        return final_x, final_y
    
    def _overlaps_existing(self, x, y, width, height):
        """V├®rifie si un rectangle chevauche les positions existantes"""
        for pos in self.used_positions:
            # V├®rification de chevauchement entre deux rectangles
            if not (x + width < pos['x'] or 
                    x > pos['x'] + pos['width'] or
                    y + height < pos['y'] or 
                    y > pos['y'] + pos['height']):
                return True
        return False


class PlanMasseGenerator:
    """G├®n├¿re un plan de masse cadastral avec implantation PV r├®elle"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = A3  # Format A3 pour plus de détails
        self.label_manager = LabelManager()  # Gestionnaire d'étiquettes
        self.computed_scale = 500          # Echelle par défaut
        self.computed_meters_per_cm = 5.0  # 1cm = 5m par défaut

    def _compute_best_scale(self, plan_width_cm, plan_height_cm):
        """Calcule l'échelle optimale en fonction de l'étendue réelle des zones PV.
        Choisit dans les échelles cadastrales standards: 1/500, 1/1000, 1/2000, 1/5000.
        Ajoute une marge de 40% autour du bâtiment pour ne pas le tronquer.
        """
        all_lats, all_lons = [], []
        if self.calpinage and 'zones' in self.calpinage:
            for z in self.calpinage['zones']:
                for coord in z.get('coordinates', []):
                    all_lats.append(coord['lat'])
                    all_lons.append(coord['lng'])
                if not z.get('coordinates'):
                    b = z.get('bounds', {})
                    for k in ('_southWest', '_northEast'):
                        pt = b.get(k, {})
                        if pt.get('lat'):
                            all_lats.append(pt['lat'])
                            all_lons.append(pt['lng'])

        if not all_lats or not all_lons:
            # Pas de zones PV : échelle 1/500 par défaut
            print("[PLAN] ℹ️ Pas de zones PV → échelle 1/500 par défaut")
            return 500

        # Facteurs de conversion GPS→mètres
        lat_c = (min(all_lats) + max(all_lats)) / 2
        gps_conv = None
        if self.calpinage:
            gps_conv = self.calpinage.get('gpsConversion')
            if not gps_conv and self.calpinage.get('zones'):
                gps_conv = self.calpinage['zones'][0].get('gpsConversion')
        if gps_conv and 'metersPerDegreeLat' in gps_conv:
            mpd_lat = gps_conv['metersPerDegreeLat']
            mpd_lng = gps_conv['metersPerDegreeLng']
        else:
            import math as _math
            mpd_lat = 1 / 111320.0
            mpd_lng = 1 / (111320.0 * _math.cos(lat_c * _math.pi / 180))

        # Dimensions réelles du bâtiment en mètres (+ 40% de marge)
        lat_extent_m = (max(all_lats) - min(all_lats)) / mpd_lat * 1.4
        lon_extent_m = (max(all_lons) - min(all_lons)) / mpd_lng * 1.4

        print(f"[PLAN] 📐 Étendue bâtiment: {lon_extent_m:.1f}m × {lat_extent_m:.1f}m (avec marge 40%)")

        # Échelles cadastrales standards (plus précis → moins précis) — max 1/500
        standard_scales = [500, 1000, 2000, 5000]
        for scale in standard_scales:
            mpc = scale / 100.0  # mètres par cm sur le plan
            req_w = lon_extent_m / mpc
            req_h = lat_extent_m / mpc
            if req_w <= plan_width_cm and req_h <= plan_height_cm:
                print(f"[PLAN] ✅ Échelle retenue: 1/{scale} "
                      f"(bâtiment {req_w:.1f}cm × {req_h:.1f}cm dans cadre {plan_width_cm:.1f}cm × {plan_height_cm:.1f}cm)")
                return scale

        # Trop grand pour toutes les échelles : calculer une échelle personnalisée
        import math as _math
        min_mpc = max(lon_extent_m / plan_width_cm, lat_extent_m / plan_height_cm)
        raw_scale = min_mpc * 100
        custom_scale = int(_math.ceil(raw_scale / 500) * 500)
        print(f"[PLAN] ⚠️ Échelle personnalisée: 1/{custom_scale} (bâtiment trop grand pour les échelles standards)")
        return custom_scale

    def generate(self):
        """Génère le plan de masse PDF"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A3)

        # Réinitialiser le gestionnaire d'étiquettes avec centre de l'image
        # Le centre sera défini après calcul de la bbox du plan
        self.label_manager = None

        # ─── Calcul de l'échelle optimale AVANT le dessin ───
        _plan_w = self.width - 4*cm
        _plan_h = self.height - 18*cm
        self.computed_scale = self._compute_best_scale(_plan_w / cm, _plan_h / cm)
        self.computed_meters_per_cm = self.computed_scale / 100.0
        print(f"[PLAN] 🔍 Échelle sélectionnée: 1/{self.computed_scale} ("
              f"{self.computed_meters_per_cm:.2f} m/cm)")

        # En-tête
        self._draw_header(c)
        
        # Zone principale : plan cadastral + calpinage
        self._draw_plan_cadastral(c)
        
        # L├®gende et informations
        self._draw_legend(c)
        
        # Cartouche technique
        self._draw_cartouche(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_header(self, c):
        """En-t├¬te du document"""
        y = self.height - 2*cm
        
        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawString(3*cm, y, "PLAN DE MASSE - INSTALLATION PHOTOVOLTAIQUE")
        
        y -= 0.7*cm
        c.setFont("Helvetica", 10)
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"{adresse}, {commune}")
        
        # Echelle réelle (calculée dynamiquement selon la taille du bâtiment)
        scale_label = f"Echelle 1/{self.computed_scale:,}".replace(',', ' ')
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.drawRightString(self.width - 3*cm, y, scale_label)
        c.setFillColor(colors.black)
        
    def _draw_plan_cadastral(self, c):
        """Dessine le plan cadastral avec parcelles et modules PV"""
        
        # Zone de dessin - Optimis├®e pour ├®viter chevauchements avec l├®gende et cartouche
        plan_x = 2*cm
        plan_y = 15*cm  # Plus haut pour laisser place ├á la l├®gende
        plan_width = self.width - 4*cm
        plan_height = self.height - 18*cm  # Hauteur ajust├®e
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(plan_x, plan_y, plan_width, plan_height)
        
        # Fond
        c.setFillColor(colors.HexColor('#F5F5F5'))
        c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')

        # ═══════════════════════════════════════════════════════════════════╗
        # CORRECTION DÉCALAGE : centrer sur les zones PV réelles             ║
        # lat/lon du prospect = adresse géocodée, peut être à 50–300m        ║
        # de la toiture réelle → gps_bounds serait décalé → modules décalés  ║
        # ═══════════════════════════════════════════════════════════════════╝
        if self.calpinage and 'zones' in self.calpinage and self.calpinage['zones']:
            all_lats, all_lons = [], []
            for z in self.calpinage['zones']:
                for coord in z.get('coordinates', []):
                    all_lats.append(coord['lat'])
                    all_lons.append(coord['lng'])
                # aussi regarder bounds si coordinates vides
                if not z.get('coordinates'):
                    b = z.get('bounds', {})
                    if b:
                        for k in ('_southWest', '_northEast'):
                            pt = b.get(k, {})
                            if pt.get('lat'):
                                all_lats.append(pt['lat'])
                                all_lons.append(pt['lng'])
            if all_lats and all_lons:
                lat_zones = (min(all_lats) + max(all_lats)) / 2
                lon_zones = (min(all_lons) + max(all_lons)) / 2
                print(f"[PLAN] 🎯 Centre recalé sur zones PV: ({lat_zones:.6f}, {lon_zones:.6f})"
                      f" — adresse: ({lat:.6f}, {lon:.6f})"
                      f" — écart: {abs(lat_zones-lat)*111320:.0f}m lat / {abs(lon_zones-lon)*111320*0.7:.0f}m lon")
                lat, lon = lat_zones, lon_zones
        
        print(f"[PLAN] ­ƒôî D├®marrage _draw_plan_cadastral: lat={lat}, lon={lon}")
        
        # Initialiser screenshot_used
        self.screenshot_used = False
        
        # ­ƒöÑ CORRECTION GPS: Utiliser syst├®matiquement les facteurs de conversion pr├®cis
        # sauvegard├®s dans le calpinage (issus de map.distance() de Leaflet)
        gps_conversion = None
        if self.calpinage:
            gps_conversion = self.calpinage.get('gpsConversion')
            # Fallback: chercher dans la première zone si non présent au niveau racine
            if not gps_conversion and 'zones' in self.calpinage and self.calpinage['zones']:
                gps_conversion = self.calpinage['zones'][0].get('gpsConversion')
                if gps_conversion:
                    print(f"[PLAN] ℹ️ gpsConversion récupéré depuis la zone 1 (fallback)")
        
        if gps_conversion and 'metersPerDegreeLat' in gps_conversion and 'metersPerDegreeLng' in gps_conversion:
            # Utiliser les facteurs de conversion PR├ëCIS du calpinage
            meters_per_degree_lat = gps_conversion['metersPerDegreeLat']
            meters_per_degree_lng = gps_conversion['metersPerDegreeLng']
            print(f"[PLAN] Ô£à Utilisation des facteurs GPS pr├®cis: lat={1/meters_per_degree_lat:.9f}┬░/m, lng={1/meters_per_degree_lng:.9f}┬░/m")
        else:
            # Fallback: approximation bas├®e sur la latitude (moins pr├®cis)
            import math
            lat_rad = lat * math.pi / 180 if lat else 0.785398  # 45┬░ par d├®faut
            meters_per_degree_lat = 1 / 111320  # Plus pr├®cis que 111000
            meters_per_degree_lng = 1 / (111320 * math.cos(lat_rad))
            print(f"[PLAN] ÔÜá´©Å Facteurs GPS approximatifs (gpsConversion manquant)")
        
        # Échelle adaptée dynamiquement (calculée dans generate())
        mpc = self.computed_meters_per_cm  # mètres par cm sur le plan
        plan_width_cm = plan_width / cm
        plan_height_cm = plan_height / cm

        bbox_width_meters = plan_width_cm * mpc
        bbox_height_meters = plan_height_cm * mpc

        print(f"[PLAN] Échelle 1/{self.computed_scale}: Cadre {plan_width_cm:.1f}x{plan_height_cm:.1f}cm = {bbox_width_meters:.0f}x{bbox_height_meters:.0f}m réels")
        
        # Convertir en degr├®s avec les BONS facteurs - DIMENSIONS EXACTES pour 1/500
        # Demi-dimensions (rayon) pour centrer autour du point GPS
        meters_to_lat = (bbox_height_meters / 2) * meters_per_degree_lat
        meters_to_lon = (bbox_width_meters / 2) * meters_per_degree_lng
        
        # Stocker les limites GPS r├®elles - EXACTES pour ├®chelle 1/500
        self.gps_bounds = {
            'min_lat': lat - meters_to_lat,
            'max_lat': lat + meters_to_lat,
            'min_lon': lon - meters_to_lon,
            'max_lon': lon + meters_to_lon
        }
        
        # Stocker les facteurs de conversion pour r├®utilisation dans _fetch_satellite_image_rect
        self.gps_conversion_factors = {
            'meters_per_degree_lat': meters_per_degree_lat,
            'meters_per_degree_lng': meters_per_degree_lng
        }
        
        if lat and lon:
            # ­ƒöÑ PRIORIT├ë 1: Utiliser le screenshot de la carte si disponible
            screenshot_data = None  # Force désactivation screenshot (éviter doublon modules)
            
            if False:  # Screenshot désactivé
                try:
                    # Le screenshot est en base64 data URL: "data:image/png;base64,..."
                    import base64
                    import re
                    
                    # Extraire les donn├®es base64
                    base64_match = re.search(r'base64,(.+)', screenshot_data)
                    if base64_match:
                        base64_str = base64_match.group(1)
                        img_data = base64.b64decode(base64_str)
                        img_buffer = io.BytesIO(img_data)
                        
                        print(f"[PLAN] ­ƒô© Utilisation du screenshot de la carte ({len(img_data)} bytes)")
                        
                        # R├®cup├®rer les m├®tadonn├®es de la carte pour calibrer GPSÔåÆPDF
                        map_metadata = self.calpinage.get('map_metadata', {})
                        if map_metadata and 'bounds' in map_metadata:
                            bounds = map_metadata['bounds']
                            dimensions = map_metadata.get('dimensions', {})
                            
# ­ƒöÑ Comme on dessine avec preserveAspectRatio=False,
                            # l'image remplit TOUT le cadre, donc pas besoin de calculer actual_image_bbox
                            # Les bounds GPS correspondent au cadre PDF complet
                            
                            self.gps_bounds = {
                                'min_lat': bounds['south'],
                                'max_lat': bounds['north'],
                                'min_lon': bounds['west'],
                                'max_lon': bounds['east']
                            }
                            print(f"[PLAN] ­ƒù║´©Å Bounds GPS screenshot (cadre complet): lat[{bounds['south']:.6f}, {bounds['north']:.6f}] lon[{bounds['west']:.6f}, {bounds['east']:.6f}]")
                        
                        # Dessiner le screenshot - REMPLIR TOUT LE CADRE
                        c.drawImage(ImageReader(img_buffer), 
                                  plan_x, plan_y, 
                                  width=plan_width, height=plan_height,
                                  preserveAspectRatio=False, mask='auto')  # False = remplit tout
                        
                        self.screenshot_used = True
                    else:
                        self.screenshot_used = False
                except Exception as e:
                    print(f"[PLAN] ÔÜá´©Å Erreur lecture screenshot: {e}")
                    self.screenshot_used = False
            else:
                self.screenshot_used = False
            
            # 🔑 FALLBACK: Image satellite si pas de screenshot
            if not self.screenshot_used:
                print(f"[PLAN] 🔙 Tentative téléchargement image satellite...")
                print(f"[PLAN]   GPS: lat={lat}, lon={lon}")
                print(f"[PLAN]   Dimensions plan: {bbox_width_meters:.0f}x{bbox_height_meters:.0f}m (échelle 1/{self.computed_scale})")
                
                # 🔑 CORRECTION: Utiliser les dimensions EXACTES du plan (pas de bbox élargie)
                # L'élargissement causait un décalage d'échelle entre l'image satellite et les modules PV
                # L'API IGN Géoplateforme WMS accepte toutes les tailles de bbox
                satellite_width = bbox_width_meters
                satellite_height = bbox_height_meters
                
                satellite_img = self._fetch_satellite_image_rect(lat, lon, satellite_width, satellite_height, width=800, height=600)
                if satellite_img:
                    # REMPLIR TOUT LE CADRE (pas de blanc autour)
                    c.drawImage(ImageReader(satellite_img), 
                              plan_x, plan_y, 
                              width=plan_width, height=plan_height,
                              preserveAspectRatio=False, mask='auto')  # False = remplit tout
                    print(f"[PLAN] ✅ Image satellite affichée (recadrée à l'échelle 1/{self.computed_scale})")
                else:
                    print(f"[PLAN] ÔØî ERREUR: Image satellite = None, pas d'image charg├®e !")
                self.screenshot_used = False  # Image satellite, pas de screenshot
        
        # Syst├¿me de coordonn├®es : conversion GPS ÔåÆ PDF
        # Centre du plan = position GPS du b├ótiment
        self.plan_bbox = {
            'x': plan_x,
            'y': plan_y,
            'width': plan_width,
            'height': plan_height,
            'lat_center': lat,
            'lon_center': lon,
            'meters_per_cm': self.computed_meters_per_cm  # Échelle adaptée dynamiquement
        }

        # ── Barre d'échelle graphique (en bas à droite du cadre plan) ──
        self._draw_scale_bar(c, plan_x, plan_y, plan_width)
        
        # Initialiser le LabelManager avec le centre du plan
        center_x = plan_x + plan_width / 2
        center_y = plan_y + plan_height / 2
        self.label_manager = LabelManager(center_x, center_y)
        
        # NOUVEAU: Pré-enregistrer les zones PV dans le LabelManager AVANT les parcelles
        # pour éviter que les étiquettes de parcelles se superposent aux zones PV
        if self.calpinage and 'zones' in self.calpinage:
            self._register_pv_zones_in_label_manager()
        
        # 1. PARCELLES CADASTRALES (avec vraies g├®om├®tries si disponibles)
        self._draw_parcelles(c, self.plan_bbox['x'] + self.plan_bbox['width']/2, self.plan_bbox['y'] + self.plan_bbox['height']/2, lat, lon)
        
        # 2. B├éTIMENT (├á la position GPS) - D├ëSACTIV├ë pour plan de masse simple
        # self._draw_batiment(c, self.plan_bbox['x'] + self.plan_bbox['width']/2, self.plan_bbox['y'] + self.plan_bbox['height']/2)
        
        # 3. MODULES PV - TOUJOURS dessiner avec coordonn├®es GPS pr├®cises
        # ­ƒöÑ CORRECTION: Le screenshot contient les modules MAL PLAC├ëS (ancienne position)
        # On dessine TOUJOURS avec Python qui a les coordonn├®es GPS CORRIG├ëES
        if self.calpinage:
            self._draw_modules_pv_from_gps(c)
            if self.screenshot_used:
                print("[PLAN] ÔÜá´©Å Screenshot utilis├® mais modules redessin├®s avec GPS corrig├®s (├®crasent l'ancienne position)")
        
        # 4. COTATIONS - Dessiner les cotations sur les zones PV
        if self.calpinage and 'zones' in self.calpinage:
            self._draw_cotations_zones(c)
        
        # 5. ROSE DES VENTS - OBLIGATOIRE pour plan cadastral
        self._draw_compass(c, plan_x, plan_y, plan_width, plan_height)
        
    def _draw_scale_bar(self, c, plan_x, plan_y, plan_width):
        """Dessine une barre d'échelle graphique en bas à droite du cadre plan."""
        mpc = self.computed_meters_per_cm
        scale = self.computed_scale

        # Choisir une longueur de barre «propre» (multiple rond de mètres)
        # On veut la barre ≈ 4 cm sur le plan
        target_cm = 4.0
        target_meters = target_cm * mpc  # mètres réels représentés par 4 cm
        # Arrondir au chiffre «propre» le plus proche
        magnitudes = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]
        bar_meters = min(magnitudes, key=lambda v: abs(v - target_meters))
        bar_cm_pdf = (bar_meters / mpc) * cm  # taille en points PDF

        # Position : coin inférieur droit du cadre plan, avec marge
        bar_x = plan_x + plan_width - bar_cm_pdf - 0.5*cm
        bar_y = plan_y + 0.4*cm
        bar_h = 0.25*cm

        # Rectangle de fond blanc
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(bar_x - 0.1*cm, bar_y - 0.05*cm,
               bar_cm_pdf + 0.2*cm, bar_h + 0.5*cm, fill=1, stroke=0)

        # Segments alternés noir/blanc
        nb_seg = 4
        seg_w = bar_cm_pdf / nb_seg
        for i in range(nb_seg):
            c.setFillColor(colors.black if i % 2 == 0 else colors.white)
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.rect(bar_x + i * seg_w, bar_y, seg_w, bar_h, fill=1, stroke=1)

        # Étiquettes de la barre
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.black)
        # 0 m
        c.drawCentredString(bar_x, bar_y - 0.25*cm, "0")
        # Demi
        c.drawCentredString(bar_x + bar_cm_pdf / 2, bar_y - 0.25*cm,
                            f"{bar_meters // 2}m")
        # Total
        c.drawCentredString(bar_x + bar_cm_pdf, bar_y - 0.25*cm,
                            f"{bar_meters}m")

        # Texte échelle
        c.setFont("Helvetica-Bold", 7)
        scale_str = f"1/{scale:,}".replace(',', ' ')
        c.drawCentredString(bar_x + bar_cm_pdf / 2, bar_y + bar_h + 0.15*cm, scale_str)

    def _draw_compass(self, c, plan_x, plan_y, plan_width, plan_height):
        """Dessine la rose des vents (Nord/Sud/Est/Ouest) - OBLIGATOIRE"""
        # Position : coin sup├®rieur gauche du plan
        compass_x = plan_x + 1*cm
        compass_y = plan_y + plan_height - 3*cm
        compass_size = 2*cm
        
        # Fond blanc
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.circle(compass_x, compass_y, compass_size/2, fill=1, stroke=1)
        
        # Fl├¿che Nord (rouge)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(2)
        
        # Ligne Nord
        north_y = compass_y + compass_size/2 - 0.2*cm
        c.line(compass_x, compass_y, compass_x, north_y)
        
        # Triangle Nord
        path = c.beginPath()
        path.moveTo(compass_x, north_y)
        path.lineTo(compass_x - 0.25*cm, north_y - 0.4*cm)
        path.lineTo(compass_x + 0.25*cm, north_y - 0.4*cm)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        
        # Texte Nord
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(compass_x, north_y + 0.15*cm, "N")
        
        # Sud (gris)
        c.setStrokeColor(colors.HexColor('#757575'))
        c.setFillColor(colors.HexColor('#757575'))
        c.setLineWidth(1.5)
        south_y = compass_y - compass_size/2 + 0.2*cm
        c.line(compass_x, compass_y, compass_x, south_y)
        c.setFont("Helvetica", 9)
        c.drawCentredString(compass_x, south_y - 0.35*cm, "S")
        
        # Est
        east_x = compass_x + compass_size/2 - 0.2*cm
        c.line(compass_x, compass_y, east_x, compass_y)
        c.drawCentredString(east_x + 0.3*cm, compass_y - 0.15*cm, "E")
        
        # Ouest
        west_x = compass_x - compass_size/2 + 0.2*cm
        c.line(compass_x, compass_y, west_x, compass_y)
        c.drawCentredString(west_x - 0.3*cm, compass_y - 0.15*cm, "O")
        
    def _calculate_bbox_from_data(self):
        """Calcule la taille de la bbox en m├¿tres bas├®e sur les donn├®es"""
        # Estimer depuis les parcelles ou d├®faut 60m
        parcelles = self._extract_parcelles()
        if parcelles:
            total_surface = sum(float(p.get('surface', 0)) for p in parcelles)
            if total_surface > 0:
                # Approximation: bbox = racine(surface) * 1.5 pour avoir de la marge
                return (total_surface ** 0.5) * 1.5
        
        # D├®faut: 60m de rayon (120m de c├┤t├®)
        return 60
    
    def _lat_lon_to_pdf(self, lat, lon):
        """
        Convertit coordonn├®es GPS en coordonn├®es PDF
        Utilise les M├èMES limites GPS que l'image satellite pour assurer l'alignement
        """
        if not hasattr(self, 'gps_bounds'):
            return (0, 0)
        
        # ­ƒöÑ Utiliser plan_bbox car l'image remplit TOUT le cadre (preserveAspectRatio=False)
        if hasattr(self, 'plan_bbox'):
            bbox = self.plan_bbox
        else:
            return (0, 0)
        
        gps = self.gps_bounds
        
        # ­ƒöÑ CORRECTION: Conversion GPS ÔåÆ PDF bas├®e sur les limites GPS r├®elles de l'image
        # Normaliser lat/lon dans l'intervalle [0, 1] par rapport aux limites
        lat_range = gps['max_lat'] - gps['min_lat']
        lon_range = gps['max_lon'] - gps['min_lon']
        
        if lat_range == 0 or lon_range == 0:
            return (bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2)
        
        lat_ratio = (lat - gps['min_lat']) / lat_range
        lon_ratio = (lon - gps['min_lon']) / lon_range
        
        # Convertir en coordonn├®es PDF
        # ÔÜá´©Å Attention: PDF Y augmente vers le haut, mais latitude aussi
        pdf_x = bbox['x'] + lon_ratio * bbox['width']
        pdf_y = bbox['y'] + lat_ratio * bbox['height']
        
        return (pdf_x, pdf_y)
    
    def _draw_parcelles(self, c, center_x, center_y, lat, lon):
        """Dessine les parcelles avec leurs vraies g├®om├®tries GeoJSON si disponibles"""
        parcelles = self._extract_parcelles()
        
        if not parcelles:
            print("[PLAN] ÔÜá´©Å Aucune parcelle ├á dessiner")
            return
        
        print(f"[PLAN] ­ƒÅÿ´©Å Dessin de {len(parcelles)} parcelles...")
        print(f"[PLAN] DEBUG plan_bbox: x={self.plan_bbox.get('x', 0):.1f}, y={self.plan_bbox.get('y', 0):.1f}, width={self.plan_bbox.get('width', 0):.1f}, height={self.plan_bbox.get('height', 0):.1f}")
        print(f"[PLAN] DEBUG gps_bounds: lat[{self.gps_bounds.get('min_lat', 0):.6f}, {self.gps_bounds.get('max_lat', 0):.6f}], lon[{self.gps_bounds.get('min_lon', 0):.6f}, {self.gps_bounds.get('max_lon', 0):.6f}]")
        
        # ­ƒöÑ SAUVEGARDER l'├®tat du canvas avant le clipping
        c.saveState()
        
        # Ajouter un clipPath pour limiter le dessin au cadre
        if hasattr(self, 'plan_bbox'):
            bbox = self.plan_bbox
            clip_path = c.beginPath()
            clip_path.rect(bbox['x'], bbox['y'], bbox['width'], bbox['height'])
            c.clipPath(clip_path, stroke=0, fill=0)
        
        for i, parcelle in enumerate(parcelles):
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson') or parcelle.get('geometry')
            
            print(f"[PLAN] Parcelle {section}{numero}: geojson={'OUI' if geojson else 'NON'}, surface={surface}")
            print(f"[PLAN] DEBUG parcelle keys: {list(parcelle.keys())}")
            if geojson:
                print(f"[PLAN] DEBUG geojson type: {type(geojson)}, keys: {list(geojson.keys()) if isinstance(geojson, dict) else 'N/A'}")
            
            # Si g├®om├®trie GeoJSON disponible, l'utiliser
            if geojson and isinstance(geojson, dict):
                print(f"[PLAN] ÔåÆ Dessin avec GeoJSON")
                self._draw_parcelle_from_geojson(c, geojson, section, numero, surface)
            else:
                # Fallback: rectangle approximatif centr├® TR├êS VISIBLE
                print(f"[PLAN] ÔåÆ Dessin approximatif (pas de GeoJSON)")
                self._draw_parcelle_approximative(c, section, numero, surface, i, len(parcelles))
        
        # ­ƒöÑ RESTAURER l'├®tat du canvas pour ne pas affecter la l├®gende et le cartouche
        c.restoreState()
    
    def _draw_parcelle_from_geojson(self, c, geojson, section, numero, surface):
        """Dessine une parcelle depuis sa g├®om├®trie GeoJSON r├®elle"""
        try:
            geometry = geojson.get('geometry', geojson)
            coords = geometry.get('coordinates', [])
            geom_type = geometry.get('type', '')
            
            print(f"[PLAN] ­ƒÄ¿ Dessin parcelle {section}{numero} avec g├®om├®trie {geom_type}")
            
            # Calculer surface depuis g├®om├®trie si surface==0
            if not surface or float(surface) == 0:
                try:
                    from shapely.geometry import shape
                    shp = shape(geometry)
                    # Transformer en L93 pour calcul pr├®cis de surface
                    from pyproj import Transformer
                    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
                    from shapely.ops import transform as shp_transform
                    shp_l93 = shp_transform(to_l93.transform, shp)
                    surface = int(shp_l93.area)  # m┬▓
                    print(f"[PLAN] ­ƒôÉ Surface calcul├®e pour {section}{numero}: {surface}m┬▓")
                except Exception as e:
                    print(f"[PLAN] ÔÜá´©Å Calcul surface impossible: {e}")
                    surface = 0
            
            # Gestion Polygon et MultiPolygon
            polygons_to_draw = []
            
            if geom_type == 'Polygon' and coords:
                polygons_to_draw.append(coords[0])  # Premier anneau (contour ext├®rieur)
            elif geom_type == 'MultiPolygon' and coords:
                # Dessiner tous les polygones du MultiPolygon
                for polygon in coords:
                    if polygon and len(polygon) > 0:
                        polygons_to_draw.append(polygon[0])
            
            if not polygons_to_draw:
                print(f"[PLAN] ÔØî Pas de polygone ├á dessiner pour {section}{numero}")
                return
            
            print(f"[PLAN] ­ƒôì {len(polygons_to_draw)} polygone(s) ├á dessiner")
            
            # Dessiner chaque polygone
            label_x, label_y = None, None
            
            for polygon_idx, exterior_ring in enumerate(polygons_to_draw):
                # Convertir chaque point GPS ÔåÆ PDF
                path = c.beginPath()
                first_point = True
                points_converted = 0
                
                for coord in exterior_ring:
                    lon, lat = coord[0], coord[1]
                    pdf_x, pdf_y = self._lat_lon_to_pdf(lat, lon)
                    
                    if first_point:
                        path.moveTo(pdf_x, pdf_y)
                        first_point = False
                        if label_x is None:  # Position ├®tiquette sur le premier polygone
                            label_x, label_y = pdf_x, pdf_y
                        print(f"[PLAN] DEBUG premier point: GPS({lat:.6f}, {lon:.6f}) → PDF({pdf_x:.1f}, {pdf_y:.1f})")
                        points_converted += 1
                    else:
                        path.lineTo(pdf_x, pdf_y)
                        points_converted += 1
                
                path.close()
                print(f"[PLAN]   Polygone #{polygon_idx+1}: {points_converted} points convertis")
                
                # CONTOUR PARCELLE TR├êS VISIBLE
                # 1. Fond jaune semi-transparent pour voir la parcelle
                c.setFillColorRGB(1, 1, 0, 0.15)  # Jaune transparent 15%
                c.setStrokeColor(colors.HexColor('#FF0000'))  # Rouge vif
                c.setLineWidth(2.5)  # Trait ├®pais
                c.drawPath(path, stroke=1, fill=1)
                
                # 2. Bordure en pointill├®s noirs pour contraste
                c.setStrokeColor(colors.black)
                c.setLineWidth(1)
                c.setDash(6, 3)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()  # R├®initialiser
            
            # ├ëtiquette VISIBLE avec fond blanc - POSITIONNEMENT EXT├ëRIEUR ANTI-SUPERPOSITION
            if label_x is not None and label_y is not None:
                # Dimensions de l'├®tiquette
                text_w = 3*cm  # Légèrement plus large
                text_h = 0.9*cm  # Légèrement plus haute
                
                # Placer l'étiquette à l'extérieur (au-dessus et à droite de la parcelle)
                # Augmenter les offsets initiaux pour éviter le centre
                offset_x = 4*cm  # Décalage horizontal vers la droite (augmenté)
                offset_y = 3*cm  # Décalage vertical vers le haut (augmenté)
                initial_x = label_x + offset_x
                initial_y = label_y + offset_y
                
                # Trouver une position non superpos├®e avec l'algorithme amélioré
                final_x, final_y = self.label_manager.find_non_overlapping_position(
                    initial_x, initial_y, text_w, text_h
                )
                
                # Ligne de repère VISIBLE pour relier l'étiquette à la parcelle
                # Ligne avec point de départ à la bordure de l'étiquette (pas au centre)
                c.setStrokeColor(colors.HexColor('#000000'))  # Noir pour meilleure visibilité
                c.setLineWidth(1.2)  # Plus épaisse
                c.setDash(4, 3)  # Tirets plus visibles
                
                # Calculer le point de connexion sur le bord de l'étiquette le plus proche du point d'origine
                label_center_x = final_x + text_w / 2
                label_center_y = final_y + text_h / 2
                
                # Point de connexion sur le bord de l'étiquette
                if label_x < label_center_x:
                    connect_x = final_x  # Bord gauche
                else:
                    connect_x = final_x + text_w  # Bord droit
                    
                if label_y < label_center_y:
                    connect_y = final_y  # Bord bas
                else:
                    connect_y = final_y + text_h  # Bord haut
                
                # Ligne de repère du point de la parcelle au bord de l'étiquette
                c.line(label_x, label_y, connect_x, connect_y)
                
                # Petit cercle au point d'origine pour marquer la position sur la parcelle
                c.setFillColor(colors.HexColor('#FF0000'))
                c.circle(label_x, label_y, 0.12*cm, fill=1, stroke=0)
                
                c.setDash()  # Réinitialiser
                
                # Fond blanc opaque
                c.setFillColor(colors.white)
                c.setStrokeColor(colors.HexColor('#FF0000'))
                c.setLineWidth(1.5)
                
                # Rectangle de fond
                c.rect(final_x + 0.1*cm, final_y + 0.1*cm, text_w, text_h, fill=1, stroke=1)
                
                # Texte en gras et visible
                c.setFillColor(colors.HexColor('#FF0000'))
                c.setFont("Helvetica-Bold", 9)
                c.drawString(final_x + 0.2*cm, final_y + 0.5*cm, 
                            f"Parcelle {section} {numero}")
                
                # Surface en dessous
                if surface and float(surface) > 0:
                    c.setFont("Helvetica", 7)
                    c.setFillColor(colors.black)
                    # Utiliser decode pour assurer l'encodage UTF-8
                    surface_text = f"Surface: {int(float(surface))} m2"
                    c.drawString(final_x + 0.2*cm, final_y + 0.25*cm, surface_text)
            
            print(f"[PLAN] Ô£à Parcelle {section}{numero} dessin├®e avec succ├¿s")
            return
            
        except Exception as e:
            print(f"[PLAN] ÔØî Erreur dessin parcelle GeoJSON {section}{numero}: {e}")
            import traceback
            traceback.print_exc()
            pass
    
    def _draw_parcelle_approximative(self, c, section, numero, surface, index, total):
        """Dessine une parcelle approximative (rectangle)"""
        if not hasattr(self, 'plan_bbox'):
            return
            
        bbox = self.plan_bbox
        center_x = bbox['x'] + bbox['width'] / 2
        center_y = bbox['y'] + bbox['height'] / 2
        
        # Estimer dimensions
        try:
            surface_m2 = float(surface)
            largeur = (surface_m2 / 1.5) ** 0.5
            longueur = largeur * 1.5
        except:
            largeur = 30
            longueur = 45
        
        # ├ëchelle
        meters_per_cm = bbox['meters_per_cm']
        parc_w = (longueur / meters_per_cm) * cm
        parc_h = (largeur / meters_per_cm) * cm
        
        # D├®calage si plusieurs parcelles
        offset_x = (index - total/2) * 5 * cm
        
        parc_x = center_x - parc_w/2 + offset_x
        parc_y = center_y - parc_h/2
        
        # Contour VISIBLE mais pas trop ├®pais
        c.setStrokeColor(colors.HexColor('#FF00FF'))  # Magenta
        c.setLineWidth(3)  # Ligne normale
        c.setDash(10, 5)  # Pointill├®s
        c.rect(parc_x, parc_y, parc_w, parc_h, fill=0, stroke=1)
        c.setDash()
        
        # ├ëtiquette à l'extérieur de la parcelle - POSITIONNEMENT EXT├ëRIEUR
        label_bg_w = 2.5*cm
        label_bg_h = 0.6*cm
        
        # Placer l'étiquette à l'extérieur (au-dessus et à droite de la parcelle)
        offset_x = 3*cm  # Décalage horizontal vers la droite
        offset_y = 2*cm  # Décalage vertical vers le haut
        initial_x = parc_x + offset_x
        initial_y = parc_y + offset_y
        
        # Trouver une position non superpos├®e
        final_parc_x, final_parc_y = self.label_manager.find_non_overlapping_position(
            initial_x, initial_y, label_bg_w, label_bg_h
        )
        
        # Ligne de repère TOUJOURS affichée pour relier l'étiquette à la parcelle
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(0.8)
        c.setDash(3, 2)  # Tirets courts
        # Ligne du coin de la parcelle au centre de l'étiquette
        label_center_x = final_parc_x + label_bg_w / 2
        label_center_y = final_parc_y + label_bg_h / 2
        c.line(parc_x, parc_y, label_center_x, label_center_y)
        c.setDash()  # Réinitialiser
        
        c.setFillColorRGB(1, 1, 1, 0.8)  # Blanc semi-transparent
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(1)
        c.rect(final_parc_x + 0.1*cm, final_parc_y + 0.1*cm, label_bg_w, label_bg_h, fill=1, stroke=1)
        
        # ├ëtiquette texte compact
        c.setFillColor(colors.HexColor('#FF00FF'))
        c.setFont("Helvetica-Bold", 7)
        c.drawString(final_parc_x + 0.2*cm, final_parc_y + 0.35*cm, 
                    f"{section}{numero}")
        if surface and float(surface) > 0:
            c.setFont("Helvetica", 6)
            c.drawString(final_parc_x + 0.2*cm, final_parc_y + 0.15*cm, 
                        f"{int(float(surface))}m2")
    
    def _draw_batiment(self, c, center_x, center_y):
        """Dessine le b├ótiment"""
        echelle = 0.3  # cm par m├¿tre
        
        # Dimensions avec conversion s├®curis├®e
        try:
            longueur = float(self.data.get('longueur_batiment_m', 15))
            largeur = float(self.data.get('largeur_batiment_m', 10))
        except (ValueError, TypeError):
            longueur = 15
            largeur = 10
        
        bat_w = longueur * echelle * cm
        bat_h = largeur * echelle * cm
        
        bat_x = center_x - bat_w/2
        bat_y = center_y - bat_h/2
        
        # Rectangle b├ótiment
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.HexColor('#FFE4B5'))  # Beige
        c.setLineWidth(2)
        c.rect(bat_x, bat_y, bat_w, bat_h, fill=1, stroke=1)
        
        # Etiquette
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(center_x, center_y, "BATIMENT")
    
    def _draw_modules_pv_reels(self, c, center_x, center_y, lat, lon):
        """DEPRECATED - Utiliser _draw_modules_pv_from_gps ├á la place"""
        pass
    
    def _register_pv_zones_in_label_manager(self):
        """Pré-enregistre les zones PV dans le LabelManager pour éviter superpositions avec étiquettes parcelles"""
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        zones = self.calpinage['zones']
        
        for zone in zones:
            zone_coords = zone.get('coordinates', [])
            if not zone_coords or len(zone_coords) < 4:
                continue
            
            # Convertir les coordonnées GPS en PDF pour obtenir la bbox de la zone
            pdf_coords = []
            for coord in zone_coords:
                pdf_x, pdf_y = self._lat_lon_to_pdf(coord['lat'], coord['lng'])
                pdf_coords.append((pdf_x, pdf_y))
            
            if len(pdf_coords) < 4:
                continue
            
            # Calculer la bounding box de la zone PV
            min_x = min(p[0] for p in pdf_coords)
            max_x = max(p[0] for p in pdf_coords)
            min_y = min(p[1] for p in pdf_coords)
            max_y = max(p[1] for p in pdf_coords)
            
            zone_width = max_x - min_x
            zone_height = max_y - min_y
            
            # Enregistrer la zone dans le LabelManager avec une marge de sécurité
            margin = 1*cm  # Marge autour de la zone PV
            self.label_manager.used_positions.append({
                'x': min_x - margin,
                'y': min_y - margin,
                'width': zone_width + 2*margin,
                'height': zone_height + 2*margin
            })
            
            # Enregistrer aussi l'espace pour l'étiquette de zone (estimé)
            zone_label_w = 5*cm
            zone_label_h = 0.6*cm
            label_x, label_y = pdf_coords[0]  # Position approximative
            self.label_manager.used_positions.append({
                'x': label_x,
                'y': label_y,
                'width': zone_label_w,
                'height': zone_label_h
            })
            
            print(f"[PLAN] 🔒 Zone PV enregistrée dans LabelManager: {zone_width/cm:.1f}x{zone_height/cm:.1f}cm")
    
    def _draw_modules_pv_from_gps(self, c):
        """Dessine les modules PV selon leurs VRAIES coordonn├®es GPS sauvegard├®es"""
        
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        zones = self.calpinage['zones']
        
        for zone in zones:
            # R├®cup├®rer les positions GPS de chaque module
            modules_positions = zone.get('modulesPositions', [])
            
            if not modules_positions:
                print(f"[PLAN] ÔÜá´©Å Aucune position GPS pour zone {zone.get('numero', '?')}")
                continue
            
            print(f"[PLAN] 📌 Dessin {len(modules_positions)} modules avec coordonnées GPS pour zone {zone.get('numero', '?')}")
            
            # 🔑 Dessiner chaque module INDIVIDUELLEMENT avec bordure visible
            # Étape 1: Remplissage semi-transparent de chaque module
            c.saveState()
            c.setFillColor(colors.HexColor('#1565C0'))  # Bleu foncé
            c.setFillAlpha(0.35)  # Semi-transparent pour voir le satellite en dessous
            c.setStrokeColor(colors.HexColor('#0D47A1'))  # Bordure bleu très foncé
            c.setStrokeAlpha(0.9)
            c.setLineWidth(0.5)
            
            for module in modules_positions:
                corners = module.get('corners', [])
                
                if len(corners) < 4:
                    continue
                
                # Convertir les 4 coins GPS → coordonnées PDF
                path = c.beginPath()
                first = True
                
                for corner in corners:
                    pdf_x, pdf_y = self._lat_lon_to_pdf(corner['lat'], corner['lng'])
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                c.drawPath(path, stroke=0, fill=1)
            
            c.restoreState()
            
            # Étape 2: Dessiner les bordures de chaque module PAR-DESSUS
            # (séparé du fill pour que les bordures soient toujours visibles)
            c.saveState()
            c.setStrokeColor(colors.HexColor('#0D47A1'))
            c.setLineWidth(0.6)
            
            for module in modules_positions:
                corners = module.get('corners', [])
                
                if len(corners) < 4:
                    continue
                
                path = c.beginPath()
                first = True
                
                for corner in corners:
                    pdf_x, pdf_y = self._lat_lon_to_pdf(corner['lat'], corner['lng'])
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                c.drawPath(path, stroke=1, fill=0)
            
            c.restoreState()
    
    def _draw_cotations_zones(self, c):
        """Dessine les cotations (largeur et longueur) sur chaque zone PV"""
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        zones = self.calpinage['zones']
        
        for zone in zones:
            zone_coords = zone.get('coordinates', [])
            if not zone_coords or len(zone_coords) < 4:
                continue
            
            # Convertir les coordonn├®es GPS en PDF
            pdf_coords = []
            for coord in zone_coords:
                pdf_x, pdf_y = self._lat_lon_to_pdf(coord['lat'], coord['lng'])
                pdf_coords.append((pdf_x, pdf_y))
            
            if len(pdf_coords) < 4:
                continue
            
            # Calculer les dimensions r├®elles
            largeur_m = zone.get('largeurMetres', 0)
            longueur_m = zone.get('longueurMetres', 0)
            
            if largeur_m == 0 or longueur_m == 0:
                continue
            
            # Points de la zone (rectangle)
            p1, p2, p3, p4 = pdf_coords[0], pdf_coords[1], pdf_coords[2], pdf_coords[3]
            
            # Style cotations
            c.setStrokeColor(colors.HexColor('#D32F2F'))
            c.setFillColor(colors.HexColor('#D32F2F'))
            c.setFont("Helvetica-Bold", 9)
            c.setLineWidth(1.5)
            
            # Cotation longueur (bas) - entre p1 et p2
            offset_y = -0.8*cm
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = min(p1[1], p2[1]) + offset_y
            
            c.line(p1[0], mid_y, p2[0], mid_y)
            c.line(p1[0], mid_y - 0.15*cm, p1[0], mid_y + 0.15*cm)
            c.line(p2[0], mid_y - 0.15*cm, p2[0], mid_y + 0.15*cm)
            c.drawCentredString(mid_x, mid_y - 0.4*cm, f"{longueur_m:.1f} m")
            
            # Cotation largeur (droite) - entre p2 et p3
            offset_x = 0.8*cm
            mid_x = max(p2[0], p3[0]) + offset_x
            mid_y = (p2[1] + p3[1]) / 2
            
            c.line(mid_x, p2[1], mid_x, p3[1])
            c.line(mid_x - 0.15*cm, p2[1], mid_x + 0.15*cm, p2[1])
            c.line(mid_x - 0.15*cm, p3[1], mid_x + 0.15*cm, p3[1])
            
            c.saveState()
            c.translate(mid_x + 0.4*cm, mid_y)
            c.rotate(90)
            c.drawCentredString(0, 0, f"{largeur_m:.1f} m")
            c.restoreState()

    
    def _draw_cotations(self, c, center_x, center_y):
        """Dessine les cotations"""
        echelle = 0.3
        
        longueur = self.data.get('longueur_batiment_m', 15)
        largeur = self.data.get('largeur_batiment_m', 10)
        
        bat_w = longueur * echelle * cm
        bat_h = largeur * echelle * cm
        
        # Cotation longueur (bas)
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setFont("Helvetica-Bold", 9)
        c.setLineWidth(1.5)
        
        cote_y = center_y - bat_h/2 - 1*cm
        c.line(center_x - bat_w/2, cote_y, center_x + bat_w/2, cote_y)
        c.line(center_x - bat_w/2, cote_y - 0.2*cm, center_x - bat_w/2, cote_y + 0.2*cm)
        c.line(center_x + bat_w/2, cote_y - 0.2*cm, center_x + bat_w/2, cote_y + 0.2*cm)
        c.drawCentredString(center_x, cote_y - 0.5*cm, f"{longueur:.1f} m")
        
        # Cotation largeur (droite)
        cote_x = center_x + bat_w/2 + 1*cm
        c.line(cote_x, center_y - bat_h/2, cote_x, center_y + bat_h/2)
        c.line(cote_x - 0.2*cm, center_y - bat_h/2, cote_x + 0.2*cm, center_y - bat_h/2)
        c.line(cote_x - 0.2*cm, center_y + bat_h/2, cote_x + 0.2*cm, center_y + bat_h/2)
        
        c.saveState()
        c.translate(cote_x + 0.5*cm, center_y)
        c.rotate(90)
        c.drawCentredString(0, 0, f"{largeur:.1f} m")
        c.restoreState()
    
    def _draw_legend(self, c):
        """Dessine la legende"""
        x = 2*cm
        y = 13*cm  # Plus haut pour eviter chevauchement
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(x, y, "LÉGENDE :")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 9)
        
        # Parcelles cadastrales - Contour rouge épais + fond jaune
        c.setFillColorRGB(1, 1, 0, 0.15)  # Jaune transparent
        c.setStrokeColor(colors.HexColor('#FF0000'))
        c.setLineWidth(2.5)
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Parcelles cadastrales (fond jaune + contour rouge)")
        
        # Modules PV individuels
        y -= 0.55*cm
        c.setFillColor(colors.HexColor('#2196F3'))
        c.setStrokeColor(colors.HexColor('#0D47A1'))  # Bordure foncée
        c.setLineWidth(2)  # Bordure épaisse comme sur le plan
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Modules photovoltaïques (contour bleu foncé)")
        
        # Cotations
        y -= 0.55*cm
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(1.5)
        c.line(x, y, x + 1.5*cm, y)
        # Petites barres perpendiculaires pour montrer le style de cotation
        c.line(x, y - 0.15*cm, x, y + 0.15*cm)
        c.line(x + 1.5*cm, y - 0.15*cm, x + 1.5*cm, y + 0.15*cm)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Cotations dimensions (en mètres)")
    
    def _draw_cartouche(self, c):
        """Cartouche technique avec informations completes"""
        x = self.width - 14*cm
        y = 2*cm  # En bas pour eviter chevauchement
        w = 12*cm
        h = 10*cm  # Hauteur augment├®e pour toutes les infos
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, w, h)
        
        # Titre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(x, y + h - 0.8*cm, w, 0.8*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + w/2, y + h - 0.55*cm, "CARACTERISTIQUES TECHNIQUES")
        
        # Contenu
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        info_y = y + h - 1.3*cm
        
        # Informations du projet
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 0.3*cm, info_y, "Projet :")
        info_y -= 0.35*cm
        c.setFont("Helvetica", 8)
        
        commune = self.data.get('commune', 'N/A')
        adresse = self.data.get('adresse', 'N/A')
        c.drawString(x + 0.5*cm, info_y, f"- {adresse}")
        info_y -= 0.3*cm
        c.drawString(x + 0.5*cm, info_y, f"- {commune}")
        info_y -= 0.5*cm
        
        # Parcelles cadastrales
        parcelles = self._extract_parcelles()
        if parcelles:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Parcelles cadastrales :")
            info_y -= 0.35*cm
            c.setFont("Helvetica", 7.5)
            
            # Afficher TOUTES les parcelles (max 6 pour tenir dans le cadre)
            for p in parcelles[:6]:
                section = p.get('section', '')
                numero = p.get('numero', '')
                surface = p.get('surface', 0)
                # N'afficher la surface que si elle est disponible
                if surface and float(surface) > 0:
                    c.drawString(x + 0.5*cm, info_y, f"- {section}{numero} - {surface} m2")
                else:
                    c.drawString(x + 0.5*cm, info_y, f"- {section}{numero} - Surface N/A")
                info_y -= 0.3*cm
            
            if len(parcelles) > 6:
                c.drawString(x + 0.5*cm, info_y, f"  ... et {len(parcelles) - 6} autre(s)")
                info_y -= 0.3*cm
            
            info_y -= 0.2*cm
        
        # Installation PV
        if self.calpinage and 'zones' in self.calpinage:
            total_modules = sum(z.get('nbModules', 0) for z in self.calpinage['zones'])
            puissance_module = self.calpinage.get('module', {}).get('puissance', 560)
            puissance_totale = total_modules * float(puissance_module) / 1000  # kWc
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Installation photovoltaique :")
            info_y -= 0.35*cm
            c.setFont("Helvetica", 8)
            c.drawString(x + 0.5*cm, info_y, f"- {total_modules} modules de {puissance_module}W")
            info_y -= 0.3*cm
            c.drawString(x + 0.5*cm, info_y, f"- Puissance totale : {puissance_totale:.2f} kWc")
            info_y -= 0.3*cm
            c.drawString(x + 0.5*cm, info_y, f"- {len(self.calpinage['zones'])} zone(s) PV")
        
        # Date, echelle et signature
        info_y = y + 0.5*cm
        c.setFont("Helvetica", 8)
        scale_str = f"1/{self.computed_scale:,}".replace(',', ' ')
        c.drawString(x + 0.3*cm, info_y, f"Date : _______________   Echelle : {scale_str}")
        c.drawString(x + w/2 + 0.3*cm, info_y, "Signature :")
    
    def _fetch_satellite_image(self, lat, lon, zoom=19, width=1200, height=1000):
        """Récupère une image satellite via API (IGN prioritaire, ArcGIS fallback)"""
        delta = 0.0001 * (20 - zoom)  # Approximatif
        min_lat = lat - delta
        max_lat = lat + delta
        min_lon = lon - delta
        max_lon = lon + delta
        
        # Méthode 1: IGN Géoplateforme WMS
        try:
            ign_params = {
                'SERVICE': 'WMS',
                'VERSION': '1.3.0',
                'REQUEST': 'GetMap',
                'LAYERS': 'ORTHOIMAGERY.ORTHOPHOTOS',
                'CRS': 'EPSG:4326',
                'BBOX': f'{min_lat},{min_lon},{max_lat},{max_lon}',
                'WIDTH': str(width),
                'HEIGHT': str(height),
                'FORMAT': 'image/png',
                'STYLES': ''
            }
            response = requests.get('https://data.geopf.fr/wms-r', params=ign_params, timeout=15)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('image'):
                if len(response.content) > 5000:
                    return io.BytesIO(response.content)
        except Exception as e:
            print(f"IGN satellite error: {e}")
        
        # Méthode 2: ArcGIS Export (fallback)
        try:
            params = {
                'bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}',
                'bboxSR': '4326',
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            response = requests.get('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export', params=params, timeout=15)
            if response.status_code == 200:
                return io.BytesIO(response.content)
        except Exception as e:
            print(f"ArcGIS satellite error: {e}")
        
        return None
    
    def _fetch_satellite_image_rect(self, lat, lon, width_meters, height_meters, width=1600, height=1400):
        """
        Télécharge une image satellite rectangulaire
        RESPECTE l'échelle 1/500 avec dimensions exactes
        
        Essaye dans l'ordre:
        1. IGN Géoplateforme WMS (orthophotos françaises, gratuit, fiable)
        2. ArcGIS World Imagery Export (fallback)
        
        Args:
            lat, lon: Coordonnées GPS du centre
            width_meters: Largeur en mètres (dimension Est-Ouest)
            height_meters: Hauteur en mètres (dimension Nord-Sud)
            width, height: Dimensions de l'image en pixels
            
        Returns:
            BytesIO de l'image ou None
        """
        print(f"[PLAN] 🎿 _fetch_satellite_image_rect appelée: lat={lat}, lon={lon}, w={width_meters}m, h={height_meters}m")
        
        # Vérifier que les coordonnées GPS sont valides
        if lat is None or lon is None:
            print(f"[PLAN] ❌ Coordonnées GPS manquantes (lat={lat}, lon={lon})")
            return None
        
        try:
            # 🔑 UTILISER LES MÊMES FACTEURS GPS que pour le plan (CRITIQUE pour alignement)
            if hasattr(self, 'gps_conversion_factors'):
                meters_per_degree_lat = self.gps_conversion_factors['meters_per_degree_lat']
                meters_per_degree_lng = self.gps_conversion_factors['meters_per_degree_lng']
                print(f"[PLAN] 🔑 Utilisation facteurs GPS précis pour image satellite")
            else:
                # Fallback (ne devrait jamais arriver)
                import math
                lat_rad = lat * math.pi / 180 if lat else 0.785398
                meters_per_degree_lat = 1 / 111320
                meters_per_degree_lng = 1 / (111320 * math.cos(lat_rad))
                print(f"[PLAN] ⚠️ Facteurs GPS fallback (gps_conversion_factors manquant)")
            
            # Conversion mètres → degrés avec facteurs PRÉCIS
            meters_to_lat = (height_meters / 2) * meters_per_degree_lat  # Demi-hauteur
            meters_to_lon = (width_meters / 2) * meters_per_degree_lng   # Demi-largeur
            
            # Calculer bbox rectangulaire
            min_lon = lon - meters_to_lon
            max_lon = lon + meters_to_lon
            min_lat = lat - meters_to_lat
            max_lat = lat + meters_to_lat
            
            bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            
            print(f"[PLAN] 🖼️ Téléchargement image satellite: {width_meters:.0f}x{height_meters:.0f}m (échelle 1/{self.computed_scale}), {width}x{height}px")
            print(f"[PLAN] 📌 GPS bbox: lat[{min_lat:.6f}, {max_lat:.6f}] lon[{min_lon:.6f}, {max_lon:.6f}]")
            
            # ========================================
            # MÉTHODE 1: Tuiles Google Satellite (même source que fond de carte Leaflet)
            # → parfait alignement avec les polygones dessinés sur fond Google
            # ========================================
            try:
                print(f"[PLAN] 🗺️ Tentative assemblage tuiles Google Satellite (alignement carte)...")
                tile_img = self._fetch_satellite_from_tiles(
                    lat, lon, width_meters, height_meters, width, height,
                    tile_url_template="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
                )
                if tile_img:
                    print(f"[PLAN] ✅ Image Google Satellite assemblée — alignement carte OK")
                    return tile_img
            except Exception as e:
                print(f"[PLAN] ⚠️ Tuiles Google échoué: {e}")

            # ========================================
            # MÉTHODE 2: ArcGIS World Imagery (fallback tuiles)
            # ========================================
            try:
                print(f"[PLAN] 🌍 Tentative assemblage tuiles ArcGIS...")
                tile_img = self._fetch_satellite_from_tiles(
                    lat, lon, width_meters, height_meters, width, height,
                    tile_url_template="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                )
                if tile_img:
                    print(f"[PLAN] ✅ Image ArcGIS assemblée")
                    return tile_img
            except Exception as e:
                print(f"[PLAN] ⚠️ Tuiles ArcGIS échoué: {e}")

            # ========================================
            # MÉTHODE 3: ArcGIS WMS Export (fallback WMS)
            # ========================================
            try:
                arcgis_url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
                arcgis_params = {
                    'bbox': bbox_str,
                    'bboxSR': '4326',
                    'size': f'{width},{height}',
                    'format': 'png',
                    'f': 'image'
                }
                
                print(f"[PLAN] 🌍 Tentative ArcGIS WMS Export...")
                response = requests.get(arcgis_url, params=arcgis_params, timeout=15)
                if response.status_code == 200:
                    img_size_kb = len(response.content) / 1024
                    print(f"[PLAN] ✅ Image satellite ArcGIS WMS OK ({img_size_kb:.1f} KB)")
                    return io.BytesIO(response.content)
                else:
                    print(f"[PLAN] ❌ ArcGIS WMS: HTTP {response.status_code}")
            except Exception as e:
                print(f"[PLAN] ❌ ArcGIS WMS échoué: {e}")

            # ========================================
            # MÉTHODE 4: IGN Géoplateforme WMS (dernier recours)
            # ========================================
            try:
                ign_url = "https://data.geopf.fr/wms-r"
                ign_params = {
                    'SERVICE': 'WMS',
                    'VERSION': '1.3.0',
                    'REQUEST': 'GetMap',
                    'LAYERS': 'ORTHOIMAGERY.ORTHOPHOTOS',
                    'CRS': 'EPSG:4326',
                    'BBOX': f"{min_lat},{min_lon},{max_lat},{max_lon}",  # WMS 1.3.0: lat,lon order
                    'WIDTH': str(width),
                    'HEIGHT': str(height),
                    'FORMAT': 'image/png',
                    'STYLES': ''
                }
                
                print(f"[PLAN] 🇫🇷 Tentative IGN Géoplateforme WMS...")
                response = requests.get(ign_url, params=ign_params, timeout=15)
                
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('image'):
                    img_size_kb = len(response.content) / 1024
                    if img_size_kb > 5:
                        print(f"[PLAN] ✅ Image satellite IGN OK ({img_size_kb:.1f} KB)")
                        return io.BytesIO(response.content)
                    else:
                        print(f"[PLAN] ⚠️ Image IGN trop petite ({img_size_kb:.1f} KB)")
                else:
                    print(f"[PLAN] ⚠️ IGN WMS: HTTP {response.status_code}, content-type: {response.headers.get('content-type', 'N/A')}")
            except Exception as e:
                print(f"[PLAN] ⚠️ IGN WMS échoué: {e}")
                    
        except Exception as e:
            print(f"[PLAN] ❌ Erreur téléchargement satellite: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[PLAN] ❌ TOUTES les méthodes satellite ont échoué!")
        return None

    def _fetch_satellite_from_tiles(self, lat, lon, width_meters, height_meters, img_width=800, img_height=600,
                                       tile_url_template=None):
        """
        Assemble une image satellite à partir des tuiles XYZ (même serveur que Leaflet).
        
        Args:
            tile_url_template: URL template avec {z}/{x}/{y} ou {z}/{y}/{x}.
                Par défaut: Google Satellite (même fond que la carte → alignement parfait).
        """
        import math
        from PIL import Image
        
        # Google Satellite par défaut — même source que le fond Leaflet → alignement carte garantit
        if tile_url_template is None:
            tile_url_template = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
        
        # Zoom 19 : meilleure résolution (~0.21 m/px) → erreur de crop sub-pixel < 0.21m
        # vs zoom 18 (~0.42 m/px, erreur jusqu'à 0.42m = 1mm à 1:200 sur 50m)
        zoom = 19
        
        # Convertir lat/lon en coordonnées de tuile
        n = 2 ** zoom
        x_center = (lon + 180.0) / 360.0 * n
        y_center = (1.0 - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n
        
        tile_size = 256
        
        # Calculer combien de tuiles couvrir
        # À zoom 18, une tuile couvre environ 0.6m/pixel → 256px = ~150m
        meters_per_pixel = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
        pixels_needed_x = int(width_meters / meters_per_pixel) + tile_size
        pixels_needed_y = int(height_meters / meters_per_pixel) + tile_size
        
        tiles_x = max(3, pixels_needed_x // tile_size + 2)
        tiles_y = max(3, pixels_needed_y // tile_size + 2)
        
        # Limiter pour ne pas faire trop de requêtes
        tiles_x = min(tiles_x, 8)
        tiles_y = min(tiles_y, 8)
        
        x_start = int(x_center) - tiles_x // 2
        y_start = int(y_center) - tiles_y // 2
        
        # Créer image composite
        composite = Image.new('RGB', (tiles_x * tile_size, tiles_y * tile_size))
        
        tile_count = 0
        for tx in range(tiles_x):
            for ty in range(tiles_y):
                tile_x = x_start + tx
                tile_y = y_start + ty
                
                # Construire l'URL — supporte les deux conventions {z}/{y}/{x} et {z}/{x}/{y}
                tile_url = tile_url_template.format(z=zoom, x=tile_x, y=tile_y)
                try:
                    # User-Agent nécessaire pour Google et certains serveurs
                    headers = {'User-Agent': 'Mozilla/5.0 (compatible; AgriWeb/1.0)'}
                    r = requests.get(tile_url, timeout=5, headers=headers)
                    if r.status_code == 200:
                        tile_img = Image.open(io.BytesIO(r.content))
                        composite.paste(tile_img, (tx * tile_size, ty * tile_size))
                        tile_count += 1
                except:
                    pass
        
        if tile_count < 2:
            print(f"[PLAN] ❌ Seulement {tile_count} tuiles récupérées, abandon")
            return None
        
        # ════════════════════════════════════════════════════════════════════
        # RECADRAGE PRÉCIS : centrer sur la position GPS exacte (x_center/y_center).
        # ⚠️ CORRECTION ALIGNEMENT : utiliser round() et non int() pour éviter
        #    un décalage systématique de 0–1 px (= 0–0.42m à zoom 18) entre
        #    le centre GPS et le centre de l'image.
        #    Sur un plan 1:200 (50m), 1px source → ~1mm sur le PDF = 50cm réels.
        # ════════════════════════════════════════════════════════════════════
        px_center = (x_center - x_start) * tile_size   # position exacte en pixels (float)
        py_center = (y_center - y_start) * tile_size

        # ← round() au lieu de int() pour centrage symétrique ─────────────
        cx_i = round(px_center)
        cy_i = round(py_center)

        crop_w = int(width_meters  / meters_per_pixel)
        crop_h = int(height_meters / meters_per_pixel)

        left   = max(0, cx_i - crop_w // 2)
        top    = max(0, cy_i - crop_h // 2)
        right  = min(composite.width,  cx_i + crop_w // 2)
        bottom = min(composite.height, cy_i + crop_h // 2)

        print(f"[PLAN] 🎯 Recadrage précis: centre pixel ({px_center:.2f}→{cx_i}, {py_center:.2f}→{cy_i})"
              f" → crop ({left},{top},{right},{bottom}) sur composite {composite.width}×{composite.height}")

        # ── Mettre à jour gps_bounds avec les VRAIS bords GPS de l'image ────────
        # Après la découpe en pixels, les bords réels ≠ gps_bounds théorique (1–2 px
        # d'écart dû à la troncature entière). En recalculant depuis les coordonnées
        # de tuile exactes, les modules GPS sont projetés sur le contenu exact de l'image.
        try:
            actual_tile_left   = x_start + left   / tile_size   # en unités-tuile (float)
            actual_tile_right  = x_start + right  / tile_size
            actual_tile_top    = y_start + top    / tile_size
            actual_tile_bottom = y_start + bottom / tile_size
            # Longitude : linéaire en Mercator
            actual_west_lon = actual_tile_left  / n * 360.0 - 180.0
            actual_east_lon = actual_tile_right / n * 360.0 - 180.0
            # Latitude : fonction inverse de Mercator
            def _tile_y_to_lat(ty):
                gy = ty / n
                return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * gy))))
            actual_north_lat = _tile_y_to_lat(actual_tile_top)
            actual_south_lat = _tile_y_to_lat(actual_tile_bottom)
            self.gps_bounds = {
                'min_lat': actual_south_lat,
                'max_lat': actual_north_lat,
                'min_lon': actual_west_lon,
                'max_lon': actual_east_lon,
            }
            print(f"[PLAN] 📌 gps_bounds recalibré depuis crop réel: "
                  f"lat[{actual_south_lat:.6f},{actual_north_lat:.6f}] "
                  f"lon[{actual_west_lon:.6f},{actual_east_lon:.6f}]")
        except Exception as _e_gb:
            print(f"[PLAN] ⚠️ Impossible de recalibrer gps_bounds depuis tuiles: {_e_gb}")

        cropped = composite.crop((left, top, right, bottom))
        cropped = cropped.resize((img_width, img_height), Image.LANCZOS)

        buf = io.BytesIO()
        cropped.save(buf, format='PNG')
        buf.seek(0)

        print(f"[PLAN] ✅ Image satellite assemblée depuis {tile_count} tuiles ({img_width}x{img_height}px)")
        return buf
    
    def _fetch_satellite_image_bbox(self, lat, lon, bbox_meters, width=1200, height=1000):
        """
        Récupère une image satellite avec une bbox en mètres autour du point central.
        Utilise IGN en priorité, ArcGIS en fallback.
        """
        try:
            meters_to_lat = bbox_meters / 111000
            meters_to_lon = bbox_meters / (111000 * 0.7)
            
            min_lon = lon - meters_to_lon
            max_lon = lon + meters_to_lon
            min_lat = lat - meters_to_lat
            max_lat = lat + meters_to_lat
            
            print(f"[PLAN] 🖼️ Téléchargement image satellite: bbox={bbox_meters:.0f}m, size={width}x{height}px")
            print(f"[PLAN] 📌 GPS bounds: lat[{min_lat:.6f}, {max_lat:.6f}] lon[{min_lon:.6f}, {max_lon:.6f}]")
            
            # Méthode 1: IGN Géoplateforme WMS
            try:
                ign_params = {
                    'SERVICE': 'WMS',
                    'VERSION': '1.3.0',
                    'REQUEST': 'GetMap',
                    'LAYERS': 'ORTHOIMAGERY.ORTHOPHOTOS',
                    'CRS': 'EPSG:4326',
                    'BBOX': f'{min_lat},{min_lon},{max_lat},{max_lon}',
                    'WIDTH': str(width),
                    'HEIGHT': str(height),
                    'FORMAT': 'image/png',
                    'STYLES': ''
                }
                response = requests.get('https://data.geopf.fr/wms-r', params=ign_params, timeout=15)
                if response.status_code == 200 and response.headers.get('content-type', '').startswith('image'):
                    img_size_kb = len(response.content) / 1024
                    if img_size_kb > 5:
                        print(f"[PLAN] ✅ Image satellite IGN OK ({img_size_kb:.1f} KB)")
                        return io.BytesIO(response.content)
            except Exception as e:
                print(f"[PLAN] ⚠️ IGN WMS échoué: {e}")
            
            # Méthode 2: ArcGIS Export (fallback)
            try:
                params = {
                    'bbox': f'{min_lon},{min_lat},{max_lon},{max_lat}',
                    'bboxSR': '4326',
                    'size': f'{width},{height}',
                    'format': 'png',
                    'f': 'image'
                }
                response = requests.get('https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export', params=params, timeout=15)
                if response.status_code == 200:
                    img_size_kb = len(response.content) / 1024
                    print(f"[PLAN] ✅ Image satellite ArcGIS OK ({img_size_kb:.1f} KB)")
                    return io.BytesIO(response.content)
                else:
                    print(f"[PLAN] ❌ ArcGIS: HTTP {response.status_code}")
            except Exception as e:
                print(f"[PLAN] ❌ ArcGIS échoué: {e}")
                
        except Exception as e:
            print(f"[PLAN] ❌ Erreur image satellite: {e}")
        
        return None
    
    def _extract_parcelles(self):
        """Extrait les parcelles cadastrales"""
        # Essayer plusieurs champs possibles
        for field in ['parcelles_cadastrales', 'parcelles', 'cadastre', 'data_json']:
            parcelles_data = self.data.get(field)
            
            if parcelles_data:
                # Si c'est un dict avec une clé 'parcelles'
                if isinstance(parcelles_data, dict):
                    # 🔥 CORRECTION: Chercher dans data_json.parcelles_cadastrales (rapport par point)
                    if 'parcelles_cadastrales' in parcelles_data:
                        parcelles_data = parcelles_data['parcelles_cadastrales']
                        print(f"[PLAN] ✅ Parcelles trouvées dans {field}.parcelles_cadastrales")
                    elif 'parcelles' in parcelles_data:
                        parcelles_data = parcelles_data['parcelles']
                        print(f"[PLAN] ✅ Parcelles trouvées dans {field}.parcelles")
                
                # Si c'est déjà une liste
                if isinstance(parcelles_data, list) and len(parcelles_data) > 0:
                    print(f"[PLAN] ✅ Trouvé {len(parcelles_data)} parcelles dans '{field}'")
                    # Enrichir avec g├®om├®tries depuis API Cadastre si manquantes
                    parcelles_data = self._enrich_parcelles_with_geometry(parcelles_data)
                    # Normaliser les surfaces (essayer plusieurs cl├®s)
                    for p in parcelles_data:
                        surface_val = p.get('surface', 0)
                        if not surface_val or surface_val == 0:
                            # Essayer d'autres cl├®s
                            surface_val = p.get('superficie') or p.get('contenance') or p.get('surface_m2') or 0
                            if isinstance(surface_val, str):
                                try:
                                    surface_val = float(surface_val.replace(' ', '').replace('m┬▓', '').replace(',', '.'))
                                except:
                                    surface_val = 0
                            p['surface'] = surface_val
                        if surface_val > 0:
                            print(f"[PLAN] ­ƒôè Parcelle {p.get('section', '')}{p.get('numero', '')}: surface={surface_val:.0f}m┬▓")
                    return parcelles_data
                
                # Si c'est une cha├«ne JSON
                if isinstance(parcelles_data, str) and parcelles_data:
                    try:
                        parsed = json.loads(parcelles_data)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            print(f"[PLAN] Ô£à Trouv├® {len(parsed)} parcelles (JSON) dans '{field}'")
                            # ­ƒöÑ ENRICHIR avec l'API Cadastre IGN
                            parsed = self._enrich_parcelles_with_geometry(parsed)
                            return parsed
                        elif isinstance(parsed, dict):
                            for subkey in ['parcelles_cadastrales', 'parcelles']:
                                if subkey in parsed and isinstance(parsed[subkey], list):
                                    print(f"[PLAN] Ô£à Trouv├® {len(parsed[subkey])} parcelles dans '{field}.{subkey}'")
                                    # ­ƒöÑ ENRICHIR avec l'API Cadastre IGN
                                    enriched = self._enrich_parcelles_with_geometry(parsed[subkey])
                                    return enriched
                    except:
                        pass
        
        print(f"[PLAN] ÔÜá´©Å Aucune parcelle cadastrale trouv├®e dans les donn├®es prospect")
        print(f"[PLAN] Champs disponibles: {list(self.data.keys())}")
        return []
    
    def _enrich_parcelles_with_geometry(self, parcelles):
        """Enrichit les parcelles avec leurs g├®om├®tries depuis l'API Cadastre Apicarto"""
        
        print(f"\n[PLAN] ­ƒöì ENRICHISSEMENT PARCELLES - D├®but")
        print(f"[PLAN] Nombre de parcelles ├á enrichir: {len(parcelles)}")
        
        # Afficher les parcelles disponibles
        for p in parcelles:
            print(f"[PLAN]   - Parcelle: section={p.get('section')}, numero={p.get('numero')}, a_geometry={bool(p.get('geojson') or p.get('geometry'))}")
        
        # Calculer la bbox englobante de toutes les zones PV
        if not self.calpinage or 'zones' not in self.calpinage:
            print(f"[PLAN] ÔÜá´©Å Aucune zone PV pour calculer la bbox - utilisation des coordonn├®es du prospect")
            # Fallback: utiliser les coordonn├®es du prospect avec un buffer de 200m
            lat = self.data.get('latitude')
            lon = self.data.get('longitude')
            if not lat or not lon:
                print(f"[PLAN] ÔØî Pas de coordonn├®es disponibles")
                return parcelles
            
            buffer_deg = 200 / 111000  # 200m en degr├®s
            min_lat, max_lat = lat - buffer_deg, lat + buffer_deg
            min_lon, max_lon = lon - buffer_deg, lon + buffer_deg
        else:
            zones = self.calpinage['zones']
            if not zones:
                print(f"[PLAN] ÔÜá´©Å Liste zones vide")
                return parcelles
            
            # Collecter toutes les coordonn├®es GPS des zones
            all_lats = []
            all_lons = []
            
            for zone in zones:
                zone_coords = zone.get('coordinates', [])
                for coord in zone_coords:
                    all_lats.append(coord['lat'])
                    all_lons.append(coord['lng'])
            
            if not all_lats or not all_lons:
                print(f"[PLAN] ÔÜá´©Å Aucune coordonn├®e GPS dans les zones")
                return parcelles
            
            # Calculer la bbox avec un petit buffer (10m)
            buffer_deg = 10 / 111000
            min_lat = min(all_lats) - buffer_deg
            max_lat = max(all_lats) + buffer_deg
            min_lon = min(all_lons) - buffer_deg
            max_lon = max(all_lons) + buffer_deg
        
        # Cr├®er un polygon GeoJSON de la bbox pour l'API Cadastre
        bbox_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat]
            ]]
        }
        
        print(f"[PLAN] ­ƒôì Bbox recherche API: [{min_lat:.6f}, {max_lat:.6f}] x [{min_lon:.6f}, {max_lon:.6f}]")
        
        try:
            # Appel API Cadastre avec bbox des zones PV
            url = "https://apicarto.ign.fr/api/cadastre/parcelle"
            params = {
                "geom": json.dumps(bbox_polygon),
                "_limit": 1000,
                "source_ign": "PCI"
            }
            
            print(f"[PLAN] ­ƒîÉ Appel API Cadastre IGN...")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                api_features = data.get('features', [])
                
                print(f"[PLAN] Ô£à API retourne {len(api_features)} parcelles dans la bbox")
                
                # ­ƒöÑ SI CALPINAGE: Filtrer les parcelles qui INTERSECTENT r├®ellement les zones PV
                if self.calpinage and 'zones' in self.calpinage and len(self.calpinage['zones']) > 0:
                    print(f"[PLAN] ­ƒÄ» MODE CALPINAGE: Filtrage des {len(api_features)} parcelles par intersection avec zones PV")
                    
                    # Cr├®er les g├®om├®tries des zones PV
                    from shapely.geometry import Polygon, shape
                    from shapely.ops import unary_union
                    
                    pv_polygons = []
                    for zone in self.calpinage['zones']:
                        zone_coords = zone.get('coordinates', [])
                        if len(zone_coords) >= 3:
                            # Convertir en format shapely (lon, lat)
                            shapely_coords = [(c['lng'], c['lat']) for c in zone_coords]
                            try:
                                poly = Polygon(shapely_coords)
                                if poly.is_valid:
                                    pv_polygons.append(poly)
                            except Exception as e:
                                print(f"[PLAN] ÔÜá´©Å Zone PV invalide: {e}")
                    
                    if not pv_polygons:
                        print(f"[PLAN] ÔÜá´©Å Aucune zone PV valide pour filtrage")
                        return parcelles
                    
                    # Union de toutes les zones PV
                    pv_union = unary_union(pv_polygons)
                    print(f"[PLAN] ­ƒÄì {len(pv_polygons)} zone(s) PV cr├®├®e(s) pour filtrage")
                    
                    # Filtrer les parcelles qui INTERSECTENT les zones PV
                    enriched = []
                    for feat in api_features:
                        props = feat.get('properties', {})
                        geom = feat.get('geometry', {})
                        
                        try:
                            parcelle_shape = shape(geom)
                            if parcelle_shape.is_valid and parcelle_shape.intersects(pv_union):
                                # Cette parcelle intersecte les zones PV
                                parcelle_formatted = {
                                    "section": props.get('section', ''),
                                    "numero": props.get('numero', ''),
                                    "surface": props.get('contenance', 0),
                                    "commune": props.get('commune', ''),
                                    "code_insee": props.get('code_insee', ''),
                                    "geometry": geom,
                                    "geojson": feat
                                }
                                enriched.append(parcelle_formatted)
                                print(f"[PLAN]   Ô£à {props.get('section')}{props.get('numero')}: {props.get('contenance', 0)}m┬▓ (INTERSECTE)")
                            else:
                                print(f"[PLAN]   Ôåû {props.get('section')}{props.get('numero')}: ignor├®e (hors zones PV)")
                        except Exception as e:
                            print(f"[PLAN] ÔÜá´©Å Erreur intersection {props.get('section')}{props.get('numero')}: {e}")
                    
                    print(f"[PLAN] Ô£à {len(enriched)} parcelles intersectant les zones PV")
                    return enriched
                
                # Mode normal: enrichir les parcelles existantes
                # Afficher les premi├¿res parcelles de l'API pour debug
                for i, feat in enumerate(api_features[:3]):
                    props = feat.get('properties', {})
                    print(f"[PLAN]   API parcelle #{i+1}: section={props.get('section')}, numero={props.get('numero')}, commune={props.get('commune')}")
                
                # Enrichir chaque parcelle de notre liste avec les donn├®es de l'API
                enriched = []
                for p in parcelles:
                    section = str(p.get('section', '')).strip()
                    numero = str(p.get('numero', '')).strip().lstrip('0')  # Supprimer les 0 initiaux
                    
                    print(f"\n[PLAN] ­ƒöÄ Recherche parcelle {section}{numero}...")
                    
                    # Si d├®j├á une g├®om├®trie, garder telle quelle
                    if p.get('geojson') or p.get('geometry'):
                        enriched.append(p)
                        print(f"[PLAN] Ô£à Parcelle {section}{numero} a d├®j├á une g├®om├®trie")
                        continue
                    
                    # Chercher la correspondance dans les features de l'API
                    found = False
                    for api_feature in api_features:
                        api_props = api_feature.get('properties', {})
                        api_section = str(api_props.get('section', '')).strip()
                        api_numero = str(api_props.get('numero', '')).strip().lstrip('0')  # Supprimer les 0 initiaux
                        
                        # Matching plus tol├®rant
                        if api_section == section and api_numero == numero:
                            p['geojson'] = api_feature
                            p['geometry'] = api_feature.get('geometry')
                            
                            # R├®cup├®rer la surface si disponible
                            if 'contenance' in api_props and api_props['contenance']:
                                p['surface'] = api_props['contenance']
                            
                            print(f"[PLAN] Ô£àÔ£à MATCH TROUV├ë pour {section}{numero} (surface: {p.get('surface', 'N/A')}m┬▓)")
                            found = True
                            break
                    
                    if not found:
                        print(f"[PLAN] ÔØî Parcelle {section}{numero} NON TROUV├ëE dans l'API")
                    
                    enriched.append(p)
                
                print(f"\n[PLAN] ­ƒôè R├®sum├® enrichissement: {sum(1 for p in enriched if p.get('geojson') or p.get('geometry'))}/{len(enriched)} parcelles ont une g├®om├®trie")
                return enriched
            else:
                print(f"[PLAN] ÔØî API erreur HTTP {response.status_code}")
                print(f"[PLAN] R├®ponse: {response.text[:200]}")
                return parcelles
                
        except Exception as e:
            print(f"[PLAN] ÔØî Exception API Cadastre: {e}")
            import traceback
            traceback.print_exc()
            return parcelles


def generate_plan_masse(prospect_data, calpinage_data=None):
    """
    G├®n├¿re un plan de masse cadastral avec calpinage PV
    
    Args:
        prospect_data: dict avec donn├®es prospect (parcelles, adresse, lat/lon, dimensions b├ótiment)
        calpinage_data: dict optionnel avec zones PV et modules
        
    Returns:
        BytesIO buffer du PDF
    """
    generator = PlanMasseGenerator(prospect_data, calpinage_data)
    return generator.generate()
