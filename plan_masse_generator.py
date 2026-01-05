"""
Générateur de Plan de Masse Cadastral avec Calpinage PV
Version simplifiée et professionnelle
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


class PlanMasseGenerator:
    """Génère un plan de masse cadastral avec implantation PV réelle"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = A3  # Format A3 pour plus de détails
        
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
        
        y -= 0.7*cm
        c.setFont("Helvetica", 10)
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"{adresse}, {commune}")
        
        # Échelle
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(self.width - 3*cm, y, "Échelle 1/200")
        
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
        
        # Fond
        c.setFillColor(colors.HexColor('#F5F5F5'))
        c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        # Calculer bbox réelle basée sur les dimensions
        bbox_meters = self._calculate_bbox_from_data()
        
        # 🔥 CORRECTION: Calculer la bbox GPS AVANT de récupérer l'image
        # pour assurer cohérence entre image et conversion GPS→PDF
        meters_to_lat = bbox_meters / 111000
        meters_to_lon = bbox_meters / (111000 * 0.7)  # cos(45°)
        
        # Stocker les limites GPS réelles
        self.gps_bounds = {
            'min_lat': lat - meters_to_lat,
            'max_lat': lat + meters_to_lat,
            'min_lon': lon - meters_to_lon,
            'max_lon': lon + meters_to_lon
        }
        
        if lat and lon:
            # 🔥 PRIORITÉ 1: Utiliser le screenshot de la carte si disponible
            screenshot_data = self.calpinage.get('screenshot_map') if self.calpinage else None
            
            if screenshot_data:
                try:
                    # Le screenshot est en base64 data URL: "data:image/png;base64,..."
                    import base64
                    import re
                    
                    # Extraire les données base64
                    base64_match = re.search(r'base64,(.+)', screenshot_data)
                    if base64_match:
                        base64_str = base64_match.group(1)
                        img_data = base64.b64decode(base64_str)
                        img_buffer = io.BytesIO(img_data)
                        
                        print(f"[PLAN] 📸 Utilisation du screenshot de la carte ({len(img_data)} bytes)")
                        
                        # Récupérer les métadonnées de la carte pour calibrer GPS→PDF
                        map_metadata = self.calpinage.get('map_metadata', {})
                        if map_metadata and 'bounds' in map_metadata:
                            bounds = map_metadata['bounds']
                            self.gps_bounds = {
                                'min_lat': bounds['south'],
                                'max_lat': bounds['north'],
                                'min_lon': bounds['west'],
                                'max_lon': bounds['east']
                            }
                            print(f"[PLAN] 🗺️ Utilisation des bounds de la carte Leaflet")
                        
                        # Dessiner le screenshot (EXACT de Leaflet)
                        c.drawImage(ImageReader(img_buffer), 
                                  plan_x, plan_y, 
                                  width=plan_width, height=plan_height,
                                  preserveAspectRatio=True, anchor='c', mask='auto')
                        
                        screenshot_used = True
                    else:
                        screenshot_used = False
                except Exception as e:
                    print(f"[PLAN] ⚠️ Erreur lecture screenshot: {e}")
                    screenshot_used = False
            else:
                screenshot_used = False
            
            # 🔥 FALLBACK: Image satellite si pas de screenshot
            if not screenshot_used:
                satellite_img = self._fetch_satellite_image_bbox(lat, lon, bbox_meters, width=1200, height=1000)
                if satellite_img:
                    # 🔥 CORRECTION: Conserver l'aspect ratio pour éviter déformation
                    c.drawImage(ImageReader(satellite_img), 
                              plan_x, plan_y, 
                              width=plan_width, height=plan_height,
                              preserveAspectRatio=True, anchor='c', mask='auto')
        
        # Système de coordonnées : conversion GPS → PDF
        # Centre du plan = position GPS du bâtiment
        self.plan_bbox = {
            'x': plan_x,
            'y': plan_y,
            'width': plan_width,
            'height': plan_height,
            'lat_center': lat,
            'lon_center': lon,
            'meters_per_cm': bbox_meters / (plan_width / cm) if plan_width > 0 else 1
        }
        
        # 1. PARCELLES CADASTRALES (avec vraies géométries si disponibles)
        self._draw_parcelles(c, bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2, lat, lon)
        
        # 2. BÂTIMENT (à la position GPS)
        self._draw_batiment(c, bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2)
        
        # 3. MODULES PV selon COORDONNÉES GPS DU CALPINAGE
        if self.calpinage:
            self._draw_modules_pv_from_gps(c)
        
        # 4. COTATIONS
        self._draw_cotations(c, bbox['x'] + bbox['width']/2, bbox['y'] + bbox['height']/2)
        
    def _calculate_bbox_from_data(self):
        """Calcule la taille de la bbox en mètres basée sur les données"""
        # Estimer depuis les parcelles ou défaut 60m
        parcelles = self._extract_parcelles()
        if parcelles:
            total_surface = sum(float(p.get('surface', 0)) for p in parcelles)
            if total_surface > 0:
                # Approximation: bbox = racine(surface) * 1.5 pour avoir de la marge
                return (total_surface ** 0.5) * 1.5
        
        # Défaut: 60m de rayon (120m de côté)
        return 60
    
    def _lat_lon_to_pdf(self, lat, lon):
        """
        Convertit coordonnées GPS en coordonnées PDF
        Utilise les MÊMES limites GPS que l'image satellite pour assurer l'alignement
        """
        if not hasattr(self, 'plan_bbox') or not hasattr(self, 'gps_bounds'):
            return (0, 0)
        
        bbox = self.plan_bbox
        gps = self.gps_bounds
        
        # 🔥 CORRECTION: Conversion GPS → PDF basée sur les limites GPS réelles de l'image
        # Normaliser lat/lon dans l'intervalle [0, 1] par rapport aux limites
        lat_ratio = (lat - gps['min_lat']) / (gps['max_lat'] - gps['min_lat'])
        lon_ratio = (lon - gps['min_lon']) / (gps['max_lon'] - gps['min_lon'])
        
        # Convertir en coordonnées PDF
        # ⚠️ Attention: PDF Y augmente vers le haut, mais latitude aussi
        pdf_x = bbox['x'] + lon_ratio * bbox['width']
        pdf_y = bbox['y'] + lat_ratio * bbox['height']
        
        return (pdf_x, pdf_y)
    
    def _draw_parcelles(self, c, center_x, center_y, lat, lon):
        """Dessine les parcelles avec leurs vraies géométries GeoJSON si disponibles"""
        parcelles = self._extract_parcelles()
        
        if not parcelles:
            return
        
        for i, parcelle in enumerate(parcelles):
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            geojson = parcelle.get('geojson')
            
            # Si géométrie GeoJSON disponible, l'utiliser
            if geojson and isinstance(geojson, dict):
                self._draw_parcelle_from_geojson(c, geojson, section, numero, surface)
            else:
                # Fallback: rectangle approximatif centré
                self._draw_parcelle_approximative(c, section, numero, surface, i, len(parcelles))
    
    def _draw_parcelle_from_geojson(self, c, geojson, section, numero, surface):
        """Dessine une parcelle depuis sa géométrie GeoJSON réelle"""
        try:
            geometry = geojson.get('geometry', geojson)
            coords = geometry.get('coordinates', [])
            geom_type = geometry.get('type', '')
            
            if geom_type == 'Polygon' and coords:
                # Prendre le premier ring (exterior)
                exterior_ring = coords[0]
                
                # Convertir chaque point GPS → PDF
                path = c.beginPath()
                first_point = True
                
                for coord in exterior_ring:
                    lon, lat = coord[0], coord[1]
                    pdf_x, pdf_y = self._lat_lon_to_pdf(lat, lon)
                    
                    if first_point:
                        path.moveTo(pdf_x, pdf_y)
                        first_point = False
                        label_x, label_y = pdf_x, pdf_y  # Position étiquette
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                
                # Dessiner contour parcelle
                c.setStrokeColor(colors.HexColor('#FF00FF'))  # Magenta
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
                return
        except Exception as e:
            print(f"[PLAN] Erreur dessin parcelle GeoJSON: {e}")
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
        
        # Échelle
        meters_per_cm = bbox['meters_per_cm']
        parc_w = (longueur / meters_per_cm) * cm
        parc_h = (largeur / meters_per_cm) * cm
        
        # Décalage si plusieurs parcelles
        offset_x = (index - total/2) * 5 * cm
        
        parc_x = center_x - parc_w/2 + offset_x
        parc_y = center_y - parc_h/2
        
        # Contour
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(3)
        c.setDash(8, 4)
        c.rect(parc_x, parc_y, parc_w, parc_h, fill=0, stroke=1)
        c.setDash()
        
        # Étiquette
        c.setFillColor(colors.HexColor('#FF00FF'))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(parc_x + 0.3*cm, parc_y + parc_h + 0.3*cm, 
                    f"Parcelle {section}{numero}")
        c.setFont("Helvetica", 8)
        c.drawString(parc_x + 0.3*cm, parc_y + parc_h - 0.2*cm, 
                    f"{surface} m²")
    
    def _draw_parcelles(self, c, center_x, center_y, lat, lon):
        """DEPRECATED - Utiliser _draw_parcelles_geojson"""
        pass
    
    def _draw_batiment(self, c, center_x, center_y):
        """Dessine le bâtiment"""
        echelle = 0.3  # cm par mètre
        
        # Dimensions avec conversion sécurisée
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
        
        # Rectangle bâtiment
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.HexColor('#FFE4B5'))  # Beige
        c.setLineWidth(2)
        c.rect(bat_x, bat_y, bat_w, bat_h, fill=1, stroke=1)
        
        # Étiquette
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(center_x, center_y, "BÂTIMENT")
    
    def _draw_modules_pv_reels(self, c, center_x, center_y, lat, lon):
        """DEPRECATED - Utiliser _draw_modules_pv_from_gps à la place"""
        pass
    
    def _draw_modules_pv_from_gps(self, c):
        """Dessine les modules PV selon leurs VRAIES coordonnées GPS sauvegardées"""
        
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        zones = self.calpinage['zones']
        
        for zone in zones:
            # Récupérer les positions GPS de chaque module
            modules_positions = zone.get('modulesPositions', [])
            
            if not modules_positions:
                print(f"[PLAN] ⚠️ Aucune position GPS pour zone {zone.get('numero', '?')}")
                continue
            
            print(f"[PLAN] 📍 Dessin {len(modules_positions)} modules avec coordonnées GPS pour zone {zone.get('numero', '?')}")
            
            # Dessiner chaque module selon ses coordonnées GPS
            c.setStrokeColor(colors.HexColor('#1565C0'))  # Bleu foncé
            c.setFillColor(colors.HexColor('#2196F3'))    # Bleu clair
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
                
                # Contour zone rouge en pointillés
                c.setStrokeColor(colors.HexColor('#D32F2F'))
                c.setLineWidth(2)
                c.setDash(4, 2)
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()
                
                # Étiquette zone
                if zone_coords:
                    label_x, label_y = self._lat_lon_to_pdf(zone_coords[0]['lat'], zone_coords[0]['lng'])
                    c.setFillColor(colors.HexColor('#D32F2F'))
                    c.setFont("Helvetica-Bold", 8)
                    nb_modules = zone.get('nbModules', len(modules_positions))
                    nb_cols = zone.get('nbCols', 0)
                    nb_rows = zone.get('nbRows', 0)
                    c.drawString(label_x + 0.4*cm, label_y + 0.4*cm,
                                f"Zone PV: {nb_modules} modules ({nb_cols}×{nb_rows})")

    
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
        """Dessine la légende"""
        x = 3*cm
        y = 6*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(x, y, "LÉGENDE :")
        
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
        
        # Bâtiment
        y -= 0.5*cm
        c.setFillColor(colors.HexColor('#FFE4B5'))
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Bâtiment existant")
        
        # Modules PV
        y -= 0.5*cm
        c.setFillColor(colors.HexColor('#2196F3'))
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Modules photovoltaïques (position réelle)")
        
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
        c.drawString(x + 2*cm, y - 0.15*cm, "Cotations (en mètres)")
    
    def _draw_cartouche(self, c):
        """Cartouche technique"""
        x = self.width - 15*cm
        y = 6*cm
        w = 12*cm
        h = 6*cm
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, w, h)
        
        # Titre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(x, y + h - 0.8*cm, w, 0.8*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + w/2, y + h - 0.55*cm, "CARACTÉRISTIQUES TECHNIQUES")
        
        # Contenu
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
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
    
    def _fetch_satellite_image(self, lat, lon, zoom=19, width=1200, height=1000):
        """Récupère une image satellite via API"""
        try:
            # ArcGIS World Imagery (gratuit, haute résolution)
            url = f"https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            # Calculer bbox autour du point
            # À zoom 19, ~10m de rayon
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
        Récupère une image satellite avec une bbox en mètres autour du point central
        
        Args:
            lat, lon: Coordonnées GPS du centre
            bbox_meters: Rayon en mètres pour la bbox
            width, height: Dimensions de l'image en pixels
            
        Returns:
            BytesIO de l'image ou None
        """
        try:
            # Conversion mètres → degrés (approximatif pour France métropolitaine)
            # 1 degré latitude ≈ 111 km
            # 1 degré longitude ≈ 111 km * cos(latitude) ≈ 78 km à 45° de latitude
            meters_to_lat = bbox_meters / 111000
            meters_to_lon = bbox_meters / (111000 * 0.7)  # cos(45°) ≈ 0.7
            
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
            
            print(f"[PLAN] 🛰️ Téléchargement image satellite: bbox={bbox_meters:.0f}m, size={width}x{height}")
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                print(f"[PLAN] ✅ Image satellite téléchargée ({len(response.content)} bytes)")
                return io.BytesIO(response.content)
            else:
                print(f"[PLAN] ❌ Erreur API: {response.status_code}")
        except Exception as e:
            print(f"[PLAN] ❌ Erreur image satellite: {e}")
        
        return None
    
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
    generator = PlanMasseGenerator(prospect_data, calpinage_data)
    return generator.generate()
