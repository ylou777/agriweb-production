"""
Plan de Masse SIMPLE - Génération directe depuis coordonnées GPS
Sans capture d'écran, sans complications
"""

from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io
import requests
from PIL import Image
import math


class PlanMasseSimple:
    """Générateur simplifié de plan de masse"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = A3
        
        # Zone de dessin (en cm)
        self.plan_x = 3*cm
        self.plan_y = 8*cm
        self.plan_width = self.width - 6*cm
        self.plan_height = self.height - 14*cm
        
    def generate(self):
        """Génère le PDF"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A3)
        
        # En-tête
        self._draw_header(c)
        
        # Cadre du plan
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(self.plan_x, self.plan_y, self.plan_width, self.plan_height)
        
        # 1. Image satellite
        sat_image = self._get_satellite_image()
        if sat_image:
            c.drawImage(ImageReader(sat_image), 
                       self.plan_x, self.plan_y,
                       width=self.plan_width, height=self.plan_height,
                       preserveAspectRatio=False)
        
        # 2. Dessiner les modules directement depuis les coordonnées GPS
        if self.calpinage and 'zones' in self.calpinage:
            self._draw_modules_from_gps(c)
        
        # Légende
        self._draw_legend(c)
        
        # Cartouche
        self._draw_cartouche(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_header(self, c):
        """En-tête"""
        y = self.height - 2*cm
        c.setFont("Helvetica-Bold", 16)
        c.drawString(3*cm, y, "PLAN DE MASSE - INSTALLATION PHOTOVOLTAÏQUE")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 10)
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"{adresse}, {commune}")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(self.width - 3*cm, y, "Échelle 1/500")
    
    def _get_satellite_image(self):
        """Récupère l'image satellite statique"""
        try:
            lat = float(self.data.get('latitude', 0))
            lon = float(self.data.get('longitude', 0))
            
            if lat == 0 or lon == 0:
                return None
            
            # Calculer la bbox (environ 100m de rayon)
            # À 45° latitude: 1 degré ≈ 111km
            delta = 0.0009  # ≈ 100m
            
            # Image 1200x900 pour bonne qualité
            width_px = 1200
            height_px = 900
            
            # API Mapbox satellite
            mapbox_token = "pk.eyJ1IjoieWxvdTc3NyIsImEiOiJjbTRyOGJ5aTQwNHduMm1zYWJ0YWEzaTRsIn0.FVO3aJy_MiAW0wXO8rtX6w"
            
            # Style satellite
            url = f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/{lon},{lat},18,0/{width_px}x{height_px}@2x?access_token={mapbox_token}"
            
            print(f"[PLAN] 📡 Téléchargement image satellite...")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"[PLAN] ✅ Image satellite téléchargée ({len(response.content)} bytes)")
                return io.BytesIO(response.content)
            else:
                print(f"[PLAN] ❌ Erreur API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[PLAN] ❌ Erreur satellite: {e}")
            return None
    
    def _draw_modules_from_gps(self, c):
        """Dessine les modules depuis leurs coordonnées GPS réelles"""
        try:
            zones = self.calpinage.get('zones', [])
            
            if not zones:
                print("[PLAN] ⚠️ Pas de zones dans le calepinage")
                return
            
            # Coordonnées du centre
            center_lat = float(self.data.get('latitude', 0))
            center_lon = float(self.data.get('longitude', 0))
            
            print(f"[PLAN] 📍 Centre: {center_lat}, {center_lon}")
            print(f"[PLAN] 🔲 Zones à dessiner: {len(zones)}")
            
            # Dessiner chaque zone
            for idx, zone in enumerate(zones):
                bounds = zone.get('bounds', {})
                
                # Récupérer les coordonnées GPS des coins
                north = bounds.get('_northEast', {}).get('lat')
                east = bounds.get('_northEast', {}).get('lng')
                south = bounds.get('_southWest', {}).get('lat')
                west = bounds.get('_southWest', {}).get('lng')
                
                if not all([north, east, south, west]):
                    print(f"[PLAN] ⚠️ Zone {idx}: coordonnées manquantes")
                    continue
                
                # Convertir GPS → PDF
                x1, y1 = self._gps_to_pdf(south, west, center_lat, center_lon)
                x2, y2 = self._gps_to_pdf(north, east, center_lat, center_lon)
                
                # Dimensions du rectangle
                rect_x = min(x1, x2)
                rect_y = min(y1, y2)
                rect_w = abs(x2 - x1)
                rect_h = abs(y2 - y1)
                
                # Dessiner le rectangle de la zone
                c.setStrokeColor(colors.HexColor('#2196F3'))
                c.setFillColor(colors.HexColor('#2196F3'))
                c.setFillAlpha(0.3)
                c.setLineWidth(2)
                c.rect(rect_x, rect_y, rect_w, rect_h, fill=1, stroke=1)
                
                # Dessiner les modules individuels
                nb_modules = zone.get('nbModules', 0)
                module_width_m = zone.get('largeurModule', 1.134)
                module_height_m = zone.get('hauteurModule', 1.722)
                
                # Convertir dimensions modules en pixels PDF
                module_w_pdf = self._meters_to_pdf(module_width_m)
                module_h_pdf = self._meters_to_pdf(module_height_m)
                
                # Disposition des modules dans la zone
                cols = zone.get('cols', 1)
                rows = zone.get('rows', 1)
                
                c.setFillAlpha(1)
                c.setFillColor(colors.HexColor('#1565C0'))
                
                for row in range(rows):
                    for col in range(cols):
                        # Position relative dans la zone
                        mod_x = rect_x + col * module_w_pdf
                        mod_y = rect_y + row * module_h_pdf
                        
                        # Dessiner le module
                        c.rect(mod_x, mod_y, module_w_pdf, module_h_pdf, fill=1, stroke=0)
                
                # Label de la zone
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 10)
                label = f"{nb_modules} modules ({zone.get('puissance', 0):.2f} kWc)"
                c.drawString(rect_x + 2*mm, rect_y + rect_h + 2*mm, label)
                
                print(f"[PLAN] ✅ Zone {idx}: {nb_modules} modules dessinés")
                
        except Exception as e:
            print(f"[PLAN] ❌ Erreur dessin modules: {e}")
            import traceback
            traceback.print_exc()
    
    def _gps_to_pdf(self, lat, lon, center_lat, center_lon):
        """Convertit GPS → coordonnées PDF"""
        # Delta par rapport au centre
        delta_lat = lat - center_lat
        delta_lon = lon - center_lon
        
        # Conversion degrés → mètres
        meters_per_deg_lat = 111000
        meters_per_deg_lon = 111000 * math.cos(math.radians(center_lat))
        
        meters_y = delta_lat * meters_per_deg_lat
        meters_x = delta_lon * meters_per_deg_lon
        
        # Échelle 1/500 → 1m = 2mm sur le plan
        # Mais on a une zone de 30x20cm → représente environ 150x100m
        scale_x = self.plan_width / 150  # pixels PDF par mètre
        scale_y = self.plan_height / 100
        
        # Position PDF (centre + offset)
        pdf_x = self.plan_x + self.plan_width / 2 + meters_x * scale_x
        pdf_y = self.plan_y + self.plan_height / 2 + meters_y * scale_y
        
        return (pdf_x, pdf_y)
    
    def _meters_to_pdf(self, meters):
        """Convertit des mètres en pixels PDF selon l'échelle"""
        # Échelle approximative de la zone
        scale = self.plan_width / 150  # pixels PDF par mètre
        return meters * scale
    
    def _draw_legend(self, c):
        """Légende"""
        x = 3*cm
        y = 6*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "LÉGENDE:")
        
        y -= 0.5*cm
        c.setFont("Helvetica", 9)
        
        # Module PV
        c.setFillColor(colors.HexColor('#1565C0'))
        c.rect(x, y - 3*mm, 8*mm, 4*mm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.drawString(x + 1*cm, y, "Modules photovoltaïques")
        
        y -= 0.5*cm
        c.setStrokeColor(colors.HexColor('#2196F3'))
        c.setLineWidth(2)
        c.rect(x, y - 3*mm, 8*mm, 4*mm, fill=0, stroke=1)
        c.drawString(x + 1*cm, y, "Zones d'installation")
    
    def _draw_cartouche(self, c):
        """Cartouche technique"""
        x = self.width - 10*cm
        y = 6*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y - 3*cm, 7*cm, 3*cm)
        
        y_text = y - 0.5*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 0.3*cm, y_text, "INFORMATIONS TECHNIQUES")
        
        y_text -= 0.5*cm
        c.setFont("Helvetica", 8)
        
        # Puissance totale
        total_kwc = 0
        if self.calpinage:
            total_kwc = sum(z.get('puissance', 0) for z in self.calpinage.get('zones', []))
        
        c.drawString(x + 0.3*cm, y_text, f"Puissance totale: {total_kwc:.2f} kWc")
        
        y_text -= 0.4*cm
        total_modules = 0
        if self.calpinage:
            total_modules = sum(z.get('nbModules', 0) for z in self.calpinage.get('zones', []))
        c.drawString(x + 0.3*cm, y_text, f"Nombre de modules: {total_modules}")
        
        y_text -= 0.4*cm
        c.drawString(x + 0.3*cm, y_text, f"Échelle: 1/500")


def generate_plan_masse_simple(prospect_data, calpinage_data=None):
    """Fonction d'entrée pour générer le plan"""
    generator = PlanMasseSimple(prospect_data, calpinage_data)
    return generator.generate()
