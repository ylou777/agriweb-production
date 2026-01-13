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
import io
import requests
from PIL import Image
import json
import base64
import re
import math


class LabelManager:
    """Gestion intelligente du positionnement des ├®tiquettes pour ├®viter les superpositions"""
    
    def __init__(self):
        self.used_positions = []  # Liste des rectangles d├®j├á utilis├®s
    
    def find_non_overlapping_position(self, initial_x, initial_y, width, height, max_attempts=8):
        """Trouve une position non superpos├®e pour une ├®tiquette"""
        # Positions alternatives ├á essayer (offsets relatifs)
        offsets = [
            (0, 0),           # Position originale
            (0.5*cm, 0.5*cm),   # D├®cal├® haut-droite
            (-0.5*cm, 0.5*cm),  # D├®cal├® haut-gauche
            (0.5*cm, -0.5*cm),  # D├®cal├® bas-droite
            (-0.5*cm, -0.5*cm), # D├®cal├® bas-gauche
            (1*cm, 0),          # D├®cal├® droite
            (-1*cm, 0),         # D├®cal├® gauche
            (0, 1*cm),          # D├®cal├® haut
            (0, -1*cm),         # D├®cal├® bas
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
        self.width, self.height = A3  # Format A3 pour plus de d├®tails
        self.label_manager = LabelManager()  # Gestionnaire d'├®tiquettes
        
    def generate(self):
        """G├®n├¿re le plan de masse PDF"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A3)
        
        # En-t├¬te
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
        
        # Echelle reglementaire
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.drawRightString(self.width - 3*cm, y, "Echelle 1/500")
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
        
        # Initialiser screenshot_used
        self.screenshot_used = False
        
        # ­ƒöÑ CORRECTION GPS: Utiliser syst├®matiquement les facteurs de conversion pr├®cis
        # sauvegard├®s dans le calpinage (issus de map.distance() de Leaflet)
        gps_conversion = None
        if self.calpinage:
            gps_conversion = self.calpinage.get('gpsConversion')
        
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
        
        # ­ƒöÑ ├ëCHELLE 1/500 OBLIGATOIRE pour plan cadastral
        # 1 cm sur le plan = 500 cm (5 m) dans la r├®alit├®
        # Calculer la bbox en m├¿tres selon la taille du cadre PDF
        plan_width_cm = plan_width / cm
        plan_height_cm = plan_height / cm
        
        bbox_width_meters = plan_width_cm * 5  # 1cm = 5m ├á l'├®chelle 1/500
        bbox_height_meters = plan_height_cm * 5
        
        # Prendre la plus grande dimension et AUGMENTER MASSIVEMENT pour couverture TOTALE
        bbox_meters = max(bbox_width_meters, bbox_height_meters) * 3.5  # 350% de rayon pour GARANTIR couverture
        
        print(f"[PLAN] ├ëchelle 1/500: Cadre {plan_width_cm:.1f}x{plan_height_cm:.1f}cm = {bbox_width_meters:.0f}x{bbox_height_meters:.0f}m r├®els")
        print(f"[PLAN] Bbox satellite: {bbox_meters*2:.0f}m de c├┤t├® (rayon {bbox_meters:.0f}m)")
        
        # Convertir en degr├®s avec les BONS facteurs
        meters_to_lat = bbox_meters * meters_per_degree_lat
        meters_to_lon = bbox_meters * meters_per_degree_lng
        
        # Stocker les limites GPS r├®elles
        self.gps_bounds = {
            'min_lat': lat - meters_to_lat,
            'max_lat': lat + meters_to_lat,
            'min_lon': lon - meters_to_lon,
            'max_lon': lon + meters_to_lon
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
            
            # ­ƒöÑ FALLBACK: Image satellite si pas de screenshot
            if not self.screenshot_used:
                satellite_img = self._fetch_satellite_image_bbox(lat, lon, bbox_meters, width=1600, height=1400)
                if satellite_img:
                    # REMPLIR TOUT LE CADRE (pas de blanc autour)
                    c.drawImage(ImageReader(satellite_img), 
                              plan_x, plan_y, 
                              width=plan_width, height=plan_height,
                              preserveAspectRatio=False, mask='auto')  # False = remplit tout
                    print(f"[PLAN] Ô£à Image satellite: {bbox_meters*2:.0f}m de rayon ├á l'├®chelle 1/500")
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
            'meters_per_cm': bbox_meters / (plan_width / cm) if plan_width > 0 else 1
        }
        
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
            
            # ├ëtiquette VISIBLE avec fond blanc - POSITIONNEMENT ANTI-SUPERPOSITION
            if label_x is not None and label_y is not None:
                # Dimensions de l'├®tiquette
                text_w = 2.8*cm
                text_h = 0.8*cm
                
                # Trouver une position non superpos├®e
                final_x, final_y = self.label_manager.find_non_overlapping_position(
                    label_x, label_y, text_w, text_h
                )
                
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
                    c.drawString(final_x + 0.2*cm, final_y + 0.25*cm, 
                                f"Surface: {int(float(surface))} m┬▓")
            
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
        
        # ├ëtiquette DISCR├êTE en bas ├á gauche de la parcelle - POSITIONNEMENT ANTI-SUPERPOSITION
        label_bg_w = 2.5*cm
        label_bg_h = 0.6*cm
        
        # Trouver une position non superpos├®e
        final_parc_x, final_parc_y = self.label_manager.find_non_overlapping_position(
            parc_x, parc_y, label_bg_w, label_bg_h
        )
        
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
            
            print(f"[PLAN] ­ƒôì Dessin {len(modules_positions)} modules avec coordonn├®es GPS pour zone {zone.get('numero', '?')}")
            
            # Dessiner chaque module selon ses coordonn├®es GPS
            c.setStrokeColor(colors.HexColor('#1565C0'))  # Bleu fonc├®
            c.setFillColor(colors.HexColor('#2196F3'))    # Bleu clair
            c.setLineWidth(0.5)
            
            for module in modules_positions:
                corners = module.get('corners', [])
                
                if len(corners) < 4:
                    continue
                
                # Convertir les 4 coins GPS ÔåÆ coordonn├®es PDF
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
                
                # Dessiner le module
                c.drawPath(path, stroke=1, fill=1)
            
            # Dessiner le contour de la zone (optionnel)
            zone_coords = zone.get('coordinates', [])
            if zone_coords:
                path = c.beginPath()
                first = True
                
                for coord in zone_coords:
                    pdf_x, pdf_y = self._lat_lon_to_pdf(coord['lat'], coord['lng'])
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Contour zone rouge en pointill├®s
                c.setStrokeColor(colors.HexColor('#D32F2F'))
                c.setLineWidth(2)
                c.setDash(4, 2)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()
                
                # ├ëtiquette zone - POSITIONNEMENT ANTI-SUPERPOSITION
                if zone_coords:
                    label_x, label_y = self._lat_lon_to_pdf(zone_coords[0]['lat'], zone_coords[0]['lng'])
                    
                    # Dimensions de l'├®tiquette de zone
                    zone_label_w = 5*cm
                    zone_label_h = 0.6*cm
                    
                    # Trouver une position non superpos├®e
                    final_label_x, final_label_y = self.label_manager.find_non_overlapping_position(
                        label_x, label_y, zone_label_w, zone_label_h
                    )
                    
                    c.setFillColor(colors.HexColor('#D32F2F'))
                    c.setFont("Helvetica-Bold", 8)
                    nb_modules = zone.get('nbModules', len(modules_positions))
                    nb_cols = zone.get('nbCols', 0)
                    nb_rows = zone.get('nbRows', 0)
                    c.drawString(final_label_x + 0.4*cm, final_label_y + 0.4*cm,
                                f"Zone PV: {nb_modules} modules ({nb_cols}├ù{nb_rows})")
    
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
        y = 12*cm  # Plus haut pour eviter chevauchement
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(x, y, "LEGENDE :")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 9)
        
        # Parcelle
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(2)
        c.setDash(8, 4)
        c.line(x, y, x + 1.5*cm, y)
        c.setDash()
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Limites parcellaires cadastrales")
        
        # Batiment
        y -= 0.5*cm
        c.setFillColor(colors.HexColor('#FFE4B5'))
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Batiment existant")
        
        # Modules PV
        y -= 0.5*cm
        c.setFillColor(colors.HexColor('#2196F3'))
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Modules photovoltaiques (position reelle)")
        
        # Zone PV
        y -= 0.5*cm
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(2)
        c.setDash(4, 2)
        c.line(x, y, x + 1.5*cm, y)
        c.setDash()
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Contour zone PV")
        
        # Cotations
        y -= 0.5*cm
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(1.5)
        c.line(x, y, x + 1.5*cm, y)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Cotations (en metres)")
    
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
        
        # Date et signature
        info_y = y + 0.5*cm
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.3*cm, info_y, "Date : _______________")
        c.drawString(x + w/2 + 0.3*cm, info_y, "Signature :")
    
    def _fetch_satellite_image(self, lat, lon, zoom=19, width=1200, height=1000):
        """R├®cup├¿re une image satellite via API"""
        try:
            # ArcGIS World Imagery (gratuit, haute r├®solution)
            url = f"https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            # Calculer bbox autour du point
            # ├Ç zoom 19, ~10m de rayon
            delta = 0.0001 * (20 - zoom)  # Approximatif
            bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta}"
            
            params = {
                'bbox': bbox,
                'bboxSR': '4326',
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return io.BytesIO(response.content)
        except Exception as e:
            print(f"Erreur image satellite: {e}")
        
        return None
    
    def _fetch_satellite_image_bbox(self, lat, lon, bbox_meters, width=1200, height=1000):
        """
        R├®cup├¿re une image satellite avec une bbox en m├¿tres autour du point central
        
        Args:
            lat, lon: Coordonn├®es GPS du centre
            bbox_meters: Rayon en m├¿tres pour la bbox
            width, height: Dimensions de l'image en pixels
            
        Returns:
            BytesIO de l'image ou None
        """
        try:
            # Conversion m├¿tres ÔåÆ degr├®s (approximatif pour France m├®tropolitaine)
            # 1 degr├® latitude Ôëê 111 km
            # 1 degr├® longitude Ôëê 111 km * cos(latitude) Ôëê 78 km ├á 45┬░ de latitude
            meters_to_lat = bbox_meters / 111000
            meters_to_lon = bbox_meters / (111000 * 0.7)  # cos(45┬░) Ôëê 0.7
            
            # Calculer bbox
            min_lon = lon - meters_to_lon
            max_lon = lon + meters_to_lon
            min_lat = lat - meters_to_lat
            max_lat = lat + meters_to_lat
            
            # ArcGIS World Imagery
            url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            
            params = {
                'bbox': bbox_str,
                'bboxSR': '4326',
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            
            print(f"[PLAN] ­ƒø░´©Å T├®l├®chargement image satellite: bbox={bbox_meters:.0f}m ({bbox_meters*2:.0f}m c├┤t├®), size={width}x{height}")
            print(f"[PLAN] ­ƒôì GPS bounds: [{min_lat:.6f}, {max_lat:.6f}] x [{min_lon:.6f}, {max_lon:.6f}]")
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                img_size_kb = len(response.content) / 1024
                print(f"[PLAN] Ô£à Image satellite t├®l├®charg├®e ({img_size_kb:.1f} KB)")
                return io.BytesIO(response.content)
            else:
                print(f"[PLAN] ÔØî Erreur API ArcGIS: HTTP {response.status_code}")
                print(f"[PLAN] ­ƒöù URL: {response.url}")
        except Exception as e:
            print(f"[PLAN] ÔØî Erreur image satellite: {e}")
        
        return None
    
    def _extract_parcelles(self):
        """Extrait les parcelles cadastrales"""
        # Essayer plusieurs champs possibles
        for field in ['parcelles_cadastrales', 'parcelles', 'cadastre', 'data_json']:
            parcelles_data = self.data.get(field)
            
            if parcelles_data:
                # Si c'est un dict avec une cl├® 'parcelles'
                if isinstance(parcelles_data, dict):
                    if 'parcelles_cadastrales' in parcelles_data:
                        parcelles_data = parcelles_data['parcelles_cadastrales']
                    elif 'parcelles' in parcelles_data:
                        parcelles_data = parcelles_data['parcelles']
                
                # Si c'est d├®j├á une liste
                if isinstance(parcelles_data, list) and len(parcelles_data) > 0:
                    print(f"[PLAN] Ô£à Trouv├® {len(parcelles_data)} parcelles dans '{field}'")
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
