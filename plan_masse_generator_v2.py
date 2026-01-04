"""
Générateur de Plan de Masse Cadastral avec Calpinage PV - Version 2
Utilise les coordonnées GPS réelles pour un positionnement précis
"""

from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io
import requests
from PIL import Image
import json
import math


class PlanMasseGeneratorV2:
    """Génère un plan de masse cadastral avec positionnement GPS précis"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = A3
        
    def generate(self):
        """Génère le plan de masse PDF"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A3)
        
        # En-tête
        self._draw_header(c)
        
        # Zone principale : plan cadastral + calpinage
        self._draw_plan_cadastral(c)
        
        # Légende et informations
        self._draw_legend(c)
        
        # Cartouche technique
        self._draw_cartouche(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_header(self, c):
        """En-tête du document"""
        y = self.height - 2*cm
        
        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawString(3*cm, y, "PLAN DE MASSE - INSTALLATION PHOTOVOLTAÏQUE")
        
        # Adresse
        y -= 0.6*cm
        c.setFont("Helvetica", 10)
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"{adresse}, {commune}")
        
        # Échelle dynamique
        c.setFont("Helvetica-Bold", 12)
        echelle_txt = self._calculate_scale_text()
        c.drawRightString(self.width - 3*cm, y, echelle_txt)
    
    def _calculate_scale_text(self):
        """Calcule l'échelle du plan dynamiquement"""
        # Essayer de calculer l'échelle réelle depuis les données du calpinage
        if self.calpinage and 'zones' in self.calpinage:
            # Si on a des zones avec coordonnées GPS, calculer l'échelle réelle
            zones = self.calpinage['zones']
            if zones and len(zones) > 0:
                zone = zones[0]
                coords = zone.get('coordinates', [])
                if len(coords) >= 2:
                    # Calculer distance réelle entre 2 points
                    try:
                        from math import radians, cos, sin, sqrt, atan2
                        lat1, lon1 = coords[0]['lat'], coords[0]['lng']
                        lat2, lon2 = coords[1]['lat'], coords[1]['lng']
                        
                        # Formule haversine pour distance GPS
                        R = 6371000  # Rayon terre en mètres
                        phi1, phi2 = radians(lat1), radians(lat2)
                        dphi = radians(lat2 - lat1)
                        dlambda = radians(lon2 - lon1)
                        a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
                        c = 2 * atan2(sqrt(a), sqrt(1-a))
                        distance_m = R * c
                        
                        # Distance en pixels sur l'image (approximatif: zone fait ~200px)
                        # Cette valeur devrait être extraite de l'image réelle
                        # Pour l'instant approximation
                        distance_px = 200  # À ajuster
                        
                        # Échelle = distance réelle / distance papier
                        # Si 200px représentent distance_m, et sont affichés sur ~10cm
                        # Échelle ≈ distance_m / 0.1
                        echelle = int(distance_m * 10)
                        return f"Échelle approx. 1/{echelle}"
                    except Exception as e:
                        print(f"[PLAN] Erreur calcul échelle: {e}")
        
        # Échelle par défaut
        return "Échelle 1/500 (approx.)"
    
    def _draw_plan_cadastral(self, c):
        """Dessine le plan cadastral avec parcelles et modules PV"""
        
        # Zone de dessin
        plan_x = 3*cm
        plan_y = 8*cm
        plan_width = self.width - 6*cm
        plan_height = self.height - 14*cm
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(plan_x, plan_y, plan_width, plan_height)
        
        # 🔥 STRATÉGIE CORRECTE : Préserver les proportions de l'image du calpinage
        # L'image contient : satellite + modules positionnés + zones
        # On doit centrer l'image sans la déformer pour garder l'échelle
        
        calpinage_image = self._get_calpinage_screenshot()
        
        if calpinage_image:
            # Afficher l'image du calpinage EN PRÉSERVANT LES PROPORTIONS
            try:
                # Obtenir les dimensions réelles de l'image
                img = Image.open(calpinage_image)
                img_width, img_height = img.size
                print(f"[PLAN] 📏 Dimensions image: {img_width}x{img_height}px")
                print(f"[PLAN] 📐 Zone PDF: {plan_width/cm:.1f}x{plan_height/cm:.1f}cm")
                
                # 🔥 CORRECTION: Calculer le ratio pour préserver les proportions
                # On ajuste pour que l'image remplisse la zone tout en gardant son ratio
                ratio_w = plan_width / img_width
                ratio_h = plan_height / img_height
                
                # Utiliser le ratio le plus petit pour que l'image tienne dans la zone
                ratio = min(ratio_w, ratio_h)
                
                # Nouvelles dimensions avec proportions préservées
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                # Centrer l'image dans la zone
                offset_x = (plan_width - new_width) / 2
                offset_y = (plan_height - new_height) / 2
                
                # Réinitialiser le buffer pour la relecture
                calpinage_image.seek(0)
                
                # Dessiner l'image EN PRÉSERVANT LE RATIO (pas d'étirement)
                c.drawImage(ImageReader(calpinage_image), 
                          plan_x + offset_x, plan_y + offset_y, 
                          width=new_width, height=new_height,
                          preserveAspectRatio=True, mask='auto')
                print(f"[PLAN] ✅ Image affichée avec proportions préservées: {new_width/cm:.1f}x{new_height/cm:.1f}cm")
                print(f"[PLAN] 📍 Offset: x={offset_x/cm:.1f}cm, y={offset_y/cm:.1f}cm")
                
                # Stocker les infos pour le positionnement des overlays
                self.image_offset_x = plan_x + offset_x
                self.image_offset_y = plan_y + offset_y
                self.image_display_width = new_width
                self.image_display_height = new_height
                
            except Exception as e:
                print(f"[PLAN] ❌ Erreur affichage image: {e}")
                import traceback
                traceback.print_exc()
                # Fond par défaut
                c.setFillColor(colors.HexColor('#E8F5E9'))
                c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
        else:
            print("[PLAN] ⚠️ Pas de screenshot disponible - utilisez le bouton 'Sauvegarder' d'abord")
            # Message à l'utilisateur
            c.setFillColor(colors.HexColor('#FFF3E0'))
            c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
            c.setFillColor(colors.HexColor('#F57C00'))
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(plan_x + plan_width/2, plan_y + plan_height/2,
                              "⚠️ Veuillez sauvegarder le calpinage avant de générer le plan")
        
        # Ajouter UNIQUEMENT les contours et références des parcelles cadastrales
        # (si disponibles dans les données)
        self._draw_parcelles_overlay(c, plan_x, plan_y, plan_width, plan_height)
    
    def _draw_parcelles_overlay(self, c, plan_x, plan_y, plan_width, plan_height):
        """Dessine les contours et références des parcelles en overlay sur l'image"""
        parcelles = self._extract_parcelles()
        
        print(f"[PLAN] Nombre de parcelles à afficher: {len(parcelles)}")
        
        if not parcelles:
            return
        
        # Pour chaque parcelle, dessiner son contour et sa référence
        for i, parcelle in enumerate(parcelles):
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson')
            
            if geojson and isinstance(geojson, dict):
                # Dessiner avec géométrie réelle
                self._draw_parcelle_overlay_geojson(c, geojson, section, numero, surface,
                                                   plan_x, plan_y, plan_width, plan_height)
            else:
                # Dessiner référence simple (texte uniquement)
                print(f"[PLAN] Parcelle {section}{numero} : pas de géométrie - texte seulement")
                # Position arbitraire en haut à gauche
                label_x = plan_x + 1*cm + (i * 5*cm)
                label_y = plan_y + plan_height - 2*cm
                
                c.setFillColor(colors.HexColor('#FF00FF'))
                c.setFont("Helvetica-Bold", 10)
                c.drawString(label_x, label_y, f"📍 Parcelle {section}{numero}")
                c.setFont("Helvetica", 8)
                c.drawString(label_x, label_y - 0.4*cm, f"{surface} m²")
    
    def _draw_parcelle_overlay_geojson(self, c, geojson, section, numero, surface,
                                      plan_x, plan_y, plan_width, plan_height):
        """Dessine le contour d'une parcelle depuis GeoJSON (overlay transparent)"""
        try:
            geometry = geojson.get('geometry', geojson)
            coords = geometry.get('coordinates', [])
            geom_type = geometry.get('type', '')
            
            if geom_type == 'Polygon' and coords:
                exterior = coords[0]
                
                # Calculer la bbox de la parcelle pour la positionner
                lons = [c[0] for c in exterior]
                lats = [c[1] for c in exterior]
                
                # Conversion simplifiée : projection proportionnelle
                # On suppose que l'image du calpinage est déjà à la bonne échelle
                # Positionnement approximatif (au centre du plan)
                
                path = c.beginPath()
                first = True
                label_x, label_y = 0, 0
                
                # Dessiner le contour (on garde la géométrie mais on l'affiche en overlay)
                # Pour l'instant, on affiche juste un contour au centre
                # TODO: Calculer la vraie position GPS → pixels si besoin
                
                # Simplified: afficher au centre avec échelle arbitraire
                center_x = plan_x + plan_width / 2
                center_y = plan_y + plan_height / 2
                
                # Contour magenta épais
                c.setStrokeColor(colors.HexColor('#FF00FF'))
                c.setLineWidth(4)
                c.setDash(10, 5)
                
                # Rectangle approximatif (pour l'instant)
                # TODO: Utiliser les vraies coords GPS
                parc_w = 8*cm
                parc_h = 6*cm
                c.rect(center_x - parc_w/2, center_y - parc_h/2, parc_w, parc_h, 
                      fill=0, stroke=1)
                c.setDash()
                
                # Étiquette
                c.setFillColor(colors.HexColor('#FFFFFF'))
                c.setStrokeColor(colors.HexColor('#FF00FF'))
                c.setLineWidth(2)
                
                # Fond blanc pour la lisibilité
                label_w = 4*cm
                label_h = 1*cm
                label_x = center_x - label_w/2
                label_y = center_y + parc_h/2 + 0.3*cm
                
                c.rect(label_x, label_y, label_w, label_h, fill=1, stroke=1)
                
                c.setFillColor(colors.HexColor('#FF00FF'))
                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(center_x, label_y + 0.5*cm,
                                  f"Parcelle {section}{numero}")
                c.setFont("Helvetica", 9)
                c.drawCentredString(center_x, label_y + 0.1*cm,
                                  f"{surface} m²")
                
                print(f"[PLAN] ✅ Parcelle {section}{numero} affichée en overlay")
                
        except Exception as e:
            print(f"[PLAN] ❌ Erreur overlay parcelle: {e}")
    
    def _calculate_bbox_from_data(self):
        """Calcule la taille de la bbox en mètres"""
        # Essayer d'estimer depuis les parcelles
        parcelles = self._extract_parcelles()
        if parcelles:
            total_surface = sum(float(p.get('surface', 0)) for p in parcelles)
            if total_surface > 0:
                # bbox = √surface * 2 pour avoir de la marge
                return max(60, (total_surface ** 0.5) * 2)
        
        # Défaut: 120m (60m de rayon)
        return 120
    
    def _gps_to_pdf(self, lat, lon):
        """Convertit coordonnées GPS en coordonnées PDF"""
        if not hasattr(self, 'projection'):
            return (0, 0)
        
        proj = self.projection
        
        # Conversion GPS → mètres (projection simplifiée)
        # Pour petites distances, approximation linéaire valide
        delta_lat = lat - proj['lat_center']
        delta_lon = lon - proj['lon_center']
        
        # 1 degré latitude ≈ 111 km
        # 1 degré longitude ≈ 111 km * cos(latitude)
        lat_rad = math.radians(proj['lat_center'])
        meters_per_degree_lat = 111000
        meters_per_degree_lon = 111000 * math.cos(lat_rad)
        
        meters_y = delta_lat * meters_per_degree_lat
        meters_x = delta_lon * meters_per_degree_lon
        
        # Conversion mètres → pixels PDF
        pixel_x = meters_x / proj['meters_per_pixel_x']
        pixel_y = meters_y / proj['meters_per_pixel_y']
        
        # Position PDF (centre + offset)
        pdf_x = proj['plan_x'] + proj['plan_width'] / 2 + pixel_x
        pdf_y = proj['plan_y'] + proj['plan_height'] / 2 + pixel_y
        
        return (pdf_x, pdf_y)
    
    def _get_calpinage_screenshot(self):
        """Récupère l'image capturée du calpinage si disponible"""
        if not self.calpinage:
            return None
        
        screenshot_data = self.calpinage.get('screenshot_map')
        
        if not screenshot_data:
            return None
        
        try:
            # Décoder base64 en image
            import base64
            
            # Retirer le préfixe "data:image/png;base64," si présent
            if screenshot_data.startswith('data:image'):
                screenshot_data = screenshot_data.split(',', 1)[1]
            
            # Décoder base64
            image_data = base64.b64decode(screenshot_data)
            return io.BytesIO(image_data)
            
        except Exception as e:
            print(f"[PLAN] Erreur décodage screenshot calpinage: {e}")
            return None
    
    def _fetch_satellite_with_bbox(self, lat, lon, bbox_meters):
        """Récupère image satellite avec bbox précise"""
        try:
            # Calculer bbox en degrés GPS
            # Pour 45° de latitude (France), 1 degré ≈ 111 km
            lat_rad = math.radians(lat)
            meters_per_degree_lat = 111000
            meters_per_degree_lon = 111000 * math.cos(lat_rad)
            
            delta_deg_lat = (bbox_meters / 2) / meters_per_degree_lat
            delta_deg_lon = (bbox_meters / 2) / meters_per_degree_lon
            
            min_lon = lon - delta_deg_lon
            max_lon = lon + delta_deg_lon
            min_lat = lat - delta_deg_lat
            max_lat = lat + delta_deg_lat
            
            # ArcGIS World Imagery
            url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
            
            params = {
                'bbox': bbox,
                'bboxSR': '4326',
                'size': '1200,1000',
                'format': 'png',
                'f': 'image'
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return io.BytesIO(response.content)
        except Exception as e:
            print(f"[PLAN] Erreur image satellite: {e}")
        
        return None
    
    def _draw_parcelles_with_geojson(self, c):
        """Dessine les parcelles avec leurs géométries GeoJSON"""
        parcelles = self._extract_parcelles()
        
        print(f"[PLAN] Nombre de parcelles: {len(parcelles)}")
        
        for parcelle in parcelles:
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson')
            
            if geojson and isinstance(geojson, dict):
                self._draw_geojson_polygon(c, geojson, section, numero, surface)
            else:
                # Fallback: rectangle approximatif
                print(f"[PLAN] Pas de GeoJSON pour parcelle {section}{numero}")
    
    def _draw_geojson_polygon(self, c, geojson, section, numero, surface):
        """Dessine un polygone depuis GeoJSON"""
        try:
            geometry = geojson.get('geometry', geojson)
            coords = geometry.get('coordinates', [])
            geom_type = geometry.get('type', '')
            
            if geom_type == 'Polygon' and coords:
                # Premier ring (exterior)
                exterior = coords[0]
                
                path = c.beginPath()
                first = True
                label_x, label_y = 0, 0
                
                for coord in exterior:
                    lon, lat = coord[0], coord[1]
                    pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        label_x, label_y = pdf_x, pdf_y
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Contour magenta
                c.setStrokeColor(colors.HexColor('#FF00FF'))
                c.setLineWidth(3)
                c.setDash(8, 4)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()
                
                # Étiquette
                c.setFillColor(colors.HexColor('#FF00FF'))
                c.setFont("Helvetica-Bold", 9)
                c.drawString(label_x + 0.3*cm, label_y + 0.3*cm,
                            f"Parcelle {section}{numero}")
                c.setFont("Helvetica", 8)
                c.drawString(label_x + 0.3*cm, label_y - 0.2*cm,
                            f"{surface} m²")
        except Exception as e:
            print(f"[PLAN] Erreur dessin GeoJSON: {e}")
    
    def _draw_batiment_at_gps(self, c):
        """Dessine le bâtiment à sa position GPS"""
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        print(f"[PLAN] Dessin bâtiment - GPS: ({lat}, {lon})")
        
        if not lat or not lon:
            return
        
        # Position centrale
        pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
        
        # Dimensions bâtiment
        try:
            longueur_m = float(self.data.get('longueur_batiment_m', 15))
            largeur_m = float(self.data.get('largeur_batiment_m', 10))
        except:
            longueur_m, largeur_m = 15, 10
        
        # Conversion mètres → PDF
        proj = self.projection
        bat_w = longueur_m / proj['meters_per_pixel_x']
        bat_h = largeur_m / proj['meters_per_pixel_y']
        
        bat_x = pdf_x - bat_w / 2
        bat_y = pdf_y - bat_h / 2
        
        # Rectangle bâtiment
        c.setStrokeColor(colors.HexColor('#FF6B35'))
        c.setFillColor(colors.HexColor('#FFA07A'))
        c.setLineWidth(2.5)
        c.rect(bat_x, bat_y, bat_w, bat_h, fill=1, stroke=1)
        
        # Label
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(pdf_x, pdf_y, "BÂTIMENT")
    
    def _draw_modules_from_calpinage(self, c):
        """Dessine les modules PV depuis les coordonnées GPS EXACTES du calpinage"""
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        print(f"[PLAN] 🎨 Dessin de {len(self.calpinage['zones'])} zones avec modules...")
        
        for zone in self.calpinage['zones']:
            # 🔥 UTILISER les positions GPS exactes des modules sauvegardées
            modules_positions = zone.get('modulesPositions', [])
            gps_conversion = zone.get('gpsConversion', {})
            
            if not modules_positions:
                print(f"[PLAN] ⚠️ Zone {zone.get('numero')} : pas de modulesPositions sauvegardées")
                continue
            
            # 🔥 Créer une fonction de conversion GPS→PDF spécifique à cette zone
            # qui utilise les MÊMES facteurs que ceux utilisés lors du dessin Leaflet
            def gps_to_pdf_zone(lat, lon):
                """Convertit GPS → PDF en utilisant les facteurs EXACTS de la zone"""
                if not gps_conversion:
                    # Fallback sur la méthode globale
                    return self._gps_to_pdf(lat, lon)
                
                # Récupérer le centre de la zone
                bounds = zone.get('bounds', {})
                sw = bounds.get('_southWest', {})
                ne = bounds.get('_northEast', {})
                center_lat = (sw.get('lat', 0) + ne.get('lat', 0)) / 2
                center_lng = (sw.get('lng', 0) + ne.get('lng', 0)) / 2
                
                # 🔥 Utiliser les MÊMES facteurs que dans le JavaScript
                meters_per_deg_lng = gps_conversion.get('metersPerDegreeLng')
                meters_per_deg_lat = gps_conversion.get('metersPerDegreeLat')
                
                if not meters_per_deg_lng or not meters_per_deg_lat:
                    return self._gps_to_pdf(lat, lon)
                
                # Calcul offset en degrés depuis le centre
                delta_lat = lat - center_lat
                delta_lon = lon - center_lng
                
                # Conversion en mètres (même formule que JavaScript)
                meters_y = delta_lat / meters_per_deg_lat
                meters_x = delta_lon / meters_per_deg_lng
                
                # Conversion mètres → pixels PDF
                proj = self.projection
                pixel_x = meters_x / proj['meters_per_pixel_x']
                pixel_y = meters_y / proj['meters_per_pixel_y']
                
                # Position PDF (centre du plan + offset)
                pdf_x = proj['plan_x'] + proj['plan_width'] / 2 + pixel_x
                pdf_y = proj['plan_y'] + proj['plan_height'] / 2 + pixel_y
                
                return (pdf_x, pdf_y)
            
            print(f"[PLAN] 📍 Zone {zone.get('numero')} : {len(modules_positions)} modules à dessiner")
            print(f"[PLAN] 🔧 Facteurs GPS: lng={gps_conversion.get('metersPerDegreeLng')}, lat={gps_conversion.get('metersPerDegreeLat')}")
            
            # Dessiner chaque module individuellement
            for i, mod in enumerate(modules_positions):
                corners = mod.get('corners', [])
                if len(corners) < 4:
                    continue
                
                # Convertir les 4 coins GPS → PDF
                path = c.beginPath()
                first = True
                
                for corner in corners:
                    lat, lon = corner.get('lat'), corner.get('lng')
                    if lat and lon:
                        pdf_x, pdf_y = gps_to_pdf_zone(lat, lon)
                        
                        if first:
                            path.moveTo(pdf_x, pdf_y)
                            first = False
                        else:
                            path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Style module (bleu semi-transparent)
                c.setFillColor(colors.HexColor('#4285F4'), alpha=0.4)
                c.setStrokeColor(colors.HexColor('#1976D2'))
                c.setLineWidth(0.5)
                c.drawPath(path, stroke=1, fill=1)
            
            print(f"[PLAN] ✅ Zone {zone.get('numero')} : {len(modules_positions)} modules dessinés")
    
    def _fill_zone_with_modules(self, c, zone_points, nb_cols, nb_rows, 
                                mod_l, mod_w, orientation):
        """Remplit une zone avec les modules"""
        if not zone_points:
            return
        
        # Point de départ (premier coin)
        start_x, start_y = zone_points[0]
        
        # Dimensions module selon orientation
        if orientation == 'paysage':
            mod_w_m, mod_h_m = mod_l, mod_w  # 2.28×1.13
        else:
            mod_w_m, mod_h_m = mod_w, mod_l  # 1.13×2.28
        
        proj = self.projection
        mod_w_pdf = mod_w_m / proj['meters_per_pixel_x']
        mod_h_pdf = mod_h_m / proj['meters_per_pixel_y']
        
        # Dessiner grille de modules (échantillonné pour performance)
        sample = max(1, int(nb_cols * nb_rows / 100))  # Max 100 modules affichés
        
        c.setFillColor(colors.HexColor('#2196F3'))
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.setLineWidth(0.5)
        
        for row in range(0, nb_rows, sample):
            for col in range(0, nb_cols, sample):
                mod_x = start_x + col * (mod_w_pdf + 0.02/proj['meters_per_pixel_x'])
                mod_y = start_y + row * (mod_h_pdf + 0.02/proj['meters_per_pixel_y'])
                
                c.rect(mod_x, mod_y, mod_w_pdf, mod_h_pdf, fill=1, stroke=1)
    
    def _draw_measurements(self, c):
        """Dessine les cotations du bâtiment"""
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if not lat or not lon:
            return
        
        pdf_x, pdf_y = self._gps_to_pdf(lat, lon)
        
        try:
            longueur = float(self.data.get('longueur_batiment_m', 15))
            largeur = float(self.data.get('largeur_batiment_m', 10))
        except:
            longueur, largeur = 15, 10
        
        proj = self.projection
        bat_w = longueur / proj['meters_per_pixel_x']
        bat_h = largeur / proj['meters_per_pixel_y']
        
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setFont("Helvetica-Bold", 9)
        c.setLineWidth(1.5)
        
        # Cotation longueur
        cote_y = pdf_y - bat_h/2 - 1*cm
        c.line(pdf_x - bat_w/2, cote_y, pdf_x + bat_w/2, cote_y)
        c.line(pdf_x - bat_w/2, cote_y - 0.2*cm, pdf_x - bat_w/2, cote_y + 0.2*cm)
        c.line(pdf_x + bat_w/2, cote_y - 0.2*cm, pdf_x + bat_w/2, cote_y + 0.2*cm)
        c.drawCentredString(pdf_x, cote_y - 0.6*cm, f"{longueur:.2f} m")
        
        # Cotation largeur
        cote_x = pdf_x + bat_w/2 + 1*cm
        c.line(cote_x, pdf_y - bat_h/2, cote_x, pdf_y + bat_h/2)
        c.line(cote_x - 0.2*cm, pdf_y - bat_h/2, cote_x + 0.2*cm, pdf_y - bat_h/2)
        c.line(cote_x - 0.2*cm, pdf_y + bat_h/2, cote_x + 0.2*cm, pdf_y + bat_h/2)
        
        c.saveState()
        c.translate(cote_x + 0.6*cm, pdf_y)
        c.rotate(90)
        c.drawCentredString(0, 0, f"{largeur:.2f} m")
        c.restoreState()
    
    def _draw_legend(self, c):
        """Dessine la légende"""
        x = 3*cm
        y = 6*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "LÉGENDE:")
        
        y -= 0.5*cm
        
        # Parcelle
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(4)
        c.setDash(10, 5)
        c.line(x, y, x + 1*cm, y)
        c.setDash()
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Limites parcelles cadastrales")
        
        y -= 0.5*cm
        
        # Note
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(x, y, "Plan issu du calpinage photovoltaïque")
    
    def _draw_cartouche(self, c):
        """Cartouche technique"""
        x = self.width - 10*cm
        y = 4*cm
        w = 8*cm
        h = 3*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, w, h)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 0.3*cm, y + h - 0.6*cm, "CARACTÉRISTIQUES TECHNIQUES")
        
        info_y = y + h - 1.5*cm
        
        # Parcelles
        parcelles = self._extract_parcelles()
        if parcelles:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Parcelles cadastrales :")
            info_y -= 0.4*cm
            c.setFont("Helvetica", 8)
            for p in parcelles[:3]:
                section = p.get('section', '')
                numero = p.get('numero', '')
                surface = p.get('surface', '')
                c.drawString(x + 0.5*cm, info_y, f"• {section}{numero} - {surface} m²")
                info_y -= 0.35*cm
        
        # Installation PV
        info_y -= 0.2*cm
        if self.calpinage and 'zones' in self.calpinage:
            total_modules = sum(z.get('nbModules', 0) for z in self.calpinage['zones'])
            puissance_module = self.calpinage.get('module', {}).get('puissance', 560)
            puissance_totale = total_modules * float(puissance_module) / 1000  # kWc
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3*cm, info_y, "Installation photovoltaïque :")
            info_y -= 0.4*cm
            c.setFont("Helvetica", 8)
            c.drawString(x + 0.5*cm, info_y, f"• {total_modules} modules")
            info_y -= 0.35*cm
            c.drawString(x + 0.5*cm, info_y, f"• Puissance : {puissance_totale:.2f} kWc")
            info_y -= 0.35*cm
            c.drawString(x + 0.5*cm, info_y, f"• {len(self.calpinage['zones'])} zone(s) PV")
        
        # Date et signature
        info_y = y + 0.5*cm
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.3*cm, info_y, "Date : _______________")
        c.drawString(x + w/2 + 0.3*cm, info_y, "Signature :")
    
    def _extract_parcelles(self):
        """Extrait les parcelles cadastrales"""
        parcelles_data = self.data.get('parcelles_cadastrales', [])
        
        if isinstance(parcelles_data, list):
            return parcelles_data
        
        if isinstance(parcelles_data, str) and parcelles_data:
            try:
                return json.loads(parcelles_data)
            except:
                return []
        
        return []


def generate_plan_masse(prospect_data, calpinage_data=None):
    """
    Génère un plan de masse cadastral avec calpinage PV
    
    Args:
        prospect_data: dict avec données prospect (parcelles, adresse, lat/lon, dimensions bâtiment)
        calpinage_data: dict optionnel avec zones PV et modules
        
    Returns:
        BytesIO buffer du PDF
    """
    generator = PlanMasseGeneratorV2(prospect_data, calpinage_data)
    return generator.generate()
