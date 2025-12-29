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
        
        if lat and lon:
            # Image satellite de fond
            satellite_img = self._fetch_satellite_image(lat, lon, zoom=19, width=1200, height=1000)
            if satellite_img:
                c.drawImage(ImageReader(satellite_img), 
                          plan_x, plan_y, 
                          width=plan_width, height=plan_height,
                          preserveAspectRatio=True, mask='auto')
        
        # Centre du plan
        center_x = plan_x + plan_width / 2
        center_y = plan_y + plan_height / 2
        
        # 1. PARCELLES CADASTRALES
        self._draw_parcelles(c, center_x, center_y, lat, lon)
        
        # 2. BÂTIMENT
        self._draw_batiment(c, center_x, center_y)
        
        # 3. MODULES PV selon CALPINAGE RÉEL
        if self.calpinage:
            self._draw_modules_pv_reels(c, center_x, center_y, lat, lon)
        
        # 4. COTATIONS
        self._draw_cotations(c, center_x, center_y)
        
    def _draw_parcelles(self, c, center_x, center_y, lat, lon):
        """Dessine les limites des parcelles cadastrales"""
        parcelles = self._extract_parcelles()
        
        if not parcelles:
            return
        
        # Échelle approximative : 1 mètre = 0.3 cm sur le plan (échelle 1/333)
        echelle = 0.3  # cm par mètre
        
        # Pour chaque parcelle
        for i, parcelle in enumerate(parcelles):
            section = parcelle.get('section', '')
            numero = parcelle.get('numero', '')
            surface = parcelle.get('surface', 0)
            
            # Estimer dimensions parcelle depuis surface
            try:
                surface_m2 = float(surface)
                # Approximation rectangulaire (ratio 1.5:1)
                largeur = (surface_m2 / 1.5) ** 0.5
                longueur = largeur * 1.5
            except:
                largeur = 30
                longueur = 45
            
            # Décalage si plusieurs parcelles
            offset_x = (i - len(parcelles)/2) * 5 * cm
            
            # Dimensions sur le plan
            parc_w = longueur * echelle * cm
            parc_h = largeur * echelle * cm
            
            # Position
            parc_x = center_x - parc_w/2 + offset_x
            parc_y = center_y - parc_h/2
            
            # Contour parcelle
            c.setStrokeColor(colors.HexColor('#FF00FF'))  # Magenta
            c.setLineWidth(3)
            c.setDash(8, 4)
            c.rect(parc_x, parc_y, parc_w, parc_h, fill=0, stroke=1)
            c.setDash()  # Reset
            
            # Étiquette parcelle
            c.setFillColor(colors.HexColor('#FF00FF'))
            c.setFont("Helvetica-Bold", 9)
            label = f"Parcelle {section}{numero}\n{surface} m²"
            c.drawString(parc_x + 0.3*cm, parc_y + parc_h + 0.3*cm, 
                        f"Parcelle {section}{numero}")
            c.setFont("Helvetica", 8)
            c.drawString(parc_x + 0.3*cm, parc_y + parc_h - 0.2*cm, 
                        f"{surface} m²")
    
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
        """Dessine les modules PV selon le CALPINAGE RÉEL"""
        
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        echelle = 0.3  # cm par mètre
        
        # Récupérer dimensions module avec conversion sécurisée
        try:
            module_longueur_mm = self.calpinage.get('module', {}).get('longueur', 2278)
            module_largeur_mm = self.calpinage.get('module', {}).get('largeur', 1134)
            
            # Convertir en float (gère string et int)
            module_longueur = float(module_longueur_mm) / 1000  # mm → m
            module_largeur = float(module_largeur_mm) / 1000    # mm → m
        except (ValueError, TypeError):
            # Valeurs par défaut si conversion échoue
            module_longueur = 2.278  # m
            module_largeur = 1.134   # m
        
        # Pour chaque zone du calpinage
        for zone in self.calpinage['zones']:
            nb_modules = zone.get('nbModules', 0)
            nb_cols = zone.get('nbCols', 0)
            nb_rows = zone.get('nbRows', 0)
            orientation_module = zone.get('moduleOrientation', 'paysage')
            
            # Dimensions selon orientation
            if orientation_module == 'paysage':
                mod_h = module_longueur  # 2.28m horizontal
                mod_v = module_largeur   # 1.13m vertical
            else:  # portrait
                mod_h = module_largeur   # 1.13m horizontal
                mod_v = module_longueur  # 2.28m vertical
            
            # Espacement entre modules
            espacement = 0.02  # 2cm entre modules
            
            # Dimensions totales de la zone
            zone_width = nb_cols * (mod_h + espacement)
            zone_height = nb_rows * (mod_v + espacement)
            
            # Position de départ (centré sur bâtiment)
            start_x = center_x - (zone_width * echelle * cm) / 2
            start_y = center_y - (zone_height * echelle * cm) / 2
            
            # Dessiner chaque module
            c.setStrokeColor(colors.HexColor('#1565C0'))  # Bleu foncé
            c.setFillColor(colors.HexColor('#2196F3'))    # Bleu clair
            c.setLineWidth(0.5)
            
            for row in range(nb_rows):
                for col in range(nb_cols):
                    mod_x = start_x + col * (mod_h + espacement) * echelle * cm
                    mod_y = start_y + row * (mod_v + espacement) * echelle * cm
                    mod_w = mod_h * echelle * cm
                    mod_h_draw = mod_v * echelle * cm
                    
                    # Rectangle module
                    c.rect(mod_x, mod_y, mod_w, mod_h_draw, fill=1, stroke=1)
            
            # Contour zone
            c.setStrokeColor(colors.HexColor('#D32F2F'))  # Rouge
            c.setLineWidth(2)
            c.setDash(4, 2)
            c.rect(start_x - 0.1*cm, start_y - 0.1*cm, 
                  zone_width * echelle * cm + 0.2*cm, 
                  zone_height * echelle * cm + 0.2*cm, 
                  fill=0, stroke=1)
            c.setDash()
            
            # Étiquette zone
            c.setFillColor(colors.HexColor('#D32F2F'))
            c.setFont("Helvetica-Bold", 8)
            c.drawString(start_x, start_y + zone_height * echelle * cm + 0.4*cm,
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
