"""
Plan de Masse = SCREENSHOT UNIQUEMENT
AUCUN calcul GPS, AUCUN redessin de modules
Juste afficher le screenshot du calpinage Leaflet
"""

from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io
import json
import base64


class PlanMasseGenerator:
    """Plan de masse = Screenshot du calpinage, point final"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = A3
        
    def generate(self):
        """Génère le PDF avec screenshot uniquement"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A3)
        
        # En-tête
        self._draw_header(c)
        
        # JUSTE LE SCREENSHOT
        self._draw_screenshot(c)
        
        # Légende minimaliste
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
        
        y -= 0.7*cm
        c.setFont("Helvetica", 10)
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"{adresse}, {commune}")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(self.width - 3*cm, y, "Echelle 1/200")
    
    def _draw_screenshot(self, c):
        """Affiche le screenshot Leaflet (vue exacte du calpinage)"""
        print(f"\n[PLAN SIMPLE] ===== SCREENSHOT UNIQUEMENT =====")
        
        # Zone de dessin
        plan_x = 3*cm
        plan_y = 8*cm
        plan_width = self.width - 6*cm
        plan_height = self.height - 14*cm
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(plan_x, plan_y, plan_width, plan_height)
        
        # Récupérer le screenshot
        screenshot_img = self._get_map_screenshot()
        
        if screenshot_img:
            print(f"[PLAN SIMPLE] ✅ Screenshot trouvé - Affichage")
            c.drawImage(ImageReader(screenshot_img), 
                      plan_x, plan_y, 
                      width=plan_width, height=plan_height,
                      preserveAspectRatio=False, mask='auto')
        else:
            print(f"[PLAN SIMPLE] ❌ Pas de screenshot")
            c.setFillColor(colors.white)
            c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
            
            c.setFillColor(colors.red)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(plan_x + plan_width/2, plan_y + plan_height/2, 
                              "⚠️ Screenshot non disponible")
            c.setFont("Helvetica", 10)
            c.drawCentredString(plan_x + plan_width/2, plan_y + plan_height/2 - 0.5*cm, 
                              "Veuillez sauvegarder le calpinage")
    
    def _get_map_screenshot(self):
        """Récupère le screenshot Leaflet"""
        # Chercher dans data_json.calpinage.screenshot_map
        screenshot_data = None
        
        if self.calpinage:
            screenshot_data = self.calpinage.get('screenshot_map')
        
        if not screenshot_data and self.data.get('data_json'):
            try:
                if isinstance(self.data['data_json'], str):
                    data_json = json.loads(self.data['data_json'])
                else:
                    data_json = self.data['data_json']
                    
                calpinage = data_json.get('calpinage', {})
                screenshot_data = calpinage.get('screenshot_map')
            except:
                pass
        
        if not screenshot_data:
            print("[PLAN SIMPLE] Pas de screenshot_map trouvé")
            return None
        
        print(f"[PLAN SIMPLE] Screenshot trouvé: {len(screenshot_data)} chars")
        
        try:
            if isinstance(screenshot_data, str):
                if screenshot_data.startswith('data:image'):
                    base64_data = screenshot_data.split(',')[1]
                    image_data = base64.b64decode(base64_data)
                    return io.BytesIO(image_data)
                else:
                    image_data = base64.b64decode(screenshot_data)
                    return io.BytesIO(image_data)
        except Exception as e:
            print(f"[PLAN SIMPLE] Erreur décodage screenshot: {e}")
        
        return None
    
    def _draw_legend(self, c):
        """Légende minimaliste"""
        x = 3*cm
        y = 6*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "LÉGENDE :")
        
        y -= 0.5*cm
        c.setFont("Helvetica", 9)
        
        # Modules PV
        c.setFillColor(colors.HexColor('#2196F3'))
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.rect(x, y - 0.25*cm, 1.5*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 2*cm, y - 0.15*cm, "Modules photovoltaïques")
    
    def _draw_cartouche(self, c):
        """Cartouche technique"""
        x = self.width - 15*cm
        y = 6*cm
        w = 12*cm
        h = 6*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, w, h)
        
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + w/2, y + h - 0.7*cm, "CARACTÉRISTIQUES TECHNIQUES")
        
        c.setFont("Helvetica", 9)
        yy = y + h - 1.5*cm
        
        if self.calpinage:
            # Nombre total de modules
            total_modules = sum(zone.get('nbModules', 0) for zone in self.calpinage.get('zones', []))
            puissance_kw = sum(zone.get('puissanceKw', 0) for zone in self.calpinage.get('zones', []))
            
            c.drawString(x + 0.3*cm, yy, f"Installation photovoltaïque")
            yy -= 0.5*cm
            c.drawString(x + 0.3*cm, yy, f"{total_modules} modules → {puissance_kw:.2f} kWc")
            yy -= 0.5*cm
            
            module_info = self.calpinage.get('module', {})
            if module_info:
                nom = module_info.get('nom', 'Module PV')
                c.drawString(x + 0.3*cm, yy, f"Modules: {nom}")
        
        # Date et signature
        yy = y + 0.5*cm
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.3*cm, yy, "Date : ____________")
        c.drawString(x + 6*cm, yy, "Signature : ____________")


def generate_plan_masse(prospect_data, calpinage_data=None):
    """Fonction principale"""
    generator = PlanMasseGenerator(prospect_data, calpinage_data)
    return generator.generate()
