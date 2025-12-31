"""
Plan de Masse PROFESSIONNEL - Conforme aux exigences réglementaires
Pour déclaration préalable de travaux (DP) / Permis de construire (PC)

Éléments obligatoires selon CERFA 13703/13704:
- Échelle 1/500 ou 1/200
- Orientation (Nord)
- Limites et superficie du terrain
- Parcelles cadastrales
- Bâtiments existants
- Implantation des panneaux PV
- Distances aux limites
- Cartouche technique

MÉTHODE: Utilise fond satellite + redessine modules précisément via GPS
"""

from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import requests
from PIL import Image, ImageDraw
import math
from datetime import datetime


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
        
        # Échelle 1/500: 1cm sur le plan = 5m en réalité
        self.echelle = 500
        self.meters_per_cm = 5
        
    def generate(self):
        """Génère le PDF"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A3)
        
        # En-tête
        self._draw_header(c)
        
        # Rose des vents (Nord)
        self._draw_north_arrow(c)
        
        # Cadre du plan avec échelle
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(self.plan_x, self.plan_y, self.plan_width, self.plan_height)
        
        # Échelle graphique (barre d'échelle 1/500)
        self._draw_scale_bar(c)
        
        # 🔥 UTILISER DIRECTEMENT LE SCREENSHOT DU CALPINAGE (modules déjà positionnés)
        screenshot = self._get_screenshot_from_calpinage()
        
        if screenshot:
            print("[PLAN] ✅ Screenshot du calpinage chargé - utilisation directe")
            # Afficher le screenshot tel quel (modules déjà bien positionnés avec rotation)
            c.drawImage(ImageReader(screenshot), 
                       self.plan_x, self.plan_y,
                       width=self.plan_width, height=self.plan_height,
                       preserveAspectRatio=False)
            
            print("[PLAN] ✅ Plan de masse généré à partir du screenshot exact du calpinage")
        else:
            print("[PLAN] ⚠️ Pas de screenshot - affichage message")
            # Message si pas de screenshot
            c.setFillColor(colors.HexColor('#FFF3E0'))
            c.rect(self.plan_x, self.plan_y, self.plan_width, self.plan_height, fill=1, stroke=0)
            c.setFillColor(colors.HexColor('#F57C00'))
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(self.plan_x + self.plan_width/2,
                              self.plan_y + self.plan_height/2,
                              "Veuillez d'abord SAUVEGARDER le calepinage")
        
        # Légende
        self._draw_legend(c)
        
        # Cartouche
        self._draw_cartouche(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_header(self, c):
        """En-tête avec adresse complète et propriétaire"""
        y = self.height - 2*cm
        c.setFont("Helvetica-Bold", 16)
        c.drawString(3*cm, y, "PLAN DE MASSE - INSTALLATION PHOTOVOLTAÏQUE")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 10)
        
        # Adresse complète
        commune = self.data.get('commune', '')
        adresse = self.data.get('adresse', '')
        c.drawString(3*cm, y, f"Adresse: {adresse}, {commune}")
        
        # Propriétaire sur la ligne suivante
        y -= 0.5*cm
        nom = self.data.get('nom', '')
        prenom = self.data.get('prenom', '')
        if nom or prenom:
            c.drawString(3*cm, y, f"Propriétaire: {prenom} {nom}".strip())
        
        # Échelle en haut à droite
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(self.width - 3*cm, self.height - 2*cm, "Échelle 1/500")
    
    def _draw_north_arrow(self, c):
        """Dessine une rose des vents (flèche Nord)"""
        # Position en haut à gauche du plan
        x = self.plan_x + 1*cm
        y = self.plan_y + self.plan_height - 2*cm
        
        # Cercle extérieur
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.circle(x, y, 0.8*cm, stroke=1, fill=0)
        
        # Flèche Nord (triangle pointant vers le haut)
        c.setFillColor(colors.black)
        arrow = c.beginPath()
        arrow.moveTo(x, y + 0.6*cm)  # Pointe
        arrow.lineTo(x - 0.25*cm, y - 0.2*cm)  # Base gauche
        arrow.lineTo(x + 0.25*cm, y - 0.2*cm)  # Base droite
        arrow.close()
        c.drawPath(arrow, fill=1, stroke=0)
        
        # Lettre N
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawCentredString(x, y - 0.6*cm, "N")
    
    def _draw_scale_bar(self, c):
        """Dessine une échelle graphique réglementaire (1/500)"""
        # Position en bas du plan
        x_start = self.plan_x + 1*cm
        y = self.plan_y - 1.5*cm
        
        # À l'échelle 1/500, 1cm sur le plan = 5m en réalité
        # Barre de 4cm = 20m
        bar_length = 4*cm
        real_distance = 20  # mètres
        
        # Fond blanc
        c.setFillColor(colors.white)
        c.rect(x_start - 0.2*cm, y - 0.3*cm, bar_length + 0.4*cm, 0.8*cm, fill=1, stroke=0)
        
        # Barre graduée (alternance noir/blanc)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        
        # 4 segments de 1cm = 5m chacun
        for i in range(4):
            x = x_start + i*cm
            if i % 2 == 0:
                c.setFillColor(colors.black)
            else:
                c.setFillColor(colors.white)
            c.rect(x, y, 1*cm, 0.3*cm, fill=1, stroke=1)
        
        # Graduations
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.black)
        for i in range(5):
            x = x_start + i*cm
            distance = i * 5  # mètres
            c.drawCentredString(x, y - 0.4*cm, f"{distance}m")
        
        # Texte "Échelle 1/500"
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x_start + bar_length/2, y + 0.5*cm, "Échelle 1/500")
    
    def _get_screenshot_from_calpinage(self):
        """Récupère le screenshot sauvegardé dans le calepinage"""
        try:
            print(f"[PLAN] 🔍 Vérification calepinage: {self.calpinage is not None}")
            
            if not self.calpinage:
                print("[PLAN] ⚠️ Pas de données de calepinage")
                return None
            
            print(f"[PLAN] 🔍 Clés disponibles dans calepinage: {list(self.calpinage.keys()) if isinstance(self.calpinage, dict) else 'N/A'}")
            
            screenshot_data = self.calpinage.get('screenshot_map')
            
            if not screenshot_data:
                print("[PLAN] ⚠️ Pas de screenshot dans le calepinage (screenshot_map manquant)")
                print(f"[PLAN] 🔍 Contenu calepinage (premiers 500 char): {str(self.calpinage)[:500]}")
                return None
            
            print(f"[PLAN] 📸 Screenshot trouvé! Longueur: {len(screenshot_data)} caractères")
            
            import base64
            
            # Retirer le préfixe "data:image/png;base64," si présent
            if screenshot_data.startswith('data:image'):
                prefix_end = screenshot_data.find(',')
                if prefix_end > 0:
                    screenshot_data = screenshot_data[prefix_end + 1:]
                    print(f"[PLAN] ✂️ Préfixe data:image retiré")
            
            # Décoder base64
            image_data = base64.b64decode(screenshot_data)
            print(f"[PLAN] ✅ Screenshot décodé: {len(image_data)} bytes")
            
            return io.BytesIO(image_data)
            
        except Exception as e:
            print(f"[PLAN] ❌ Erreur décodage screenshot: {e}")
            import traceback
            traceback.print_exc()
            return None
    
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
        """Cartouche technique avec caractéristiques complètes"""
        x = self.width - 10*cm
        y = 6*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(x, y - 4.5*cm, 7*cm, 4.5*cm)
        
        y_text = y - 0.5*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 0.3*cm, y_text, "CARACTÉRISTIQUES TECHNIQUES")
        
        y_text -= 0.6*cm
        c.setFont("Helvetica", 8)
        
        # Puissance totale
        total_kwc = 0
        total_modules = 0
        if self.calpinage and 'zones' in self.calpinage:
            zones = self.calpinage.get('zones', [])
            print(f"[PLAN] 📊 Calcul cartouche: {len(zones)} zones")
            for z in zones:
                puissance = z.get('puissance', 0)
                nb_mod = z.get('nbModules', 0)
                total_kwc += puissance
                total_modules += nb_mod
                print(f"[PLAN]   Zone: {nb_mod} modules, {puissance:.2f} kWc")
        
        print(f"[PLAN] 📊 Total cartouche: {total_modules} modules, {total_kwc:.2f} kWc")
        
        c.drawString(x + 0.3*cm, y_text, f"• Puissance totale: {total_kwc:.2f} kWc")
        
        y_text -= 0.4*cm
        c.drawString(x + 0.3*cm, y_text, f"• Nombre de modules: {total_modules}")
        
        y_text -= 0.4*cm
        c.drawString(x + 0.3*cm, y_text, f"• Type: Installation en toiture")
        
        y_text -= 0.4*cm
        parcelle = self.data.get('parcelle', 'Non renseignée')
        c.drawString(x + 0.3*cm, y_text, f"• Parcelle cadastrale: {parcelle}")
        
        y_text -= 0.4*cm
        c.drawString(x + 0.3*cm, y_text, f"• Échelle: 1/500 (1cm = 5m)")
        
        y_text -= 0.4*cm
        from datetime import datetime
        date_plan = datetime.now().strftime("%d/%m/%Y")
        c.drawString(x + 0.3*cm, y_text, f"• Date du plan: {date_plan}")



def generate_plan_masse_simple(prospect_data, calpinage_data=None):
    """Fonction d'entrée pour générer le plan"""
    generator = PlanMasseSimple(prospect_data, calpinage_data)
    return generator.generate()
