"""
Générateur de formulaire CERFA 16702-01 - Demande de raccordement Enedis
Pour installations photovoltaïques
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from datetime import datetime
import io

class CerfaGenerator:
    """Génère un formulaire CERFA pré-rempli pour demande de raccordement"""
    
    def __init__(self, prospect_data):
        """
        Args:
            prospect_data: dict contenant toutes les données du prospect
        """
        self.data = prospect_data
        self.width, self.height = A4
        
    def generate(self):
        """Génère le PDF CERFA et retourne un buffer"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # En-tête CERFA
        self._draw_header(c)
        
        # Cadre 1 : Type de demande
        self._draw_section_1_type_demande(c)
        
        # Cadre 2 : Producteur (demandeur)
        self._draw_section_2_producteur(c)
        
        # Cadre 3 : Installation
        self._draw_section_3_installation(c)
        
        # Cadre 4 : Caractéristiques techniques
        self._draw_section_4_caracteristiques(c)
        
        # Cadre 5 : Raccordement
        self._draw_section_5_raccordement(c)
        
        # Pied de page
        self._draw_footer(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_header(self, c):
        """Dessine l'en-tête du CERFA"""
        y = self.height - 2*cm
        
        # Titre CERFA
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, y, "DEMANDE DE RACCORDEMENT")
        y -= 0.6*cm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, y, "Installation de production d'électricité")
        
        # Numéro CERFA
        c.setFont("Helvetica", 9)
        c.drawString(15*cm, self.height - 2*cm, "CERFA N° 16702*01")
        c.drawString(15*cm, self.height - 2.4*cm, "Enedis / ELD")
        
        # Date de demande
        y -= 1*cm
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, f"Date de la demande : {datetime.now().strftime('%d/%m/%Y')}")
        
        return y - 1*cm
    
    def _draw_section_1_type_demande(self, c):
        """Cadre 1 : Type de demande"""
        y = self.height - 5.5*cm
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(1.5*cm, y - 2.5*cm, self.width - 3*cm, 2.5*cm)
        
        # Titre
        c.setFillColor(colors.HexColor('#0066CC'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.5*cm, "1. TYPE DE DEMANDE")
        c.setFillColor(colors.black)
        
        # Type installation
        y -= 1.2*cm
        c.setFont("Helvetica", 10)
        
        # Déterminer le type
        type_installation = self.data.get('type', 'toiture')
        is_autoconso = 'autoconso' in str(self.data.get('type_raccordement', '')).lower()
        is_injection_totale = 'injection_totale' in str(self.data.get('type_raccordement', '')).lower()
        
        # Cases à cocher
        checkbox_size = 0.4*cm
        x_checkbox = 2.5*cm
        
        # Autoconsommation avec injection
        self._draw_checkbox(c, x_checkbox, y, is_autoconso and not is_injection_totale)
        c.drawString(x_checkbox + 0.6*cm, y - 0.1*cm, "Autoconsommation avec injection du surplus")
        
        y -= 0.6*cm
        # Autoconsommation sans injection
        self._draw_checkbox(c, x_checkbox, y, False)
        c.drawString(x_checkbox + 0.6*cm, y - 0.1*cm, "Autoconsommation sans injection")
        
        y -= 0.6*cm
        # Injection totale
        self._draw_checkbox(c, x_checkbox, y, is_injection_totale)
        c.drawString(x_checkbox + 0.6*cm, y - 0.1*cm, "Injection totale (vente)")
        
        return y - 1*cm
    
    def _draw_section_2_producteur(self, c):
        """Cadre 2 : Producteur (demandeur)"""
        y = self.height - 9*cm
        
        # Cadre
        c.setLineWidth(1.5)
        c.rect(1.5*cm, y - 5*cm, self.width - 3*cm, 5*cm)
        
        # Titre
        c.setFillColor(colors.HexColor('#0066CC'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.5*cm, "2. PRODUCTEUR (Demandeur)")
        c.setFillColor(colors.black)
        
        y -= 1.2*cm
        c.setFont("Helvetica", 9)
        
        # Nom/Raison sociale
        nom_prospect = self.data.get('nom_prospect') or self.data.get('contact_nom') or self.data.get('proprietaire_denomination') or 'À COMPLÉTER'
        self._draw_field(c, 2*cm, y, "Nom ou Raison sociale :", nom_prospect, width=16*cm)
        
        y -= 0.8*cm
        # SIRET
        siret = self.data.get('siret') or self.data.get('proprietaire_siren') or ''
        self._draw_field(c, 2*cm, y, "SIRET / SIREN :", siret, width=8*cm)
        
        y -= 0.8*cm
        # Adresse
        adresse = self.data.get('proprietaire_adresse') or ''
        self._draw_field(c, 2*cm, y, "Adresse :", adresse, width=16*cm)
        
        y -= 0.8*cm
        # Code postal et ville
        cp = self.data.get('proprietaire_code_postal') or ''
        ville = self.data.get('proprietaire_ville') or self.data.get('commune') or ''
        self._draw_field(c, 2*cm, y, "Code postal :", cp, width=4*cm)
        self._draw_field(c, 8*cm, y, "Ville :", ville, width=10*cm)
        
        y -= 0.8*cm
        # Contact
        contact_nom = self.data.get('contact_nom') or self.data.get('dirigeant_nom') or ''
        contact_tel = self.data.get('contact_tel') or self.data.get('dirigeant_tel') or ''
        contact_email = self.data.get('contact_email') or self.data.get('dirigeant_email') or ''
        
        self._draw_field(c, 2*cm, y, "Contact :", contact_nom, width=8*cm)
        self._draw_field(c, 11*cm, y, "Tél :", contact_tel, width=6*cm)
        
        y -= 0.8*cm
        self._draw_field(c, 2*cm, y, "Email :", contact_email, width=16*cm)
        
        return y - 1*cm
    
    def _draw_section_3_installation(self, c):
        """Cadre 3 : Localisation de l'installation"""
        y = self.height - 15.5*cm
        
        # Cadre
        c.setLineWidth(1.5)
        c.rect(1.5*cm, y - 4.5*cm, self.width - 3*cm, 4.5*cm)
        
        # Titre
        c.setFillColor(colors.HexColor('#0066CC'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.5*cm, "3. LOCALISATION DE L'INSTALLATION")
        c.setFillColor(colors.black)
        
        y -= 1.2*cm
        c.setFont("Helvetica", 9)
        
        # Adresse installation
        adresse_install = self.data.get('adresse') or ''
        self._draw_field(c, 2*cm, y, "Adresse de l'installation :", adresse_install, width=16*cm)
        
        y -= 0.8*cm
        # Code postal et commune
        commune = self.data.get('commune') or ''
        self._draw_field(c, 2*cm, y, "Code postal :", '', width=4*cm)
        self._draw_field(c, 8*cm, y, "Commune :", commune, width=10*cm)
        
        y -= 0.8*cm
        # Parcelles cadastrales
        parcelles = self.data.get('parcelles_cadastrales') or ''
        if isinstance(parcelles, str):
            try:
                import json
                parcelles_list = json.loads(parcelles)
                if isinstance(parcelles_list, list):
                    parcelles = ', '.join([str(p.get('id', p.get('reference', p))) if isinstance(p, dict) else str(p) for p in parcelles_list[:5]])
            except:
                pass
        self._draw_field(c, 2*cm, y, "Références cadastrales :", str(parcelles), width=16*cm)
        
        y -= 0.8*cm
        # Coordonnées GPS
        lat = self.data.get('latitude') or self.data.get('lat') or ''
        lon = self.data.get('longitude') or self.data.get('lon') or ''
        coords = f"{lat}, {lon}" if lat and lon else ''
        self._draw_field(c, 2*cm, y, "Coordonnées GPS :", coords, width=16*cm)
        
        return y - 1*cm
    
    def _draw_section_4_caracteristiques(self, c):
        """Cadre 4 : Caractéristiques techniques"""
        y = self.height - 21.5*cm
        
        # Cadre
        c.setLineWidth(1.5)
        c.rect(1.5*cm, y - 5*cm, self.width - 3*cm, 5*cm)
        
        # Titre
        c.setFillColor(colors.HexColor('#0066CC'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.5*cm, "4. CARACTÉRISTIQUES TECHNIQUES")
        c.setFillColor(colors.black)
        
        y -= 1.2*cm
        c.setFont("Helvetica", 9)
        
        # Type de production
        type_prod = self.data.get('type', 'photovoltaïque').upper()
        self._draw_field(c, 2*cm, y, "Type de production :", "PHOTOVOLTAÏQUE", width=10*cm)
        
        y -= 0.8*cm
        # Puissance installée
        surface_m2 = float(self.data.get('surface_m2', 0) or 0)
        surface_ha = float(self.data.get('surface_ha', 0) or 0)
        if surface_ha > 0:
            surface_m2 = surface_ha * 10000
        
        # Estimation puissance (150 Wc/m² en moyenne)
        puissance_kwc = round(surface_m2 * 0.15, 2) if surface_m2 > 0 else 0
        
        self._draw_field(c, 2*cm, y, "Puissance installée (kWc) :", f"{puissance_kwc:.2f}" if puissance_kwc > 0 else '', width=6*cm)
        
        # Puissance de raccordement
        puissance_raccord_kva = round(puissance_kwc * 0.85, 2) if puissance_kwc > 0 else 0  # Facteur de puissance
        self._draw_field(c, 10*cm, y, "Puissance de raccordement (kVA) :", f"{puissance_raccord_kva:.2f}" if puissance_raccord_kva > 0 else '', width=8*cm)
        
        y -= 0.8*cm
        # Nombre de modules
        nb_modules = int(surface_m2 / 2) if surface_m2 > 0 else 0  # Estimation ~2m² par module
        self._draw_field(c, 2*cm, y, "Nombre de modules :", str(nb_modules) if nb_modules > 0 else '', width=6*cm)
        
        y -= 0.8*cm
        # Type de raccordement (BT ou HTA)
        type_raccord = "BT (Basse Tension)" if puissance_kwc < 250 else "HTA (Haute Tension)"
        self._draw_field(c, 2*cm, y, "Type de raccordement :", type_raccord, width=10*cm)
        
        y -= 0.8*cm
        # Technologie
        self._draw_field(c, 2*cm, y, "Technologie :", "Panneaux photovoltaïques silicium polycristallin", width=16*cm)
        
        return y - 1*cm
    
    def _draw_section_5_raccordement(self, c):
        """Cadre 5 : Informations de raccordement"""
        y = self.height - 28*cm
        
        # Cadre
        c.setLineWidth(1.5)
        c.rect(1.5*cm, y - 3.5*cm, self.width - 3*cm, 3.5*cm)
        
        # Titre
        c.setFillColor(colors.HexColor('#0066CC'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.5*cm, "5. POSTE DE RACCORDEMENT")
        c.setFillColor(colors.black)
        
        y -= 1.2*cm
        c.setFont("Helvetica", 9)
        
        # Déterminer quel poste afficher (BT ou HTA selon puissance)
        puissance_kwc = round(float(self.data.get('surface_m2', 0) or 0) * 0.15, 2)
        use_hta = puissance_kwc >= 250
        
        if use_hta:
            # Poste HTA
            poste_nom = self.data.get('poste_hta_nom') or 'N/A'
            poste_distance = int(self.data.get('poste_hta_distance_m', 0) or 0)
            poste_commune = self.data.get('poste_hta_commune') or ''
            poste_lat = self.data.get('poste_hta_lat') or ''
            poste_lon = self.data.get('poste_hta_lon') or ''
        else:
            # Poste BT
            poste_nom = self.data.get('poste_bt_nom') or ''
            poste_distance = int(self.data.get('poste_bt_distance_m', 0) or 0)
            poste_commune = self.data.get('poste_bt_commune') or ''
            poste_lat = self.data.get('poste_bt_lat') or ''
            poste_lon = self.data.get('poste_bt_lon') or ''
        
        self._draw_field(c, 2*cm, y, "Nom du poste le plus proche :", poste_nom, width=10*cm)
        self._draw_field(c, 13*cm, y, "Distance :", f"{poste_distance} m" if poste_distance > 0 else '', width=5*cm)
        
        y -= 0.8*cm
        self._draw_field(c, 2*cm, y, "Commune du poste :", poste_commune, width=10*cm)
        
        y -= 0.8*cm
        coords_poste = f"{poste_lat}, {poste_lon}" if poste_lat and poste_lon else ''
        self._draw_field(c, 2*cm, y, "Coordonnées GPS du poste :", coords_poste, width=16*cm)
        
        return y - 1*cm
    
    def _draw_footer(self, c):
        """Dessine le pied de page avec signature"""
        y = 3*cm
        
        c.setFont("Helvetica", 8)
        c.drawString(2*cm, y, "Documents à joindre : plan de situation, plan de masse, schéma unifilaire, attestation Consuel")
        
        y -= 0.8*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, f"Fait à {self.data.get('commune', '.........................')} le {datetime.now().strftime('%d/%m/%Y')}")
        
        y -= 1.5*cm
        c.drawString(2*cm, y, "Signature du demandeur :")
        c.setLineWidth(0.5)
        c.line(6*cm, y - 0.3*cm, 12*cm, y - 0.3*cm)
    
    def _draw_checkbox(self, c, x, y, checked=False):
        """Dessine une case à cocher"""
        size = 0.4*cm
        c.setLineWidth(1)
        c.rect(x, y - size, size, size)
        if checked:
            c.setLineWidth(2)
            c.line(x, y - size, x + size, y)
            c.line(x, y, x + size, y - size)
    
    def _draw_field(self, c, x, y, label, value, width=8*cm):
        """Dessine un champ de formulaire"""
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        c.drawString(x, y + 0.1*cm, label)
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y - 0.3*cm, str(value) if value else '')
        
        # Ligne de soulignement
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.line(x, y - 0.4*cm, x + width, y - 0.4*cm)
        c.setStrokeColor(colors.black)


def generate_cerfa_pdf(prospect_data):
    """
    Fonction helper pour générer un CERFA
    
    Args:
        prospect_data: dict avec les données du prospect
        
    Returns:
        BytesIO buffer contenant le PDF
    """
    generator = CerfaGenerator(prospect_data)
    return generator.generate()
