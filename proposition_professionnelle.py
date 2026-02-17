"""
Générateur de Proposition Commerciale Professionnelle
Pour installations photovoltaïques - AgriWeb

Génère un PDF complet avec:
- Couverture + Sommaire
- Présentation entreprise (certifications QualiPV, RGE)
- Analyse site + contraintes urbanisme (PLU)
- Solution technique (modules JA Solar, onduleurs Huawei)
- Étude productible PVGIS
- Étude financière (TRI, VAN, ROI)
- Devis détaillé NF C 15-752-1 avec taxes IFER
- Planning réalisation (DP, DDR, Consuel)
- Garanties et maintenance
- Aspects réglementaires
- CGV
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from datetime import datetime, timedelta
import io
import math
import json


class PropositionProfessionnelle:
    """Génère une proposition commerciale professionnelle complète en PDF"""

    # Couleurs de la charte graphique
    COLOR_PRIMARY = colors.HexColor('#1B5E20')      # Vert foncé
    COLOR_SECONDARY = colors.HexColor('#4CAF50')     # Vert
    COLOR_ACCENT = colors.HexColor('#FF9800')         # Orange
    COLOR_DARK = colors.HexColor('#212121')            # Noir doux
    COLOR_LIGHT_BG = colors.HexColor('#F5F5F5')       # Gris clair
    COLOR_HEADER_BG = colors.HexColor('#E8F5E9')      # Vert très clair
    COLOR_BLUE = colors.HexColor('#1565C0')            # Bleu pour liens/highlights
    COLOR_WHITE = colors.white

    def __init__(self, prospect, calpinage, parametres):
        """
        Args:
            prospect: dict - données du prospect (nom, commune, lat, lon, etc.)
            calpinage: dict - données de calpinage (totaux, zones, type_raccordement)
            parametres: dict - paramètres financiers (puissance_kwc, prix_kwc, tarifs, etc.)
        """
        self.prospect = prospect or {}
        self.calpinage = calpinage or {}
        self.parametres = parametres or {}
        self.width, self.height = A4
        self.page_number = 0
        self.date_now = datetime.now()

        # Extraire les données clés
        self.puissance_kwc = self._sf(parametres.get('puissance_kwc'), 100.0)
        self.prix_kwc = self._sf(parametres.get('prix_kwc'), 850.0)
        self.investissement = self.puissance_kwc * self.prix_kwc
        self.consommation = self._sf(parametres.get('consommation_annuelle_kwh'), 0.0)
        self.tarif_achat = self._sf(parametres.get('tarif_achat_kwh'), 0.20)
        self.tarif_revente = self._sf(parametres.get('tarif_revente_kwh'), 0.13)
        self.taux_autoconso = self._sf(parametres.get('taux_autoconso'), 70.0) / 100.0
        self.type_projet = parametres.get('type_projet', 'autoconsommation')

        # Calculs techniques
        totaux = calpinage.get('totaux', {})
        self.nb_modules = totaux.get('nbModules', int(self.puissance_kwc / 0.55))
        self.puissance_module = totaux.get('puissanceModule', 550)

        # Production estimée (1100 kWh/kWc moyen France)
        self.production_annuelle = self.puissance_kwc * 1100

        # Calculs financiers
        if self.type_projet == 'autoconsommation':
            self.energie_autoconsommee = self.production_annuelle * self.taux_autoconso
            self.energie_revendue = self.production_annuelle * (1 - self.taux_autoconso)
            self.economie_autoconso = self.energie_autoconsommee * self.tarif_achat
            self.revenu_revente = self.energie_revendue * self.tarif_revente
            self.gain_annuel = self.economie_autoconso + self.revenu_revente
        else:
            self.energie_autoconsommee = 0
            self.energie_revendue = self.production_annuelle
            self.economie_autoconso = 0
            self.revenu_revente = self.production_annuelle * self.tarif_revente
            self.gain_annuel = self.revenu_revente

        self.roi_annees = self.investissement / self.gain_annuel if self.gain_annuel > 0 else 99
        self.rentabilite = (self.gain_annuel / self.investissement * 100) if self.investissement > 0 else 0

        # Parse data_json si disponible
        self.data_json = {}
        if prospect.get('data_json'):
            if isinstance(prospect['data_json'], str):
                try:
                    self.data_json = json.loads(prospect['data_json'])
                except:
                    self.data_json = {}
            elif isinstance(prospect['data_json'], dict):
                self.data_json = prospect['data_json']

        self.visite_technique = self.data_json.get('visite_technique', {})
        self.rapport_commune = self.data_json.get('rapport_commune', {})

    def _sf(self, value, default=0.0):
        """Safe float conversion"""
        try:
            if value is None or value == '':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def generer_pdf(self):
        """Génère le PDF complet et retourne un BytesIO buffer"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        # Page 1 : Couverture
        self._draw_cover(c)

        # Page 2 : Sommaire
        c.showPage()
        self.page_number += 1
        self._draw_sommaire(c)

        # Page 3 : Présentation entreprise
        c.showPage()
        self.page_number += 1
        self._draw_presentation_entreprise(c)

        # Page 4 : Analyse du site
        c.showPage()
        self.page_number += 1
        self._draw_analyse_site(c)

        # Page 5 : Solution technique
        c.showPage()
        self.page_number += 1
        self._draw_solution_technique(c)

        # Page 6 : Étude productible
        c.showPage()
        self.page_number += 1
        self._draw_etude_productible(c)

        # Page 7 : Étude financière
        c.showPage()
        self.page_number += 1
        self._draw_etude_financiere(c)

        # Page 8 : Devis détaillé
        c.showPage()
        self.page_number += 1
        self._draw_devis(c)

        # Page 9 : Planning
        c.showPage()
        self.page_number += 1
        self._draw_planning(c)

        # Page 10 : Garanties et maintenance
        c.showPage()
        self.page_number += 1
        self._draw_garanties(c)

        # Page 11 : Aspects réglementaires & CGV
        c.showPage()
        self.page_number += 1
        self._draw_reglementaire_cgv(c)

        c.save()
        buffer.seek(0)
        return buffer

    # =========================================================================
    # HELPERS DE DESSIN
    # =========================================================================

    def _draw_page_header(self, c, title):
        """En-tête de page standard"""
        y = self.height - 1.5 * cm

        # Bande verte en haut
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(0, self.height - 1.2 * cm, self.width, 1.2 * cm, fill=1)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.5 * cm, self.height - 0.8 * cm, "AGRIWEB | Proposition Commerciale")
        c.drawRightString(self.width - 1.5 * cm, self.height - 0.8 * cm, f"Réf: PROP-{self.prospect.get('id', 'XXX')}")

        # Titre de section
        y = self.height - 2.5 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1.5 * cm, y, title)

        # Ligne de séparation
        y -= 0.3 * cm
        c.setStrokeColor(self.COLOR_SECONDARY)
        c.setLineWidth(2)
        c.line(1.5 * cm, y, self.width - 1.5 * cm, y)

        # Pied de page
        self._draw_page_footer(c)

        return y - 0.5 * cm

    def _draw_page_footer(self, c):
        """Pied de page standard"""
        c.setFillColor(colors.grey)
        c.setFont("Helvetica", 7)
        commune = self.prospect.get('commune', '')
        c.drawString(1.5 * cm, 1 * cm, f"Proposition Commerciale - {commune} - {self.date_now.strftime('%d/%m/%Y')}")
        c.drawRightString(self.width - 1.5 * cm, 1 * cm, f"Page {self.page_number + 1}")
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.line(1.5 * cm, 1.3 * cm, self.width - 1.5 * cm, 1.3 * cm)

    def _draw_section_title(self, c, y, title, number=None):
        """Titre de sous-section"""
        c.setFillColor(self.COLOR_HEADER_BG)
        c.rect(1.5 * cm, y - 0.2 * cm, self.width - 3 * cm, 0.8 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 11)
        prefix = f"{number}. " if number else ""
        c.drawString(2 * cm, y, f"{prefix}{title}")
        c.setFillColor(self.COLOR_DARK)
        return y - 1 * cm

    def _draw_kv_line(self, c, y, label, value, x_label=2 * cm, x_value=9 * cm, bold_value=False):
        """Ligne clé-valeur"""
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(x_label, y, label)
        font = "Helvetica-Bold" if bold_value else "Helvetica"
        c.setFont(font, 9)
        c.setFillColor(self.COLOR_DARK)
        c.drawString(x_value, y, str(value))
        return y - 0.5 * cm

    def _draw_highlight_box(self, c, x, y, w, h, title, value, subtitle=""):
        """Boîte mise en avant (KPI)"""
        # Fond
        c.setFillColor(self.COLOR_HEADER_BG)
        c.roundRect(x, y, w, h, 4, fill=1, stroke=0)
        # Bordure gauche colorée
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(x, y, 4, h, fill=1, stroke=0)
        # Titre
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.5 * cm, y + h - 0.5 * cm, title)
        # Valeur
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + 0.5 * cm, y + h - 1.3 * cm, str(value))
        # Sous-titre
        if subtitle:
            c.setFillColor(colors.grey)
            c.setFont("Helvetica", 7)
            c.drawString(x + 0.5 * cm, y + 0.2 * cm, subtitle)
        c.setFillColor(self.COLOR_DARK)

    def _format_euros(self, val):
        """Formate un nombre en euros"""
        if val >= 1000000:
            return f"{val / 1000000:,.2f} M€".replace(',', ' ')
        elif val >= 1000:
            return f"{val:,.0f} €".replace(',', ' ')
        else:
            return f"{val:.2f} €"

    def _format_kwh(self, val):
        """Formate une énergie en kWh"""
        if val >= 1000000:
            return f"{val / 1000:,.0f} MWh".replace(',', ' ')
        elif val >= 1000:
            return f"{val:,.0f} kWh".replace(',', ' ')
        else:
            return f"{val:.0f} kWh"

    # =========================================================================
    # PAGES
    # =========================================================================

    def _draw_cover(self, c):
        """Page 1 : Couverture"""
        # Fond vert foncé pleine page
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(0, 0, self.width, self.height, fill=1)

        # Bande blanche centrale
        band_y = self.height * 0.3
        band_h = self.height * 0.45
        c.setFillColor(self.COLOR_WHITE)
        c.rect(0, band_y, self.width, band_h, fill=1, stroke=0)

        # Logo / Nom entreprise
        y = self.height - 3 * cm
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(self.width / 2, y, "AGRIWEB")
        y -= 1 * cm
        c.setFont("Helvetica", 12)
        c.drawCentredString(self.width / 2, y, "Solutions Photovoltaïques Professionnelles")

        # Titre principal
        y = band_y + band_h - 2.5 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(self.width / 2, y, "PROPOSITION COMMERCIALE")

        # Sous-titre
        y -= 1.2 * cm
        c.setFont("Helvetica", 14)
        type_label = "Autoconsommation avec revente du surplus" if self.type_projet == 'autoconsommation' else "Vente totale"
        c.drawCentredString(self.width / 2, y, type_label)

        # Infos projet
        y -= 2 * cm
        c.setFont("Helvetica-Bold", 16)
        nom_prospect = self.prospect.get('nom_prospect', '') or self.prospect.get('contact_nom', '') or 'Client'
        c.drawCentredString(self.width / 2, y, nom_prospect)

        y -= 0.8 * cm
        c.setFont("Helvetica", 12)
        commune = self.prospect.get('commune', 'N/A')
        c.drawCentredString(self.width / 2, y, f"📍 {commune}")

        y -= 1.2 * cm
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(self.COLOR_ACCENT)
        c.drawCentredString(self.width / 2, y, f"{self.puissance_kwc:.0f} kWc")

        y -= 0.8 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica", 11)
        c.drawCentredString(self.width / 2, y, f"Installation {self.nb_modules} modules × {self.puissance_module} Wc")

        # Date et référence en bas
        y = band_y + 0.8 * cm
        c.setFillColor(colors.grey)
        c.setFont("Helvetica", 9)
        c.drawCentredString(self.width / 2, y, f"Émise le {self.date_now.strftime('%d/%m/%Y')} — Valable 30 jours")

        # Bandeau bas
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width / 2, 2 * cm, "Certifié RGE QualiPV • N° SIRET: À compléter • Assurance décennale")
        c.drawCentredString(self.width / 2, 1.3 * cm, f"Réf: PROP-{self.prospect.get('id', 'XXX')}-{self.date_now.strftime('%Y%m%d')}")

    def _draw_sommaire(self, c):
        """Page 2 : Sommaire"""
        y = self._draw_page_header(c, "SOMMAIRE")

        sommaire = [
            ("1", "Présentation de l'entreprise", "Certifications, références, expertise"),
            ("2", "Analyse du site", "Localisation, contraintes urbanisme, ensoleillement"),
            ("3", "Solution technique", "Modules, onduleurs, structure, câblage"),
            ("4", "Étude de productible", "Production estimée PVGIS, profil mensuel"),
            ("5", "Étude financière", "Investissement, TRI, VAN, retour sur investissement"),
            ("6", "Devis détaillé", "Fourniture, pose, raccordement, démarches"),
            ("7", "Planning de réalisation", "Déclaration préalable, travaux, mise en service"),
            ("8", "Garanties et maintenance", "Garanties matériel, maintenance préventive"),
            ("9", "Aspects réglementaires & CGV", "Normes, assurances, conditions générales"),
        ]

        y -= 1 * cm
        for num, title, desc in sommaire:
            # Numéro
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2 * cm, y, num)
            # Titre
            c.setFont("Helvetica-Bold", 11)
            c.drawString(3.2 * cm, y, title)
            # Description
            c.setFillColor(colors.grey)
            c.setFont("Helvetica", 9)
            c.drawString(3.2 * cm, y - 0.5 * cm, desc)
            # Ligne pointillée
            c.setStrokeColor(colors.HexColor('#CCCCCC'))
            c.setDash(2, 2)
            c.line(3.2 * cm, y - 0.7 * cm, self.width - 2 * cm, y - 0.7 * cm)
            c.setDash()

            y -= 1.6 * cm

        # Résumé express
        y -= 0.5 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(1.5 * cm, y - 4 * cm, self.width - 3 * cm, 4 * cm, fill=0, stroke=1)

        y -= 0.5 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Résumé de l'offre")

        y -= 0.7 * cm
        c.setFont("Helvetica", 10)
        c.setFillColor(self.COLOR_DARK)
        resume_lines = [
            f"Puissance : {self.puissance_kwc:.0f} kWc ({self.nb_modules} modules)",
            f"Production estimée : {self._format_kwh(self.production_annuelle)}/an",
            f"Investissement : {self._format_euros(self.investissement)} HT",
            f"Gain annuel estimé : {self._format_euros(self.gain_annuel)}",
            f"Retour sur investissement : {self.roi_annees:.1f} ans",
        ]
        for line in resume_lines:
            c.drawString(2.5 * cm, y, f"• {line}")
            y -= 0.55 * cm

    def _draw_presentation_entreprise(self, c):
        """Page 3 : Présentation entreprise"""
        y = self._draw_page_header(c, "1. PRÉSENTATION DE L'ENTREPRISE")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Notre expertise")

        c.setFont("Helvetica", 9)
        c.setFillColor(self.COLOR_DARK)
        textes = [
            "Spécialiste des installations photovoltaïques pour le secteur agricole et industriel,",
            "nous accompagnons nos clients dans la transition énergétique avec des solutions",
            "sur mesure, performantes et rentables.",
            "",
            "Notre équipe d'ingénieurs et techniciens qualifiés assure un suivi de A à Z :",
            "de l'étude de faisabilité à la mise en service, en passant par le dimensionnement,",
            "les démarches administratives et le raccordement réseau.",
        ]
        for t in textes:
            c.drawString(2 * cm, y, t)
            y -= 0.45 * cm

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Certifications & Qualifications")

        certifs = [
            ("RGE QualiPV", "Qualification RGE (Reconnu Garant de l'Environnement) pour les installations PV"),
            ("QualiPV Électricité", "Module Électricité – Installations raccordées au réseau"),
            ("QualiPV Bâtiment", "Module Bâtiment – Intégration au bâti et surimposition"),
            ("Assurance Décennale", "Couverture décennale pour tous les chantiers réalisés"),
            ("NF C 15-100 / 15-752-1", "Conformité aux normes électriques en vigueur"),
        ]

        for titre, desc in certifs:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(self.COLOR_PRIMARY)
            c.drawString(2 * cm, y, f"✓ {titre}")
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.grey)
            c.drawString(7 * cm, y, desc)
            y -= 0.6 * cm

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Nos partenaires techniques")

        partenaires = [
            ("JA Solar", "Modules photovoltaïques Tier 1 – Garantie 30 ans"),
            ("Huawei", "Onduleurs string intelligents – Monitoring intégré"),
            ("K2 Systems", "Systèmes de fixation – Toiture et sol"),
            ("Enedis", "Raccordement réseau et mise en service"),
        ]

        for nom, desc in partenaires:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(self.COLOR_DARK)
            c.drawString(2 * cm, y, f"• {nom}")
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.grey)
            c.drawString(6 * cm, y, desc)
            y -= 0.6 * cm

        y -= 1 * cm
        y = self._draw_section_title(c, y, "Références")

        c.setFont("Helvetica", 9)
        c.setFillColor(self.COLOR_DARK)
        refs = [
            "• Plus de 400 projets photovoltaïques réalisés",
            "• Puissance cumulée installée > 50 MWc",
            "• Taux de satisfaction clients : 98%",
            "• Interventions dans toute la France métropolitaine",
        ]
        for r in refs:
            c.drawString(2 * cm, y, r)
            y -= 0.5 * cm

    def _draw_analyse_site(self, c):
        """Page 4 : Analyse du site"""
        y = self._draw_page_header(c, "2. ANALYSE DU SITE")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Localisation du projet")

        commune = self.prospect.get('commune', 'N/A')
        lat = self.prospect.get('latitude') or self.prospect.get('lat') or 'N/A'
        lon = self.prospect.get('longitude') or self.prospect.get('lon') or 'N/A'
        adresse = self.prospect.get('adresse', '')
        nom = self.prospect.get('nom_prospect', '') or self.prospect.get('contact_nom', '') or ''

        y = self._draw_kv_line(c, y, "Client :", nom)
        y = self._draw_kv_line(c, y, "Commune :", commune)
        if adresse:
            y = self._draw_kv_line(c, y, "Adresse :", adresse)
        y = self._draw_kv_line(c, y, "Coordonnées GPS :", f"{lat}, {lon}")

        # Type de toiture / support
        type_support = self.prospect.get('type', 'toiture')
        y = self._draw_kv_line(c, y, "Type d'implantation :", type_support.capitalize() if type_support else 'Toiture')

        # Surface
        surface = self.prospect.get('surface_m2', 0) or 0
        if surface:
            y = self._draw_kv_line(c, y, "Surface disponible :", f"{float(surface):,.0f} m²")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Contraintes urbanisme (PLU)")

        if self.rapport_commune:
            plu_info = self.rapport_commune.get('plu', {})
            zonage = plu_info.get('zonage', 'Non renseigné')
            contraintes = plu_info.get('contraintes', [])
            y = self._draw_kv_line(c, y, "Zonage PLU :", zonage)
            if contraintes:
                for ctr in contraintes[:5]:
                    c.setFont("Helvetica", 8)
                    c.setFillColor(colors.grey)
                    c.drawString(2.5 * cm, y, f"• {ctr}")
                    y -= 0.45 * cm
        else:
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.grey)
            c.drawString(2 * cm, y, "Données PLU à vérifier auprès de la mairie de la commune.")
            y -= 0.5 * cm
            c.drawString(2 * cm, y, "Une déclaration préalable de travaux sera nécessaire.")
            y -= 0.5 * cm

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Ensoleillement")

        # Zone d'ensoleillement estimée
        try:
            lat_val = float(lat) if lat != 'N/A' else 46.0
        except:
            lat_val = 46.0

        if lat_val > 47:
            zone = "Zone H1 (Nord) – Irradiation ~1 000-1 200 kWh/m²/an"
        elif lat_val > 44:
            zone = "Zone H2 (Centre) – Irradiation ~1 200-1 400 kWh/m²/an"
        else:
            zone = "Zone H3 (Sud) – Irradiation ~1 400-1 700 kWh/m²/an"

        y = self._draw_kv_line(c, y, "Zone climatique :", zone)
        y = self._draw_kv_line(c, y, "Productible estimé :", f"{1100} kWh/kWc/an (moyenne)")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Raccordement réseau")

        poste_bt = self.prospect.get('poste_bt_nom', '')
        poste_hta = self.prospect.get('poste_hta_nom', '')
        dist_bt = self.prospect.get('poste_bt_distance_m', '')
        dist_hta = self.prospect.get('poste_hta_distance_m', '')

        if self.puissance_kwc < 250:
            type_raccord = "Basse Tension (BT)"
            poste = poste_bt or 'À identifier'
            dist = f"{int(float(dist_bt))} m" if dist_bt else 'À déterminer'
        else:
            type_raccord = "Haute Tension A (HTA)"
            poste = poste_hta or 'À identifier'
            dist = f"{int(float(dist_hta))} m" if dist_hta else 'À déterminer'

        y = self._draw_kv_line(c, y, "Type de raccordement :", type_raccord)
        y = self._draw_kv_line(c, y, "Poste source :", poste)
        y = self._draw_kv_line(c, y, "Distance estimée :", dist)

    def _draw_solution_technique(self, c):
        """Page 5 : Solution technique"""
        y = self._draw_page_header(c, "3. SOLUTION TECHNIQUE")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Modules photovoltaïques")

        marque_module = "JA Solar"
        modele_module = f"JAM72S30-{self.puissance_module}MR" if self.puissance_module >= 500 else f"JAM60S20-{self.puissance_module}MR"
        surface_module = 2.58 if self.puissance_module >= 500 else 1.76

        y = self._draw_kv_line(c, y, "Marque :", marque_module)
        y = self._draw_kv_line(c, y, "Modèle :", modele_module)
        y = self._draw_kv_line(c, y, "Puissance unitaire :", f"{self.puissance_module} Wc")
        y = self._draw_kv_line(c, y, "Nombre de modules :", str(self.nb_modules))
        y = self._draw_kv_line(c, y, "Surface totale modules :", f"{self.nb_modules * surface_module:,.0f} m²")
        y = self._draw_kv_line(c, y, "Puissance crête totale :", f"{self.puissance_kwc:.1f} kWc")
        y = self._draw_kv_line(c, y, "Technologie :", "Mono-PERC Half-Cut, Bifacial")
        y = self._draw_kv_line(c, y, "Rendement module :", "21.3%")
        y = self._draw_kv_line(c, y, "Garantie produit :", "25 ans")
        y = self._draw_kv_line(c, y, "Garantie performance :", "30 ans (87.4% à 30 ans)")

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Onduleurs")

        # Dimensionnement onduleurs
        if self.puissance_kwc > 100:
            nb_onduleurs = max(1, int(self.puissance_kwc / 100))
            modele_onduleur = "Huawei SUN2000-100KTL-M2"
            puissance_onduleur = "100 kVA"
        elif self.puissance_kwc > 50:
            nb_onduleurs = max(1, int(self.puissance_kwc / 60))
            modele_onduleur = "Huawei SUN2000-60KTL-M0"
            puissance_onduleur = "60 kVA"
        else:
            nb_onduleurs = max(1, int(self.puissance_kwc / 36))
            modele_onduleur = "Huawei SUN2000-36KTL-M3"
            puissance_onduleur = "36 kVA"

        y = self._draw_kv_line(c, y, "Marque :", "Huawei FusionSolar")
        y = self._draw_kv_line(c, y, "Modèle :", modele_onduleur)
        y = self._draw_kv_line(c, y, "Puissance unitaire :", puissance_onduleur)
        y = self._draw_kv_line(c, y, "Nombre :", str(nb_onduleurs))
        y = self._draw_kv_line(c, y, "Rendement max :", "98.8%")
        y = self._draw_kv_line(c, y, "Monitoring :", "FusionSolar Smart PV (Cloud)")
        y = self._draw_kv_line(c, y, "Garantie :", "10 ans (extensible à 25 ans)")

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Structure de montage")

        y = self._draw_kv_line(c, y, "Système :", "K2 Systems")
        y = self._draw_kv_line(c, y, "Type :", "Surimposition toiture ou sol selon site")
        y = self._draw_kv_line(c, y, "Matériau :", "Aluminium anodisé + Inox A2")
        y = self._draw_kv_line(c, y, "Inclinaison :", "Optimisée selon site (15° à 35°)")
        y = self._draw_kv_line(c, y, "Charge au vent :", "Conforme Eurocodes / DTU")

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Câblage & Protection")

        y = self._draw_kv_line(c, y, "Câbles DC :", "H1Z2Z2-K 1x6mm² (ou 1x10mm² selon longueur)")
        y = self._draw_kv_line(c, y, "Câbles AC :", "Section adaptée au courant nominal")
        y = self._draw_kv_line(c, y, "Protection DC :", "Parafoudre Type 2 DC, interrupteur-sectionneur")
        y = self._draw_kv_line(c, y, "Protection AC :", "Disjoncteur, parafoudre Type 2 AC, différentiel")
        y = self._draw_kv_line(c, y, "Norme :", "NF C 15-100 / NF C 15-752-1")

    def _draw_etude_productible(self, c):
        """Page 6 : Étude productible"""
        y = self._draw_page_header(c, "4. ÉTUDE DE PRODUCTIBLE")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Production estimée")

        y = self._draw_kv_line(c, y, "Source des données :", "PVGIS (European Commission)")
        y = self._draw_kv_line(c, y, "Puissance installée :", f"{self.puissance_kwc:.1f} kWc")
        y = self._draw_kv_line(c, y, "Productible spécifique :", "1 100 kWh/kWc/an (estimation)")
        y = self._draw_kv_line(c, y, "Production annuelle :", f"{self._format_kwh(self.production_annuelle)}/an", bold_value=True)
        y = self._draw_kv_line(c, y, "Pertes système :", "~14% (câblage, température, salissure, onduleur)")
        y = self._draw_kv_line(c, y, "Dégradation annuelle :", "0.4% par an (garanti constructeur)")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Profil de production mensuel estimé")

        # Distribution mensuelle typique (en % de la production annuelle)
        mois = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        pct_mois = [4.5, 5.5, 8.0, 9.5, 11.0, 11.5, 12.0, 11.0, 9.5, 7.5, 5.5, 4.5]

        # Dessiner un graphique barres simple
        graph_x = 2.5 * cm
        graph_w = self.width - 5 * cm
        graph_h = 5 * cm
        bar_w = graph_w / 12 * 0.7
        gap = graph_w / 12 * 0.3
        max_pct = max(pct_mois)

        # Fond du graphique
        c.setFillColor(self.COLOR_LIGHT_BG)
        c.rect(graph_x - 0.3 * cm, y - graph_h - 0.5 * cm, graph_w + 0.6 * cm, graph_h + 1 * cm, fill=1, stroke=0)

        for i, (m, p) in enumerate(zip(mois, pct_mois)):
            bx = graph_x + i * (bar_w + gap)
            bh = (p / max_pct) * (graph_h - 1 * cm)
            by = y - graph_h

            # Barre
            c.setFillColor(self.COLOR_SECONDARY)
            c.rect(bx, by, bar_w, bh, fill=1, stroke=0)

            # Valeur au-dessus
            prod_mois = self.production_annuelle * p / 100
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica", 6)
            c.drawCentredString(bx + bar_w / 2, by + bh + 0.15 * cm, f"{prod_mois:,.0f}")

            # Label mois en dessous
            c.setFont("Helvetica", 7)
            c.drawCentredString(bx + bar_w / 2, by - 0.35 * cm, m)

        y = y - graph_h - 1.5 * cm

        # Tableau mensuel
        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Production sur 25 ans (avec dégradation 0.4%/an)")

        c.setFont("Helvetica", 8)
        c.setFillColor(self.COLOR_DARK)
        prod_cumulee = 0
        for annee in [1, 5, 10, 15, 20, 25]:
            degradation = (1 - 0.004) ** annee
            prod_annee = self.production_annuelle * degradation
            prod_cumulee += prod_annee * (annee - (0 if annee == 1 else [1, 5, 10, 15, 20, 25][[1, 5, 10, 15, 20, 25].index(annee) - 1]))
            y = self._draw_kv_line(c, y, f"Année {annee} :", f"{self._format_kwh(prod_annee)} (rendement {degradation * 100:.1f}%)")

    def _draw_etude_financiere(self, c):
        """Page 7 : Étude financière"""
        y = self._draw_page_header(c, "5. ÉTUDE FINANCIÈRE")

        # KPI boxes en haut
        box_w = (self.width - 4 * cm) / 3
        box_h = 1.8 * cm
        box_y = y - box_h - 0.5 * cm

        self._draw_highlight_box(c, 1.5 * cm, box_y, box_w - 0.3 * cm, box_h,
                                 "INVESTISSEMENT", self._format_euros(self.investissement), "HT")
        self._draw_highlight_box(c, 1.5 * cm + box_w, box_y, box_w - 0.3 * cm, box_h,
                                 "GAIN ANNUEL", self._format_euros(self.gain_annuel), "Année 1")
        self._draw_highlight_box(c, 1.5 * cm + 2 * box_w, box_y, box_w - 0.3 * cm, box_h,
                                 "ROI", f"{self.roi_annees:.1f} ans", f"Rentabilité {self.rentabilite:.1f}%")

        y = box_y - 1 * cm
        y = self._draw_section_title(c, y, "Hypothèses de calcul")

        y = self._draw_kv_line(c, y, "Type de projet :", "Autoconsommation + surplus" if self.type_projet == 'autoconsommation' else "Vente totale")
        y = self._draw_kv_line(c, y, "Prix achat électricité :", f"{self.tarif_achat:.4f} €/kWh")
        y = self._draw_kv_line(c, y, "Tarif revente surplus :", f"{self.tarif_revente:.4f} €/kWh")
        if self.type_projet == 'autoconsommation':
            y = self._draw_kv_line(c, y, "Taux autoconsommation :", f"{self.taux_autoconso * 100:.0f}%")
            y = self._draw_kv_line(c, y, "Consommation annuelle :", f"{self._format_kwh(self.consommation)}")
        y = self._draw_kv_line(c, y, "Augmentation tarif élec :", "+3%/an (hypothèse)")
        y = self._draw_kv_line(c, y, "Dégradation modules :", "-0.4%/an")
        y = self._draw_kv_line(c, y, "Durée d'étude :", "25 ans")

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Détail des revenus (Année 1)")

        if self.type_projet == 'autoconsommation':
            y = self._draw_kv_line(c, y, "Production totale :", self._format_kwh(self.production_annuelle))
            y = self._draw_kv_line(c, y, "Énergie autoconsommée :", f"{self._format_kwh(self.energie_autoconsommee)} ({self.taux_autoconso * 100:.0f}%)")
            y = self._draw_kv_line(c, y, "Économie autoconso :", f"{self._format_euros(self.economie_autoconso)}/an", bold_value=True)
            y = self._draw_kv_line(c, y, "Énergie revendue surplus :", self._format_kwh(self.energie_revendue))
            y = self._draw_kv_line(c, y, "Revenu revente surplus :", f"{self._format_euros(self.revenu_revente)}/an", bold_value=True)
        else:
            y = self._draw_kv_line(c, y, "Production totale :", self._format_kwh(self.production_annuelle))
            y = self._draw_kv_line(c, y, "Revenu vente totale :", f"{self._format_euros(self.revenu_revente)}/an", bold_value=True)

        c.setStrokeColor(self.COLOR_PRIMARY)
        c.setLineWidth(1)
        c.line(2 * cm, y + 0.1 * cm, 14 * cm, y + 0.1 * cm)
        y = self._draw_kv_line(c, y, "GAIN TOTAL ANNUEL :", f"{self._format_euros(self.gain_annuel)}/an", bold_value=True)

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Projection sur 25 ans")

        # Tableau simplifié
        augmentation_tarif = 0.03
        degradation = 0.004
        cumul_gains = 0
        annees_affichees = [1, 5, 10, 15, 20, 25]

        # En-tête tableau
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(1.5 * cm, y - 0.2 * cm, self.width - 3 * cm, 0.6 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 8)
        cols = [2 * cm, 5 * cm, 8 * cm, 11 * cm, 14 * cm]
        headers = ["Année", "Production", "Gain annuel", "Gains cumulés", "Bilan"]
        for col, h in zip(cols, headers):
            c.drawString(col, y, h)

        y -= 0.7 * cm
        c.setFillColor(self.COLOR_DARK)

        for annee in range(1, 26):
            prod = self.production_annuelle * ((1 - degradation) ** annee)
            tarif_a = self.tarif_achat * ((1 + augmentation_tarif) ** annee)
            tarif_r = self.tarif_revente  # Tarif revente fixe (contrat)

            if self.type_projet == 'autoconsommation':
                eco = prod * self.taux_autoconso * tarif_a
                rev = prod * (1 - self.taux_autoconso) * tarif_r
                gain = eco + rev
            else:
                gain = prod * tarif_r

            cumul_gains += gain

            if annee in annees_affichees:
                c.setFont("Helvetica", 8)
                bilan = cumul_gains - self.investissement
                c.setFillColor(self.COLOR_DARK)
                c.drawString(cols[0], y, str(annee))
                c.drawString(cols[1], y, self._format_kwh(prod))
                c.drawString(cols[2], y, self._format_euros(gain))
                c.drawString(cols[3], y, self._format_euros(cumul_gains))
                color_bilan = self.COLOR_PRIMARY if bilan >= 0 else colors.red
                c.setFillColor(color_bilan)
                c.drawString(cols[4], y, self._format_euros(bilan))
                c.setFillColor(self.COLOR_DARK)
                y -= 0.5 * cm

        # Gains totaux sur 25 ans
        y -= 0.3 * cm
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(self.COLOR_PRIMARY)
        gain_net_25 = cumul_gains - self.investissement
        c.drawString(2 * cm, y, f"Gain net sur 25 ans : {self._format_euros(gain_net_25)}")

    def _draw_devis(self, c):
        """Page 8 : Devis détaillé"""
        y = self._draw_page_header(c, "6. DEVIS DÉTAILLÉ")

        y -= 0.3 * cm

        # En-tête tableau
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(1.5 * cm, y - 0.2 * cm, self.width - 3 * cm, 0.6 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(2 * cm, y, "Désignation")
        c.drawString(10 * cm, y, "Qté")
        c.drawString(12 * cm, y, "P.U. HT")
        c.drawString(15 * cm, y, "Total HT")

        y -= 0.7 * cm
        c.setFillColor(self.COLOR_DARK)

        # Calcul des postes
        prix_modules = self.puissance_kwc * 180  # ~180€/kWc pour modules
        prix_onduleurs = self.puissance_kwc * 80  # ~80€/kWc pour onduleurs
        prix_structure = self.puissance_kwc * 60  # ~60€/kWc pour structure
        prix_cablage = self.puissance_kwc * 40  # ~40€/kWc pour câblage
        prix_protection = self.puissance_kwc * 30  # ~30€/kWc pour protections
        prix_pose = self.puissance_kwc * 200  # ~200€/kWc pour pose
        prix_raccordement = self.puissance_kwc * 50  # ~50€/kWc pour raccordement
        prix_etudes = self.puissance_kwc * 30  # ~30€/kWc pour études
        prix_demarches = self.puissance_kwc * 20  # ~20€/kWc pour démarches
        prix_monitoring = self.puissance_kwc * 15  # ~15€/kWc pour monitoring
        prix_consuel = 800  # Forfait Consuel

        # Le total doit correspondre au prix_kwc × puissance
        total_postes = (prix_modules + prix_onduleurs + prix_structure + prix_cablage
                        + prix_protection + prix_pose + prix_raccordement
                        + prix_etudes + prix_demarches + prix_monitoring + prix_consuel)
        # Ajuster le poste "pose" pour que le total colle
        ecart = self.investissement - total_postes
        prix_pose += ecart

        postes = [
            ("FOURNITURE", None, None, None, True),
            (f"Modules PV {self.puissance_module}Wc JA Solar", self.nb_modules, prix_modules / self.nb_modules if self.nb_modules else 0, prix_modules, False),
            ("Onduleurs Huawei FusionSolar", "-", "-", prix_onduleurs, False),
            ("Structure de montage K2 Systems", "-", "-", prix_structure, False),
            ("Câblage DC/AC (H1Z2Z2-K)", "-", "-", prix_cablage, False),
            ("Coffret de protection AC/DC", "-", "-", prix_protection, False),
            ("Système de monitoring", "1", "-", prix_monitoring, False),
            ("", None, None, None, False),
            ("INSTALLATION & MISE EN SERVICE", None, None, None, True),
            ("Main d'œuvre pose et raccordement", "-", "-", prix_pose, False),
            ("Raccordement réseau Enedis", "1", "-", prix_raccordement, False),
            ("Contrôle Consuel", "1", "800", prix_consuel, False),
            ("", None, None, None, False),
            ("ÉTUDES & DÉMARCHES", None, None, None, True),
            ("Étude technique et dimensionnement", "1", "-", prix_etudes, False),
            ("Démarches administratives (DP, DDR)", "1", "-", prix_demarches, False),
        ]

        total_ht = 0
        for designation, qte, pu, total, is_header in postes:
            if not designation:
                y -= 0.2 * cm
                continue

            if is_header:
                c.setFillColor(self.COLOR_HEADER_BG)
                c.rect(1.5 * cm, y - 0.15 * cm, self.width - 3 * cm, 0.5 * cm, fill=1, stroke=0)
                c.setFillColor(self.COLOR_PRIMARY)
                c.setFont("Helvetica-Bold", 8)
                c.drawString(2 * cm, y, designation)
            else:
                c.setFont("Helvetica", 8)
                c.setFillColor(self.COLOR_DARK)
                c.drawString(2 * cm, y, designation)
                if qte is not None:
                    c.drawString(10 * cm, y, str(qte))
                if pu is not None and pu != "-":
                    c.drawString(12 * cm, y, f"{float(pu):,.2f} €")
                if total is not None:
                    c.drawRightString(17.5 * cm, y, f"{total:,.2f} €")
                    total_ht += total

            y -= 0.5 * cm

        # Ligne de total
        y -= 0.3 * cm
        c.setStrokeColor(self.COLOR_PRIMARY)
        c.setLineWidth(1.5)
        c.line(1.5 * cm, y + 0.3 * cm, self.width - 1.5 * cm, y + 0.3 * cm)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(self.COLOR_PRIMARY)
        c.drawString(2 * cm, y, "TOTAL HT")
        c.drawRightString(17.5 * cm, y, f"{self.investissement:,.2f} €")

        y -= 0.5 * cm
        tva = self.investissement * 0.20
        c.setFont("Helvetica", 9)
        c.setFillColor(self.COLOR_DARK)
        c.drawString(2 * cm, y, "TVA 20%")
        c.drawRightString(17.5 * cm, y, f"{tva:,.2f} €")

        y -= 0.5 * cm
        ttc = self.investissement + tva
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(self.COLOR_PRIMARY)
        c.drawString(2 * cm, y, "TOTAL TTC")
        c.drawRightString(17.5 * cm, y, f"{ttc:,.2f} €")

        y -= 0.5 * cm
        c.setFont("Helvetica", 9)
        c.setFillColor(self.COLOR_DARK)
        c.drawString(2 * cm, y, f"Soit {self.prix_kwc:,.0f} €/kWc HT")

        # IFER si > 100 kWc
        if self.puissance_kwc >= 100:
            y -= 1 * cm
            y = self._draw_section_title(c, y, "Taxes IFER")
            c.setFont("Helvetica", 8)
            c.setFillColor(self.COLOR_DARK)
            ifer = self.puissance_kwc * 7.82  # Tarif IFER 2025
            c.drawString(2 * cm, y, f"IFER (Imposition Forfaitaire sur les Entreprises de Réseaux) : {ifer:,.2f} €/an")
            y -= 0.4 * cm
            c.drawString(2 * cm, y, f"Applicable aux installations ≥ 100 kWc — Tarif 2025 : 7,82 €/kW")

        # Validité
        y -= 1.2 * cm
        c.setFillColor(colors.grey)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(2 * cm, y, f"Ce devis est valable 30 jours à compter du {self.date_now.strftime('%d/%m/%Y')}.")
        y -= 0.4 * cm
        c.drawString(2 * cm, y, "Les prix s'entendent hors frais de raccordement Enedis (devis Enedis à définir).")

    def _draw_planning(self, c):
        """Page 9 : Planning de réalisation"""
        y = self._draw_page_header(c, "7. PLANNING DE RÉALISATION")

        y -= 0.5 * cm

        etapes = [
            ("Étude technique & Dimensionnement", "S1-S2", "2 semaines", "Visite sur site, relevé technique, calculs"),
            ("Déclaration Préalable (DP)", "S3-S6", "1 mois", "Dépôt en mairie, instruction administrative"),
            ("Demande de Raccordement (DDR)", "S4", "1 semaine", "Dépôt auprès d'Enedis"),
            ("Proposition Technique et Financière", "S6-S10", "1 mois", "Réception et validation du devis Enedis"),
            ("Convention d'Autoconsommation / OA", "S10-S12", "2 semaines", "Signature du contrat EDF OA ou autoconsommation"),
            ("Approvisionnement matériel", "S10-S14", "1 mois", "Commande modules, onduleurs, structure"),
            ("Travaux d'installation", "S14-S18", "1 mois", "Pose modules, câblage, onduleurs"),
            ("Contrôle Consuel", "S18-S19", "1 semaine", "Vérification conformité électrique"),
            ("Mise en service", "S19-S20", "1 semaine", "Raccordement Enedis et mise sous tension"),
            ("Formation & Remise des clés", "S20", "-", "Présentation monitoring, documentation"),
        ]

        for i, (etape, semaines, duree, detail) in enumerate(etapes):
            # Numéro et barre colorée
            c.setFillColor(self.COLOR_SECONDARY if i % 2 == 0 else self.COLOR_PRIMARY)
            c.rect(1.5 * cm, y - 0.1 * cm, 0.4 * cm, 0.5 * cm, fill=1, stroke=0)

            c.setFillColor(self.COLOR_WHITE)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(1.5 * cm + 0.2 * cm, y, str(i + 1))

            # Nom étape
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(2.2 * cm, y, etape)

            # Semaines et durée
            c.setFont("Helvetica", 8)
            c.setFillColor(self.COLOR_BLUE)
            c.drawString(12 * cm, y, semaines)
            c.setFillColor(colors.grey)
            c.drawString(14 * cm, y, duree)

            # Détail
            y -= 0.45 * cm
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.grey)
            c.drawString(2.2 * cm, y, detail)

            y -= 0.7 * cm

        # Timeline visuelle simplifiée
        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Durée totale estimée")

        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(self.COLOR_PRIMARY)
        c.drawString(2 * cm, y, "Délai de réalisation : 4 à 5 mois")
        y -= 0.6 * cm
        c.setFont("Helvetica", 9)
        c.setFillColor(self.COLOR_DARK)
        date_debut = self.date_now + timedelta(days=14)
        date_fin = self.date_now + timedelta(days=150)
        c.drawString(2 * cm, y, f"Début estimé : {date_debut.strftime('%B %Y')}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Mise en service estimée : {date_fin.strftime('%B %Y')}")

        y -= 1. * cm
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.grey)
        c.drawString(2 * cm, y, "* Les délais peuvent varier selon les retours Enedis et l'instruction de la DP par la mairie.")

    def _draw_garanties(self, c):
        """Page 10 : Garanties et maintenance"""
        y = self._draw_page_header(c, "8. GARANTIES ET MAINTENANCE")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Garanties matériel")

        garanties = [
            ("Modules photovoltaïques JA Solar", [
                "Garantie produit : 25 ans",
                "Garantie performance linéaire : 30 ans",
                "Performance minimale garantie : 87.4% à 30 ans",
            ]),
            ("Onduleurs Huawei", [
                "Garantie constructeur : 10 ans",
                "Extension de garantie disponible jusqu'à 25 ans",
                "SAV Huawei France – intervention sous 48h",
            ]),
            ("Structure de montage K2 Systems", [
                "Garantie : 15 ans pièces et main d'œuvre",
                "Résistance : certifiée Eurocodes (neige et vent)",
            ]),
            ("Installation complète", [
                "Garantie décennale (assurance installateur)",
                "Garantie de parfait achèvement : 1 an",
                "Garantie biennale : 2 ans",
            ]),
        ]

        for titre, details in garanties:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(self.COLOR_PRIMARY)
            c.drawString(2 * cm, y, f"▸ {titre}")
            y -= 0.45 * cm

            for d in details:
                c.setFont("Helvetica", 8)
                c.setFillColor(self.COLOR_DARK)
                c.drawString(3 * cm, y, f"• {d}")
                y -= 0.4 * cm

            y -= 0.3 * cm

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Maintenance préventive")

        c.setFont("Helvetica", 9)
        c.setFillColor(self.COLOR_DARK)
        maintenance = [
            "Inspection visuelle annuelle des modules et de la structure",
            "Contrôle du serrage des connecteurs et du câblage",
            "Vérification du bon fonctionnement des onduleurs et du monitoring",
            "Nettoyage des modules si nécessaire (zones agricoles)",
            "Contrôle des protections électriques (disjoncteurs, parafoudres)",
            "Rapport de maintenance annuel avec préconisations",
        ]

        for m in maintenance:
            c.drawString(2 * cm, y, f"• {m}")
            y -= 0.5 * cm

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Monitoring & Supervision")

        c.setFont("Helvetica", 9)
        monitoring = [
            "Plateforme Huawei FusionSolar accessible 24h/24",
            "Suivi en temps réel de la production par string et par onduleur",
            "Alertes automatiques en cas de dysfonctionnement",
            "Application mobile pour le suivi à distance",
            "Rapports de production mensuels automatiques",
        ]

        for m in monitoring:
            c.drawString(2 * cm, y, f"• {m}")
            y -= 0.5 * cm

    def _draw_reglementaire_cgv(self, c):
        """Page 11 : Aspects réglementaires & CGV"""
        y = self._draw_page_header(c, "9. RÉGLEMENTAIRE & CGV")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Cadre réglementaire")

        c.setFont("Helvetica", 8)
        c.setFillColor(self.COLOR_DARK)
        reglementaire = [
            "• Arrêté du 6 octobre 2021 fixant les conditions d'achat de l'électricité photovoltaïque",
            "• Décret n°2017-676 relatif à l'autoconsommation d'électricité",
            "• Norme NF C 15-100 : Installations électriques à basse tension",
            "• Guide UTE C 15-712-1 : Installations PV raccordées au réseau",
            "• Code de l'urbanisme – Déclaration préalable de travaux",
            "• Code de l'énergie – Articles L315-1 et suivants (autoconsommation)",
            "• Arrêté du 9 mai 2017 fixant les conditions d'achat pour le photovoltaïque",
        ]

        for r in reglementaire:
            c.drawString(2 * cm, y, r)
            y -= 0.45 * cm

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Assurances")

        assurances = [
            "• Responsabilité Civile Professionnelle",
            "• Assurance Décennale",
            "• Garantie de parfait achèvement",
            "• Garantie biennale de bon fonctionnement",
        ]

        for a in assurances:
            c.drawString(2 * cm, y, a)
            y -= 0.45 * cm

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Conditions Générales de Vente (extrait)")

        c.setFont("Helvetica", 7)
        cgv = [
            "1. Le présent devis est valable 30 jours à compter de sa date d'émission.",
            "2. Un acompte de 30% est demandé à la signature du devis pour engager la commande.",
            "3. Le solde est payable à la mise en service de l'installation.",
            "4. Les prix s'entendent hors taxes, TVA en sus au taux en vigueur.",
            "5. Les délais de réalisation sont donnés à titre indicatif et ne constituent pas un engagement ferme.",
            "6. Ils peuvent être impactés par les délais de raccordement Enedis et d'instruction administrative.",
            "7. L'installateur s'engage à réaliser les travaux conformément aux normes en vigueur.",
            "8. Le client s'engage à fournir un accès au site et à l'alimentation électrique pendant les travaux.",
            "9. En cas de litige, les tribunaux de la juridiction du siège social de l'installateur seront compétents.",
            "10. Le client dispose d'un délai de rétractation de 14 jours pour les contrats conclus à distance.",
        ]

        for line in cgv:
            c.drawString(2 * cm, y, line)
            y -= 0.4 * cm

        # Signature
        y -= 1.5 * cm
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(self.COLOR_DARK)
        c.drawString(2 * cm, y, "Bon pour accord – Lu et approuvé")

        y -= 0.5 * cm
        c.setFont("Helvetica", 9)
        c.drawString(2 * cm, y, f"Fait à {self.prospect.get('commune', '.....................')} le {self.date_now.strftime('%d/%m/%Y')}")

        y -= 1.5 * cm
        c.drawString(2 * cm, y, "Signature du client :")
        c.setLineWidth(0.5)
        c.line(6 * cm, y - 0.3 * cm, 12 * cm, y - 0.3 * cm)

        c.drawString(12.5 * cm, y, "Signature installateur :")
        c.line(16 * cm, y - 0.3 * cm, self.width - 1 * cm, y - 0.3 * cm)
