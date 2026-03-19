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
- Devis détaillé UTE C 15-712-1 avec taxes IFER
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

    # ── Charte graphique moderne ─────────────────────────────────────────────
    COLOR_PRIMARY    = colors.HexColor('#0f1b2d')   # Bleu marine profond (brand)
    COLOR_SECONDARY  = colors.HexColor('#10b981')   # Vert émeraude (app accent)
    COLOR_ACCENT     = colors.HexColor('#f59e0b')   # Ambre/Orange (app accent)
    COLOR_BLUE       = colors.HexColor('#3b82f6')   # Bleu vif (app)
    COLOR_DARK       = colors.HexColor('#1e293b')   # Texte principal
    COLOR_LIGHT_BG   = colors.HexColor('#F8FAFC')   # Fond page très clair
    COLOR_HEADER_BG  = colors.HexColor('#ECFDF5')   # Fond card vert
    COLOR_CARD_BG    = colors.HexColor('#EFF6FF')   # Fond card bleu
    COLOR_WHITE      = colors.white
    COLOR_GREY       = colors.HexColor('#94A3B8')   # Gris neutre
    COLOR_SEPARATOR  = colors.HexColor('#E2E8F0')   # Ligne de séparation

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
        self.type_projet = parametres.get('type_projet', 'autoconsommation')
        self.taux_autoconso = self._sf(parametres.get('taux_autoconso'), 70.0) / 100.0
        # ── Tarif revente — arrêté S21 (6 oct. 2021, mod. 26 mars 2025) ─────────
        # Source : CRE / photovoltaique.info — Q1 2026 (01/01 au 31/03/2026)
        # Vente du surplus (autoconsommation individuelle) :
        #   4,00 c€/kWh  pour P+Q ≤  9 kWc
        #   5,36 c€/kWh  pour P+Q de 9 à 100 kWc
        # Vente en totalité (injection totale) — estimation Q1-2026 :
        #   12,61 c€/kWh (≤3 kWc)  | 11,89 c€/kWh (3-9 kWc)
        #    9,47 c€/kWh (9-36 kWc) |  8,36 c€/kWh (36-100 kWc)
        # ⚠  Mettre à jour via parametres['tarif_revente_kwh'] chaque trimestre
        _p = self.puissance_kwc
        if self.type_projet == 'autoconsommation':
            _tr_default = 0.0400 if _p <= 9 else 0.0536   # surplus OA S21 Q1-2026
        elif self.type_projet == 'sans_injection':
            _tr_default = 0.0                              # aucune injection réseau
        elif self.type_projet == 'autoconsommation_collective':
            _tr_default = 0.0400 if _p <= 9 else 0.0536   # surplus OAC — mêmes tarifs
        else:  # vente totale (injection en totalité)
            if _p <= 3:    _tr_default = 0.1261
            elif _p <= 9:  _tr_default = 0.1189
            elif _p <= 36: _tr_default = 0.0947
            else:          _tr_default = 0.0836            # 36-100 kWc
        self.tarif_revente = self._sf(parametres.get('tarif_revente_kwh'), _tr_default)

        # Calculs techniques
        totaux   = calpinage.get('totaux', {})
        _module  = calpinage.get('module', {})
        _puiss_m = self._sf(_module.get('puissance'), 0)  # puissance module en W
        _puiss_t = self._sf(totaux.get('puissanceTotale'), 0)  # puissance totale kWc
        if _puiss_m > 0 and _puiss_t > 0:
            self.nb_modules      = int(round(_puiss_t * 1000 / _puiss_m))
            self.puissance_module = int(_puiss_m)
        else:
            self.nb_modules      = totaux.get('nbModules', int(self.puissance_kwc / 0.55))
            self.puissance_module = totaux.get('puissanceModule', 550)

        # ── Résultats simulation autoconsommation (si disponibles) ────────────────
        # Priorité : données issues de la simulation PVGIS 8760h > estimations
        self.autoconso_data = parametres.get('autoconso_data') or {}
        _kpis = self.autoconso_data.get('kpis', {})
        _eco  = self.autoconso_data.get('economics', {})

        # Production : réelle PVGIS si dispos, sinon productibleTotal du calpinage, sinon 1100 kWh/kWc moyen France
        # Clés issues de compute_autoconsommation() : production_annuelle_kwh, autoconso_kwh, surplus_kwh, taux_autoconsommation (en %)
        if _kpis.get('production_annuelle_kwh'):
            self.production_annuelle   = self._sf(_kpis['production_annuelle_kwh'])
            self.energie_autoconsommee = self._sf(_kpis.get('autoconso_kwh', 0))
            self.energie_revendue      = self._sf(_kpis.get('surplus_kwh', 0))
            # taux_autoconsommation est en % (75.0), self.taux_autoconso est en fraction (0.75)
            self.taux_autoconso        = self._sf(_kpis.get('taux_autoconsommation', self.taux_autoconso * 100)) / 100.0
            self.consommation          = self._sf(_kpis.get('consommation_annuelle_kwh', self.consommation))
        else:
            # Utiliser productibleTotal du calpinage (somme PVGIS par zone, en MWh) si disponible
            _prod_calpinage_mwh = self._sf(totaux.get('productibleTotal'), 0)
            if _prod_calpinage_mwh > 0:
                self.production_annuelle = _prod_calpinage_mwh * 1000  # MWh → kWh
            else:
                self.production_annuelle = self.puissance_kwc * 1100  # estimation France
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
            elif self.type_projet == 'sans_injection':
                # Autoconsommation totale : 0 injection, économie = prod autoconsommée × tarif achat
                self.energie_autoconsommee = (min(self.production_annuelle, self.consommation)
                                              if self.consommation > 0 else self.production_annuelle)
                self.energie_revendue      = 0.0
                self.economie_autoconso    = self.energie_autoconsommee * self.tarif_achat
                self.revenu_revente        = 0.0
                self.gain_annuel           = self.economie_autoconso
            else:  # vente totale / injection totale
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
                    parsed = json.loads(prospect['data_json'])
                    # S'assurer que c'est bien un dict (pas une liste — ancien format)
                    self.data_json = parsed if isinstance(parsed, dict) else {}
                except:
                    self.data_json = {}
            elif isinstance(prospect['data_json'], dict):
                self.data_json = prospect['data_json']
            # Si c'est déjà une liste, on ignore (format non supporté)

        # Garantie : self.calpinage (source de vérité directe) est toujours
        # accessible via self.data_json['calpinage'], même si prospect.data_json
        # était absent, malformé, ou ne contenait pas encore le calpinage.
        # Cela assure que tous les appels self.data_json.get('calpinage', {})
        # dans les méthodes de dessin trouvent bien les screenshots.
        if self.calpinage:
            self.data_json['calpinage'] = self.calpinage

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
        _lat = (self.data_json.get('rapport', {}).get('lat')
                or self.prospect.get('lat') or self.prospect.get('latitude'))
        _lon = (self.data_json.get('rapport', {}).get('lon')
                or self.prospect.get('lon') or self.prospect.get('longitude'))
        # helper : premier screenshot non-vide entre data_json et self.calpinage
        def _ss(key):
            return (self.data_json.get('calpinage', {}).get(key, '')
                    or self.calpinage.get(key, ''))

        _screenshot       = _ss('screenshot_map')
        # Plan de masse : UNIQUEMENT si screenshot dédié disponible (pas de repli sur screenshot_map)
        _screenshot_masse = _ss('screenshot_plan_masse')
        _s3d  = _ss('screenshot_3d')
        _sirr = _ss('screenshot_irradiation')

        if _lat and _lon:
            c.showPage()
            self.page_number += 1
            self._draw_plan_situation(c)

        # Page 4c : Plan de masse (uniquement si screenshot plan masse dédié disponible)
        if _screenshot_masse:
            c.showPage()
            self.page_number += 1
            self._draw_plan_masse(c)

        # Page 4c2 : Visuels 3D + irradiation (si disponibles)
        if _s3d or _sirr:
            c.showPage()
            self.page_number += 1
            self._draw_visuels_calpinage(c)

        # Page 4d : Plan de calpinage (si screenshot disponible)
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
        """En-tête de page — design moderne marine/vert émeraude"""
        hdr_h = 1.5 * cm

        # Fond marine pleine largeur
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(0, self.height - hdr_h, self.width, hdr_h, fill=1, stroke=0)

        # Barre accent verte à l'extrémité gauche
        c.setFillColor(self.COLOR_SECONDARY)
        c.rect(0, self.height - hdr_h, 0.45 * cm, hdr_h, fill=1, stroke=0)

        # Titre de section (blanc, gras)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(0.85 * cm, self.height - 0.95 * cm, title)

        # Référence entreprise (gris clair, droite)
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor('#94A3B8'))
        c.drawRightString(self.width - 0.6 * cm, self.height - 0.6 * cm,
                          "AGRIWEB  ·  Solutions Photovoltaïques")
        c.drawRightString(self.width - 0.6 * cm, self.height - 1.15 * cm,
                          f"Réf: PROP-{self.prospect.get('id', 'XXX')}")

        # Ligne fine séparatrice vert émeraude
        sep_y = self.height - hdr_h - 0.05 * cm
        c.setStrokeColor(self.COLOR_SECONDARY)
        c.setLineWidth(1.5)
        c.line(0, sep_y, self.width, sep_y)
        c.setLineWidth(1)

        # Pied de page
        self._draw_page_footer(c)

        return sep_y - 0.6 * cm

    def _draw_page_footer(self, c):
        """Pied de page moderne avec fond et badge page"""
        footer_h = 0.9 * cm
        # Fond gris très clair
        c.setFillColor(self.COLOR_LIGHT_BG)
        c.rect(0, 0, self.width, footer_h, fill=1, stroke=0)
        # Ligne accent verte en haut du footer
        c.setStrokeColor(self.COLOR_SECONDARY)
        c.setLineWidth(1)
        c.line(0, footer_h, self.width, footer_h)
        # Texte gauche — forcer stroke=none pour éviter le rendu doublé PPrrooppoossiittiioonn
        c.setLineWidth(0)
        commune = self.prospect.get('commune', '')
        c.setFont("Helvetica", 6.5)
        c.setFillColor(self.COLOR_GREY)
        c.drawString(0.8 * cm, 0.28 * cm,
                     f"Proposition Commerciale  ·  {commune}  ·  {self.date_now.strftime('%d/%m/%Y')}  ·  Confidentiel")
        # Badge numéro de page (cercle marine)
        pg_x = self.width - 0.9 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.circle(pg_x, 0.44 * cm, 0.32 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(pg_x, 0.37 * cm, str(self.page_number + 1))

    def _draw_section_title(self, c, y, title, number=None):
        """Titre de sous-section — barre latérale accent + fond léger"""
        h = 0.78 * cm
        # Fond très léger
        c.setFillColor(self.COLOR_LIGHT_BG)
        c.rect(1.5 * cm, y - h + 0.18 * cm, self.width - 3 * cm, h, fill=1, stroke=0)
        # Barre gauche vert émeraude
        c.setFillColor(self.COLOR_SECONDARY)
        c.rect(1.5 * cm, y - h + 0.18 * cm, 0.28 * cm, h, fill=1, stroke=0)
        if number:
            # Badge circulaire marine avec numéro
            badge_cx = 2.5 * cm
            badge_cy = y - h / 2 + 0.18 * cm
            c.setFillColor(self.COLOR_PRIMARY)
            c.circle(badge_cx, badge_cy, 0.29 * cm, fill=1, stroke=0)
            c.setFillColor(self.COLOR_WHITE)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(badge_cx, badge_cy - 0.08 * cm, str(number))
            text_x = 3.1 * cm
        else:
            text_x = 2.1 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(text_x, y - 0.02 * cm, title)
        c.setFillColor(self.COLOR_DARK)
        return y - h - 0.45 * cm

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
        """Carte KPI moderne — bande marine + valeur centrale"""
        radius = 4
        # Ombre simulée (rectangle décalé, gris)
        c.setFillColor(self.COLOR_SEPARATOR)
        c.roundRect(x + 1.5, y - 1.5, w, h, radius, fill=1, stroke=0)
        # Fond blanc pré-carte
        c.setFillColor(self.COLOR_WHITE)
        c.roundRect(x, y, w, h, radius, fill=1, stroke=0)
        # Bordure légère
        c.setStrokeColor(self.COLOR_SEPARATOR)
        c.setLineWidth(0.5)
        c.roundRect(x, y, w, h, radius, fill=0, stroke=1)
        c.setLineWidth(1)
        # Bande supérieure marine (header de la carte)
        band_h = 0.5 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.roundRect(x, y + h - band_h, w, band_h + radius, radius, fill=1, stroke=0)
        c.rect(x, y + h - band_h, w, band_h * 0.6, fill=1, stroke=0)  # partie basse droite
        # Titre dans la bande
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x + w / 2, y + h - 0.35 * cm, title)
        # Valeur principale
        c.setFillColor(self.COLOR_PRIMARY)
        val_str = str(value)
        fs = 13 if len(val_str) <= 12 else 10
        c.setFont("Helvetica-Bold", fs)
        c.drawCentredString(x + w / 2, y + h - 1.15 * cm, val_str)
        # Sous-titre
        if subtitle:
            c.setFillColor(self.COLOR_GREY)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x + w / 2, y + 0.22 * cm, subtitle)
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

    def _get_raccordement_profile(self):
        """
        Retourne le profil complet de raccordement réseau selon la puissance
        installée et le type de projet (CARD S06 Enedis / CARD S01 RTE).

        Seuils CARD S06 Enedis (puissance AC nominale onduleur, ≈ kWc) :
          S06-a :        P ≤   3 kVA  → injection au PDL monophasé
          S06-b :  3 < P ≤  36 kVA   → injection au TGBT triphasé
          S06-c : 36 < P ≤ 250 kVA   → coffret de coupure BT réseau
          S06-d :      P >  250 kVA   → poste de livraison HTA 20 kV
          HTB   :      P > 12 000 kVA → raccordement direct RTE (CARD S01)

        Types de projets pris en charge :
          'autoconsommation'            → CACSI + revente surplus OA
          'sans_injection'              → autoconsommation totale, 0 injection
          'autoconsommation_collective' → OAC, Art. L315-2, TURPE réduit
          tout autre                    → vente totale, obligation d'achat
        """
        p = self.puissance_kwc
        t = self.type_projet

        # ── Autoconsommation Collective ───────────────────────────────────────
        if t == 'autoconsommation_collective':
            return {
                'type':         'Autoconsommation Collective (OAC)',
                'tension':      'BT 400 V — périmètre d\'un même poste HTA/BT',
                'point_inj':    'PDL de chaque participant via réseau BT commun',
                'carte':        'CARD S06 Enedis + UTE C 15-712-3',
                'contrat':      'Convention OAC — Art. L315-2 Code énergie',
                'compteur':     'Linky bidirectionnel par participant (Enedis)',
                'pmo':          'PMO (Personne Morale Organisatrice) obligatoire',
                'turpe_reduit': True,
                'oa_requis':    False,
            }

        # ── Autoconsommation totale sans injection ────────────────────────────
        if t == 'sans_injection':
            return {
                'type':         'Autoconsommation totale — SANS injection réseau',
                'tension':      'Raccordement interne uniquement (côté production)',
                'point_inj':    'Aucun — limiteur de production ou découplage auto.',
                'carte':        'UTE C 15-712-1 (pas de CARD Enedis côté production)',
                'contrat':      'Aucun contrat OA — CONSUEL + déclaration CCAS',
                'compteur':     'Compteur de production interne (monitoring FusionSolar)',
                'pmo':          '',
                'turpe_reduit': False,
                'oa_requis':    False,
            }

        # ── Vente totale OU autoconsommation individuelle + surplus ───────────
        is_ac = (t == 'autoconsommation')

        # Seuil éligibilité arrêté S21 (6 oct. 2021, mod. 26 mars 2025) :
        #   P+Q ≤ 100 kWc → obligation d'achat EDF OA  (depuis 22/09/2025)
        #   P+Q > 100 kWc → appel d'offres CRE obligatoire
        # Tarifs OA surplus Q1-2026 : 4,00 c€/kWh (≤9 kWc) | 5,36 c€/kWh (9-100 kWc)
        in_s21    = (p <= 100)
        tarif_sup = '4,00 c\u20ac/kWh' if p <= 9 else '5,36 c\u20ac/kWh'

        if p <= 3:
            return {
                'type':         'BT individuel \u2014 CARD S06-a Enedis',
                'tension':      'BT 230 V monophas\u00e9',
                'point_inj':    'PDL client \u2014 compteur Linky remis en bidirectionnel',
                'carte':        'CARD S06-a Enedis',
                'contrat':      ('CACSI + prime IAP \u2014 surplus OA ' + tarif_sup + ' (S21)'
                                 if is_ac else 'OA monophas\u00e9 S21 \u2014 Art. L314-1 Code \u00e9nergie'),
                'compteur':     'Linky bidirectionnel existant (remplacement gratuit Enedis)',
                'pmo':          '',
                'turpe_reduit': False,
                'oa_requis':    True,
            }
        elif p <= 36:
            return {
                'type':         'BT au TGBT \u2014 CARD S06-b Enedis',
                'tension':      'BT 400 V triphas\u00e9',
                'point_inj':    'TGBT (Tableau G\u00e9n\u00e9ral BT) \u2014 en aval du compteur Enedis',
                'carte':        'CARD S06-b Enedis',
                'contrat':      ('CACSI + prime IAP \u2014 surplus OA ' + tarif_sup + ' (S21, P+Q \u2264 100 kWc)'
                                 if is_ac else 'OA triphas\u00e9 S21 \u2014 Art. L314-1 (P+Q \u2264 100 kWc)'),
                'compteur':     'Linky bidirectionnel ou 2\u1d49 compteur de production Enedis',
                'pmo':          '',
                'turpe_reduit': False,
                'oa_requis':    True,
            }
        elif p <= 250:
            if is_ac:
                _ctr = ('CACSI + prime IAP \u2014 surplus OA ' + tarif_sup + ' (S21, P+Q \u2264 100 kWc)'
                        if in_s21 else 'Appel d\'offres CRE \u2014 P+Q > 100 kWc (hors S21)')
            else:
                _ctr = ('OA injection totale S21 \u2014 P+Q \u2264 100 kWc'
                        if in_s21 else 'Appel d\'offres CRE \u2014 P+Q > 100 kWc (hors S21)')
            return {
                'type':         'BT r\u00e9seau \u2014 CARD S06-c Enedis',
                'tension':      'BT 400 V triphas\u00e9',
                'point_inj':    'Coffret de coupure BT au poste HTA/BT le plus proche',
                'carte':        'CARD S06-c Enedis',
                'contrat':      _ctr,
                'compteur':     '2 compteurs Enedis : PDL production + PDL consommation',
                'pmo':          '',
                'turpe_reduit': False,
                'oa_requis':    True,
            }
        elif p <= 12000:
            return {
                'type':         'HTA 20 kV \u2014 CARD S06-d Enedis',
                'tension':      'HTA 20 kV',
                'point_inj':    'Poste de livraison HTA d\u00e9di\u00e9 (propri\u00e9t\u00e9 du producteur)',
                'carte':        'CARD S06-d Enedis',
                'contrat':      'Appel d\'offres CRE \u2014 TURPE producteur HTA',
                'compteur':     'Compteur de production HTA (m\u00e9trologie Enedis)',
                'pmo':          '',
                'turpe_reduit': False,
                'oa_requis':    True,
            }
        else:
            return {
                'type':         'HTB — CARD S01 RTE',
                'tension':      'HTB (> 50 kV)',
                'point_inj':    'Poste source HTB — raccordement direct réseau RTE',
                'carte':        'CARD S01 RTE',
                'contrat':      'Appel d\'offres CRE',
                'compteur':     'Métrologie HTB (RTE)',
                'pmo':          '',
                'turpe_reduit': False,
                'oa_requis':    True,
            }

    # =========================================================================
    # PAGES
    # =========================================================================

    def _draw_cover(self, c):
        """Page de couverture moderne \u2014 marine / vert \u00e9meraude / blanc"""
        w, h = self.width, self.height

        # \u2500\u2500 Fond pleine page marine \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # \u2500\u2500 Bande diagonale verte (accent d\u00e9coratif) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        p_diag = c.beginPath()
        p_diag.moveTo(0, h * 0.54)
        p_diag.lineTo(w * 0.62, h * 0.54)
        p_diag.lineTo(w * 0.48, h * 0.52)
        p_diag.lineTo(0, h * 0.52)
        p_diag.close()
        c.setFillColor(self.COLOR_SECONDARY)
        c.drawPath(p_diag, fill=1, stroke=0)

        # Mince lign verte traversante
        c.setStrokeColor(self.COLOR_SECONDARY)
        c.setLineWidth(1)
        c.line(0, h * 0.52, w, h * 0.52)

        # \u2500\u2500 Zone image 3D (partie haute) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        hero_top    = h * 0.52
        hero_bottom = h * 0.28
        hero_h      = hero_top - hero_bottom

        screenshot_3d = self.calpinage.get('screenshot_3d', '')
        if screenshot_3d:
            img_3d = self._decode_base64_image(screenshot_3d)
            if img_3d:
                c.drawImage(img_3d, 0, hero_bottom, width=w, height=hero_h,
                            preserveAspectRatio=False, mask='auto')
                # Overlay fonc\u00e9 pour lisibilit\u00e9
                c.setFillColor(colors.Color(0.06, 0.11, 0.18, alpha=0.55))
                c.rect(0, hero_bottom, w, hero_h, fill=1, stroke=0)
        else:
            # Motif g\u00e9om\u00e9trique de substitution (grille de points)
            c.setFillColor(colors.Color(0.16, 0.31, 0.56, alpha=0.25))
            c.rect(0, hero_bottom, w, hero_h, fill=1, stroke=0)
            c.setStrokeColor(colors.Color(0.26, 0.5, 0.96, alpha=0.1))
            c.setLineWidth(0.3)
            for ix in range(0, int(w / cm) + 2):
                c.line(ix * cm, hero_bottom, ix * cm, hero_top)
            for iy in range(int(hero_bottom / cm), int(hero_top / cm) + 2):
                c.line(0, iy * cm, w, iy * cm)

        # \u2500\u2500 Logo / Nom entreprise (zone sup\u00e9rieure) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        # Pill verte avec texte AGRIWEB
        pill_y = h - 3.2 * cm
        pill_w = 7 * cm
        pill_h = 1.1 * cm
        pill_x = (w - pill_w) / 2
        c.setFillColor(self.COLOR_SECONDARY)
        c.roundRect(pill_x, pill_y, pill_w, pill_h, pill_h / 2, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(w / 2, pill_y + 0.28 * cm, "AGRIWEB")

        # Tagline
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica", 10)
        c.drawCentredString(w / 2, h - 4.5 * cm, "Solutions Photovolta\u00efques Professionnelles")

        # Ligne s\u00e9paratrice courte
        c.setStrokeColor(colors.Color(1, 1, 1, alpha=0.2))
        c.setLineWidth(0.5)
        c.line(w * 0.3, h - 4.9 * cm, w * 0.7, h - 4.9 * cm)

        # \u2500\u2500 Titre grand format au-dessus de la zone image \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(w / 2, h - 6.2 * cm, "PROPOSITION COMMERCIALE")
        _type_labels = {
            'autoconsommation':            'Autoconsommation individuelle + revente du surplus',
            'sans_injection':              'Autoconsommation totale \u2014 sans injection r\u00e9seau',
            'autoconsommation_collective': 'Autoconsommation collective (OAC \u2014 Art. L315-2)',
        }
        type_label = _type_labels.get(self.type_projet,
                                      'Injection totale sur le r\u00e9seau (obligation d\'achat)')
        c.setFillColor(self.COLOR_SECONDARY)
        c.setFont("Helvetica", 11)
        c.drawCentredString(w / 2, h - 7.2 * cm, type_label)

        # \u2500\u2500 Carte blanche projet (partie basse) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        card_x = 1.5 * cm
        card_y = 2.8 * cm
        card_w = w - 3 * cm
        card_h = h * 0.28 - 0.5 * cm   # ~8.3cm
        radius = 6

        # Ombre
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.25))
        c.roundRect(card_x + 3, card_y - 3, card_w, card_h, radius, fill=1, stroke=0)
        # Carte blanche
        c.setFillColor(self.COLOR_WHITE)
        c.roundRect(card_x, card_y, card_w, card_h, radius, fill=1, stroke=0)

        # Bande sup\u00e9rieure de la carte (marine)
        top_band_h = 1.1 * cm
        c.setFillColor(self.COLOR_PRIMARY)
        c.roundRect(card_x, card_y + card_h - top_band_h, card_w, top_band_h + radius,
                    radius, fill=1, stroke=0)
        c.rect(card_x, card_y + card_h - top_band_h,
               card_w, top_band_h / 2, fill=1, stroke=0)
        # Titre dans la bande
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 9)
        nom_prospect = (self.prospect.get('nom', '') or
                        self.prospect.get('nom_prospect', '') or
                        self.prospect.get('contact_nom', '') or
                        self.prospect.get('lien_annuaire', '') or 'Client')
        commune = self.prospect.get('commune', 'N/A')
        c.drawCentredString(card_x + card_w / 2,
                            card_y + card_h - 0.78 * cm,
                            f"Projet pour :  {nom_prospect}  \u2014  {commune}")

        # Contenu de la carte
        inner_x = card_x + 1 * cm
        inner_y = card_y + card_h - top_band_h - 1.0 * cm

        # Puissance kWc \u2014 valeur phare center
        c.setFillColor(self.COLOR_ACCENT)
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(card_x + card_w / 2, inner_y - 1.3 * cm,
                            f"{self.puissance_kwc:.0f} kWc")
        c.setFillColor(self.COLOR_GREY)
        c.setFont("Helvetica", 10)
        c.drawCentredString(card_x + card_w / 2, inner_y - 2.1 * cm,
                            f"Installation {self.nb_modules} modules \u00d7 {self.puissance_module} Wc")

        # Ligne s\u00e9paratrice interne
        sep_inner_y = inner_y - 2.55 * cm
        c.setStrokeColor(self.COLOR_SEPARATOR)
        c.setLineWidth(0.5)
        c.line(card_x + 1 * cm, sep_inner_y, card_x + card_w - 1 * cm, sep_inner_y)

        # 3 KPI en bas de la carte
        kpi_y = sep_inner_y - 0.5 * cm
        kpi_items = [
            ("Investissement", self._format_euros(self.investissement)),
            ("Production est.", self._format_kwh(self.production_annuelle) + "/an"),
            ("ROI estim\u00e9", f"{self.roi_annees:.1f} ans"),
        ]
        kpi_w = card_w / 3
        for ki, (klbl, kval) in enumerate(kpi_items):
            kx = card_x + ki * kpi_w
            # S\u00e9parateur vertical entre KPIs
            if ki > 0:
                c.setStrokeColor(self.COLOR_SEPARATOR)
                c.setLineWidth(0.5)
                c.line(kx, kpi_y - 1.0 * cm, kx, sep_inner_y)
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(kx + kpi_w / 2, kpi_y - 0.55 * cm, kval)
            c.setFillColor(self.COLOR_GREY)
            c.setFont("Helvetica", 7.5)
            c.drawCentredString(kx + kpi_w / 2, kpi_y - 1.0 * cm, klbl)

        # \u2500\u2500 Bande bas de page (r\u00e9f\u00e9rence, certifs) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        c.setFillColor(colors.Color(0, 0, 0, alpha=0.3))
        c.rect(0, 0, w, 2.6 * cm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_SECONDARY)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(w / 2, 1.8 * cm, "Certifi\u00e9 RGE QualiPV  \u00b7  Assurance d\u00e9cennale  \u00b7  NF C 15-100")
        c.setFillColor(self.COLOR_GREY)
        c.setFont("Helvetica", 7)
        c.drawCentredString(w / 2, 1.2 * cm,
                            f"\u00c9mise le {self.date_now.strftime('%d/%m/%Y')}  \u00b7  Valable 30 jours  \u00b7  Confidentiel")
        c.drawCentredString(w / 2, 0.65 * cm,
                            f"R\u00e9f: PROP-{self.prospect.get('id', 'XXX')}-{self.date_now.strftime('%Y%m%d')}")

        # \u2500\u2500 Bandeau \u00ab Sous r\u00e9serve de visite technique \u00bb (si VT non faite) \u2500\u2500\u2500\u2500\u2500\u2500
        _vt = self.visite_technique or {}
        _vt_faite = bool(_vt.get('date') or _vt.get('notes') or _vt.get('rapport'))
        if not _vt_faite:
            vt_band_h = 0.65 * cm
            vt_band_y = 2.65 * cm   # juste au-dessus de la bande certifs
            c.setFillColor(colors.Color(0.92, 0.60, 0.04, alpha=0.92))  # ambre
            c.rect(0, vt_band_y, w, vt_band_h, fill=1, stroke=0)
            c.setFillColor(colors.Color(0.1, 0.06, 0.0))
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(w / 2, vt_band_y + 0.19 * cm,
                                "\u26a0  Proposition \u00e9mise SANS visite technique  \u2014  "
                                "dimensions, contraintes et faisabilit\u00e9 \u00e0 confirmer sur site")

    def _draw_sommaire(self, c):
        """Page 2 : Sommaire \u2014 design moderne"""
        y = self._draw_page_header(c, "SOMMAIRE")

        sommaire = [
            ("1", "Pr\u00e9sentation de l'entreprise",   "Certifications, r\u00e9f\u00e9rences, expertise"),
            ("2", "Analyse du site",                  "Localisation, contraintes urbanisme, ensoleillement"),
            ("3", "Solution technique",               "Modules, onduleurs, structure, c\u00e2blage"),
            ("4", "\u00c9tude de productible",              "Production estim\u00e9e PVGIS, profil mensuel"),
            ("5", "\u00c9tude financi\u00e8re",                  "Investissement, TRI, VAN, retour sur investissement"),
            ("6", "Devis d\u00e9taill\u00e9",                    "Fourniture, pose, raccordement, d\u00e9marches"),
            ("7", "Planning de r\u00e9alisation",          "D\u00e9claration pr\u00e9alable, travaux, mise en service"),
            ("8", "Garanties et maintenance",          "Garanties mat\u00e9riel, maintenance pr\u00e9ventive"),
            ("9", "Aspects r\u00e9glementaires & CGV",     "Normes, assurances, conditions g\u00e9n\u00e9rales"),
        ]

        y -= 0.6 * cm
        row_h = 1.55 * cm
        for idx, (num, title, desc) in enumerate(sommaire):
            # Fond alternatif l\u00e9ger
            if idx % 2 == 0:
                c.setFillColor(self.COLOR_LIGHT_BG)
                c.rect(1.5 * cm, y - row_h + 0.15 * cm, self.width - 3 * cm, row_h, fill=1, stroke=0)

            # Cercle num\u00e9ro marine
            cx = 2.3 * cm
            cy = y - row_h / 2
            c.setFillColor(self.COLOR_PRIMARY)
            c.circle(cx, cy, 0.38 * cm, fill=1, stroke=0)
            c.setFillColor(self.COLOR_WHITE)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(cx, cy - 0.1 * cm, num)

            # Titre + description
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(3.1 * cm, y - 0.55 * cm, title)
            c.setFillColor(self.COLOR_GREY)
            c.setFont("Helvetica", 8)
            c.drawString(3.1 * cm, y - 1.0 * cm, desc)

            # Ligne pointill\u00e9e de s\u00e9paration
            c.setStrokeColor(self.COLOR_SEPARATOR)
            c.setLineWidth(0.3)
            c.setDash(2, 3)
            c.line(3.1 * cm, y - row_h + 0.25 * cm, self.width - 2 * cm, y - row_h + 0.25 * cm)
            c.setDash()
            c.setLineWidth(1)

            y -= row_h

        # \u2500\u2500 Carte r\u00e9sum\u00e9 \u00e0 la fin du sommaire \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        y -= 0.4 * cm
        card_h = 5.2 * cm
        # Ombre
        c.setFillColor(self.COLOR_SEPARATOR)
        c.roundRect(1.7 * cm, y - card_h - 0.05 * cm, self.width - 3.4 * cm, card_h, 5, fill=1, stroke=0)
        # Fond blanc
        c.setFillColor(self.COLOR_WHITE)
        c.roundRect(1.5 * cm, y - card_h, self.width - 3 * cm, card_h, 5, fill=1, stroke=0)
        # Bande marine
        c.setFillColor(self.COLOR_PRIMARY)
        c.roundRect(1.5 * cm, y - 0.85 * cm, self.width - 3 * cm, 0.85 * cm + 5, 5, fill=1, stroke=0)
        c.rect(1.5 * cm, y - 0.85 * cm, self.width - 3 * cm, 0.85 * cm / 2, fill=1, stroke=0)
        c.setFillColor(self.COLOR_WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(self.width / 2, y - 0.6 * cm, "R\u00c9SUM\u00c9 DE L'OFFRE")

        # 5 lignes KPI en \u00e9ventail
        resume_lines = [
            ("Puissance",           f"{self.puissance_kwc:.0f} kWc  ({self.nb_modules} modules)"),
            ("Production estim\u00e9e",  f"{self._format_kwh(self.production_annuelle)}/an"),
            ("Investissement",      f"{self._format_euros(self.investissement)} HT"),
            ("Gain annuel estim\u00e9",  f"{self._format_euros(self.gain_annuel)}"),
            ("Retour sur invest.",  f"{self.roi_annees:.1f} ans"),
        ]
        ry = y - 1.35 * cm
        half_n = len(resume_lines)
        col_w2 = (self.width - 4 * cm) / 2
        for i, (lbl, val) in enumerate(resume_lines):
            col = 0 if i < 3 else 1
            row = i if i < 3 else i - 3
            rx = 2.2 * cm + col * (col_w2 + 0.5 * cm)
            ry_cur = ry - row * 0.72 * cm
            # Puce verte
            c.setFillColor(self.COLOR_SECONDARY)
            c.circle(rx + 0.12 * cm, ry_cur + 0.08 * cm, 0.12 * cm, fill=1, stroke=0)
            # Label
            c.setFillColor(self.COLOR_GREY)
            c.setFont("Helvetica", 8)
            c.drawString(rx + 0.38 * cm, ry_cur, lbl + " :")
            # Valeur
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(rx + 4.5 * cm, ry_cur, val)

    def _draw_presentation_entreprise(self, c):
        """Page 3 : Présentation entreprise — design moderne"""
        y = self._draw_page_header(c, "1. PRÉSENTATION DE L'ENTREPRISE")

        y -= 0.4 * cm
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

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Certifications & Qualifications")

        certifs = [
            ("RGE  QualiPV",         "Qualification RGE (Reconnu Garant de l'Environnement)",         self.COLOR_SECONDARY),
            ("QualiPV Électricité",  "Module Électricité – Installations raccordées au réseau",        self.COLOR_BLUE),
            ("QualiPV Bâtiment",     "Module Bâtiment – Intégration au bâti et surimposition",         self.COLOR_BLUE),
            ("Assurance Décennale",  "Couverture décennale pour tous les chantiers réalisés",           self.COLOR_ACCENT),
            ("NF C 15-100/752-1",   "Conformité aux normes électriques en vigueur",                     self.COLOR_GREY),
        ]
        for titre, desc, badge_col in certifs:
            # Pill badge
            pill_w = 4.2 * cm
            pill_h = 0.55 * cm
            c.setFillColor(badge_col)
            c.roundRect(2 * cm, y - 0.38 * cm, pill_w, pill_h, pill_h / 2, fill=1, stroke=0)
            c.setFillColor(self.COLOR_WHITE)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(2 * cm + pill_w / 2, y - 0.1 * cm, titre)
            # Description
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica", 8.5)
            c.drawString(6.8 * cm, y - 0.1 * cm, desc)
            y -= 0.72 * cm

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Nos partenaires techniques")

        partenaires = [
            ("JA Solar",  "Modules photovoltaïques Tier 1 – Garantie 30 ans"),
            ("Huawei",    "Onduleurs string intelligents – Monitoring intégré"),
            ("K2 Systems","Systèmes de fixation – Toiture et sol"),
            ("Enedis",    "Raccordement réseau et mise en service"),
        ]
        # 2 colonnes
        col_w3 = (self.width - 3 * cm) / 2
        for i, (nom, desc) in enumerate(partenaires):
            px = 2 * cm + (i % 2) * col_w3
            if i % 2 == 0 and i > 0:
                y -= 0.7 * cm
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(px, y, f"\u25b8  {nom}")
            c.setFillColor(self.COLOR_GREY)
            c.setFont("Helvetica", 8)
            c.drawString(px, y - 0.42 * cm, desc)
            if i % 2 == 1:
                y -= 0.75 * cm
        y -= 0.75 * cm

        y -= 0.3 * cm
        y = self._draw_section_title(c, y, "Références")

        c.setFont("Helvetica", 9)
        c.setFillColor(self.COLOR_DARK)
        refs = [
            "Plus de 400 projets photovoltaïques réalisés",
            "Puissance cumulée installée > 50 MWc",
            "Taux de satisfaction clients : 98%",
            "Interventions dans toute la France métropolitaine",
        ]
        for r in refs:
            c.setFillColor(self.COLOR_SECONDARY)
            c.circle(2.12 * cm, y + 0.1 * cm, 0.1 * cm, fill=1, stroke=0)
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica", 9)
            c.drawString(2.35 * cm, y, r)
            y -= 0.5 * cm

    def _draw_analyse_site(self, c):
        """Page 4 : Analyse du site"""
        y = self._draw_page_header(c, "2. ANALYSE DU SITE")

        # Bandeau avertissement si visite technique non réalisée
        _vt = self.visite_technique or {}
        _vt_faite = bool(_vt.get('date') or _vt.get('notes') or _vt.get('rapport'))
        if not _vt_faite:
            band_h = 1.3 * cm
            band_y = y - band_h - 0.2 * cm
            c.setFillColor(colors.Color(1.0, 0.95, 0.80))
            c.roundRect(1.5 * cm, band_y, self.width - 3 * cm, band_h, 4, fill=1, stroke=0)
            c.setStrokeColor(colors.Color(0.92, 0.60, 0.04))
            c.setLineWidth(1)
            c.roundRect(1.5 * cm, band_y, self.width - 3 * cm, band_h, 4, fill=0, stroke=1)
            c.setFillColor(colors.Color(0.55, 0.35, 0.0))
            c.setFont("Helvetica-Bold", 8)
            c.drawString(2.1 * cm, band_y + 0.82 * cm,
                         "\u26a0  SANS VISITE TECHNIQUE")
            c.setFont("Helvetica", 8)
            c.drawString(2.1 * cm, band_y + 0.44 * cm,
                         "Cette proposition est \u00e9mise sur la base des donn\u00e9es cadastrales et a\u00e9riennes uniquement.")
            c.drawString(2.1 * cm, band_y + 0.12 * cm,
                         "Elle devra \u00eatre confirm\u00e9e apr\u00e8s visite technique sur site.")
            y = band_y - 0.5 * cm
        else:
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
        _prod_spec = int(self.production_annuelle / self.puissance_kwc) if self.puissance_kwc > 0 else 1100
        y = self._draw_kv_line(c, y, "Productible estimé :", f"{_prod_spec} kWh/kWc/an")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Raccordement réseau")

        poste_bt  = self.prospect.get('poste_bt_nom',         '')
        poste_hta = self.prospect.get('poste_hta_nom',        '')
        dist_bt   = self.prospect.get('poste_bt_distance_m',  '')
        dist_hta  = self.prospect.get('poste_hta_distance_m', '')

        rp      = self._get_raccordement_profile()
        is_hta  = self.puissance_kwc > 250
        poste   = (poste_hta or 'À identifier') if is_hta else (poste_bt or 'À identifier')
        _dist_r = dist_hta if is_hta else dist_bt
        try:
            dist = f"{int(float(_dist_r))} m" if _dist_r else 'À déterminer'
        except (ValueError, TypeError):
            dist = str(_dist_r) if _dist_r else 'À déterminer'

        y = self._draw_kv_line(c, y, "Régime de raccordement :",  rp['type'])
        y = self._draw_kv_line(c, y, "Tension d'injection :",      rp['tension'])
        y = self._draw_kv_line(c, y, "Point d'injection réseau :", rp['point_inj'])
        y = self._draw_kv_line(c, y, "Référence CARD :",           rp['carte'])
        y = self._draw_kv_line(c, y, "Contrat / Convention :",     rp['contrat'])
        y = self._draw_kv_line(c, y, "Comptage :",                 rp['compteur'])
        if rp.get('pmo'):
            y = self._draw_kv_line(c, y, "PMO :",                  rp['pmo'])
        if rp.get('turpe_reduit'):
            y = self._draw_kv_line(c, y, "TURPE :",
                                   "Réduit (Art. L341-4-1 Code énergie)")
        y = self._draw_kv_line(c, y, "Poste source :",             poste)
        y = self._draw_kv_line(c, y, "Distance estimée :",         dist)

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

        rp_cable = self._get_raccordement_profile()
        y = self._draw_kv_line(c, y, "Câbles DC :",
                               "H1Z2Z2-K 1x6mm² (ou 1x10mm² si longueur > 30 m)")
        y = self._draw_kv_line(c, y, "Câbles AC :",
                               "Section calculée au courant nominal (NF C 15-100 §5.2)")
        y = self._draw_kv_line(c, y, "Protection DC :",
                               "Parafoudre Type 2 DC, interrupteur-sectionneur DC")
        y = self._draw_kv_line(c, y, "Protection AC :",
                               "Disjoncteur de branchement, parafoudre Type 2 AC, DDR")
        y = self._draw_kv_line(c, y, "Point d'injection réseau :", rp_cable['point_inj'])
        y = self._draw_kv_line(c, y, "Norme électrique :",
                               "NF C 15-100 éd. 2023 / UTE C 15-712-1")

    def _draw_etude_productible(self, c):
        """Page 6 : Étude productible"""
        y = self._draw_page_header(c, "4. ÉTUDE DE PRODUCTIBLE")

        y -= 0.5 * cm
        y = self._draw_section_title(c, y, "Production estimée")

        y = self._draw_kv_line(c, y, "Source des données :", "PVGIS (European Commission)")
        y = self._draw_kv_line(c, y, "Puissance installée :", f"{self.puissance_kwc:.1f} kWc")
        _prod_spec_5 = int(self.production_annuelle / self.puissance_kwc) if self.puissance_kwc > 0 else 1100
        y = self._draw_kv_line(c, y, "Productible spécifique :", f"{_prod_spec_5} kWh/kWc/an")
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
        c.roundRect(graph_x - 0.3 * cm, y - graph_h - 0.5 * cm,
                    graph_w + 0.6 * cm, graph_h + 1 * cm, 3, fill=1, stroke=0)
        # Grille horizontale légère
        for pct_g in [0.25, 0.5, 0.75, 1.0]:
            gy = (y - graph_h) + pct_g * (graph_h - 1 * cm)
            c.setStrokeColor(self.COLOR_SEPARATOR)
            c.setLineWidth(0.3)
            c.line(graph_x - 0.15 * cm, gy, graph_x + graph_w + 0.15 * cm, gy)
        c.setLineWidth(1)

        for i, (m, p) in enumerate(zip(mois, pct_mois)):
            bx = graph_x + i * (bar_w + gap)
            bh = (p / max_pct) * (graph_h - 1 * cm)
            by = y - graph_h

            # Barre
            c.setFillColor(self.COLOR_BLUE)
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
        for annee in [1, 5, 10, 15, 20, 25]:
            degradation = (1 - 0.004) ** annee
            prod_annee = self.production_annuelle * degradation
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

        _proj_labels = {
            'autoconsommation':            'Autoconsommation individuelle + surplus (CACSI)',
            'sans_injection':              'Autoconsommation totale — sans injection réseau',
            'autoconsommation_collective': 'Autoconsommation collective (OAC — Art. L315-2)',
        }
        y = self._draw_kv_line(c, y, "Type de projet :",
                               _proj_labels.get(self.type_projet,
                                                'Vente totale — injection totale (OA/CRE)'))
        y = self._draw_kv_line(c, y, "Prix achat électricité :", f"{self.tarif_achat:.4f} €/kWh")
        # Libellé dynamique selon type_projet et tranche de puissance
        if self.type_projet == 'autoconsommation':
            _seuil_lbl = '≤9 kWc' if self.puissance_kwc <= 9 else '9-100 kWc'
            _tarif_lbl = f"Tarif OA surplus S21 ({_seuil_lbl}, Q1-2026) :"
        elif self.type_projet == 'sans_injection':
            _tarif_lbl = "Tarif revente (aucune injection) :"
        else:
            _tarif_lbl = "Tarif OA injection totale S21 :"
        y = self._draw_kv_line(c, y, _tarif_lbl, f"{self.tarif_revente:.4f} €/kWh")
        if self.type_projet == 'autoconsommation':
            y = self._draw_kv_line(c, y, "Éligibilité arrêté S21 :", "P+Q ≤ 100 kWc (depuis 22/09/2025)")
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

        # En-tête tableau finances
        c.setFillColor(self.COLOR_PRIMARY)
        c.roundRect(1.5 * cm, y - 0.2 * cm, self.width - 3 * cm, 0.65 * cm, 3, fill=1, stroke=0)
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
            tarif_a = self.tarif_achat * ((1 + augmentation_tarif) ** (annee - 1))
            tarif_r = self.tarif_revente  # Tarif revente fixe (contrat OA sur 20 ans)

            if self.type_projet == 'autoconsommation':
                eco = prod * self.taux_autoconso * tarif_a
                rev = prod * (1 - self.taux_autoconso) * tarif_r
                gain = eco + rev
            else:
                gain = prod * tarif_r

            cumul_gains += gain

            if annee in annees_affichees:
                c.setFillColor(self.COLOR_LIGHT_BG if annee % 2 == 0 else self.COLOR_WHITE)
                c.rect(1.5 * cm, y - 0.1 * cm, self.width - 3 * cm, 0.5 * cm, fill=1, stroke=0)
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
        y = self._draw_page_header(c, "SIMULATION AUTOCONSOMMATION DÉTAILLÉE")

        tariff_label = self._tariff_label
        profil_label = self.autoconso_data.get('profil_label', '')
        date_calcul  = (self.autoconso_data.get('date_calcul', '') or '')[:10]
        data_source  = self.autoconso_data.get('data_source', 'profil_type')
        enedis_pdl   = self.autoconso_data.get('enedis_pdl', '')
        _is_theorique = (data_source != 'enedis_dataconnect' or not enedis_pdl)

        # ── Bandeau avertissement courbes théoriques ─────────────────────────────
        if _is_theorique:
            band_y = y - 1.6 * cm
            band_h = 1.4 * cm
            c.setFillColor(colors.Color(1.0, 0.97, 0.88))
            c.roundRect(1.5 * cm, band_y, self.width - 3 * cm, band_h, 4, fill=1, stroke=0)
            c.setStrokeColor(colors.Color(0.92, 0.60, 0.04))
            c.setLineWidth(1)
            c.roundRect(1.5 * cm, band_y, self.width - 3 * cm, band_h, 4, fill=0, stroke=1)
            # Icône + titre
            c.setFillColor(colors.Color(0.55, 0.35, 0.0))
            c.setFont("Helvetica-Bold", 8)
            c.drawString(2.1 * cm, band_y + 0.85 * cm,
                         "⚠  ÉTUDE BASSÉE SUR COURBES THÉORIQUES ENEDIS (profil type « {} »)".format(profil_label))
            c.setFont("Helvetica", 7.5)
            c.setFillColor(colors.Color(0.40, 0.25, 0.0))
            c.drawString(2.1 * cm, band_y + 0.28 * cm,
                         "Les résultats devront être confirmés avec les courbes de charge réelles du client. "
                         "Un mandat de collecte de données et le numéro de PDL (point de livraison) "
                         "sont nécessaires pour accéder aux données Enedis.")
            y = band_y - 0.5 * cm
        else:
            y -= 0.3 * cm

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
        y = self._draw_page_header(c, "BILAN MENSUEL AUTOCONSOMMATION")

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

        # En-tête tableau mensuel
        c.setFillColor(self.COLOR_PRIMARY)
        c.roundRect(1.5 * cm, y - row_h + 0.15*cm, tbl_w, row_h, 3, fill=1, stroke=0)
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

            if i % 2 == 0:
                c.setFillColor(colors.HexColor('#F0FDF4'))
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

        # Ligne total mensuel
        c.setFillColor(colors.HexColor('#ECFDF5'))
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
        y = self._draw_page_header(c, "PROFILS JOURNALIERS SAISONNIERS")

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
        """Assemble une carte depuis les tuiles OSM (tile.openstreetmap.org).
        Retourne un ImageReader ReportLab ou None si indisponible."""
        try:
            from PIL import Image as PILImage, ImageDraw
            import math

            def _deg2tile(lat_d, lon_d, z):
                lat_r = math.radians(lat_d)
                n = 2 ** z
                xt = int((lon_d + 180.0) / 360.0 * n)
                yt = int((1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n)
                return xt, yt

            def _tile_frac(lat_d, lon_d, z):
                lat_r = math.radians(lat_d)
                n = 2 ** z
                xf = (lon_d + 180.0) / 360.0 * n
                yf = (1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n
                return xf, yf

            TILE = 256
            # Tuiles à récupérer pour couvrir width×height pixels autour de (lat,lon)
            tx_center, ty_center = _deg2tile(lat, lon, zoom)
            xf, yf = _tile_frac(lat, lon, zoom)
            # Décalage pixel du centre par rapport au coin supérieur gauche de la tuile centrale
            px_off = int((xf - tx_center) * TILE)
            py_off = int((yf - ty_center) * TILE)

            tiles_x = math.ceil(width / TILE) + 2
            tiles_y = math.ceil(height / TILE) + 2
            canvas_w = tiles_x * TILE
            canvas_h = tiles_y * TILE
            canvas = PILImage.new('RGB', (canvas_w, canvas_h), (240, 240, 240))

            tx0 = tx_center - tiles_x // 2
            ty0 = ty_center - tiles_y // 2

            sess = requests.Session()
            sess.headers['User-Agent'] = 'AgriWeb-PV-Proposition/1.0'
            n_tiles = 2 ** zoom
            for ix in range(tiles_x):
                for iy in range(tiles_y):
                    tx = (tx0 + ix) % n_tiles
                    ty = ty0 + iy
                    if ty < 0 or ty >= n_tiles:
                        continue
                    url = f"https://tile.openstreetmap.org/{zoom}/{tx}/{ty}.png"
                    try:
                        r = sess.get(url, timeout=6)
                        if r.status_code == 200:
                            tile_img = PILImage.open(io.BytesIO(r.content)).convert('RGB')
                            canvas.paste(tile_img, (ix * TILE, iy * TILE))
                    except Exception:
                        pass

            # Centrer le crop sur (lat,lon)
            cx = (tiles_x // 2) * TILE + px_off
            cy = (tiles_y // 2) * TILE + py_off
            left  = cx - width  // 2
            top   = cy - height // 2
            cropped = canvas.crop((left, top, left + width, top + height))

            # Marqueur rouge (croix) au centre
            draw = ImageDraw.Draw(cropped)
            mx, my = width // 2, height // 2
            r = 8
            draw.ellipse((mx - r, my - r, mx + r, my + r), fill=(220, 30, 30), outline=(255, 255, 255), width=2)
            draw.line((mx - r - 4, my, mx + r + 4, my), fill=(220, 30, 30), width=2)
            draw.line((mx, my - r - 4, mx, my + r + 4), fill=(220, 30, 30), width=2)

            buf = io.BytesIO()
            cropped.save(buf, format='PNG')
            buf.seek(0)
            return ImageReader(buf)
        except Exception:
            pass
        return None

    def _decode_base64_image(self, b64_str):
        """Decode une image base64 (avec ou sans header data:...) en ImageReader."""
        try:
            if not b64_str:
                return None
            # Si screenshot_map est stocké comme objet {screenshot, bounds, ...}
            if isinstance(b64_str, dict):
                b64_str = b64_str.get('screenshot', '')
            if not b64_str or not isinstance(b64_str, str):
                return None
            # Si c'est un objet JSON sérialisé en string (ex: '{"screenshot":"data:..."}')
            if b64_str.startswith('{') and '"screenshot"' in b64_str:
                try:
                    obj = json.loads(b64_str)
                    b64_str = obj.get('screenshot', b64_str)
                except Exception:
                    pass
            if ',' in b64_str:
                b64_str = b64_str.split(',', 1)[1]
            img_bytes = base64.b64decode(b64_str)
            return ImageReader(io.BytesIO(img_bytes))
        except Exception as e:
            print(f"[PDF] ⚠️ _decode_base64_image failed: {type(b64_str).__name__} len={len(str(b64_str))} err={e}")
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

        # ─ Production calpinage ──────────────────────────────────────────────
        # Productible précis issu de la simulation calpinage (tilt/azimuth réels)
        # Priorité : calpinage simulation > rapport PVGIS (approximation 30° plein sud)
        if self.production_annuelle > 0 and self.puissance_kwc > 0:
            kwh_kwc = self.production_annuelle / self.puissance_kwc
        else:
            kwh_kwc = rapport.get('kwh_per_kwc', '')
        # Irradiation (kWh/m²) — valeur solaire uniquement, depuis rapport si disponible
        pvgis = rapport.get('pvgis_data', {})
        irradiation = ''
        if isinstance(pvgis, dict):
            irr = pvgis.get('yearly_irradiation') or pvgis.get('H(i)_m') or pvgis.get('irradiation')
            if irr:
                irradiation = f"{irr:.0f} kWh/m²/an"
        # Source label
        prod_source = "simulation calpinage" if (self.production_annuelle > 0 and self.puissance_kwc > 0) else "PVGIS"
        c.setFillColor(self.COLOR_ACCENT)
        c.rect(bx, y - 7.5 * cm, bw, 1.7 * cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(bx + 0.3 * cm, y - 6.1 * cm, f"PRODUCTIBLE SOLAIRE ({prod_source.upper()})")
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
                        preserveAspectRatio=False, mask='auto')
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

        # ─ Vue détaillée : tuile OSM satellite zoom 18 (sans modules) ─
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.5 * cm, y, "Vue détaillée")
        y -= 0.6 * cm

        map2_w = (self.width - 3 * cm)
        map2_h = 8.0 * cm

        # Tuile OSM zoom 18 — vue satellite pure, sans modules
        img17 = None
        if lat and lon:
            img17 = self._fetch_static_map_image(float(lat), float(lon), zoom=18, width=700, height=380)

        if img17:
            c.drawImage(img17, 1.5 * cm, y - map2_h, width=map2_w, height=map2_h,
                        preserveAspectRatio=False, mask='auto')
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

            # En-tête colonnes Google Solar
            c.setFillColor(self.COLOR_PRIMARY)
            c.roundRect(1.5 * cm, y - 0.15 * cm, self.width - 3 * cm, 0.55 * cm, 3, fill=1, stroke=0)
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

    def _draw_visuels_calpinage(self, c):
        """Page Visuels ambiance : vue 3D WebGL + calque irradiation solaire."""
        y = self._draw_page_header(c, "VISUELS DE L'INSTALLATION")

        calpinage   = self.data_json.get('calpinage', {})
        s3d         = calpinage.get('screenshot_3d', '')
        sirr        = calpinage.get('screenshot_irradiation', '')
        img3d       = self._decode_base64_image(s3d)  if s3d  else None
        img_irr     = self._decode_base64_image(sirr) if sirr else None

        has_both = img3d and img_irr

        # ─ Sous-titre intro ─────────────────────────────────────────────────
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor('#64748b'))
        c.drawString(1.5 * cm, y,
                     "Modélisation 3D de l'installation et analyse de l'irradiation solaire reçue par les modules.")
        y -= 0.8 * cm

        img_h = 10.5 * cm if has_both else 14 * cm
        box_w = (self.width - 3.5 * cm) / 2 if has_both else (self.width - 3 * cm)

        def _draw_img_box(img, bx, by, bw, bh, title, legend):
            # Cadre titre
            c.setFillColor(self.COLOR_PRIMARY)
            c.roundRect(bx, by + 0.1 * cm, bw, 0.7 * cm, 4, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(bx + 0.3 * cm, by + 0.35 * cm, title)
            by -= bh + 0.25 * cm
            if img:
                c.drawImage(img, bx, by, width=bw, height=bh,
                            preserveAspectRatio=False, mask='auto')
            else:
                c.setFillColor(self.COLOR_LIGHT_BG)
                c.rect(bx, by, bw, bh, fill=1, stroke=1)
                c.setFillColor(colors.HexColor('#AAAAAA'))
                c.setFont("Helvetica-Oblique", 9)
                c.drawCentredString(bx + bw / 2, by + bh / 2, "Visuel non disponible")
                c.setFont("Helvetica-Oblique", 7.5)
                c.drawCentredString(bx + bw / 2, by + bh / 2 - 0.55 * cm,
                                    "Activez la vue puis sauvegardez le calpinage")
            # Légende sous l'image
            c.setFont("Helvetica-Oblique", 7)
            c.setFillColor(colors.HexColor('#888888'))
            c.drawCentredString(bx + bw / 2, by - 0.3 * cm, legend)

        if has_both:
            _draw_img_box(img3d,  1.5 * cm,           y, box_w, img_h,
                          "🏠  VUE 3D — MODÉLISATION WEBGL",
                          "Rendu 3D temps réel — terrain LiDAR IGN + modules inclinés")
            _draw_img_box(img_irr, 1.5 * cm + box_w + 0.5 * cm, y, box_w, img_h,
                          "☀️  IRRADIATION SOLAIRE — ANALYSE SITE",
                          "Flux solaire reçu (kWh/m²/an) — source Google Solar / PVGIS")
        elif img3d:
            _draw_img_box(img3d,  1.5 * cm, y, box_w, img_h,
                          "🏠  VUE 3D — MODÉLISATION WEBGL",
                          "Rendu 3D temps réel — terrain LiDAR IGN + modules inclinés")
        else:
            _draw_img_box(img_irr, 1.5 * cm, y, box_w, img_h,
                          "☀️  IRRADIATION SOLAIRE — ANALYSE SITE",
                          "Flux solaire reçu (kWh/m²/an) — source Google Solar / PVGIS")

        y -= img_h + 1.5 * cm

        # ─ Bloc interprétatif technologique ─────────────────────────────────
        c.setFillColor(self.COLOR_HEADER_BG)
        c.roundRect(1.5 * cm, y - 3.2 * cm, self.width - 3 * cm, 3.2 * cm, 6, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2 * cm, y - 0.4 * cm, "ANALYSE ET MÉTHODOLOGIE")

        items = [
            ("Modélisation 3D",   "Reconstruction à partir du MNT LiDAR IGN 1 m/px — pentes et orientations des pans réels."),
            ("Irradiation fine",  "Cartographie pixel par pixel du flux solaire reçu selon l'ombrage et l'orientation."),
            ("Précision du calcul", f"Production simulée zone par zone — PVGIS 8760h/an à {self.prospect.get('commune', 'ce site')}."),
        ]
        ky = y - 1.0 * cm
        for titre, texte in items:
            c.setFillColor(self.COLOR_SECONDARY)
            c.circle(2.2 * cm, ky + 0.05 * cm, 0.18 * cm, fill=1, stroke=0)
            c.setFillColor(self.COLOR_PRIMARY)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(2.5 * cm, ky, titre + " :")
            c.setFillColor(self.COLOR_DARK)
            c.setFont("Helvetica", 8)
            c.drawString(2.5 * cm + 4.2 * cm, ky, texte)
            ky -= 0.75 * cm

        self._draw_page_footer(c)

    def _draw_plan_masse(self, c):
        """Page Plan de masse officiel : screenshot + nord, échelle, légende, cartouche."""
        y = self._draw_page_header(c, "PLAN DE MASSE - INSTALLATION PHOTOVOLTAÏQUE")

        calpinage = self.data_json.get('calpinage', {})
        # Priorité : screenshot_plan_masse (vue cadastrale dédiée) > screenshot_map (vue calpinage)
        # Chercher dans data_json ET self.calpinage (direct pass from route)
        screenshot = (calpinage.get('screenshot_plan_masse', '')
                      or self.calpinage.get('screenshot_plan_masse', '')
                      or calpinage.get('screenshot_map', '')
                      or self.calpinage.get('screenshot_map', ''))
        zones = calpinage.get('zones', self.calpinage.get('zones', []))

        # ─ Infos propriétaire / adresse ──────────────────────────────────────
        c.setFont("Helvetica", 8)
        c.setFillColor(self.COLOR_DARK)
        nom = self.prospect.get('nom', '')
        prenom = self.prospect.get('prenom', '')
        adresse = self.prospect.get('adresse', '')
        commune = self.prospect.get('commune', '')
        parcelle = self.prospect.get('parcelle', 'Non renseignée')
        if nom or prenom:
            c.drawString(1.5 * cm, y, f"Propriétaire : {prenom} {nom}".strip())
        if adresse or commune:
            c.drawRightString(self.width - 1.5 * cm, y,
                              f"Adresse : {adresse}, {commune}".strip(', '))
        y -= 0.5 * cm

        # ─ Zone image ─────────────────────────────────────────────────────────
        plan_x = 1.5 * cm
        plan_w = self.width - 3 * cm
        max_img_h = 16 * cm   # hauteur maximale de la zone image

        img = self._decode_base64_image(screenshot) if screenshot else None
        if img:
            iw_px, ih_px = img.getSize()
            aspect = iw_px / ih_px
            img_w = plan_w
            img_h = img_w / aspect
            if img_h > max_img_h:
                img_h = max_img_h
                img_w = img_h * aspect
            img_x = plan_x + (plan_w - img_w) / 2

            # Cadre puis image
            c.setStrokeColor(colors.black)
            c.setLineWidth(1.5)
            c.rect(img_x, y - img_h, img_w, img_h)
            c.drawImage(img, img_x, y - img_h, width=img_w, height=img_h,
                        preserveAspectRatio=False, mask='auto')

            # Rose des vents (coin supérieur droit de l'image, fond blanc semi-opaque)
            ax = img_x + img_w - 1.3 * cm
            ay = y - 1.3 * cm
            c.setFillColor(colors.white)
            c.circle(ax, ay, 0.75 * cm, stroke=0, fill=1)
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.8)
            c.circle(ax, ay, 0.75 * cm, stroke=1, fill=0)
            path = c.beginPath()
            path.moveTo(ax, ay + 0.55 * cm)
            path.lineTo(ax - 0.2 * cm, ay - 0.15 * cm)
            path.lineTo(ax + 0.2 * cm, ay - 0.15 * cm)
            path.close()
            c.setFillColor(colors.black)
            c.drawPath(path, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(ax, ay - 0.58 * cm, "N")

            actual_h = img_h
        else:
            c.setFillColor(self.COLOR_LIGHT_BG)
            c.rect(plan_x, y - max_img_h, plan_w, max_img_h, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#AAAAAA'))
            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(self.width / 2, y - max_img_h / 2,
                                "Veuillez sauvegarder le calpinage pour générer le plan de masse")
            actual_h = max_img_h

        y -= actual_h + 0.5 * cm

        # ─ Échelle + légende + cartouche ─────────────────────────────────────
        # Barre d'échelle 1/500 (à gauche)
        sb_x = plan_x
        sb_y = y
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(self.COLOR_DARK)
        c.drawString(sb_x, sb_y + 0.15 * cm, "Échelle 1/500 (1 cm = 5 m)")
        for i in range(4):
            xi = sb_x + i * cm
            c.setFillColor(colors.black if i % 2 == 0 else colors.white)
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.rect(xi, sb_y - 0.55 * cm, 1 * cm, 0.3 * cm, fill=1, stroke=1)
        c.setFont("Helvetica", 6.5)
        c.setFillColor(self.COLOR_DARK)
        for i in range(5):
            c.drawCentredString(sb_x + i * cm, sb_y - 0.75 * cm, f"{i * 5}m")

        # Légende (centre)
        leg_x = plan_x + 6 * cm
        leg_y = y
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(self.COLOR_PRIMARY)
        c.drawString(leg_x, leg_y, "LÉGENDE :")
        leg_y -= 0.45 * cm
        c.setFillColor(colors.HexColor('#1565C0'))
        c.rect(leg_x, leg_y - 2 * mm, 8 * mm, 3.5 * mm, fill=1, stroke=0)
        c.setFillColor(self.COLOR_DARK)
        c.setFont("Helvetica", 8)
        c.drawString(leg_x + 1 * cm, leg_y, "Modules photovoltaïques")

        # Cartouche (à droite)
        total_kwc = sum(z.get('puissanceKwc', z.get('puissance_kwc', 0)) for z in zones)
        total_modules = int(sum(z.get('nbModules', z.get('nb_modules', 0)) for z in zones))
        cart_x = self.width - 8.5 * cm
        cart_y = y + 0.05 * cm
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.rect(cart_x, cart_y - 2.8 * cm, 7 * cm, 2.8 * cm)
        c.setFillColor(self.COLOR_PRIMARY)
        c.rect(cart_x, cart_y - 0.55 * cm, 7 * cm, 0.55 * cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(cart_x + 3.5 * cm, cart_y - 0.38 * cm,
                            "CARACTÉRISTIQUES TECHNIQUES")
        c.setFillColor(self.COLOR_DARK)
        c.setFont("Helvetica", 7.5)
        cart_items = [
            f"Puissance totale : {total_kwc:.2f} kWc",
            f"Nombre de modules : {total_modules}",
            f"Parcelle cadastrale : {parcelle}",
            f"Date du plan : {datetime.now().strftime('%d/%m/%Y')}",
        ]
        for i, txt in enumerate(cart_items):
            c.drawString(cart_x + 0.3 * cm, cart_y - 0.95 * cm - i * 0.45 * cm, txt)

        self._draw_page_footer(c)

    # ── Plan de calpinage ─────────────────────────────────────────────────────

    def _draw_plan_calpinage(self, c):
        """Page Plan de calpinage : screenshot Leaflet + résumé des zones."""
        y = self._draw_page_header(c, "PLAN DE CALPINAGE")

        calpinage  = self.data_json.get('calpinage', {})
        # Chercher screenshot dans data_json ET self.calpinage (direct pass from route)
        screenshot = (calpinage.get('screenshot_map', '')
                      or self.calpinage.get('screenshot_map', ''))
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
            # Ombre
            c.setFillColor(self.COLOR_SEPARATOR)
            c.roundRect(bx2 + 0.2 * cm, y - 1.35 * cm, bw_box - 0.2 * cm, 1.3 * cm, 4, fill=1, stroke=0)
            c.setFillColor(self.COLOR_PRIMARY if i % 2 == 0 else self.COLOR_BLUE)
            c.roundRect(bx2 + 0.1 * cm, y - 1.25 * cm, bw_box - 0.2 * cm, 1.3 * cm, 4, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(bx2 + bw_box / 2, y - 0.42 * cm, ttl)
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(bx2 + bw_box / 2, y - 1.02 * cm, val)
        y -= 1.6 * cm

        # ─ Image du calpinage ────────────────────────────────────────────────
        img_calp = self._decode_base64_image(screenshot) if screenshot else None
        max_img_h = 14 * cm
        box_w = self.width - 3 * cm
        if img_calp:
            iw_px, ih_px = img_calp.getSize()
            aspect = iw_px / ih_px
            img_w = box_w
            img_h = img_w / aspect
            if img_h > max_img_h:
                img_h = max_img_h
                img_w = img_h * aspect
            img_x = 1.5 * cm + (box_w - img_w) / 2
            c.drawImage(img_calp, img_x, y - img_h, width=img_w, height=img_h,
                        preserveAspectRatio=False, mask='auto')
        else:
            img_h = max_img_h
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
            hdrs = ["Zone", "Modules", "Puissance (kWc)", "Surface (m²)", "Orientation"]
            cols = [1.5 * cm, 4.5 * cm, 7.5 * cm, 11.5 * cm, 15 * cm]
            # En-tête colonnes plan calpinage zones
            c.setFillColor(self.COLOR_PRIMARY)
            c.roundRect(1.5 * cm, y - 0.15 * cm, self.width - 3 * cm, 0.55 * cm, 3, fill=1, stroke=0)
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

        # ── Fallback GPU : si plu_info vide, lire depuis api_details.gpu.details ──────
        gpu_details = rapport.get('api_details', {}).get('gpu', {}).get('details', {})
        if not plu_list and gpu_details:
            z_layer = gpu_details.get('Zone Urba') or gpu_details.get('zone-urba') or {}
            for feat_props in z_layer.get('features', [])[:5]:
                # Normaliser les clés en minuscules pour compatibilité avec le code existant
                props_lower = {k.lower(): v for k, v in feat_props.items() if v}
                plu_list.append({'properties': props_lower, '_source': 'gpu'})

        # Idem pour ZAER si vide
        if not zaer_list and gpu_details:
            z_zaer = gpu_details.get('ZAER') or gpu_details.get('zaer') or {}
            for feat_props in z_zaer.get('features', [])[:3]:
                props_lower = {k.lower(): v for k, v in feat_props.items() if v}
                zaer_list.append({'properties': props_lower, '_source': 'gpu'})

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
                typezone  = props.get('typezone', props.get('Typezone', props.get('zone', '')))
                libelle   = props.get('libelle', props.get('Libelle', props.get('libelong', props.get('Libelong', props.get('lib', '')))))
                c.setFillColor(self.COLOR_ACCENT)
                c.roundRect(col1_x, y - 0.6 * cm, 1.8 * cm, 0.7 * cm, 3, fill=1, stroke=0)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 9)
                c.drawCentredString(col1_x + 0.9 * cm, y - 0.2 * cm, typezone or "—")
                c.setFillColor(self.COLOR_DARK)
                c.setFont("Helvetica", 8)
                c.drawString(col1_x + 2 * cm, y - 0.2 * cm, (libelle or "Zone urbanisme")[:55])
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

        # Sismicité — clé réelle : 'sismique' (liste)
        sismo_list = georisques.get('sismique', [])
        if not isinstance(sismo_list, list):
            sismo_list = [sismo_list] if sismo_list else []
        sismo = sismo_list[0] if sismo_list else {}
        sismo_zone = str(sismo.get('niv_zone', sismo.get('zone', sismo.get('niveau', '—'))))
        sismo_desc = sismo.get('codtxt', sismo.get('description', ''))

        # Argile — clé réelle : 'argiles' (liste de risques gaspar)
        argile_list = georisques.get('argiles', [])
        if not isinstance(argile_list, list):
            argile_list = [argile_list] if argile_list else []
        argile = argile_list[0] if argile_list else {}
        argile_risque = str(argile.get('libelle_risque_long', argile.get('risque', argile.get('classe', '—'))))
        if len(argile_risque) > 30:
            argile_risque = argile_risque[:28] + '…'

        # Radon — clé réelle : 'radon' (liste)
        radon_list = georisques.get('radon', [])
        if not isinstance(radon_list, list):
            radon_list = [radon_list] if radon_list else []
        radon = radon_list[0] if radon_list else {}
        radon_cls = str(radon.get('classePotentiel', radon.get('classe', radon.get('potentiel', '—'))))

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
                try:
                    val = f"{int(float(val))} m"
                except (ValueError, TypeError):
                    val = str(val)
            if key == 'puissance' and val not in ('—', None, 'None', ''):
                val = f"{val} kVA"
            elif key == 'puissance':
                val = '—'
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
            if val is None: val = '—'
            if key == 'distance_m' and val != '—':
                try:
                    val = f"{int(float(val))} m"
                except:
                    pass
            if key == 'puissance' and val not in ('—', None, 'None', ''):
                val = f"{val} kVA"
            elif key == 'puissance':
                val = '—'
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
        # SECTION E : Contraintes GPU (protection patrimoniaux, etc.)
        # ─────────────────────────────────────────────────────────────────────
        protection_keywords = ['patrimoine', 'monument', 'perimetre', 'sauvegarde', 'abf',
                               'psmv', 'pm1', 'pm2', 'pm3', 'spt', 'sct', 'protection',
                               'prescription', 'servitude']
        protection_layers_found = {}
        mh_present = False
        if gpu_details:
            for layer_key, layer_info in gpu_details.items():
                if not isinstance(layer_info, dict):
                    continue
                lk_lower = layer_key.lower()
                if any(kw in lk_lower for kw in protection_keywords):
                    cnt = layer_info.get('count', 0)
                    if cnt and cnt > 0:
                        protection_layers_found[layer_key] = layer_info
                        mh_present = True

        if gpu_details:
            y -= 0.1 * cm
            y = self._draw_section_title(c, y, "Contraintes Urbanisme GPU (toutes couches)", number="E")
            # Résumé des couches GPU disponibles
            non_empty_layers = {k: v for k, v in gpu_details.items()
                                if isinstance(v, dict) and v.get('count', 0) > 0}
            if non_empty_layers:
                row_y = y
                for i, (layer_key, layer_info) in enumerate(list(non_empty_layers.items())[:8]):
                    cnt = layer_info.get('count', 0)
                    name_fr = layer_info.get('name_fr', layer_key.replace('-', ' ').replace('_', ' ').title())[:35]
                    # Badge couleur selon type de couche
                    lk_l = layer_key.lower()
                    is_risk = any(kw in lk_l for kw in protection_keywords)
                    badge_col = colors.HexColor('#E53935') if is_risk else self.COLOR_PRIMARY
                    c.setFillColor(badge_col)
                    c.roundRect(1.5 * cm, row_y - 0.45 * cm, 0.5 * cm, 0.45 * cm, 2, fill=1, stroke=0)
                    c.setFillColor(colors.white)
                    c.setFont("Helvetica-Bold", 6.5)
                    c.drawCentredString(1.75 * cm, row_y - 0.28 * cm, str(cnt))
                    c.setFillColor(self.COLOR_DARK)
                    c.setFont("Helvetica", 7.5)
                    c.drawString(2.2 * cm, row_y - 0.28 * cm, name_fr)
                    # Première feature (valeur principale)
                    feats = layer_info.get('features', [])
                    if feats:
                        f0 = feats[0]
                        sample = ', '.join(f"{v}" for k, v in list(f0.items())[:2] if v)[:50]
                        c.setFont("Helvetica-Oblique", 7)
                        c.setFillColor(colors.HexColor('#555555'))
                        c.drawString(9.5 * cm, row_y - 0.28 * cm, sample)
                    row_y -= 0.5 * cm
                y = row_y
                if len(non_empty_layers) > 8:
                    c.setFont("Helvetica-Oblique", 7)
                    c.setFillColor(colors.HexColor('#777777'))
                    c.drawString(1.7 * cm, y, f"  … et {len(non_empty_layers) - 8} autre(s) couche(s) GPU")
                    y -= 0.4 * cm
            else:
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColor(colors.HexColor('#777777'))
                c.drawString(1.7 * cm, y, "Aucune contrainte GPU détectée au point exact.")
                y -= 0.45 * cm

        # ─────────────────────────────────────────────────────────────────────
        # SECTION 5 : Note de synthèse
        # ─────────────────────────────────────────────────────────────────────
        y -= 0.2 * cm
        # Ajuster hauteur note selon contenu
        note_lines_count = 1 + (1 if plu_list else 0) + (1 if ppri_present else 0) + \
                           (1 if sismo_zone not in ['—', '1', 'Zone 1'] else 0) + \
                           (1 if mh_present else 0)
        note_h = max(2.5 * cm, note_lines_count * 0.55 * cm + 1.2 * cm)
        c.setFillColor(self.COLOR_HEADER_BG)
        c.rect(1.5 * cm, y - note_h, self.width - 3 * cm, note_h, fill=1, stroke=0)
        c.setFillColor(self.COLOR_PRIMARY)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1.8 * cm, y - 0.3 * cm, "NOTE DE SYNTHÈSE RÉGLEMENTAIRE")
        c.setFont("Helvetica", 8)
        c.setFillColor(self.COLOR_DARK)
        notes = []
        if plu_list:
            zones_str = ", ".join([
                (f.get('properties', f) if isinstance(f, dict) else {}).get('typezone',
                 (f.get('properties', f) if isinstance(f, dict) else {}).get('Typezone', '?'))
                for f in plu_list[:3]
            ])
            notes.append(f"Zonage PLU identifié : {zones_str}.")
        if mh_present:
            layers_str = ', '.join(list(protection_layers_found.keys())[:2])
            notes.append(f"Contrainte patrimoniaux/protection détectée : {layers_str[:60]}.")
        else:
            notes.append("Périmètre de protection patrimoniale (MH 500 m) : aucun identifié.")
        if ppri_present:
            notes.append("Attention : le site est concerné par un PPRI — consulter la Mairie / DDT.")
        if sismo_zone not in ['—', '1', 'Zone 1']:
            notes.append(f"Zone sismique {sismo_zone} — respecter la réglementation para-sismique.")
        if not [n for n in notes if n.startswith('Zonage') or n.startswith('Attention') or n.startswith('Zone sis')]:
            notes.insert(0, "Aucune contrainte majeure identifiée. Vérification en Mairie recommandée.")
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
        # Ajuster le poste "pose" pour que le total colle — clampé à 0 minimum
        ecart = self.investissement - total_postes
        prix_pose = max(0.0, prix_pose + ecart)

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
            ifer = self.puissance_kwc * 8.46  # Tarif IFER 2026 (CGI art. 1519 F)
            c.drawString(2 * cm, y, f"IFER (Imposition Forfaitaire sur les Entreprises de Réseaux) : {ifer:,.2f} €/an")
            y -= 0.4 * cm
            c.drawString(2 * cm, y, f"Applicable aux installations ≥ 100 kWc — Tarif 2026 : 8,46 €/kW")

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
        rp_cgv = self._get_raccordement_profile()
        # ── Textes réglementaires communs à tous les types
        reglementaire = [
            f"• {rp_cgv['carte']} — référence de raccordement applicable à ce projet",
            "• NF C 15-100 éd. 2023 : Installations électriques basse tension",
            "• UTE C 15-712-1 : Installations PV raccordées au réseau public",
            "• Code de l'urbanisme — Art. R421-9 : Déclaration préalable de travaux",
        ]
        # ── Textes spécifiques au type de projet
        if self.type_projet == 'autoconsommation':
            reglementaire += [
                "• Code de l'énergie — Art. L315-1 : Autoconsommation individuelle",
                "• Décret n°2017-676 du 28 avril 2017 — autoconsommation d'électricité",
                "• Arrêté S21 du 6 oct. 2021 (mod. 26 mars 2025) — tarifs OA surplus autoconsommation",
                "• Seuils tarifaires S21 : 4,00 c€/kWh (P+Q ≤ 9 kWc) | 5,36 c€/kWh (9-100 kWc)",
                "• P+Q ≤ 100 kWc obligatoire pour éligibilité S21 (depuis le 22 sept. 2025)",
                "• Décret n°2020-1452 du 27 nov. 2020 — prime à l'investissement (IAP)",
                "• Contrat CACSI (Convention Autoconsommation avec Surplus et Injection EDF OA)",
            ]
        elif self.type_projet == 'autoconsommation_collective':
            reglementaire += [
                "• Code de l'énergie — Art. L315-2 : Autoconsommation collective (OAC)",
                "• Décret n°2017-676 du 28 avril 2017 — autoconsommation d'électricité",
                "• Art. L341-4-1 Code énergie — TURPE réduit pour OAC",
                "• Arrêté du 21 novembre 2019 — modalités techniques OAC",
                "• PMO (Personne Morale Organisatrice) obligatoire",
            ]
        elif self.type_projet == 'sans_injection':
            reglementaire += [
                "• Code de l'énergie — Art. L315-1 : Autoconsommation totale",
                "• Aucun contrat OA ni CACSI — CONSUEL + déclaration CCAS",
                "• Dispositif de limitation de production ou anti-îlotage obligatoire",
            ]
        else:  # vente totale
            reglementaire += [
                "• Code de l'énergie — Art. L314-1 : Obligation d'achat (OA)",
                "• Arrêté S21 du 6 oct. 2021 (mod. 26 mars 2025) — conditions d'achat OA photovoltaïque",
                "• OA (contrat EDF OA) : P+Q ≤ 100 kWc — appel d'offres CRE si P+Q > 100 kWc",
            ]
        if self.puissance_kwc >= 100:
            reglementaire.append(
                f"• Art. 1519 F CGI — IFER : {self.puissance_kwc * 8.46:,.0f} €/an (8,46 €/kW — 2026)")
        if self.puissance_kwc > 100:
            reglementaire.append("• Appel d'offres CRE obligatoire (P+Q > 100 kWc depuis 22/09/2025)")

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
