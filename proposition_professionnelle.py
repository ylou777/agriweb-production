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
from reportlab.lib.utils import ImageReader
from datetime import datetime, timedelta
import io
import math
import json
import base64
import requests


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

        # ── Résultats simulation autoconsommation (si disponibles) ────────────────
        # Priorité : données issues de la simulation PVGIS 8760h > estimations
        self.autoconso_data = parametres.get('autoconso_data') or {}
        _kpis = self.autoconso_data.get('kpis', {})
        _eco  = self.autoconso_data.get('economics', {})

        # Production : réelle PVGIS si dispos, sinon 1100 kWh/kWc moyen France
        # Clés issues de compute_autoconsommation() : production_annuelle_kwh, autoconso_kwh, surplus_kwh, taux_autoconsommation (en %)
        if _kpis.get('production_annuelle_kwh'):
            self.production_annuelle   = self._sf(_kpis['production_annuelle_kwh'])
            self.energie_autoconsommee = self._sf(_kpis.get('autoconso_kwh', 0))
            self.energie_revendue      = self._sf(_kpis.get('surplus_kwh', 0))
            # taux_autoconsommation est en % (75.0), self.taux_autoconso est en fraction (0.75)
            self.taux_autoconso        = self._sf(_kpis.get('taux_autoconsommation', self.taux_autoconso * 100)) / 100.0
            self.consommation          = self._sf(_kpis.get('consommation_annuelle_kwh', self.consommation))
        else:
            self.production_annuelle   = self.puissance_kwc * 1100  # estimation
            self.energie_autoconsommee = self.production_annuelle * self.taux_autoconso
            self.energie_revendue      = self.production_annuelle * (1 - self.taux_autoconso)

        # Financier : réel simulation si dispos, sinon estimation
        if _eco.get('economie_an1'):
            self.economie_autoconso = self._sf(_eco.get('economie_an1', 0))
            self.revenu_revente     = self._sf(_eco.get('revenu_surplus_an1', 0))
            self.gain_annuel        = self._sf(_eco.get('gain_total_an1', 0))
            self.tarif_achat        = self._sf(_eco.get('tarif_achat', self.tarif_achat))
            self.tarif_revente      = self._sf(_eco.get('tarif_revente', self.tarif_revente))
            # Projections multi-années depuis simulation
            self._economies_par_an  = [self._sf(v) for v in _eco.get('economies_par_an', [])]
            self._revenus_par_an    = [self._sf(v) for v in _eco.get('revenus_par_an', [])]
            self._tariff_label      = _eco.get('tariff_label', self.autoconso_data.get('tariff_label', ''))
        else:
            if self.type_projet == 'autoconsommation':
                self.economie_autoconso = self.energie_autoconsommee * self.tarif_achat
                self.revenu_revente     = self.energie_revendue * self.tarif_revente
                self.gain_annuel        = self.economie_autoconso + self.revenu_revente
            else:
                self.energie_autoconsommee = 0
                self.energie_revendue      = self.production_annuelle
                self.economie_autoconso    = 0
                self.revenu_revente        = self.production_annuelle * self.tarif_revente
                self.gain_annuel           = self.revenu_revente
            self._economies_par_an  = []
            self._revenus_par_an    = []
            self._tariff_label      = ''

        self.roi_annees   = self.investissement / self.gain_annuel if self.gain_annuel > 0 else 99
        self.rentabilite  = (self.gain_annuel / self.investissement * 100) if self.investissement > 0 else 0

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

        # Page 4b : Plan de situation (si lat/lon disponibles)
        _lat = self.data_json.get('rapport', {}).get('lat') or self.prospect.get('lat')
        _lon = self.data_json.get('rapport', {}).get('lon') or self.prospect.get('lon')
        if _lat and _lon:
            c.showPage()
            self.page_number += 1
            self._draw_plan_situation(c)

        # Page 4c : Plan de calpinage (si screenshot disponible)
        _screenshot = self.data_json.get('calpinage', {}).get('screenshot_map', '')
        if _screenshot:
            c.showPage()
            self.page_number += 1
            self._draw_plan_calpinage(c)

        # Page 4c2 : Analyse irradiance Google Solar (si données disponibles)
        if self.data_json.get('calpinage', {}).get('solar_analysis'):
            c.showPage()
            self.page_number += 1
            self._draw_google_solar(c)

        # Page 4d : Rapport contraintes site (si rapport_point disponible)
        if self.data_json.get('rapport'):
            c.showPage()
            self.page_number += 1
            self._draw_rapport_contraintes(c)

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

        # Pages 8A-8C : Simulation autoconsommation (si données disponibles)
        if self.autoconso_data:
            c.showPage()
            self.page_number += 1
            self._draw_etude_autoconsommation(c)

            c.showPage()
            self.page_number += 1
            self._draw_autoconso_monthly_table(c)

            c.showPage()
            self.page_number += 1
            self._draw_autoconso_daily_profiles(c)

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
        band_top = band_y + band_h  # y = 75 % de la hauteur de page

        # Image 3D en fond de la zone haute (au-dessus de la bande blanche)
        screenshot_3d = self.calpinage.get('screenshot_3d', '')
        if screenshot_3d:
            img_3d = self._decode_base64_image(screenshot_3d)
            if img_3d:
                zone_h = self.height - band_top          # 25 % de la page
                c.drawImage(img_3d, 0, band_top,
                            width=self.width, height=zone_h,
                            preserveAspectRatio=False, mask='auto')
                # Overlay vert semi-transparent pour lisibilité du texte AGRIWEB
                overlay = colors.Color(0, 0.18, 0.08, alpha=0.48)
                c.setFillColor(overlay)
                c.rect(0, band_top, self.width, zone_h, fill=1, stroke=0)

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

    def _draw_etude_autoconsommation(self, c):
        """Page 8A : KPI + bilan + graphique mensuel production vs consommation"""
        y = self._draw_page_header(c, "8. SIMULATION AUTOCONSOMMATION")

        tariff_label = self._tariff_label
        profil_label = self.autoconso_data.get('profil_label', '')
        date_calcul  = (self.autoconso_data.get('date_calcul', '') or '')[:10]

        # Mention source
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.HexColor('#78909C'))
        src_txt = f"Simulation horaire PVGIS 8760h × Profil {profil_label}"
        if tariff_label:
            src_txt += f" | Tarif : {tariff_label}"
        if date_calcul:
            src_txt += f" | Calculé le {date_calcul}"
        c.drawString(1.5 * cm, y + 0.15 * cm, src_txt)
        y -= 1.0 * cm

        # ── KPIs (clés correctes issues de compute_autoconsommation) ────────────
        _kpis = self.autoconso_data.get('kpis', {})
        _eco  = self.autoconso_data.get('economics', {})

        prod_kwh     = self._sf(_kpis.get('production_annuelle_kwh'))
        conso_kwh    = self._sf(_kpis.get('consommation_annuelle_kwh', self.consommation))
        auto_kwh     = self._sf(_kpis.get('autoconso_kwh'))
        surplus_kwh  = self._sf(_kpis.get('surplus_kwh'))
        # taux_autoconsommation est déjà en % (ex: 75.0)
        taux_ac      = self._sf(_kpis.get('taux_autoconsommation', 0))
        taux_ap      = self._sf(_kpis.get('taux_autosuffisance', 0))
        eco_an1      = self._sf(_eco.get('economie_an1'))
        rev_an1      = self._sf(_eco.get('revenu_surplus_an1'))
        gain_an1     = self._sf(_eco.get('gain_total_an1'))
        cumul        = self._sf(_eco.get('cumul_total'))
        duree_ans    = int(_eco.get('duree_ans', 20))
        detail_tarif = _eco.get('detail_tariff', {})

        box_w = (self.width - 3.5 * cm) / 4
        box_h = 1.9 * cm
        box_y = y - box_h
        kpi_boxes = [
            ("PRODUCTION",    self._format_kwh(prod_kwh),    "kWh/an PVGIS",    '#1565C0'),
            ("AUTOCONSOMMÉE", self._format_kwh(auto_kwh),    f"{taux_ac:.0f}% du total", '#2E7D32'),
            ("ÉCONOMIES AN 1", self._format_euros(eco_an1),   f"+ {self._format_euros(rev_an1)} surplus", '#E65100'),
            (f"CUMUL {duree_ans} ANS", self._format_euros(cumul), f"ROI {self.roi_annees:.1f} ans",  '#4A148C'),
        ]
        for i, (label, val, sub, color_hex) in enumerate(kpi_boxes):
            bx = 1.5 * cm + i * (box_w + 0.1 * cm)
            self._draw_highlight_box(c, bx, box_y, box_w - 0.1 * cm, box_h, label, val, sub)

        y = box_y - 1.2 * cm

        # ── Tableau synthèse gauche ────────────────────────────────────────────
        y = self._draw_section_title(c, y, "Bilan énergétique annuel")
        y = self._draw_kv_line(c, y, "Production PV totale :",      self._format_kwh(prod_kwh))
        y = self._draw_kv_line(c, y, "Consommation annuelle :",     self._format_kwh(conso_kwh))
        y = self._draw_kv_line(c, y, "Énergie autoconsommée :",    f"{self._format_kwh(auto_kwh)} ({taux_ac:.0f}%)", bold_value=True)
        y = self._draw_kv_line(c, y, "Surplus injecté réseau :",   f"{self._format_kwh(surplus_kwh)} ({100-taux_ac:.0f}%)")
        if taux_ap > 0:
            y = self._draw_kv_line(c, y, "Taux d'autosuffisance :",  f"{taux_ap:.0f}% de la conso couverte par le PV")
        if tariff_label:
            y = self._draw_kv_line(c, y, "Option tarifaire :",       tariff_label)
        if detail_tarif:
            prix_moy = self._sf(detail_tarif.get('mean')) * 100
            prix_min = self._sf(detail_tarif.get('min'))  * 100
            prix_max = self._sf(detail_tarif.get('max'))  * 100
            y = self._draw_kv_line(c, y, "Prix achat électricite :",
                f"moy. {prix_moy:.2f} c€  ·  min {prix_min:.2f} c€  ·  max {prix_max:.2f} c€/kWh")
        y -= 0.2 * cm

        # ── Graphique mensuel : production vs consommation ──────────────────────
        # monthly est un dict { 'labels':[], 'production':[], 'consommation':[], 'autoconso':[], ... }
        monthly = self.autoconso_data.get('monthly', {})
        m_prod  = monthly.get('production', [])
        m_conso = monthly.get('consommation', [])
        m_auto  = monthly.get('autoconso', [])
        if len(m_prod) >= 12:
            y = self._draw_section_title(c, y, "Production mensuelle vs Consommation (kWh)")
            MOIS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                    'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
            prods  = [self._sf(v) for v in m_prod[:12]]
            consos = [self._sf(v) for v in m_conso[:12]]
            autos  = [self._sf(v) for v in m_auto[:12]]

            max_val = max(max(prods), max(consos), 1)
            graph_w = self.width - 3 * cm
            graph_h = 4.5 * cm
            bar_group_w = graph_w / 12
            bar_w       = bar_group_w * 0.35

            # Axe
            c.setStrokeColor(colors.HexColor('#CFD8DC'))
            c.setLineWidth(0.5)
            c.line(1.5 * cm, y - graph_h - 0.4 * cm, 1.5 * cm + graph_w, y - graph_h - 0.4 * cm)

            for i, mois in enumerate(MOIS):
                bx_base = 1.5 * cm + i * bar_group_w

                # Barre production (bleu)
                ph = prods[i] / max_val * graph_h if max_val > 0 else 0
                c.setFillColor(colors.HexColor('#1E88E5'))
                c.rect(bx_base + bar_group_w * 0.05, y - graph_h - 0.4 * cm, bar_w, ph, fill=1, stroke=0)

                # Zone autoconsommée sur barre prod (vert)
                ah = min(autos[i], prods[i]) / max_val * graph_h if max_val > 0 else 0
                c.setFillColor(colors.HexColor('#43A047'))
                c.setFillAlpha(0.6)
                c.rect(bx_base + bar_group_w * 0.05, y - graph_h - 0.4 * cm, bar_w, ah, fill=1, stroke=0)
                c.setFillAlpha(1.0)

                # Barre conso (orange)
                ch = consos[i] / max_val * graph_h if max_val > 0 else 0
                c.setFillColor(colors.HexColor('#FB8C00'))
                c.rect(bx_base + bar_group_w * 0.45, y - graph_h - 0.4 * cm, bar_w, ch, fill=1, stroke=0)

                # Valeur en haut de chaque barre (prod)
                c.setFont("Helvetica", 5)
                c.setFillColor(self.COLOR_DARK)
                c.drawCentredString(bx_base + bar_group_w * 0.225,
                                    y - graph_h - 0.4 * cm + ph + 0.05 * cm,
                                    f"{int(prods[i])}")

                # Label mois
                c.setFont("Helvetica", 6)
                c.drawCentredString(bx_base + bar_group_w * 0.5, y - graph_h - 0.8 * cm, mois)

            y -= graph_h + 1.3 * cm

            # Légende
            legend_items = [
                (colors.HexColor('#1E88E5'), "Production PV"),
                (colors.HexColor('#43A047'), "Autoconsommée"),
                (colors.HexColor('#FB8C00'), "Consommation"),
            ]
            lx = 1.5 * cm
            for col, lbl in legend_items:
                c.setFillColor(col)
                c.rect(lx, y + 0.1 * cm, 0.35 * cm, 0.3 * cm, fill=1, stroke=0)
                c.setFillColor(self.COLOR_DARK)
                c.setFont("Helvetica", 7)
                c.drawString(lx + 0.45 * cm, y + 0.12 * cm, lbl)
                lx += 3.8 * cm
            y -= 0.7 * cm

        # ── Graphique cumul des gains sur N ans ─────────────────────────────────
        if self._economies_par_an:
            y = self._draw_section_title(c, y, f"Cumul des gains sur {duree_ans} ans")
            n = len(self._economies_par_an)
            cumul_eco   = []
            cumul_rev   = []
            cumul_total = []
            s_e = s_r = 0
            for i in range(n):
                s_e += self._economies_par_an[i]
                s_r += (self._revenus_par_an[i] if i < len(self._revenus_par_an) else 0)
                cumul_eco.append(s_e)
                cumul_rev.append(s_r)
                cumul_total.append(s_e + s_r)

            max_c = max(max(cumul_total), self.investissement, 1)
            g2_w  = self.width - 3 * cm
            g2_h  = 4.0 * cm
            step  = g2_w / max(n - 1, 1)
            base_y = y - g2_h - 0.3 * cm

            # Axe horizontal + investissement ligne
            c.setStrokeColor(colors.HexColor('#CFD8DC'))
            c.setLineWidth(0.5)
            c.line(1.5 * cm, base_y, 1.5 * cm + g2_w, base_y)

            # Trait investissement (rouge pointillé)
            inv_y = base_y + (self.investissement / max_c) * g2_h
            c.setStrokeColor(colors.HexColor('#E53935'))
            c.setDash(3, 3)
            c.line(1.5 * cm, inv_y, 1.5 * cm + g2_w, inv_y)
            c.setDash()
            c.setFont("Helvetica-Oblique", 6)
            c.setFillColor(colors.HexColor('#E53935'))
            c.drawString(1.5 * cm + g2_w + 0.1 * cm, inv_y, "Invest.")

            # Courbe cumul total (vert)
            pts = [(1.5 * cm + i * step, base_y + (v / max_c) * g2_h)
                   for i, v in enumerate(cumul_total)]
            c.setStrokeColor(colors.HexColor('#2E7D32'))
            c.setLineWidth(1.5)
            p = c.beginPath()
            p.moveTo(*pts[0])
            for pt in pts[1:]:
                p.lineTo(*pt)
            c.drawPath(p, stroke=1, fill=0)

            # Courbe cumul économies seules (bleu)
            pts2 = [(1.5 * cm + i * step, base_y + (v / max_c) * g2_h)
                    for i, v in enumerate(cumul_eco)]
            c.setStrokeColor(colors.HexColor('#1565C0'))
            c.setLineWidth(1)
            p2 = c.beginPath()
            p2.moveTo(*pts2[0])
            for pt in pts2[1:]:
                p2.lineTo(*pt)
            c.drawPath(p2, stroke=1, fill=0)

            # Labels années
            c.setFont("Helvetica", 6)
            c.setFillColor(self.COLOR_DARK)
            for i in range(0, n, max(1, n // 5)):
                lx2 = 1.5 * cm + i * step
                c.drawCentredString(lx2, base_y - 0.35 * cm, f"An {i+1}")

            y = base_y - 0.8 * cm

            # Légende courbes
            lx = 1.5 * cm
            for col, lbl in [
                (colors.HexColor('#2E7D32'), "Gains cumulés totaux"),
                (colors.HexColor('#1565C0'), "Économies seules"),
                (colors.HexColor('#E53935'), "Investissement"),
            ]:
                c.setStrokeColor(col)
                c.setLineWidth(1.5)
                c.line(lx, y + 0.18 * cm, lx + 0.6 * cm, y + 0.18 * cm)
                c.setFillColor(self.COLOR_DARK)
                c.setFont("Helvetica", 7)
                c.drawString(lx + 0.7 * cm, y + 0.1 * cm, lbl)
                lx += 5.0 * cm

        self._draw_page_footer(c)

    def _draw_autoconso_monthly_table(self, c):
        """Page 8B : Tableau mensuel détaillé + graphique taux de couverture"""
        y = self._draw_page_header(c, "8B. ANALYSE MENSUELLE DÉTAILLÉE")

        _kpis = self.autoconso_data.get('kpis', {})
        monthly = self.autoconso_data.get('monthly', {})
        m_prod     = monthly.get('production',   [0]*12)
        m_conso    = monthly.get('consommation', [0]*12)
        m_auto     = monthly.get('autoconso',    [0]*12)
        m_surp     = monthly.get('surplus',      [0]*12)
        m_taux_ac  = monthly.get('taux_ac',      [0]*12)  # % de la prod autoconsommée
        m_taux_as  = monthly.get('taux_as',      [0]*12)  # % de la conso couverte par PV
        MOIS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

        # ── Tableau mensuel ─────────────────────────────────────────────────────
        y = self._draw_section_title(c, y, "Bilan mensuel (kWh)")
        col_x  = [1.5, 3.2, 5.8, 8.4, 11.0, 13.6, 16.2]  # cm
        col_w  = [1.7, 2.4, 2.4, 2.4,  2.4,  2.4,  2.4]
        hdrs   = ["Mois", "Prod. (kWh)", "Conso (kWh)", "Autoconso.", "Surplus", "Taux AC%", "Cov.*%"]
        row_h  = 0.52 * cm
        tbl_w  = self.width - 3 * cm

        # En-tête
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(1.5 * cm, y - row_h + 0.15*cm, tbl_w, row_h, fill=1, stroke=0)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 7.5)
        for j, hdr in enumerate(hdrs):
            c.drawString((col_x[j] + 0.15) * cm, y - row_h + 0.35*cm, hdr)
        y -= row_h

        total_prod = total_conso = total_auto = total_surp = 0
        for i, mois in enumerate(MOIS):
            prod  = self._sf(m_prod[i]  if i < len(m_prod)  else 0)
            conso = self._sf(m_conso[i] if i < len(m_conso) else 0)
            auto  = self._sf(m_auto[i]  if i < len(m_auto)  else 0)
            surp  = self._sf(m_surp[i]  if i < len(m_surp)  else 0)
            tac   = self._sf(m_taux_ac[i] if i < len(m_taux_ac) else 0)
            tas   = self._sf(m_taux_as[i]  if i < len(m_taux_as)  else 0)
            total_prod  += prod
            total_conso += conso
            total_auto  += auto
            total_surp  += surp

            # Fond alterné
            if i % 2 == 0:
                c.setFillColor(colors.HexColor('#F1F8E9'))
            else:
                c.setFillColor(colors.white)
            c.rect(1.5*cm, y - row_h + 0.15*cm, tbl_w, row_h, fill=1, stroke=0)

            # Indicateur couleur couverture (vert si bonnes, jaune si moyen, orange si faible)
            cov_color = colors.HexColor('#2E7D32') if tas >= 50 else (colors.HexColor('#F57C00') if tas >= 25 else colors.HexColor('#B71C1C'))

            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica-Bold" if i == 5 or i == 6 else "Helvetica", 7.5)  # bold juin/juil (max)
            c.drawString((col_x[0] + 0.15)*cm, y - row_h + 0.3*cm, mois)
            c.setFont("Helvetica", 7.5)
            c.drawRightString((col_x[1] + col_w[1] - 0.2)*cm, y - row_h + 0.3*cm, f"{prod:,.0f}")
            c.drawRightString((col_x[2] + col_w[2] - 0.2)*cm, y - row_h + 0.3*cm, f"{conso:,.0f}")
            c.setFillColor(colors.HexColor('#2E7D32'))
            c.drawRightString((col_x[3] + col_w[3] - 0.2)*cm, y - row_h + 0.3*cm, f"{auto:,.0f}")
            c.setFillColor(colors.HexColor('#1565C0'))
            c.drawRightString((col_x[4] + col_w[4] - 0.2)*cm, y - row_h + 0.3*cm, f"{surp:,.0f}")
            c.setFillColor(self.COLOR_DARK)
            c.drawRightString((col_x[5] + col_w[5] - 0.2)*cm, y - row_h + 0.3*cm, f"{tac:.0f}%")
            c.setFillColor(cov_color)
            c.drawRightString((col_x[6] + col_w[6] - 0.2)*cm, y - row_h + 0.3*cm, f"{tas:.0f}%")
            y -= row_h

        # Ligne total
        c.setFillColor(colors.HexColor('#E8F5E9'))
        c.rect(1.5*cm, y - row_h + 0.15*cm, tbl_w, row_h, fill=1, stroke=0)
        c.setFillColor(self.COLOR_DARK)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString((col_x[0]+0.15)*cm, y - row_h + 0.3*cm, "TOTAL")
        c.drawRightString((col_x[1]+col_w[1]-0.2)*cm, y - row_h + 0.3*cm, f"{total_prod:,.0f}")
        c.drawRightString((col_x[2]+col_w[2]-0.2)*cm, y - row_h + 0.3*cm, f"{total_conso:,.0f}")
        c.setFillColor(colors.HexColor('#2E7D32'))
        c.drawRightString((col_x[3]+col_w[3]-0.2)*cm, y - row_h + 0.3*cm, f"{total_auto:,.0f}")
        c.setFillColor(colors.HexColor('#1565C0'))
        c.drawRightString((col_x[4]+col_w[4]-0.2)*cm, y - row_h + 0.3*cm, f"{total_surp:,.0f}")
        c.setFillColor(self.COLOR_DARK)
        tac_tot  = total_auto / total_prod  * 100 if total_prod  > 0 else 0
        tas_tot  = total_auto / total_conso * 100 if total_conso > 0 else 0
        c.drawRightString((col_x[5]+col_w[5]-0.2)*cm, y - row_h + 0.3*cm, f"{tac_tot:.0f}%")
        c.drawRightString((col_x[6]+col_w[6]-0.2)*cm, y - row_h + 0.3*cm, f"{tas_tot:.0f}%")
        y -= row_h + 0.2*cm

        # Légende *
        c.setFont("Helvetica-Oblique", 6)
        c.setFillColor(colors.HexColor('#78909C'))
        c.drawString(1.5*cm, y, "* Taux AC = % de la production autoconsommée  ·  Cov. = Couverture = % de la consommation couverte par le PV")
        y -= 0.9*cm

        # ── Graphique : taux de couverture mensuel (barres empilées) ───────────
        y = self._draw_section_title(c, y, "Couverture mensuelle de la consommation")

        graph_w  = self.width - 3 * cm
        graph_h  = 4.2 * cm
        bar_gw   = graph_w / 12
        bar_base = y - graph_h - 0.4*cm

        # Axe horizontal
        c.setStrokeColor(colors.HexColor('#CFD8DC'))
        c.setLineWidth(0.5)
        c.line(1.5*cm, bar_base, 1.5*cm + graph_w, bar_base)

        # Axe vertical (grille à 25%, 50%, 75%, 100%)
        for pct in [25, 50, 75, 100]:
            gy = bar_base + pct / 100.0 * graph_h
            c.setStrokeColor(colors.HexColor('#ECEFF1'))
            c.setDash(2, 2)
            c.line(1.5*cm, gy, 1.5*cm + graph_w, gy)
            c.setDash()
            c.setFont("Helvetica", 5.5)
            c.setFillColor(colors.HexColor('#90A4AE'))
            c.drawRightString(1.4*cm, gy - 0.07*cm, f"{pct}%")

        for i, mois in enumerate(MOIS):
            conso = self._sf(m_conso[i] if i < len(m_conso) else 0)
            auto  = self._sf(m_auto[i]  if i < len(m_auto)  else 0)
            deficit = max(conso - auto, 0)
            bx = 1.5*cm + i * bar_gw + bar_gw * 0.1
            bw = bar_gw * 0.8

            if conso > 0:
                ha = auto    / conso * graph_h  # hauteur autoconsommée
                hd = deficit / conso * graph_h  # hauteur réseau

                # Réseau (gris clair) - dessous
                c.setFillColor(colors.HexColor('#CFD8DC'))
                c.rect(bx, bar_base, bw, min(ha + hd, graph_h), fill=1, stroke=0)

                # Autoconsommée (vert) - par-dessus
                c.setFillColor(colors.HexColor('#43A047'))
                c.rect(bx, bar_base, bw, min(ha, graph_h), fill=1, stroke=0)

                # Valeur %tas dans la barre si assez haute
                if ha > 0.3*cm:
                    tas_v = auto / conso * 100
                    c.setFont("Helvetica-Bold", 5.5)
                    c.setFillColor(colors.white)
                    c.drawCentredString(bx + bw/2, bar_base + ha/2 - 0.05*cm, f"{tas_v:.0f}%")

            # Label mois
            c.setFont("Helvetica", 6)
            c.setFillColor(self.COLOR_DARK)
            c.drawCentredString(bx + bw/2, bar_base - 0.35*cm, mois)

        y = bar_base - 0.8*cm

        # Légende
        lx = 1.5*cm
        for col, lbl in [(colors.HexColor('#43A047'), "Autoconsommée (PV direct)"),
                         (colors.HexColor('#CFD8DC'), "Réseau électrique")]:
            c.setFillColor(col)
            c.rect(lx, y + 0.1*cm, 0.35*cm, 0.3*cm, fill=1, stroke=0)
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica", 7)
            c.drawString(lx + 0.45*cm, y + 0.12*cm, lbl)
            lx += 5.5*cm

        self._draw_page_footer(c)

    def _draw_autoconso_daily_profiles(self, c):
        """Page 8C : Profils journaliers 24h par saison (hiver / printemps / été)"""
        y = self._draw_page_header(c, "8C. PROFILS JOURNALIERS SAISONNIERS")

        dp = self.autoconso_data.get('daily_profiles', {})
        if not dp:
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.HexColor('#78909C'))
            c.drawCentredString(self.width / 2, y - 2*cm,
                                "Données de profils journaliers non disponibles.")
            self._draw_page_footer(c)
            return

        hours        = list(range(24))
        seasons = [
            ('Hiver (Déc-Fév)',    dp.get('winter_prod',  [0]*24), dp.get('winter_conso',  [0]*24), '#1565C0', '#FB8C00'),
            ('Mi-saison (Avr-Mai)', dp.get('spring_prod',  [0]*24), dp.get('spring_conso',  [0]*24), '#1E88E5', '#FFA726'),
            ('Été (Jun-Aoû)',      dp.get('summer_prod',  [0]*24), dp.get('summer_conso',  [0]*24), '#42A5F5', '#FF7043'),
        ]

        panel_h = 5.5 * cm
        panel_w = (self.width - 3.5 * cm) / 3
        panel_gap = 0.25 * cm
        HEURES_LABEL = ['0', '', '', '', '4', '', '', '', '8', '', '', '', '12', '', '', '', '16', '', '', '', '20', '', '', '23']

        y -= 0.5 * cm

        for si, (season_lbl, s_prod, s_conso, col_prod_hex, col_conso_hex) in enumerate(seasons):
            px = 1.5 * cm + si * (panel_w + panel_gap)
            py_base = y - panel_h - 0.8 * cm

            # Cadre fond
            c.setFillColor(colors.HexColor('#FAFAFA'))
            c.setStrokeColor(colors.HexColor('#E0E0E0'))
            c.setLineWidth(0.5)
            c.roundRect(px - 0.1*cm, py_base - 0.2*cm, panel_w + 0.2*cm, panel_h + 1.2*cm, 3, fill=1, stroke=1)

            # Titre saison
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(px + panel_w/2, py_base + panel_h + 0.4*cm, season_lbl)

            # Calcul max pour normalisation
            max_val = max(max(s_prod, default=0), max(s_conso, default=0), 0.001)

            # Axe horizontal
            c.setStrokeColor(colors.HexColor('#CFD8DC'))
            c.setLineWidth(0.4)
            c.line(px, py_base, px + panel_w, py_base)

            # Grille horizontale légère
            for pct in [0.25, 0.5, 0.75, 1.0]:
                gy = py_base + pct * panel_h
                c.setStrokeColor(colors.HexColor('#F5F5F5'))
                c.line(px, gy, px + panel_w, gy)

            step_x = panel_w / 23.0

            # Zone autoconsommée (fond vert clair - min(prod, conso) à chaque heure)
            auto_pts  = [min(self._sf(s_prod[h]), self._sf(s_conso[h])) for h in range(24)]
            auto_poly = [(px, py_base)]
            for h in range(24):
                hx = px + h * step_x
                hy = py_base + (auto_pts[h] / max_val) * panel_h
                auto_poly.append((hx, hy))
            auto_poly.append((px + 23 * step_x, py_base))
            p_fill = c.beginPath()
            p_fill.moveTo(*auto_poly[0])
            for pt in auto_poly[1:]:
                p_fill.lineTo(*pt)
            p_fill.close()
            c.setFillColor(colors.HexColor('#C8E6C9'))
            c.setFillAlpha(0.7)
            c.drawPath(p_fill, stroke=0, fill=1)
            c.setFillAlpha(1.0)

            # Courbe production (bleu)
            prod_pts = [(px + h * step_x, py_base + (self._sf(s_prod[h]) / max_val) * panel_h) for h in range(24)]
            c.setStrokeColor(colors.HexColor(col_prod_hex))
            c.setLineWidth(1.3)
            path_p = c.beginPath()
            path_p.moveTo(*prod_pts[0])
            for pt in prod_pts[1:]:
                path_p.lineTo(*pt)
            c.drawPath(path_p, stroke=1, fill=0)

            # Courbe conso (orange)
            conso_pts = [(px + h * step_x, py_base + (self._sf(s_conso[h]) / max_val) * panel_h) for h in range(24)]
            c.setStrokeColor(colors.HexColor(col_conso_hex))
            c.setLineWidth(1.3)
            c.setDash(3, 2)
            path_c = c.beginPath()
            path_c.moveTo(*conso_pts[0])
            for pt in conso_pts[1:]:
                path_c.lineTo(*pt)
            c.drawPath(path_c, stroke=1, fill=0)
            c.setDash()

            # Axes heures (labels 0, 4, 8, 12, 16, 20, 23)
            c.setFont("Helvetica", 5)
            c.setFillColor(colors.HexColor('#90A4AE'))
            for h in [0, 4, 8, 12, 16, 20, 23]:
                hx = px + h * step_x
                c.drawCentredString(hx, py_base - 0.3*cm, str(h) + 'h')

        # Légende commune sous les 3 panels
        legend_y = y - panel_h - 1.9*cm
        lx = 1.5*cm
        for col, lbl, dash in [
            ('#1565C0', "Production PV (kWh moy./h)", False),
            ('#FB8C00', "Consommation (kWh moy./h)", True),
            ('#C8E6C9', "Autoconsommée (zone verte)", False),
        ]:
            if dash:
                c.setStrokeColor(colors.HexColor(col))
                c.setLineWidth(1.2)
                c.setDash(3, 2)
                c.line(lx, legend_y + 0.15*cm, lx + 0.6*cm, legend_y + 0.15*cm)
                c.setDash()
            else:
                c.setFillColor(colors.HexColor(col))
                c.rect(lx, legend_y + 0.05*cm, 0.6*cm, 0.3*cm, fill=1, stroke=0)
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica", 7)
            c.drawString(lx + 0.7*cm, legend_y + 0.1*cm, lbl)
            lx += 6.5*cm

        legend_y -= 1.0*cm

        # ── Analyse textuelle par saison ─────────────────────────────────────
        y2 = legend_y - 0.5*cm
        y2 = self._draw_section_title(c, y2, "Interprétation des profils")

        dp_summ = []
        for si, (season_lbl, s_prod, s_conso, _, _) in enumerate(seasons):
            max_prod_h = max(range(24), key=lambda h: self._sf(s_prod[h]))
            total_prod_d = sum(self._sf(v) for v in s_prod)
            total_conso_d = sum(self._sf(v) for v in s_conso)
            auto_d = sum(min(self._sf(s_prod[h]), self._sf(s_conso[h])) for h in range(24))
            cov_pct = auto_d / total_conso_d * 100 if total_conso_d > 0 else 0
            dp_summ.append((season_lbl, total_prod_d, total_conso_d, auto_d, cov_pct, max_prod_h))

        for (season_lbl, tp, tc, ta, cov, mph) in dp_summ:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(self.COLOR_PRIMARY)
            c.drawString(1.5*cm, y2, f"▸ {season_lbl}")
            y2 -= 0.45*cm
            c.setFont("Helvetica", 7.5)
            c.setFillColor(self.COLOR_DARK)
            txt = (f"Prod. jour moy. {tp:.2f} kWh  ·  Conso {tc:.2f} kWh  ·  "
                   f"Autoconsommée {ta:.2f} kWh  ·  Couverture {cov:.0f}%  ·  "
                   f"Pic production à {mph}h")
            c.drawString(2.0*cm, y2, txt)
            y2 -= 0.6*cm

        y2 -= 0.3*cm
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.HexColor('#78909C'))
        c.drawString(1.5*cm, y2,
            "Profil journalier moyen calculé sur l'ensemble des jours de la saison (PVGIS 8760h).")

        self._draw_page_footer(c)

    # =========================================================================
    # PAGES GRAPHIQUES : PLANS & RAPPORT POINT
    # =========================================================================

    def _fetch_static_map_image(self, lat, lon, zoom=16, width=600, height=380):
        """Télécharge une image de carte OSM static et retourne un ImageReader ReportLab.
        Retourne None si indisponible."""
        try:
            url = (
                f"https://staticmap.openstreetmap.de/staticmap.php"
                f"?center={lat},{lon}&zoom={zoom}&size={width}x{height}"
                f"&markers={lat},{lon},red"
            )
            resp = requests.get(url, timeout=8,
                                headers={"User-Agent": "AgriWeb-PV-Proposition/1.0"})
            if resp.status_code == 200 and resp.content:
                return ImageReader(io.BytesIO(resp.content))
        except Exception:
            pass
        return None

    def _decode_base64_image(self, b64_str):
        """Decode une image base64 (avec ou sans header data:...) en ImageReader."""
        try:
            if not b64_str:
                return None
            if ',' in b64_str:
                b64_str = b64_str.split(',', 1)[1]
            img_bytes = base64.b64decode(b64_str)
            return ImageReader(io.BytesIO(img_bytes))
        except Exception:
            return None

    def _draw_risk_badge(self, c, x, y, label, value, color):
        """Dessine un badge de risque coloré (petit rectangle)."""
        bw, bh = 3.8 * cm, 0.9 * cm
        c.setFillColor(color)
        c.roundRect(x, y - 0.6 * cm, bw, bh, 4, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x + bw / 2, y - 0.05 * cm, label[:20])
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + bw / 2, y - 0.38 * cm, str(value)[:22])

    # ── Plan de situation ─────────────────────────────────────────────────────

    def _draw_plan_situation(self, c):
        """Page Plan de situation : carte OSM + données géographiques + PVGIS."""
        y = self._draw_page_header(c, "PLAN DE SITUATION")

        rapport = self.data_json.get('rapport', {})
        lat  = rapport.get('lat')  or self.prospect.get('lat')
        lon  = rapport.get('lon')  or self.prospect.get('lon')
        commune    = rapport.get('commune_name') or self.prospect.get('commune', '')
        cp         = rapport.get('code_postal')  or self.prospect.get('code_postal', '')
        adresse    = rapport.get('adresse')      or self.prospect.get('adresse_complete', '')
        altitude   = rapport.get('altitude_m')   or rapport.get('altitude', '')
        kwh_kwc    = rapport.get('kwh_per_kwc', '')
        # Parcelle
        api_details = rapport.get('api_details', {})
        cadastre    = api_details.get('cadastre', {}).get('details', {}) if isinstance(api_details, dict) else {}
        section     = cadastre.get('section', '')
        parcelle_n  = cadastre.get('parcelle_numero', '')
        contenance  = cadastre.get('contenance_m2', '')
        code_insee  = cadastre.get('code_insee', '')

        y -= 0.3 * cm

        # ─ Bloc info gauche ─────────────────────────────────────────────────
        bx, bw = 1.5 * cm, 8 * cm
        c.setFillColor(self.COLOR_HEADER_BG)
        c.rect(bx, y - 5.5 * cm, bw, 5.5 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(bx + 0.3 * cm, y - 0.3 * cm, "IDENTIFICATION DU SITE")
        ky = y - 0.8 * cm
        for lbl, val in [
            ("Commune :", f"{commune} ({cp})"),
            ("Adresse :", adresse[:45] if adresse else "—"),
            ("Coordonnées :", f"{lat:.5f}, {lon:.5f}" if lat and lon else "—"),
            ("Altitude :", f"{altitude} m" if altitude else "—"),
            ("Code INSEE :", code_insee or "—"),
            ("Parcelle :", f"Section {section} n°{parcelle_n}" if section else "—"),
            ("Surface parcelle :", f"{contenance} m²" if contenance else "—"),
        ]:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.HexColor('#555555'))
            c.drawString(bx + 0.3 * cm, ky, lbl)
            c.setFont("Helvetica", 8)
            c.setFillColor(self.COLOR_DARK)
            c.drawString(bx + 3.8 * cm, ky, str(val))
            ky -= 0.6 * cm

        # ─ PVGIS / Ensoleillement ────────────────────────────────────────────
        pvgis = rapport.get('pvgis_data', {})
        irradiation = ''
        if isinstance(pvgis, dict):
            irr = pvgis.get('yearly_irradiation') or pvgis.get('H(i)_m') or pvgis.get('irradiation')
            if irr:
                irradiation = f"{irr:.0f} kWh/m²/an"
        c.setFillColor(self.COLOR_ACCENT)
        c.rect(bx, y - 7.5 * cm, bw, 1.7 * cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(bx + 0.3 * cm, y - 6.1 * cm, "ENSOLEILLEMENT PVGIS")
        c.setFont("Helvetica", 8)
        c.drawString(bx + 0.3 * cm, y - 6.65 * cm, f"Productible : {kwh_kwc:.0f} kWh/kWc/an" if kwh_kwc else "Productible : —")
        c.drawString(bx + 0.3 * cm, y - 7.15 * cm, f"Irradiation : {irradiation}" if irradiation else "Irradiation : —")

        # ─ Carte OSM grande (vue commune, zoom 14) ───────────────────────────
        map_x  = bx + bw + 0.5 * cm
        map_w  = self.width - map_x - 1.5 * cm
        map_h  = 7.5 * cm
        img14 = None
        if lat and lon:
            img14 = self._fetch_static_map_image(float(lat), float(lon), zoom=14, width=500, height=330)
        if img14:
            c.drawImage(img14, map_x, y - map_h, width=map_w, height=map_h,
                        preserveAspectRatio=True, anchor='c')
        else:
            c.setFillColor(self.COLOR_LIGHT_BG)
            c.rect(map_x, y - map_h, map_w, map_h, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#AAAAAA'))
            c.setFont("Helvetica-Oblique", 9)
            c.drawCentredString(map_x + map_w / 2, y - map_h / 2 - 0.2 * cm, "Carte non disponible (hors-ligne)")
        # Légende carte
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.HexColor('#888888'))
        c.drawCentredString(map_x + map_w / 2, y - map_h - 0.3 * cm, "Vue d'ensemble — OpenStreetMap © contributeurs")

        y -= 8.3 * cm

        # ─ Carte OSM zoom (vue parcelle, zoom 17) ────────────────────────────
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.5 * cm, y, "Vue détaillée — parcelle cadastrale")
        y -= 0.6 * cm

        map2_w = (self.width - 3 * cm)
        map2_h = 8.0 * cm
        img17 = None
        if lat and lon:
            img17 = self._fetch_static_map_image(float(lat), float(lon), zoom=18, width=700, height=380)
        if img17:
            c.drawImage(img17, 1.5 * cm, y - map2_h, width=map2_w, height=map2_h,
                        preserveAspectRatio=True, anchor='c')
        else:
            c.setFillColor(self.COLOR_LIGHT_BG)
            c.rect(1.5 * cm, y - map2_h, map2_w, map2_h, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#AAAAAA'))
            c.setFont("Helvetica-Oblique", 9)
            c.drawCentredString(1.5 * cm + map2_w / 2, y - map2_h / 2 - 0.2 * cm, "Carte non disponible (hors-ligne)")
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.HexColor('#888888'))
        c.drawCentredString(1.5 * cm + map2_w / 2, y - map2_h - 0.3 * cm,
                            "Vue rapprochée — OpenStreetMap © contributeurs — zoom parcelle")

        self._draw_page_footer(c)

    # ── Google Solar — Irradiance & Pans de toiture ────────────────────────────

    def _draw_irradiance_scale(self, c, x, y, w, h, val_min, val_max, val_mean):
        """Dessine une échelle colorée de type Google Solar (bleu→vert→jaune→rouge)."""
        stops = [
            (0.00, colors.HexColor('#0000ff')),
            (0.20, colors.HexColor('#00aaff')),
            (0.40, colors.HexColor('#00cc88')),
            (0.55, colors.HexColor('#aadd00')),
            (0.70, colors.HexColor('#ffcc00')),
            (0.85, colors.HexColor('#ff6600')),
            (1.00, colors.HexColor('#ff0000')),
        ]
        nb = 60
        seg_w = w / nb
        for i in range(nb):
            t = i / (nb - 1)
            # Interpoler la couleur
            col = stops[0][1]
            for j in range(len(stops) - 1):
                t0, c0 = stops[j]
                t1, c1 = stops[j + 1]
                if t0 <= t <= t1:
                    f = (t - t0) / (t1 - t0)
                    r = c0.red   + f * (c1.red   - c0.red)
                    g = c0.green + f * (c1.green - c0.green)
                    b = c0.blue  + f * (c1.blue  - c0.blue)
                    col = colors.Color(r, g, b)
                    break
            c.setFillColor(col)
            c.rect(x + i * seg_w, y, seg_w + 0.5, h, fill=1, stroke=0)
        # Légende valeurs
        c.setFont('Helvetica', 6.5)
        c.setFillColor(self.COLOR_DARK)
        if val_min is not None:
            c.drawString(x, y - 0.35 * cm, f'{val_min:.0f} kWh/m²')
        if val_mean is not None:
            c.drawCentredString(x + w / 2, y - 0.35 * cm, f'moy: {val_mean:.0f} kWh/m²')
        if val_max is not None:
            c.drawRightString(x + w, y - 0.35 * cm, f'{val_max:.0f} kWh/m²')

    def _irr_color(self, val, irr_min, irr_max):
        """Retourne une couleur ReportLab interpolée selon l'irradiance."""
        if val is None or irr_min is None or irr_max is None or irr_max == irr_min:
            return colors.HexColor('#78909C')
        t = max(0.0, min(1.0, (val - irr_min) / (irr_max - irr_min)))
        stops = [
            (0.00, (0, 0, 255)),
            (0.40, (0, 200, 140)),
            (0.65, (255, 200, 0)),
            (0.85, (255, 100, 0)),
            (1.00, (255, 0, 0)),
        ]
        for j in range(len(stops) - 1):
            t0, c0 = stops[j]; t1, c1 = stops[j + 1]
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0)
                r = int(c0[0] + f * (c1[0] - c0[0]))
                g = int(c0[1] + f * (c1[1] - c0[1]))
                b = int(c0[2] + f * (c1[2] - c0[2]))
                return colors.Color(r/255, g/255, b/255)
        return colors.HexColor('#FF0000')

    def _draw_google_solar(self, c):
        """Page Analyse Google Solar : irradiance, bâtiment, pans de toiture."""
        solar = self.data_json.get('calpinage', {}).get('solar_analysis', {})
        if not solar:
            return

        y = self._draw_page_header(c, "ANALYSE IRRADIANCE GOOGLE SOLAR")
        y -= 0.2 * cm

        bldg   = solar.get('building_dims') or {}
        dsm    = solar.get('dsm_stats')     or {}
        pot    = solar.get('solar_potential') or {}
        segs   = solar.get('roof_segments')  or []
        flux_min  = solar.get('flux_min')
        flux_max  = solar.get('flux_max')
        flux_mean = solar.get('flux_mean')
        img_date  = solar.get('imagery_date') or {}
        source    = solar.get('source', '')

        # Date imagerie
        if isinstance(img_date, dict):
            img_date_str = f"{img_date.get('month', '?')}/{img_date.get('year', '?')}"
        else:
            img_date_str = str(img_date)[:10] if img_date else '—'

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 1 : KPI boxes (4 colonnes)
        # ─────────────────────────────────────────────────────────────────────
        kpis = [
            ("Surface toiture",   f"{bldg.get('roof_total_m2', '—')} m²"   if bldg.get('roof_total_m2')   else "—"),
            ("Surface utilisable",f"{bldg.get('roof_usable_m2', '—')} m²"  if bldg.get('roof_usable_m2')  else "—"),
            ("Max. puissance",    f"{bldg.get('max_kwp', '—')} kWc"         if bldg.get('max_kwp')         else
                                   f"{pot.get('max_kwp', '—')} kWc"),
            ("Ensoleillement max",f"{bldg.get('sunshine_h_yr') or pot.get('max_sunshine_hours') or '—'} h/an"),
        ]
        box_w = (self.width - 3 * cm) / len(kpis)
        for i, (lbl, val) in enumerate(kpis):
            bx = 1.5 * cm + i * box_w
            c.setFillColor(self.COLOR_PRIMARY if i % 2 == 0 else self.COLOR_SECONDARY)
            c.roundRect(bx + 0.1 * cm, y - 1.3 * cm, box_w - 0.2 * cm, 1.3 * cm, 4, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont('Helvetica-Bold', 8)
            c.drawCentredString(bx + box_w / 2, y - 0.45 * cm, lbl)
            c.setFont('Helvetica-Bold', 11)
            c.drawCentredString(bx + box_w / 2, y - 1.05 * cm, str(val))
        y -= 1.6 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 2 : Bâtiment + DSM (côte à côte)
        # ─────────────────────────────────────────────────────────────────────
        col_w2 = (self.width - 3 * cm) / 2 - 0.2 * cm
        info_h = 3.0 * cm

        # Bloc Bâtiment
        c.setFillColor(self.COLOR_HEADER_BG)
        c.rect(1.5 * cm, y - info_h, col_w2, info_h, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(1.7 * cm, y - 0.3 * cm, '🏗 Bâtiment (Google Solar)')
        ky = y - 0.75 * cm
        for lbl, val in [
            ('Longueur :',   f"{bldg.get('length_m', '—')} m"),
            ('Largeur :',    f"{bldg.get('width_m',  '—')} m"),
            ('Empreinte :',  f"{int(bldg['footprint_bbox_m2'])} m²" if bldg.get('footprint_bbox_m2') else '—'),
            ('Panneaux max :', f"{bldg.get('max_panels') or pot.get('max_panel_count') or '—'} × {bldg.get('panel_wc', 400)} Wc"),
        ]:
            c.setFont('Helvetica-Bold', 7.5); c.setFillColor(colors.HexColor('#555555'))
            c.drawString(1.7 * cm, ky, lbl)
            c.setFont('Helvetica', 7.5); c.setFillColor(self.COLOR_DARK)
            c.drawString(4.8 * cm, ky, str(val))
            ky -= 0.52 * cm

        # Bloc DSM (hauteurs toiture)
        hta_x = 1.5 * cm + col_w2 + 0.4 * cm
        c.setFillColor(self.COLOR_HEADER_BG)
        c.rect(hta_x, y - info_h, col_w2, info_h, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(hta_x + 0.2 * cm, y - 0.3 * cm, '📐 Hauteurs de toiture (DSM)')
        ky2 = y - 0.75 * cm
        for lbl, val in [
            ('Égout :',    f"{dsm.get('height_egout_m', '—')} m"),
            ('Moy. :',     f"{dsm.get('height_mean_m',  '—')} m"),
            ('Faîtage :',  f"{dsm.get('height_faitage_m', '—')} m"),
            ('Altitude :', f"{dsm.get('altitude_mean_m',  '—')} m IGN"),
        ]:
            if not dsm:
                break
            c.setFont('Helvetica-Bold', 7.5); c.setFillColor(colors.HexColor('#555555'))
            c.drawString(hta_x + 0.2 * cm, ky2, lbl)
            c.setFont('Helvetica', 7.5); c.setFillColor(self.COLOR_DARK)
            c.drawString(hta_x + 3.0 * cm, ky2, str(val))
            ky2 -= 0.52 * cm
        if not dsm:
            c.setFont('Helvetica-Oblique', 7.5); c.setFillColor(colors.HexColor('#777777'))
            c.drawString(hta_x + 0.2 * cm, y - 0.9 * cm, 'DSM non disponible')
        y -= info_h + 0.4 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 3 : Échelle irradiance Google Solar
        # ─────────────────────────────────────────────────────────────────────
        if flux_min is not None or flux_max is not None:
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont('Helvetica-Bold', 8)
            c.drawString(1.5 * cm, y, f'Irradiance annuelle (kWh/m²/an)   — Imagerie Google Solar {img_date_str}')
            y -= 0.5 * cm
            self._draw_irradiance_scale(c, 1.5 * cm, y - 0.55 * cm,
                                        self.width - 3 * cm, 0.55 * cm,
                                        flux_min, flux_max, flux_mean)
            y -= 1.2 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 4 : Tableau des pans de toiture
        # ─────────────────────────────────────────────────────────────────────
        if segs:
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont('Helvetica-Bold', 9)
            c.drawString(1.5 * cm, y, f'{len(segs)} PANS DE TOITURE — orientation, inclinaison, irradiance')
            y -= 0.5 * cm

            # Déterminer irr global min/max pour colorisation
            all_irr = [s.get('irr_max_kwh') or s.get('irr_med_kwh') for s in segs if s.get('irr_max_kwh') or s.get('irr_med_kwh')]
            g_irr_min = min(all_irr) if all_irr else 0
            g_irr_max = max(all_irr) if all_irr else 1

            # En-têtes colonnes
            headers = ['#', 'Orient.', 'Inclin.', 'Haut.', 'Dimensions', 'Surface', 'kWh/m²/an']
            col_xs  = [1.5*cm, 2.4*cm, 4.3*cm, 6.0*cm, 7.8*cm, 11.5*cm, 14.2*cm]
            col_ws  = [0.8*cm, 1.8*cm, 1.6*cm, 1.7*cm, 3.6*cm, 2.6*cm, None]

            c.setFillColor(self.COLOR_PRIMARY)
            c.rect(1.5 * cm, y - 0.15 * cm, self.width - 3 * cm, 0.55 * cm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont('Helvetica-Bold', 7.5)
            for xi, h in zip(col_xs, headers):
                c.drawString(xi + 0.1 * cm, y, h)
            y -= 0.65 * cm

            for si, seg in enumerate(segs[:15]):
                row_bg = self.COLOR_LIGHT_BG if si % 2 == 0 else colors.white
                c.setFillColor(row_bg)
                c.rect(1.5 * cm, y - 0.1 * cm, self.width - 3 * cm, 0.5 * cm, fill=1, stroke=0)

                ori_lbl  = seg.get('orientation', '—')
                az_deg   = seg.get('azimuth_deg')
                pit      = seg.get('pitch_deg')
                hgt      = seg.get('height_m')
                area     = seg.get('area_m2')
                seg_l    = seg.get('seg_l_m')
                seg_w    = seg.get('seg_w_m')
                irr_min  = seg.get('irr_min_kwh')
                irr_med  = seg.get('irr_med_kwh')
                irr_max  = seg.get('irr_max_kwh')

                dim_str  = f'{seg_l}×{seg_w}' if seg_l and seg_w else ('—')
                irr_disp = irr_max or irr_med

                # Couleur barre irradiance dans dernière colonne
                irr_col = self._irr_color(irr_disp, g_irr_min, g_irr_max)

                # Couleur orientation
                ori_color_map = {'S': colors.HexColor('#FF6B35'), 'SE': colors.HexColor('#FF9800'),
                                 'SW': colors.HexColor('#FF9800'), 'SO': colors.HexColor('#FF9800'),
                                 'E': colors.HexColor('#FDD835'), 'O': colors.HexColor('#FDD835'),
                                 'NE': colors.HexColor('#90CAF9'), 'NO': colors.HexColor('#90CAF9'),
                                 'N': colors.HexColor('#64B5F6')}
                ori_fill = ori_color_map.get(ori_lbl, colors.HexColor('#B0BEC5'))

                c.setFillColor(self.COLOR_DARK)
                c.setFont('Helvetica', 7.5)
                vals = [
                    str(seg.get('id', si + 1)),
                    '',  # orientation handled separately
                    f'{pit}°' if pit is not None else '—',
                    f'{hgt} m' if hgt is not None else '—',
                    dim_str,
                    f'{area} m²' if area is not None else '—',
                    '',  # irradiance handled separately
                ]
                for xi, v in zip(col_xs, vals):
                    if v:
                        c.drawString(xi + 0.1 * cm, y, v)

                # Orientation — badge coloré
                bw = 1.6 * cm
                c.setFillColor(ori_fill)
                c.roundRect(col_xs[1] + 0.05 * cm, y - 0.08 * cm, bw, 0.4 * cm, 2, fill=1, stroke=0)
                c.setFillColor(self.COLOR_DARK)
                c.setFont('Helvetica-Bold', 7)
                az_label = f'{ori_lbl} {az_deg}°' if az_deg is not None else ori_lbl
                c.drawCentredString(col_xs[1] + bw / 2 + 0.05 * cm, y, az_label[:10])

                # Irradiance — barre colorée + valeur
                irr_x = col_xs[6]
                irr_bar_w = self.width - 1.5 * cm - irr_x - 0.5 * cm
                if irr_disp:
                    c.setFillColor(irr_col)
                    c.roundRect(irr_x, y - 0.05 * cm, irr_bar_w, 0.38 * cm, 2, fill=1, stroke=0)
                    c.setFillColor(colors.white)
                    c.setFont('Helvetica-Bold', 7.5)
                    irr_txt = f'{irr_min}–{irr_max}' if (irr_min and irr_max) else str(irr_disp)
                    c.drawCentredString(irr_x + irr_bar_w / 2, y, irr_txt)
                else:
                    c.setFillColor(self.COLOR_DARK)
                    c.setFont('Helvetica', 7.5)
                    c.drawString(irr_x + 0.1 * cm, y, '—')

                y -= 0.55 * cm

            if len(segs) > 15:
                c.setFont('Helvetica-Oblique', 7)
                c.setFillColor(colors.grey)
                c.drawString(1.5 * cm, y, f'… et {len(segs) - 15} pans supplémentaires')
                y -= 0.4 * cm

        # Source note
        y -= 0.3 * cm
        c.setFont('Helvetica-Oblique', 6.5)
        c.setFillColor(colors.HexColor('#777777'))
        c.drawString(1.5 * cm, y, f'Source : Google Solar API ({source}) — Imagerie {img_date_str} — Données indicatives')

        self._draw_page_footer(c)

    # ── Plan de calpinage ─────────────────────────────────────────────────────

    def _draw_plan_calpinage(self, c):
        """Page Plan de calpinage : screenshot Leaflet + résumé des zones."""
        y = self._draw_page_header(c, "PLAN DE CALPINAGE")

        calpinage  = self.data_json.get('calpinage', {})
        screenshot = calpinage.get('screenshot_map', '')
        totaux     = calpinage.get('totaux', self.calpinage.get('totaux', {}))
        zones      = calpinage.get('zones', self.calpinage.get('zones', []))

        nb_modules    = totaux.get('nbModules', self.nb_modules)
        puissance_kwc = totaux.get('puissanceKwc', totaux.get('puissance_kwc', self.puissance_kwc))
        surface_tot   = totaux.get('surfaceTotale', totaux.get('surface_totale', 0))
        nb_zones      = len(zones) if zones else 0

        y -= 0.2 * cm

        # ─ Bandeaux résumé en haut ───────────────────────────────────────────
        boxes = [
            ("Puissance totale", f"{puissance_kwc:.1f} kWc"),
            ("Modules", f"{int(nb_modules)} modules"),
            ("Zones", f"{nb_zones} zone(s)"),
            ("Surface", f"{surface_tot:.0f} m²" if surface_tot else "—"),
        ]
        bw_box = (self.width - 3 * cm) / len(boxes)
        for i, (ttl, val) in enumerate(boxes):
            bx2 = 1.5 * cm + i * bw_box
            c.setFillColor(self.COLOR_PRIMARY if i % 2 == 0 else self.COLOR_SECONDARY)
            c.roundRect(bx2 + 0.1 * cm, y - 1.3 * cm, bw_box - 0.2 * cm, 1.3 * cm, 4, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(bx2 + bw_box / 2, y - 0.45 * cm, ttl)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(bx2 + bw_box / 2, y - 1.05 * cm, val)
        y -= 1.6 * cm

        # ─ Image du calpinage ────────────────────────────────────────────────
        img_calp = self._decode_base64_image(screenshot) if screenshot else None
        img_h = 13 * cm
        if img_calp:
            c.drawImage(img_calp, 1.5 * cm, y - img_h, width=self.width - 3 * cm,
                        height=img_h, preserveAspectRatio=True, anchor='c')
        else:
            c.setFillColor(self.COLOR_LIGHT_BG)
            c.rect(1.5 * cm, y - img_h, self.width - 3 * cm, img_h, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#AAAAAA'))
            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(self.width / 2, y - img_h / 2,
                                "Capture de calpinage non disponible")
            c.setFont("Helvetica-Oblique", 8)
            c.drawCentredString(self.width / 2, y - img_h / 2 - 0.6 * cm,
                                "Effectuez un calpinage depuis le CRM pour générer ce plan")
        y -= img_h + 0.4 * cm

        # ─ Tableau des zones ─────────────────────────────────────────────────
        if zones:
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.5 * cm, y, "DÉTAIL DES ZONES DE POSE")
            y -= 0.5 * cm
            # En-têtes
            cols  = [1.5 * cm, 4.5 * cm, 8.5 * cm, 12.5 * cm, 16.0 * cm]
            hdrs  = ["Zone", "Modules", "Puissance (kWc)", "Surface (m²)", "Orientation"]
            c.setFillColor(self.COLOR_PRIMARY)
            c.rect(1.5 * cm, y - 0.15 * cm, self.width - 3 * cm, 0.55 * cm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8)
            for xi, h in zip(cols, hdrs):
                c.drawString(xi + 0.15 * cm, y, h)
            y -= 0.65 * cm
            for zi, zone in enumerate(zones[:8]):
                c.setFillColor(self.COLOR_LIGHT_BG if zi % 2 == 0 else colors.white)
                c.rect(1.5 * cm, y - 0.1 * cm, self.width - 3 * cm, 0.5 * cm, fill=1, stroke=0)
                z_nb   = zone.get('nbModules', zone.get('nb_modules', '—'))
                z_kwc  = zone.get('puissanceKwc', zone.get('puissance_kwc', 0))
                z_surf = zone.get('surface', zone.get('surface_m2', 0))
                z_ori  = zone.get('orientation', zone.get('azimut', '—'))
                z_name = zone.get('nom', zone.get('name', f"Zone {zi + 1}"))
                c.setFillColor(self.COLOR_DARK)
                c.setFont("Helvetica", 8)
                vals = [z_name, str(z_nb), f"{z_kwc:.2f}" if z_kwc else "—",
                        f"{z_surf:.0f}" if z_surf else "—", str(z_ori)]
                for xi, v in zip(cols, vals):
                    c.drawString(xi + 0.15 * cm, y, str(v))
                y -= 0.55 * cm

        self._draw_page_footer(c)

    # ── Rapport contraintes site ──────────────────────────────────────────────

    def _draw_rapport_contraintes(self, c):
        """Page(s) Rapport point : PLU, ZAER, PPRI, GéoRisques, raccordement électrique."""
        rapport = self.data_json.get('rapport', {})
        if not rapport:
            return

        y = self._draw_page_header(c, "ANALYSE DES CONTRAINTES DU SITE")
        y -= 0.2 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 1 : Urbanisme (PLU + ZAER)
        # ─────────────────────────────────────────────────────────────────────
        y = self._draw_section_title(c, y, "Réglementation Urbanisme", number="A")

        plu_list = rapport.get('plu_info', [])
        zaer_list = rapport.get('zaer', [])

        col1_x, col2_x = 1.5 * cm, 10.5 * cm
        col_w = 8.5 * cm

        # PLU
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(col1_x, y, "Plan Local d'Urbanisme (PLU)")
        y -= 0.45 * cm
        if plu_list:
            for feat in plu_list[:3]:
                props = feat.get('properties', feat) if isinstance(feat, dict) else {}
                typezone  = props.get('typezone', props.get('zone', ''))
                libelle   = props.get('libelle', props.get('libelong', props.get('lib', '')))
                c.setFillColor(self.COLOR_ACCENT)
                c.roundRect(col1_x, y - 0.6 * cm, 1.8 * cm, 0.7 * cm, 3, fill=1, stroke=0)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 9)
                c.drawCentredString(col1_x + 0.9 * cm, y - 0.2 * cm, typezone or "—")
                c.setFillColor(self.COLOR_DARK)
                c.setFont("Helvetica", 8)
                c.drawString(col1_x + 2 * cm, y - 0.2 * cm, (libelle or "Zone inconnue")[:55])
                y -= 0.75 * cm
        else:
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.HexColor('#777777'))
            c.drawString(col1_x, y, "Données PLU non disponibles pour cette commune.")
            y -= 0.55 * cm

        # ZAER (Zones d'Accélération EnR)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(col1_x, y, "Zones d'Accélération des EnR (ZAER)")
        y -= 0.45 * cm
        if zaer_list:
            for feat in zaer_list[:2]:
                props = feat.get('properties', feat) if isinstance(feat, dict) else {}
                lib = props.get('libelle', props.get('lib', props.get('nom', 'Zone EnR')))
                c.setFillColor(self.COLOR_SECONDARY)
                c.roundRect(col1_x, y - 0.55 * cm, 1.5 * cm, 0.65 * cm, 3, fill=1, stroke=0)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 8)
                c.drawCentredString(col1_x + 0.75 * cm, y - 0.18 * cm, "ZAER")
                c.setFillColor(self.COLOR_DARK)
                c.setFont("Helvetica", 8)
                c.drawString(col1_x + 1.7 * cm, y - 0.18 * cm, str(lib)[:60])
                y -= 0.65 * cm
        else:
            c.setFillColor(colors.HexColor('#777777'))
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(col1_x, y, "Aucune zone d'accélération EnR identifiée.")
            y -= 0.55 * cm

        y -= 0.3 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 2 : Risques naturels / GéoRisques
        # ─────────────────────────────────────────────────────────────────────
        y = self._draw_section_title(c, y, "Risques Naturels & GéoRisques", number="B")

        georisques = rapport.get('georisques_risks', {})
        if not isinstance(georisques, dict):
            georisques = {}

        # Sismicité
        sismo = georisques.get('sismicite', {}) or {}
        sismo_zone = str(sismo.get('zone', sismo.get('niveau', '—')))
        sismo_desc = sismo.get('description', '')

        # Argile
        argile = georisques.get('argile', {}) or {}
        argile_risque = str(argile.get('risque', argile.get('classe', '—')))

        # Radon
        radon = georisques.get('radon', {}) or {}
        radon_cls = str(radon.get('classe', radon.get('potentiel', '—')))

        # PPRI
        ppri = rapport.get('ppri', {})
        ppri_present = bool(ppri and (isinstance(ppri, dict) and ppri.get('features')))

        # Catnat
        catnat = georisques.get('catnat', [])
        if not isinstance(catnat, list):
            catnat = []

        # Couleurs risque
        def risk_color(val):
            v = str(val).lower()
            if any(x in v for x in ['faible', '1', 'classe 1', 'zone 1', 'très faible', 'nul']):
                return colors.HexColor('#4CAF50')   # vert
            if any(x in v for x in ['moyen', '3', 'zone 3', 'modéré', 'moyen']):
                return colors.HexColor('#FF9800')   # orange
            if any(x in v for x in ['fort', 'élevé', '4', '5', 'zone 4', 'zone 5', 'très fort', 'fort']):
                return colors.HexColor('#F44336')   # rouge
            return colors.HexColor('#78909C')        # gris

        bx_r = 1.5 * cm
        badge_gap = 4.2 * cm
        self._draw_risk_badge(c, bx_r,              y, "Sismicité", sismo_zone,  risk_color(sismo_zone))
        self._draw_risk_badge(c, bx_r + badge_gap,  y, "Argiles",  argile_risque, risk_color(argile_risque))
        self._draw_risk_badge(c, bx_r + 2*badge_gap,y, "Radon",    radon_cls,    risk_color(radon_cls))
        ppri_label = "Présent" if ppri_present else "Non identifié"
        ppri_col   = colors.HexColor('#F44336') if ppri_present else colors.HexColor('#4CAF50')
        self._draw_risk_badge(c, bx_r + 3*badge_gap,y, "PPRI",     ppri_label,   ppri_col)
        y -= 1.2 * cm

        if sismo_desc:
            c.setFont("Helvetica-Oblique", 7.5)
            c.setFillColor(colors.HexColor('#555555'))
            c.drawString(1.5 * cm, y, f"Sismicité : {sismo_desc[:100]}")
            y -= 0.45 * cm

        # CatNat
        if catnat:
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(1.5 * cm, y, f"Arrêtés de catastrophe naturelle ({len(catnat)} événement(s) recensé(s)) :")
            y -= 0.45 * cm
            for ev in catnat[:4]:
                lib = ev.get('libRisqueJo', ev.get('type_risque_long', ev.get('libelle', '—')))
                dd  = ev.get('datDebutEvt', ev.get('date_debut', ''))[:10]
                df  = ev.get('datFinEvt',   ev.get('date_fin', ''))[:10]
                c.setFont("Helvetica", 7.5)
                c.setFillColor(self.COLOR_DARK)
                c.drawString(1.7 * cm, y, f"• {lib} — du {dd} au {df}")
                y -= 0.4 * cm
            if len(catnat) > 4:
                c.setFont("Helvetica-Oblique", 7.5)
                c.setFillColor(colors.HexColor('#777777'))
                c.drawString(1.7 * cm, y, f"  … et {len(catnat) - 4} autre(s) événement(s)")
                y -= 0.4 * cm

        y -= 0.3 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 3 : Raccordement électrique
        # ─────────────────────────────────────────────────────────────────────
        y = self._draw_section_title(c, y, "Raccordement Électrique", number="C")

        poste_bt  = rapport.get('poste_bt', {})
        poste_hta = rapport.get('poste_hta', {})
        if not isinstance(poste_bt,  dict): poste_bt  = {}
        if not isinstance(poste_hta, dict): poste_hta = {}

        # BT
        c.setFillColor(self.COLOR_HEADER_BG)
        hw = (self.width - 3 * cm) / 2 - 0.2 * cm
        c.rect(1.5 * cm, y - 3.5 * cm, hw, 3.5 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.7 * cm, y - 0.3 * cm, "Poste Source BT (plus proche)")
        ky2 = y - 0.75 * cm
        for lbl, key in [("Nom :", 'nom'), ("Distance :", 'distance_m'), ("Puissance :", 'puissance'), ("État :", 'etat')]:
            val = poste_bt.get(key, '—')
            if key == 'distance_m' and val != '—':
                val = f"{int(float(val))} m"
            if key == 'puissance' and val != '—':
                val = f"{val} kVA"
            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor('#555555'))
            c.drawString(1.7 * cm, ky2, lbl)
            c.setFont("Helvetica", 7.5)
            c.setFillColor(self.COLOR_DARK)
            c.drawString(4.5 * cm, ky2, str(val)[:30])
            ky2 -= 0.52 * cm
        if not poste_bt:
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.HexColor('#777777'))
            c.drawString(1.7 * cm, y - 0.9 * cm, "Données non disponibles")

        # HTA
        hta_x = 1.5 * cm + hw + 0.4 * cm
        c.setFillColor(self.COLOR_HEADER_BG)
        c.rect(hta_x, y - 3.5 * cm, hw, 3.5 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(hta_x + 0.2 * cm, y - 0.3 * cm, "Poste Source HTA (plus proche)")
        ky3 = y - 0.75 * cm
        for lbl, key in [("Nom :", 'nom'), ("Distance :", 'distance_m'), ("Puissance :", 'puissance'), ("État :", 'etat')]:
            val = poste_hta.get(key, '—')
            if key == 'distance_m' and val != '—':
                try:
                    val = f"{int(float(val))} m"
                except:
                    pass
            if key == 'puissance' and val != '—':
                val = f"{val} kVA"
            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(colors.HexColor('#555555'))
            c.drawString(hta_x + 0.2 * cm, ky3, lbl)
            c.setFont("Helvetica", 7.5)
            c.setFillColor(self.COLOR_DARK)
            c.drawString(hta_x + 2.8 * cm, ky3, str(val)[:30])
            ky3 -= 0.52 * cm
        if not poste_hta:
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.HexColor('#777777'))
            c.drawString(hta_x + 0.2 * cm, y - 0.9 * cm, "Données non disponibles")

        y -= 3.8 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 4 : Installations classées ICPE
        # ─────────────────────────────────────────────────────────────────────
        installations = georisques.get('installations', [])
        if not isinstance(installations, list):
            installations = []

        if installations:
            y = self._draw_section_title(c, y, "Installations Classées (ICPE) à proximité", number="D")
            for inst in installations[:4]:
                nom_inst = inst.get('nomEts', inst.get('nom', inst.get('name', '—')))
                dist_inst = inst.get('distance', inst.get('dist', '—'))
                act_inst  = inst.get('activitePrincipale', inst.get('activite', ''))
                c.setFont("Helvetica", 7.5)
                c.setFillColor(self.COLOR_DARK)
                label_dist = f"— {int(float(dist_inst))} m" if dist_inst and dist_inst != '—' else ''
                c.drawString(1.7 * cm, y, f"• {nom_inst}{label_dist}" + (f" ({act_inst[:40]})" if act_inst else ""))
                y -= 0.4 * cm
            if len(installations) > 4:
                c.setFont("Helvetica-Oblique", 7.5)
                c.setFillColor(colors.HexColor('#777777'))
                c.drawString(1.7 * cm, y, f"  … et {len(installations) - 4} autre(s) installation(s)")
                y -= 0.4 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 5 : Note de synthèse
        # ─────────────────────────────────────────────────────────────────────
        y -= 0.2 * cm
        c.setFillColor(self.COLOR_HEADER_BG)
        note_h = 2.5 * cm
        c.rect(1.5 * cm, y - note_h, self.width - 3 * cm, note_h, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.8 * cm, y - 0.3 * cm, "NOTE DE SYNTHÈSE RÉGLEMENTAIRE")
        c.setFont("Helvetica", 8)
        c.setFillColor(self.COLOR_DARK)
        notes = []
        if plu_list:
            zones_str = ", ".join([
                (f.get('properties', f) if isinstance(f, dict) else {}).get('typezone', '?')
                for f in plu_list[:3]
            ])
            notes.append(f"Zonage PLU identifié : {zones_str}.")
        if ppri_present:
            notes.append("Attention : le site est concerné par un PPRI — consulter la Mairie / DDT.")
        if sismo_zone not in ['—', '1', 'Zone 1']:
            notes.append(f"Zone sismique {sismo_zone} — respecter la réglementation para-sismique.")
        if not notes:
            notes.append("Aucune contrainte majeure identifiée. Vérification en Mairie recommandée.")
        ny = y - 0.75 * cm
        for note in notes:
            c.drawString(1.8 * cm, ny, f"→ {note}"[:90])
            ny -= 0.5 * cm

        c.drawString(1.8 * cm, ny,
                     "Source : API GéoRisques, GPU Urbanisme, PVGIS — données indicatives, vérification officielle requise.")

        self._draw_page_footer(c)

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
