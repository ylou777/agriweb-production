"""
Générateur de Déclaration Préalable de Travaux (DP) - CERFA 13703*09
Pour installations photovoltaïques en toiture et au sol

Génère automatiquement :
- Formulaire CERFA 13703*09 pré-rempli
- Plans DP1 à DP8 complets
- Photo-montages avec images satellite réelles
- Documents graphiques d'insertion paysagère
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Image
from reportlab.lib.utils import ImageReader
from datetime import datetime
import io
import math
import requests
from PIL import Image as PILImage, ImageDraw, ImageFont
import base64
import json


class DeclarationPrealableGenerator:
    """Génère une Déclaration Préalable complète pour installation PV"""
    
    def __init__(self, prospect_data, calpinage_data=None):
        """
        Args:
            prospect_data: dict contenant toutes les données du prospect
                - Données propriétaire (nom, adresse, contact)
                - Données parcelle (cadastre, surface, coordonnées GPS)
                - Données installation PV (puissance, surface panneaux, type toiture/sol)
                - Données bâtiment (dimensions, hauteur, pente toiture, orientation)
            calpinage_data: dict optionnel avec données réelles du calpinage
                - zones: liste des zones avec nbModules, nbCols, nbRows, moduleOrientation
                - module: dimensions et puissance des modules
        """
        self.data = prospect_data
        self.width, self.height = A4
        
        # Récupérer les données cadastrales réelles via API IGN
        self.cadastre_data = self._fetch_cadastre_data()
        
        # Intégrer les données du calpinage si disponibles
        self.calpinage = calpinage_data or {}
        self._extract_calpinage_info()
        
    def generate_complete_dossier(self):
        """Génère le dossier DP complet (formulaire + tous les plans DP1 à DP8)"""
        dossier = {
            'formulaire': self.generate_formulaire_cerfa(),
            'plan_dp1': self.generate_plan_situation(),
            'plan_dp2': self.generate_plan_masse(),
            'plan_dp3': self.generate_plan_coupe(),
            'plan_dp4': self.generate_plan_facades_actuel(),
            'plan_dp5': self.generate_plan_facades_projet(),
            'plan_dp6': self.generate_insertion_paysagere(),
            'plan_dp7': self.generate_photo_environnement_proche(),
            'plan_dp8': self.generate_photo_environnement_lointain(),
        }
        return dossier
    
    def generate_formulaire_cerfa(self):
        """Génère le formulaire CERFA 13703*09 (4 pages)"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # PAGE 1 : Identification et nature du projet
        self._draw_page_1_identification(c)
        c.showPage()
        
        # PAGE 2 : Terrain et projet
        self._draw_page_2_terrain(c)
        c.showPage()
        
        # PAGE 3 : Engagement et autorisations
        self._draw_page_3_engagement(c)
        c.showPage()
        
        # PAGE 4 : Notice explicative
        self._draw_page_4_notice(c)
        c.showPage()
        
        c.save()
        buffer.seek(0)
        return buffer
    
    # ========== PAGE 1 : IDENTIFICATION ==========
    
    def _draw_page_1_identification(self, c):
        """Page 1 du CERFA : Identification du demandeur et du projet"""
        
        # En-tête CERFA
        y = self._draw_cerfa_header(c, page=1)
        
        # CADRE 1 : IDENTITÉ DU DEMANDEUR
        y = self._draw_cadre_1_identite(c, y)
        
        # CADRE 2 : LOCALISATION DU TERRAIN
        y = self._draw_cadre_2_localisation(c, y)
        
        # CADRE 3 : NATURE DES TRAVAUX
        y = self._draw_cadre_3_nature_travaux(c, y)
        
        # Pied de page
        self._draw_footer(c, page=1)
    
    def _draw_cerfa_header(self, c, page=1):
        """Dessine l'en-tête standard CERFA"""
        y = self.height - 1.5*cm
        
        # Bandeau bleu
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(0, y - 1.2*cm, self.width, 1.2*cm, fill=1, stroke=0)
        
        # Titre
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, y - 0.8*cm, "DÉCLARATION PRÉALABLE DE TRAVAUX")
        
        # Numéro CERFA
        c.setFont("Helvetica", 10)
        c.drawString(self.width - 6*cm, y - 0.8*cm, "CERFA N° 13703*09")
        
        # Sous-titre
        c.setFillColor(colors.black)
        y -= 1.8*cm
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, "Travaux sur maison individuelle et/ou ses annexes")
        
        y -= 0.4*cm
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(2*cm, y, "Installation photovoltaïque - Articles L.421-1 à L.421-4 et R.421-1 à R.421-13 du code de l'urbanisme")
        
        # Numéro de dossier (vide - sera complété par mairie)
        c.setFillColor(colors.black)
        y -= 0.8*cm
        c.setFont("Helvetica", 9)
        c.drawString(2*cm, y, "N° de dossier (réservé à la mairie) : .................................................")
        
        # Page
        c.setFont("Helvetica", 8)
        c.drawString(self.width - 3*cm, y, f"Page {page}/4")
        
        return y - 0.8*cm
    
    def _draw_cadre_1_identite(self, c, y_start):
        """Cadre 1 : Identité du demandeur"""
        y = y_start - 0.5*cm
        
        # Titre cadre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(1.5*cm, y - 0.6*cm, self.width - 3*cm, 0.6*cm, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.45*cm, "1. IDENTITÉ DU DEMANDEUR")
        
        y -= 1.2*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        # Type de demandeur
        is_personne_physique = True  # Par défaut
        siret = self.data.get('siret') or self.data.get('proprietaire_siren') or ''
        if siret:
            is_personne_physique = False
        
        self._checkbox(c, 2*cm, y, is_personne_physique)
        c.drawString(2.7*cm, y - 0.15*cm, "Personne physique")
        
        self._checkbox(c, 7*cm, y, not is_personne_physique)
        c.drawString(7.7*cm, y - 0.15*cm, "Personne morale")
        
        # Nom/Raison sociale
        y -= 0.8*cm
        nom = self.data.get('nom_prospect') or self.data.get('proprietaire_denomination') or self.data.get('contact_nom') or ''
        self._field_labeled(c, 2*cm, y, "Nom ou raison sociale :", nom, width=14*cm)
        
        # Prénom (si personne physique)
        if is_personne_physique:
            y -= 0.7*cm
            prenom = self.data.get('prenom_prospect') or self.data.get('dirigeant_prenom') or ''
            self._field_labeled(c, 2*cm, y, "Prénom :", prenom, width=14*cm)
        
        # Adresse
        y -= 0.7*cm
        adresse = self.data.get('proprietaire_adresse') or ''
        self._field_labeled(c, 2*cm, y, "Adresse :", adresse, width=14*cm)
        
        y -= 0.7*cm
        cp = self.data.get('proprietaire_code_postal') or ''
        ville = self.data.get('proprietaire_ville') or ''
        self._field_labeled(c, 2*cm, y, "Code postal :", cp, width=3*cm)
        self._field_labeled(c, 7*cm, y, "Commune :", ville, width=9*cm)
        
        # Contact
        y -= 0.7*cm
        tel = self.data.get('contact_tel') or self.data.get('dirigeant_tel') or ''
        email = self.data.get('contact_email') or self.data.get('dirigeant_email') or ''
        self._field_labeled(c, 2*cm, y, "Téléphone :", tel, width=5*cm)
        self._field_labeled(c, 9*cm, y, "Email :", email, width=7*cm)
        
        # Cadre de fin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.rect(1.5*cm, y - 0.5*cm, self.width - 3*cm, y_start - y - 0.7*cm)
        
        return y - 1*cm
    
    def _draw_cadre_2_localisation(self, c, y_start):
        """Cadre 2 : Localisation du terrain"""
        y = y_start - 0.5*cm
        
        # Titre cadre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(1.5*cm, y - 0.6*cm, self.width - 3*cm, 0.6*cm, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.45*cm, "2. LOCALISATION DU TERRAIN")
        
        y -= 1.2*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        # Adresse du terrain
        adresse_terrain = self.data.get('adresse') or ''
        self._field_labeled(c, 2*cm, y, "Adresse du terrain :", adresse_terrain, width=14*cm)
        
        y -= 0.7*cm
        commune = self.data.get('commune') or ''
        self._field_labeled(c, 2*cm, y, "Commune :", commune, width=14*cm)
        
        # Références cadastrales
        y -= 0.9*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, "Références cadastrales :")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 9)
        
        # PRIORITÉ 1: Utiliser TOUJOURS les parcelles du prospect
        parcelles = self._extract_parcelles()
        
        if parcelles and len(parcelles) > 0:
            # Afficher toutes les parcelles du prospect (max 5)
            for i, parcelle in enumerate(parcelles[:5]):
                section = parcelle.get('section', '')
                numero = parcelle.get('numero', '')
                surface = parcelle.get('surface', '')
                
                # Formater la surface
                surface_str = str(surface) if surface else ''
                if surface_str and not surface_str.endswith('m²'):
                    surface_str = f"{surface_str} m²"
                
                self._field_labeled(c, 2*cm, y, "Section :", section, width=2*cm)
                self._field_labeled(c, 5*cm, y, "N° :", numero, width=3*cm)
                self._field_labeled(c, 9*cm, y, "Surface :", surface_str, width=5*cm)
                
                # Badge si données validées
                if section and numero:
                    c.setFillColor(colors.HexColor('#00C851'))
                    c.setFont("Helvetica-Bold", 6)
                    c.drawString(14.5*cm, y - 0.15*cm, "✓ PROSPECT")
                    c.setFillColor(colors.black)
                    c.setFont("Helvetica", 9)
                
                y -= 0.6*cm
                
                # Si plusieurs parcelles, ajouter un petit espace
                if i < len(parcelles[:5]) - 1:
                    y -= 0.2*cm
        
        elif self.cadastre_data and self.cadastre_data.get('success'):
            # PRIORITÉ 2: API IGN si pas de parcelles dans prospect
            section = self.cadastre_data.get('section', '')
            numero = self.cadastre_data.get('numero', '')
            contenance = self.cadastre_data.get('contenance', 0)
            
            # Convertir contenance (m²)
            if contenance > 10000:
                surface = f"{contenance / 10000:.2f} ha"
            else:
                surface = f"{contenance} m²"
            
            self._field_labeled(c, 2*cm, y, "Section :", section, width=2*cm)
            self._field_labeled(c, 5*cm, y, "N° :", numero, width=3*cm)
            self._field_labeled(c, 9*cm, y, "Surface :", surface, width=5*cm)
            
            # Marque API IGN
            c.setFillColor(colors.HexColor('#FF9800'))
            c.setFont("Helvetica-Bold", 6)
            c.drawString(14.5*cm, y - 0.15*cm, "✓ API IGN")
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            y -= 0.6*cm
        else:
            # PRIORITÉ 3: Champs vides à compléter
            self._field_labeled(c, 2*cm, y, "Section :", '', width=2*cm)
            self._field_labeled(c, 5*cm, y, "N° :", '', width=3*cm)
            self._field_labeled(c, 9*cm, y, "Surface :", '', width=5*cm)
            
            c.setFillColor(colors.HexColor('#D32F2F'))
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(14.5*cm, y - 0.15*cm, "À compléter")
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
        
        # Cadre de fin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.rect(1.5*cm, y - 0.5*cm, self.width - 3*cm, y_start - y - 0.7*cm)
        
        return y - 1*cm
    
    def _draw_cadre_3_nature_travaux(self, c, y_start):
        """Cadre 3 : Nature des travaux"""
        y = y_start - 0.5*cm
        
        # Titre cadre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(1.5*cm, y - 0.6*cm, self.width - 3*cm, 0.6*cm, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.45*cm, "3. NATURE DES TRAVAUX")
        
        y -= 1.2*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        # Type d'installation
        type_install = self.data.get('type', 'toiture')
        is_toiture = 'toiture' in type_install.lower()
        is_sol = 'sol' in type_install.lower() or 'ombriere' in type_install.lower()
        
        self._checkbox(c, 2*cm, y, is_toiture)
        c.drawString(2.7*cm, y - 0.15*cm, "Installation de panneaux photovoltaïques sur toiture existante")
        
        y -= 0.6*cm
        self._checkbox(c, 2*cm, y, is_sol)
        c.drawString(2.7*cm, y - 0.15*cm, "Installation de panneaux photovoltaïques au sol ou ombrière")
        
        # Description des travaux
        y -= 1*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, "Description détaillée des travaux :")
        
        y -= 0.5*cm
        c.setFont("Helvetica", 8)
        
        # Calculer puissance
        surface_m2 = float(self.data.get('surface_m2', 0) or 0)
        surface_ha = float(self.data.get('surface_ha', 0) or 0)
        if surface_ha > 0:
            surface_m2 = surface_ha * 10000
        
        puissance_kwc = round(surface_m2 * 0.15, 2) if surface_m2 > 0 else 0
        nb_modules_estime = int(surface_m2 / 2) if surface_m2 > 0 else 0
        
        description = f"Installation d'une centrale photovoltaïque d'une puissance de {puissance_kwc:.2f} kWc, "
        description += f"composée d'environ {nb_modules_estime} modules photovoltaïques.\n"
        
        if is_toiture:
            description += "Les panneaux seront posés en surimposition sur la toiture existante, "
            description += "sans modification de la charpente. Fixation par rails et crochets de toiture.\n"
        else:
            description += "Les panneaux seront installés au sol sur structures métalliques ancrées, "
            description += "sans fondation béton (pieux battus ou vissés).\n"
        
        description += f"Raccordement au réseau public d'électricité (type {'BT' if puissance_kwc < 250 else 'HTA'})."
        
        # Afficher description (multi-lignes)
        lines = description.split('\n')
        for line in lines:
            c.drawString(2*cm, y, line)
            y -= 0.4*cm
        
        # Surfaces
        y -= 0.5*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, "Surfaces :")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 9)
        surface_panneaux = round(surface_m2, 2)
        self._field_labeled(c, 2*cm, y, "Surface des panneaux PV (m²) :", f"{surface_panneaux:.2f}", width=5*cm)
        self._field_labeled(c, 10*cm, y, "Emprise au sol (m²) :", f"{surface_panneaux:.2f}" if is_sol else "0", width=5*cm)
        
        y -= 0.6*cm
        self._field_labeled(c, 2*cm, y, "Surface de plancher créée (m²) :", "0", width=5*cm)
        
        # Hauteur
        y -= 0.8*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, "Hauteur :")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 9)
        
        hauteur_batiment = self.data.get('hauteur_batiment_m', 0) or 0
        hauteur_panneaux = 0.15  # Surimposition ~15cm
        hauteur_totale = float(hauteur_batiment) + hauteur_panneaux if is_toiture else 1.5  # Sol : 1.5m max
        
        self._field_labeled(c, 2*cm, y, "Hauteur maximale (m) :", f"{hauteur_totale:.2f}", width=5*cm)
        
        # Cadre de fin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.rect(1.5*cm, y - 0.5*cm, self.width - 3*cm, y_start - y - 0.7*cm)
        
        return y - 1*cm
    
    # ========== PAGE 2 : TERRAIN ET PROJET ==========
    
    def _draw_page_2_terrain(self, c):
        """Page 2 : Terrain et projet"""
        
        # En-tête
        y = self._draw_cerfa_header(c, page=2)
        
        # CADRE 4 : INFORMATIONS COMPLÉMENTAIRES
        y = self._draw_cadre_4_informations_complementaires(c, y)
        
        # CADRE 5 : DOCUMENTS JOINTS
        y = self._draw_cadre_5_documents_joints(c, y)
        
        # Pied de page
        self._draw_footer(c, page=2)
    
    def _draw_cadre_4_informations_complementaires(self, c, y_start):
        """Cadre 4 : Informations complémentaires"""
        y = y_start - 0.5*cm
        
        # Titre cadre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(1.5*cm, y - 0.6*cm, self.width - 3*cm, 0.6*cm, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.45*cm, "4. INFORMATIONS COMPLÉMENTAIRES")
        
        y -= 1.2*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        # Destination (production d'énergie)
        c.drawString(2*cm, y, "Destination des installations :")
        y -= 0.5*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2.5*cm, y, "Production d'électricité d'origine renouvelable (photovoltaïque)")
        
        # Type de raccordement
        y -= 0.8*cm
        c.setFont("Helvetica", 9)
        c.drawString(2*cm, y, "Type de raccordement :")
        
        type_raccord = self.data.get('type_raccordement', 'autoconso_injection')
        is_autoconso = 'autoconso' in type_raccord
        is_vente = 'injection_totale' in type_raccord
        
        y -= 0.5*cm
        self._checkbox(c, 2.5*cm, y, is_autoconso)
        c.drawString(3.2*cm, y - 0.15*cm, "Autoconsommation avec revente du surplus")
        
        y -= 0.5*cm
        self._checkbox(c, 2.5*cm, y, is_vente)
        c.drawString(3.2*cm, y - 0.15*cm, "Vente totale de l'électricité produite")
        
        # Zones protégées
        y -= 1*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, "Le projet est-il situé dans un secteur protégé ?")
        
        y -= 0.5*cm
        c.setFont("Helvetica", 9)
        self._checkbox(c, 2.5*cm, y, False)
        c.drawString(3.2*cm, y - 0.15*cm, "Oui (ABF, Monument Historique, Site Classé)")
        
        y -= 0.5*cm
        self._checkbox(c, 2.5*cm, y, True)  # Par défaut non
        c.drawString(3.2*cm, y - 0.15*cm, "Non")
        
        y -= 0.3*cm
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(3.2*cm, y, "(Si oui, l'avis de l'Architecte des Bâtiments de France sera requis)")
        c.setFillColor(colors.black)
        
        # Cadre de fin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.rect(1.5*cm, y - 0.5*cm, self.width - 3*cm, y_start - y - 0.7*cm)
        
        return y - 1*cm
    
    def _draw_cadre_5_documents_joints(self, c, y_start):
        """Cadre 5 : Documents à joindre"""
        y = y_start - 0.5*cm
        
        # Titre cadre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(1.5*cm, y - 0.6*cm, self.width - 3*cm, 0.6*cm, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.45*cm, "5. LISTE DES DOCUMENTS À JOINDRE")
        
        y -= 1*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        
        # Liste des documents (cochés par défaut)
        documents = [
            ("DP1", "Plan de situation du terrain (échelle 1/25000 ou 1/50000)", True),
            ("DP2", "Plan de masse des constructions à édifier ou à modifier (échelle 1/100 à 1/500)", True),
            ("DP3", "Plan en coupe du terrain et de la construction", True),
            ("DP4", "Plan des façades et des toitures - État actuel", True),
            ("DP5", "Plan des façades et des toitures - État projeté (avec panneaux PV)", True),
            ("DP6", "Document graphique - Insertion paysagère (photo-montage)", True),
            ("DP7", "Photographie situant le terrain dans l'environnement proche", True),
            ("DP8", "Photographie situant le terrain dans l'environnement lointain", True),
            ("", "Notice décrivant le projet (facultatif)", False),
        ]
        
        for code, label, checked in documents:
            self._checkbox(c, 2*cm, y, checked)
            c.setFont("Helvetica-Bold", 8)
            if code:
                c.drawString(2.7*cm, y - 0.15*cm, code)
                c.setFont("Helvetica", 8)
                c.drawString(3.5*cm, y - 0.15*cm, f"- {label}")
            else:
                c.setFont("Helvetica", 8)
                c.drawString(2.7*cm, y - 0.15*cm, label)
            y -= 0.5*cm
        
        # Note importante
        y -= 0.3*cm
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#DC3545'))
        c.drawString(2*cm, y, "IMPORTANT :")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        y -= 0.4*cm
        c.drawString(2*cm, y, "Le dossier doit être déposé en 4 exemplaires à la mairie du lieu du terrain.")
        y -= 0.4*cm
        c.drawString(2*cm, y, "Délai d'instruction : 1 mois (peut être porté à 2 mois si zone protégée ou consultation ABF).")
        
        # Cadre de fin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.rect(1.5*cm, y - 0.5*cm, self.width - 3*cm, y_start - y - 0.7*cm)
        
        return y - 1*cm
    
    # ========== PAGE 3 : ENGAGEMENT ==========
    
    def _draw_page_3_engagement(self, c):
        """Page 3 : Engagement du demandeur"""
        
        # En-tête
        y = self._draw_cerfa_header(c, page=3)
        
        # CADRE 6 : ENGAGEMENT
        y = self._draw_cadre_6_engagement(c, y)
        
        # CADRE 7 : SIGNATURE
        y = self._draw_cadre_7_signature(c, y)
        
        # Pied de page
        self._draw_footer(c, page=3)
    
    def _draw_cadre_6_engagement(self, c, y_start):
        """Cadre 6 : Engagement du demandeur"""
        y = y_start - 0.5*cm
        
        # Titre cadre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(1.5*cm, y - 0.6*cm, self.width - 3*cm, 0.6*cm, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.45*cm, "6. ENGAGEMENT DU DEMANDEUR")
        
        y -= 1.2*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        
        # Texte d'engagement
        engagement_text = [
            "Je, soussigné(e), déclare :",
            "",
            "• Que les renseignements fournis dans la présente déclaration sont exacts ;",
            "",
            "• Avoir qualité pour déposer cette déclaration préalable en tant que propriétaire du terrain",
            "  ou mandataire du propriétaire ;",
            "",
            "• Connaître et accepter les obligations suivantes :",
            "  - Respecter les règles du Plan Local d'Urbanisme (PLU) en vigueur ;",
            "  - Ne pas commencer les travaux avant l'obtention de la décision de non-opposition ;",
            "  - Afficher sur le terrain, de façon visible depuis la voie publique, l'autorisation",
            "    d'urbanisme pendant toute la durée du chantier ;",
            "  - Signaler l'ouverture du chantier en mairie ;",
            "  - Respecter les normes de construction en vigueur (NF C 15-100, NF C 15-712) ;",
            "",
            "• Certifier que l'installation sera conforme aux règles techniques de raccordement",
            "  définies par le gestionnaire de réseau (Enedis ou ELD) ;",
            "",
            "• M'engager à faire réaliser les travaux par une entreprise qualifiée RGE",
            "  (Reconnu Garant de l'Environnement) pour bénéficier des aides publiques.",
        ]
        
        for line in engagement_text:
            c.drawString(2*cm, y, line)
            y -= 0.4*cm
        
        # Cadre de fin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.rect(1.5*cm, y - 0.3*cm, self.width - 3*cm, y_start - y - 0.5*cm)
        
        return y - 0.8*cm
    
    def _draw_cadre_7_signature(self, c, y_start):
        """Cadre 7 : Signature"""
        y = y_start - 0.5*cm
        
        # Titre cadre
        c.setFillColor(colors.HexColor('#003366'))
        c.rect(1.5*cm, y - 0.6*cm, self.width - 3*cm, 0.6*cm, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y - 0.45*cm, "7. SIGNATURE")
        
        y -= 1.2*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        # Date et lieu
        commune = self.data.get('commune', '..................')
        date_str = datetime.now().strftime('%d/%m/%Y')
        
        c.drawString(2*cm, y, f"Fait à {commune}, le {date_str}")
        
        # Signature
        y -= 1.5*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, "Signature du demandeur (précédée de la mention « Lu et approuvé ») :")
        
        # Cadre signature
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(2*cm, y - 3*cm, 6*cm, 2.5*cm)
        
        # Cadre de fin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.rect(1.5*cm, y - 3.5*cm, self.width - 3*cm, y_start - y + 3*cm)
        
        return y - 4*cm
    
    # ========== PAGE 4 : NOTICE ==========
    
    def _draw_page_4_notice(self, c):
        """Page 4 : Notice explicative"""
        
        # En-tête
        y = self._draw_cerfa_header(c, page=4)
        
        # Titre
        y -= 0.8*cm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#003366'))
        c.drawString(2*cm, y, "NOTICE EXPLICATIVE - INSTALLATION PHOTOVOLTAÏQUE")
        
        y -= 0.8*cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        
        # Contenu notice
        notice_sections = [
            {
                'titre': "1. PRÉSENTATION DU PROJET",
                'contenu': [
                    f"Le projet consiste en l'installation d'une centrale photovoltaïque d'une puissance de",
                    f"{self._get_puissance():.2f} kWc sur {self.data.get('type', 'toiture')}.",
                    "",
                    "Les panneaux photovoltaïques convertissent l'énergie solaire en électricité, permettant",
                    "une production d'énergie propre et renouvelable.",
                ]
            },
            {
                'titre': "2. INTÉGRATION ARCHITECTURALE",
                'contenu': [
                    "Les modules sont de couleur sombre (bleu ou noir) pour une intégration discrète.",
                    "La pose en surimposition préserve l'étanchéité et la structure du bâtiment.",
                    "Aucune modification de la façade ou de la charpente n'est prévue.",
                ]
            },
            {
                'titre': "3. IMPACT ENVIRONNEMENTAL",
                'contenu': [
                    "✓ Réduction des émissions de CO2",
                    "✓ Production d'électricité verte et locale",
                    "✓ Pas de nuisance sonore (installation silencieuse)",
                    "✓ Recyclage des panneaux en fin de vie (25-30 ans)",
                ]
            },
            {
                'titre': "4. CONFORMITÉ RÉGLEMENTAIRE",
                'contenu': [
                    "✓ Conformité PLU (Plan Local d'Urbanisme)",
                    "✓ Norme NF C 15-100 (installations électriques)",
                    "✓ Norme NF C 15-712 (installations photovoltaïques)",
                    "✓ Attestation Consuel avant mise en service",
                ]
            },
        ]
        
        for section in notice_sections:
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor('#0066CC'))
            c.drawString(2*cm, y, section['titre'])
            c.setFillColor(colors.black)
            
            y -= 0.6*cm
            c.setFont("Helvetica", 8)
            
            for line in section['contenu']:
                c.drawString(2.5*cm, y, line)
                y -= 0.35*cm
            
            y -= 0.4*cm
        
        # Pied de page
        self._draw_footer(c, page=4)
    
    # ========== PLANS DP1, DP2, DP3 ==========
    
    def generate_plan_situation(self):
        """Génère le plan DP1 : Plan de situation (échelle 1/25000 ou 1/50000)"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche
        self._draw_cartouche_plan(c, "DP1 - PLAN DE SITUATION")
        
        # Récupérer coordonnées
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if lat and lon:
            # Carte IGN ou OpenStreetMap (zoom large)
            carte_buffer = self._fetch_map_image(lat, lon, zoom=13, width=600, height=600)
            
            if carte_buffer:
                # Insérer carte
                img = ImageReader(carte_buffer)
                c.drawImage(img, 1.5*cm, self.height - 20*cm, width=18*cm, height=15*cm, preserveAspectRatio=True)
                
                # Marqueur emplacement projet
                center_x = 1.5*cm + 9*cm
                center_y = self.height - 20*cm + 7.5*cm
                
                c.setStrokeColor(colors.HexColor('#FF0000'))
                c.setFillColor(colors.HexColor('#FF0000'))
                c.setLineWidth(3)
                
                # Cercle rouge
                c.circle(center_x, center_y, 0.5*cm, fill=0, stroke=1)
                
                # Croix centrale
                c.line(center_x - 0.7*cm, center_y, center_x + 0.7*cm, center_y)
                c.line(center_x, center_y - 0.7*cm, center_x, center_y + 0.7*cm)
                
                # Label
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(colors.white)
                c.rect(center_x - 1.5*cm, center_y + 0.8*cm, 3*cm, 0.5*cm, fill=1, stroke=1)
                c.setFillColor(colors.HexColor('#FF0000'))
                c.drawCentredString(center_x, center_y + 1*cm, "PROJET PV")
        else:
            # Carte générique si pas de coordonnées
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.HexColor('#666666'))
            c.drawCentredString(self.width/2, self.height - 10*cm, "PLAN DE SITUATION")
            c.setFont("Helvetica", 10)
            c.drawCentredString(self.width/2, self.height - 11*cm, "À compléter avec extrait IGN au 1/25000")
        
        # Échelle
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(2*cm, self.height - 21*cm, "Échelle : 1/25000")
        
        # Coordonnées GPS
        if lat and lon:
            c.setFont("Helvetica", 8)
            c.drawString(2*cm, self.height - 22*cm, f"Coordonnées GPS : {lat:.6f}, {lon:.6f}")
        
        # Commune et département
        commune = self.data.get('commune', '')
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, self.height - 23*cm, f"Commune : {commune}")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_plan_masse(self):
        """Génère le plan DP2 : Plan de masse coté (échelle 1/100 à 1/500)"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche
        self._draw_cartouche_plan(c, "DP2 - PLAN DE MASSE COTÉ")
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if lat and lon:
            # Carte satellite zoom proche
            carte_buffer = self._fetch_satellite_image(lat, lon, zoom=18, width=800, height=800)
            
            if carte_buffer:
                # Insérer carte satellite
                img = ImageReader(carte_buffer)
                c.drawImage(img, 1.5*cm, self.height - 20*cm, width=18*cm, height=15*cm, preserveAspectRatio=True)
                
                # Position centrale de l'image
                img_center_x = 1.5*cm + 9*cm
                img_center_y = self.height - 20*cm + 7.5*cm
                
                # NOUVEAU: Dessiner les délimitations cadastrales réelles
                if self.cadastre_data and self.cadastre_data.get('geometry'):
                    self._draw_parcelle_cadastrale(c, img_center_x, img_center_y, lat, lon, zoom=18)
                else:
                    # Fallback: rectangle générique
                    parcelle_w = 6*cm
                    parcelle_h = 5*cm
                    
                    c.setStrokeColor(colors.HexColor('#FF00FF'))
                    c.setLineWidth(2)
                    c.setDash(6, 3)
                    c.rect(img_center_x - parcelle_w/2, img_center_y - parcelle_h/2, parcelle_w, parcelle_h, fill=0, stroke=1)
                    c.setDash()
                
                # Bâtiment (toujours affiché)
                longueur = self.data.get('longueur_batiment_m', 15)
                largeur = self.data.get('largeur_batiment_m', 10)
                echelle_plan = 0.3  # 0.3cm = 1m (échelle 1/333)
                
                bat_w = longueur * echelle_plan
                bat_h = largeur * echelle_plan
                
                c.setStrokeColor(colors.black)
                c.setFillColor(colors.HexColor('#FFA500'))
                c.setLineWidth(2)
                c.setDash()
                c.rect(img_center_x - bat_w/2, img_center_y - bat_h/2, bat_w, bat_h, fill=1, stroke=1)
                
                # Cotations
                c.setStrokeColor(colors.HexColor('#D32F2F'))
                c.setFillColor(colors.HexColor('#D32F2F'))
                c.setFont("Helvetica-Bold", 8)
                
                # Longueur
                cote_y = img_center_y - bat_h/2 - 0.5*cm
                c.line(img_center_x - bat_w/2, cote_y, img_center_x + bat_w/2, cote_y)
                c.drawCentredString(img_center_x, cote_y - 0.3*cm, f"{longueur:.1f} m")
                
                # Largeur
                cote_x = img_center_x + bat_w/2 + 0.5*cm
                c.saveState()
                c.translate(cote_x, img_center_y)
                c.rotate(90)
                c.drawCentredString(0, -0.2*cm, f"{largeur:.1f} m")
                c.restoreState()
                
                # Info cadastre: afficher TOUTES les parcelles du prospect
                parcelles = self._extract_parcelles()
                if parcelles and len(parcelles) > 0:
                    c.setFillColor(colors.HexColor('#00C851'))
                    c.setFont("Helvetica-Bold", 7)
                    
                    # Construire texte avec toutes les parcelles
                    parcelles_str = ", ".join([f"{p.get('section', '')}{p.get('numero', '')}" for p in parcelles if p.get('section') or p.get('numero')])
                    if parcelles_str:
                        c.drawString(1.5*cm, self.height - 20.5*cm, f"✓ Parcelle(s) cadastrale(s): {parcelles_str}")
                    
                    c.setFillColor(colors.black)
                elif self.cadastre_data and self.cadastre_data.get('success'):
                    # Fallback API IGN
                    c.setFillColor(colors.HexColor('#FF9800'))
                    c.setFont("Helvetica-Bold", 7)
                    section = self.cadastre_data.get('section', '')
                    numero = self.cadastre_data.get('numero', '')
                    c.drawString(1.5*cm, self.height - 20.5*cm, f"✓ Parcelle cadastrale: {section}{numero} (API IGN)")
                    c.setFillColor(colors.black)
        else:
            # Plan générique
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.HexColor('#666666'))
            c.drawCentredString(self.width/2, self.height - 10*cm, "PLAN DE MASSE")
            c.setFont("Helvetica", 10)
            c.drawCentredString(self.width/2, self.height - 11*cm, "À compléter avec plan cadastral + implantation")
        
        # Échelle
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(2*cm, self.height - 21*cm, "Échelle : 1/200")
        
        # Légende
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, self.height - 23*cm, "LÉGENDE :")
        c.setFont("Helvetica", 8)
        
        # Bâtiment
        c.setFillColor(colors.HexColor('#FFA500'))
        c.rect(2*cm, self.height - 24*cm, 0.6*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(2.8*cm, self.height - 23.8*cm, "Bâtiment existant avec panneaux PV")
        
        # Limites parcelle
        c.setStrokeColor(colors.HexColor('#FF00FF'))
        c.setLineWidth(2)
        c.setDash(6, 3)
        c.line(2*cm, self.height - 24.8*cm, 2.6*cm, self.height - 24.8*cm)
        c.setDash()
        c.setFillColor(colors.black)
        c.drawString(2.8*cm, self.height - 24.9*cm, "Limites de propriété (cadastre)")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_plan_coupe(self):
        """Génère le plan DP3 : Plan en coupe du terrain et de la construction"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche
        self._draw_cartouche_plan(c, "DP3 - PLAN EN COUPE DU TERRAIN")
        
        # Titre
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, self.height - 3*cm, "COUPE TRANSVERSALE AA' - ÉTAT PROJETÉ")
        
        # Coupe détaillée (version étendue de celle dans DP5)
        self._draw_coupe_transversale(c,
                                     x=1.5*cm,
                                     y=self.height - 18*cm,
                                     width=18*cm,
                                     height=12*cm,
                                     avec_panneaux=True,
                                     titre="")
        
        # Annotations complémentaires
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#0066CC'))
        c.drawString(2*cm, self.height - 20*cm, "CARACTÉRISTIQUES :")
        
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        
        hauteur_totale = (self.data.get('hauteur_murs_m', 3) or 3) + (self.data.get('hauteur_faitage_m', 2.5) or 2.5)
        hauteur_avec_pv = hauteur_totale + 0.15
        
        infos = [
            f"• Hauteur bâtiment actuelle : {hauteur_totale:.2f} m",
            f"• Hauteur avec panneaux PV : {hauteur_avec_pv:.2f} m",
            f"• Surélévation : 0.15 m (surimposition)",
            f"• Pente toiture : {self.data.get('pente_toiture_deg', 30)}°",
            f"• Type de pose : Surimposition sur rails aluminium",
            f"• Aucune modification de la structure existante",
        ]
        
        y_info = self.height - 21*cm
        for info in infos:
            c.drawString(2.5*cm, y_info, info)
            y_info -= 0.4*cm
        
        c.save()
        buffer.seek(0)
        return buffer
    
    # ========== PLANS DP4 / DP5 ==========
    
    def generate_plan_facades_actuel(self):
        """Génère le plan DP4 : Façades et toitures - État actuel"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche plan
        self._draw_cartouche_plan(c, "DP4 - FACADES ET TOITURES - ÉTAT ACTUEL")
        
        # Plan de masse avec vue satellite (si coordonnées GPS disponibles)
        if self.data.get('latitude') and self.data.get('longitude'):
            self._draw_plan_masse_satellite(c, 
                                            x=1.5*cm, 
                                            y=self.height - 8*cm,
                                            width=8*cm,
                                            height=6*cm,
                                            avec_panneaux=False,
                                            titre="Plan de masse - Vue aérienne")
        
        # Vue de face (façade sud ou principale)
        self._draw_facade_batiment_realiste(c, 
                                   x=1.5*cm, 
                                   y=self.height - 16*cm, 
                                   width=8*cm, 
                                   height=6*cm,
                                   avec_panneaux=False,
                                   titre="Vue de face - État actuel")
        
        # Vue toiture (perspective axonométrique réaliste)
        self._draw_toiture_batiment_realiste(c,
                                    x=10.5*cm,
                                    y=self.height - 16*cm,
                                    width=8*cm,
                                    height=6*cm,
                                    avec_panneaux=False,
                                    titre="Vue toiture - État actuel")
        
        # Coupe transversale
        self._draw_coupe_transversale(c,
                                     x=1.5*cm,
                                     y=self.height - 24*cm,
                                     width=17*cm,
                                     height=5*cm,
                                     avec_panneaux=False,
                                     titre="Coupe transversale - État actuel")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_plan_facades_projet(self):
        """Génère le plan DP5 : Façades et toitures - État projeté (avec panneaux)"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche plan
        self._draw_cartouche_plan(c, "DP5 - FACADES ET TOITURES - ÉTAT PROJETÉ")
        
        # Plan de masse avec vue satellite et panneaux
        if self.data.get('latitude') and self.data.get('longitude'):
            self._draw_plan_masse_satellite(c, 
                                            x=1.5*cm, 
                                            y=self.height - 8*cm,
                                            width=8*cm,
                                            height=6*cm,
                                            avec_panneaux=True,
                                            titre="Plan de masse - Vue aérienne avec panneaux PV")
        
        # Vue de face avec panneaux
        self._draw_facade_batiment_realiste(c, 
                                   x=1.5*cm, 
                                   y=self.height - 16*cm, 
                                   width=8*cm, 
                                   height=6*cm,
                                   avec_panneaux=True,
                                   titre="Vue de face - État projeté (avec panneaux PV)")
        
        # Vue toiture avec panneaux
        self._draw_toiture_batiment_realiste(c,
                                    x=10.5*cm,
                                    y=self.height - 16*cm,
                                    width=8*cm,
                                    height=6*cm,
                                    avec_panneaux=True,
                                    titre="Vue toiture - État projeté (avec panneaux PV)")
        
        # Coupe transversale avec panneaux
        self._draw_coupe_transversale(c,
                                     x=1.5*cm,
                                     y=self.height - 24*cm,
                                     width=17*cm,
                                     height=5*cm,
                                     avec_panneaux=True,
                                     titre="Coupe transversale - État projeté (avec panneaux PV)")
        
        # Légende enrichie
        self._draw_legende_panneaux_enrichie(c, x=1.5*cm, y=3.5*cm)
        
        # Tableau surfaces et conformité
        self._draw_tableau_conformite(c, x=11*cm, y=3.5*cm)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    
    def _draw_plan_masse_satellite(self, c, x, y, width, height, avec_panneaux=False, titre=""):
        """Dessine un plan de masse avec vue satellite stylisée"""
        
        # Titre
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y + height + 0.3*cm, titre)
        
        # Cadre principal
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(x, y, width, height)
        
        # Fond satellite (dégradé vert - simule vue aérienne)
        c.setFillColor(colors.HexColor('#C8E6C9'))  # Vert clair
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # Bâtiment au centre (vue du dessus)
        longueur = self.data.get('longueur_batiment_m', 15)
        largeur = self.data.get('largeur_batiment_m', 10)
        
        # Échelle : adapter au cadre (avec marges)
        echelle = min((width * 0.6) / longueur, (height * 0.6) / largeur)
        
        bat_w = longueur * echelle
        bat_h = largeur * echelle
        bat_x = x + (width - bat_w) / 2
        bat_y = y + (height - bat_h) / 2
        
        # Orientation (rotation selon orientation toiture)
        orientation = self.data.get('orientation_toiture', 'sud')
        rotation_angle = {'sud': 0, 'nord': 180, 'est': 90, 'ouest': -90}.get(orientation.lower(), 0)
        
        # Ombre portée (effet 3D)
        c.setFillColor(colors.HexColor('#BDBDBD'))
        offset_ombre = 0.15*cm
        c.rect(bat_x + offset_ombre, bat_y - offset_ombre, bat_w, bat_h, fill=1, stroke=0)
        
        # Bâtiment
        if avec_panneaux:
            c.setFillColor(colors.HexColor('#1A237E'))  # Bleu foncé (panneaux)
        else:
            c.setFillColor(colors.HexColor('#8D6E63'))  # Brun (toiture tuiles)
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(bat_x, bat_y, bat_w, bat_h, fill=1, stroke=1)
        
        # Si panneaux : grille modules
        if avec_panneaux:
            c.setStrokeColor(colors.HexColor('#0D47A1'))
            c.setLineWidth(0.8)
            
            # Lignes horizontales (rangées)
            for i in range(1, 6):
                y_ligne = bat_y + bat_h * i / 6
                c.line(bat_x, y_ligne, bat_x + bat_w, y_ligne)
            
            # Lignes verticales (colonnes)
            for i in range(1, 8):
                x_ligne = bat_x + bat_w * i / 8
                c.line(x_ligne, bat_y, x_ligne, bat_y + bat_h)
        
        # Indication Nord (flèche)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
        c.setLineWidth(1.5)
        
        nord_x = x + width - 1*cm
        nord_y = y + height - 1*cm
        
        # Flèche nord
        c.line(nord_x, nord_y, nord_x, nord_y - 1*cm)
        # Pointe flèche
        fleche_path = c.beginPath()
        fleche_path.moveTo(nord_x, nord_y - 1*cm)
        fleche_path.lineTo(nord_x - 0.15*cm, nord_y - 0.8*cm)
        fleche_path.lineTo(nord_x + 0.15*cm, nord_y - 0.8*cm)
        fleche_path.close()
        c.drawPath(fleche_path, fill=1, stroke=1)
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(nord_x - 0.2*cm, nord_y - 1.4*cm, "N")
        
        # Échelle graphique
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        echelle_x = x + 0.5*cm
        echelle_y = y + 0.5*cm
        echelle_longueur = 2*cm  # Représente 10m
        
        c.line(echelle_x, echelle_y, echelle_x + echelle_longueur, echelle_y)
        c.line(echelle_x, echelle_y - 0.1*cm, echelle_x, echelle_y + 0.1*cm)
        c.line(echelle_x + echelle_longueur, echelle_y - 0.1*cm, echelle_x + echelle_longueur, echelle_y + 0.1*cm)
        
        c.setFont("Helvetica", 7)
        c.drawString(echelle_x + echelle_longueur/2 - 0.3*cm, echelle_y + 0.25*cm, "10 m")
        
        # Dimensions bâtiment
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#D32F2F'))
        
        # Longueur (en bas)
        c.drawString(bat_x + bat_w/2 - 0.5*cm, bat_y - 0.4*cm, f"{longueur:.1f} m")
        
        # Largeur (à droite)
        c.saveState()
        c.translate(bat_x + bat_w + 0.3*cm, bat_y + bat_h/2)
        c.rotate(90)
        c.drawString(0, 0, f"{largeur:.1f} m")
        c.restoreState()
        
        # Surface panneaux (si avec panneaux)
        if avec_panneaux:
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8)
            surface_pv = self._get_surface_panneaux()
            c.drawString(bat_x + bat_w/2 - 1*cm, bat_y + bat_h/2 - 0.15*cm, f"PV: {surface_pv:.1f} m²")
    
    def _draw_facade_batiment_realiste(self, c, x, y, width, height, avec_panneaux=False, titre=""):
        """Dessine une vue de façade réaliste du bâtiment avec détails architecturaux"""
        
        # Titre
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y + height + 0.3*cm, titre)
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(x, y, width, height)
        
        # Ciel (fond dégradé bleu)
        c.setFillColor(colors.HexColor('#E3F2FD'))
        c.rect(x, y + height*0.6, width, height*0.4, fill=1, stroke=0)
        
        # Sol/terrain
        c.setFillColor(colors.HexColor('#A5D6A7'))
        c.rect(x, y, width, height*0.05, fill=1, stroke=0)
        
        # Bâtiment - Murs
        mur_height = height * 0.55
        mur_width = width * 0.75
        mur_x = x + (width - mur_width) / 2
        mur_y = y + height * 0.05
        
        # Ombre bâtiment
        c.setFillColor(colors.HexColor('#BDBDBD'))
        c.rect(mur_x - 0.1*cm, mur_y, 0.1*cm, mur_height, fill=1, stroke=0)
        
        # Murs (texture crépi)
        c.setFillColor(colors.HexColor('#FFF8DC'))  # Blanc cassé
        c.setStrokeColor(colors.HexColor('#8D6E63'))
        c.setLineWidth(1.5)
        c.rect(mur_x, mur_y, mur_width, mur_height, fill=1, stroke=1)
        
        # Soubassement (pierres)
        c.setFillColor(colors.HexColor('#A1887F'))
        soubassement_h = mur_height * 0.15
        c.rect(mur_x, mur_y, mur_width, soubassement_h, fill=1, stroke=1)
        
        # Texture pierres (lignes horizontales)
        c.setStrokeColor(colors.HexColor('#6D4C41'))
        c.setLineWidth(0.3)
        for i in range(3):
            y_pierre = mur_y + soubassement_h * i / 3
            c.line(mur_x, y_pierre, mur_x + mur_width, y_pierre)
        
        # Toiture - Pan incliné
        toit_base_y = mur_y + mur_height
        toit_sommet_y = toit_base_y + height * 0.35
        pente_toiture = self.data.get('pente_toiture_deg', 30)
        
        # Calculer largeur débord
        debord = width * 0.05
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        
        # Pan de toit (tuiles)
        toit_path = c.beginPath()
        toit_path.moveTo(mur_x - debord, toit_base_y)  # Bas gauche
        toit_path.lineTo(mur_x + mur_width/2, toit_sommet_y)  # Sommet
        toit_path.lineTo(mur_x + mur_width + debord, toit_base_y)  # Bas droit
        toit_path.close()
        
        if avec_panneaux:
            # Toiture avec panneaux : dégradé bleu foncé
            c.setFillColor(colors.HexColor('#263238'))
        else:
            # Toiture tuiles : terre cuite
            c.setFillColor(colors.HexColor('#A0522D'))
        
        c.drawPath(toit_path, fill=1, stroke=1)
        
        # Texture tuiles (si sans panneaux)
        if not avec_panneaux:
            c.setStrokeColor(colors.HexColor('#8B4513'))
            c.setLineWidth(0.4)
            nb_lignes_tuiles = 15
            for i in range(nb_lignes_tuiles):
                progress = i / nb_lignes_tuiles
                y_tuile = toit_base_y + (toit_sommet_y - toit_base_y) * progress
                x_left = mur_x - debord + (mur_width/2 + debord) * progress
                x_right = mur_x + mur_width + debord - (mur_width/2 + debord) * progress
                c.line(x_left, y_tuile, x_right, y_tuile)
        
        # Panneaux PV (si état projeté)
        if avec_panneaux:
            self._draw_panneaux_sur_toit_facade_realiste(c, mur_x, mur_width, 
                                                         toit_base_y, toit_sommet_y, debord)
        
        # Faîtage (arête)
        c.setStrokeColor(colors.HexColor('#5D4037'))
        c.setLineWidth(2.5)
        c.line(mur_x + mur_width/2 - 0.3*cm, toit_sommet_y, 
               mur_x + mur_width/2 + 0.3*cm, toit_sommet_y)
        
        # Fenêtres (avec reflets)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        fenetre_w = mur_width * 0.15
        fenetre_h = mur_height * 0.25
        fenetre_y = mur_y + mur_height * 0.4
        
        # 2 fenêtres
        for i, pos in enumerate([0.2, 0.65]):
            fenetre_x = mur_x + mur_width * pos
            
            # Encadrement fenêtre
            c.setFillColor(colors.HexColor('#FFFFFF'))
            c.rect(fenetre_x, fenetre_y, fenetre_w, fenetre_h, fill=1, stroke=1)
            
            # Vitre (bleu reflet ciel)
            c.setFillColor(colors.HexColor('#B3E5FC'))
            c.rect(fenetre_x + 0.05*cm, fenetre_y + 0.05*cm, 
                   fenetre_w - 0.1*cm, fenetre_h - 0.1*cm, fill=1, stroke=1)
            
            # Croisillons
            c.setStrokeColor(colors.white)
            c.setLineWidth(0.5)
            c.line(fenetre_x + fenetre_w/2, fenetre_y, fenetre_x + fenetre_w/2, fenetre_y + fenetre_h)
            c.line(fenetre_x, fenetre_y + fenetre_h/2, fenetre_x + fenetre_w, fenetre_y + fenetre_h/2)
            
            # Volet (à côté)
            c.setFillColor(colors.HexColor('#5D4037'))
            c.rect(fenetre_x - fenetre_w*0.25, fenetre_y, fenetre_w*0.2, fenetre_h, fill=1, stroke=1)
            
            # Lames volet
            c.setStrokeColor(colors.HexColor('#3E2723'))
            c.setLineWidth(0.3)
            for j in range(10):
                y_lame = fenetre_y + fenetre_h * j / 10
                c.line(fenetre_x - fenetre_w*0.25, y_lame, 
                       fenetre_x - fenetre_w*0.05, y_lame)
        
        # Porte d'entrée
        porte_w = mur_width * 0.18
        porte_h = mur_height * 0.45
        porte_x = mur_x + mur_width * 0.42
        porte_y = mur_y
        
        # Encadrement porte
        c.setFillColor(colors.HexColor('#EEEEEE'))
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(porte_x - 0.1*cm, porte_y, porte_w + 0.2*cm, porte_h + 0.1*cm, fill=1, stroke=1)
        
        # Porte
        c.setFillColor(colors.HexColor('#795548'))
        c.rect(porte_x, porte_y, porte_w, porte_h, fill=1, stroke=1)
        
        # Panneau décoratif porte
        c.setStrokeColor(colors.HexColor('#5D4037'))
        c.setLineWidth(0.8)
        c.rect(porte_x + porte_w*0.1, porte_y + porte_h*0.55, 
               porte_w*0.8, porte_h*0.4, fill=0, stroke=1)
        
        # Poignée
        c.setFillColor(colors.HexColor('#FFD700'))
        c.circle(porte_x + porte_w*0.75, porte_y + porte_h*0.5, 0.08*cm, fill=1, stroke=1)
        
        # Cheminée (si applicable)
        c.setFillColor(colors.HexColor('#8D6E63'))
        cheminee_w = width * 0.08
        cheminee_h = height * 0.15
        cheminee_x = mur_x + mur_width * 0.7
        cheminee_y = toit_base_y + (toit_sommet_y - toit_base_y) * 0.4
        c.rect(cheminee_x, cheminee_y, cheminee_w, cheminee_h, fill=1, stroke=1)
        
        # Couronnement cheminée
        c.setFillColor(colors.HexColor('#6D4C41'))
        c.rect(cheminee_x - 0.05*cm, cheminee_y + cheminee_h, 
               cheminee_w + 0.1*cm, 0.15*cm, fill=1, stroke=1)
    
    def _draw_panneaux_sur_toit_facade_realiste(self, c, mur_x, mur_width, toit_base_y, toit_sommet_y, debord):
        """Dessine les panneaux PV avec effet réaliste (reflets, ombres)"""
        
        # Zone panneaux (70% du pan sud)
        c.setFillColor(colors.HexColor('#1A237E'))  # Bleu très foncé
        c.setStrokeColor(colors.HexColor('#0D47A1'))
        c.setLineWidth(1.5)
        
        # Pan droit (sud supposé)
        panneaux_path = c.beginPath()
        panneaux_path.moveTo(mur_x + mur_width/2 + 0.2*cm, toit_sommet_y - 0.5*cm)
        panneaux_path.lineTo(mur_x + mur_width + debord - 0.3*cm, toit_base_y + 0.3*cm)
        panneaux_path.lineTo(mur_x + mur_width*0.7, toit_base_y + 0.3*cm)
        panneaux_path.lineTo(mur_x + mur_width/2 + 0.2*cm, toit_sommet_y - 1.2*cm)
        panneaux_path.close()
        c.drawPath(panneaux_path, fill=1, stroke=1)
        
        # Grille modules (lignes blanches pour reflets)
        c.setStrokeColor(colors.HexColor('#90CAF9'))  # Bleu clair reflet
        c.setLineWidth(0.8)
        
        # Rangées horizontales (5 rangées)
        for i in range(1, 5):
            progress = i / 5
            y_ligne = toit_base_y + 0.3*cm + (toit_sommet_y - toit_base_y - 1.5*cm) * progress
            x_left = mur_x + mur_width/2 + 0.2*cm + (mur_width*0.2) * (1 - progress)
            x_right = mur_x + mur_width + debord - 0.3*cm - (debord + 0.3*cm) * progress
            c.line(x_left, y_ligne, x_right, y_ligne)
        
        # Colonnes verticales (6 colonnes)
        for i in range(1, 6):
            x_col_bot = mur_x + mur_width*0.7 + (mur_width*0.3 + debord - 0.3*cm) * i / 6
            y_col_bot = toit_base_y + 0.3*cm
            x_col_top = mur_x + mur_width/2 + 0.2*cm + (mur_width*0.2) * i / 6
            y_col_top = toit_sommet_y - 1.2*cm + (0.7*cm) * i / 6
            c.line(x_col_bot, y_col_bot, x_col_top, y_col_top)
        
        # Reflets lumineux (lignes diagonales blanches)
        c.setStrokeColor(colors.HexColor('#FFFFFF'))
        c.setLineWidth(0.5)
        c.setLineCap(1)  # Round cap
        
        for i in range(3):
            x_reflet_start = mur_x + mur_width*0.75 + i*0.4*cm
            y_reflet_start = toit_base_y + 0.8*cm + i*0.3*cm
            c.line(x_reflet_start, y_reflet_start, 
                   x_reflet_start + 0.6*cm, y_reflet_start + 0.4*cm)
    
    def _draw_toiture_batiment_realiste(self, c, x, y, width, height, avec_panneaux=False, titre=""):
        """Dessine une vue 3D réaliste de la toiture en perspective isométrique"""
        
        # Titre
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y + height + 0.3*cm, titre)
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(x, y, width, height)
        
        # Fond ciel
        c.setFillColor(colors.HexColor('#E3F2FD'))
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # Paramètres perspective isométrique
        angle_iso = 30  # Angle isométrique standard
        ratio_iso = 0.866  # cos(30°)
        
        longueur = self.data.get('longueur_batiment_m', 15)
        largeur = self.data.get('largeur_batiment_m', 10)
        hauteur_faitage = self.data.get('hauteur_faitage_m', 2.5) or 2.5
        
        # Échelle
        echelle = min(width * 0.7 / (longueur + largeur * ratio_iso),
                     height * 0.7 / (largeur * ratio_iso + hauteur_faitage))
        
        # Centre de dessin
        center_x = x + width / 2
        center_y = y + height * 0.4
        
        # Coordonnées 3D → 2D isométrique
        def iso_point(dx, dy, dz):
            """Convertit coordonnées 3D en 2D isométrique"""
            iso_x = center_x + (dx - dy * ratio_iso) * echelle
            iso_y = center_y + (dx * ratio_iso + dy + dz * 2) * echelle
            return iso_x, iso_y
        
        # === STRUCTURE TOITURE ===
        
        # Points clés du toit (vue isométrique)
        # Base rectangulaire
        p1 = iso_point(0, 0, 0)  # Avant-gauche bas
        p2 = iso_point(longueur, 0, 0)  # Avant-droit bas
        p3 = iso_point(longueur, largeur, 0)  # Arrière-droit bas
        p4 = iso_point(0, largeur, 0)  # Arrière-gauche bas
        
        # Faîtage (ligne centrale haute)
        p_faitage_avant = iso_point(longueur/2, 0, hauteur_faitage)
        p_faitage_arriere = iso_point(longueur/2, largeur, hauteur_faitage)
        
        # Dessiner les pans de toit
        
        # Pan gauche (visible)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        
        if avec_panneaux:
            c.setFillColor(colors.HexColor('#1565C0'))  # Bleu foncé panneaux
        else:
            c.setFillColor(colors.HexColor('#A0522D'))  # Terre cuite tuiles
        
        pan_gauche = c.beginPath()
        pan_gauche.moveTo(*p1)
        pan_gauche.lineTo(*p_faitage_avant)
        pan_gauche.lineTo(*p_faitage_arriere)
        pan_gauche.lineTo(*p4)
        pan_gauche.close()
        c.drawPath(pan_gauche, fill=1, stroke=1)
        
        # Texture tuiles pan gauche (si sans panneaux)
        if not avec_panneaux:
            c.setStrokeColor(colors.HexColor('#8B4513'))
            c.setLineWidth(0.4)
            for i in range(1, 12):
                pt_start = iso_point(longueur/2 * i/12, 0, hauteur_faitage * (1 - i/12))
                pt_end = iso_point(longueur/2 * i/12, largeur, hauteur_faitage * (1 - i/12))
                c.line(*pt_start, *pt_end)
        
        # Pan droit (visible)
        if avec_panneaux:
            c.setFillColor(colors.HexColor('#0D47A1'))  # Bleu très foncé panneaux
        else:
            c.setFillColor(colors.HexColor('#8B4513'))  # Brun tuiles
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        
        pan_droit = c.beginPath()
        pan_droit.moveTo(*p_faitage_avant)
        pan_droit.lineTo(*p2)
        pan_droit.lineTo(*p3)
        pan_droit.lineTo(*p_faitage_arriere)
        pan_droit.close()
        c.drawPath(pan_droit, fill=1, stroke=1)
        
        # Si panneaux : grille modules sur pan droit
        if avec_panneaux:
            c.setStrokeColor(colors.HexColor('#90CAF9'))  # Bleu clair reflets
            c.setLineWidth(0.8)
            
            # Utiliser les vraies dimensions et orientation du calpinage
            if self.module_orientation == 'paysage':
                # Paysage: module couché (longueur horizontale)
                nb_cols_reel = self.nb_cols  # Colonnes dans sens longueur
                nb_rows_reel = self.nb_rows  # Rangées dans sens largeur
            else:
                # Portrait: module debout (largeur horizontale)
                nb_cols_reel = self.nb_rows  # Inversé
                nb_rows_reel = self.nb_cols  # Inversé
            
            # Rangées (horizontales perspective) - selon orientation réelle
            for i in range(1, nb_rows_reel):
                pt_start = iso_point(longueur/2, i * largeur/nb_rows_reel, 
                                   hauteur_faitage - i * hauteur_faitage/nb_rows_reel)
                pt_end = iso_point(longueur, i * largeur/nb_rows_reel, 0)
                c.line(*pt_start, *pt_end)
            
            # Colonnes (verticales perspective) - selon orientation réelle
            for i in range(1, nb_cols_reel):
                ratio = i / nb_cols_reel
                pt_top = iso_point(longueur/2 + ratio * longueur/2, 0, hauteur_faitage * (1 - ratio))
                pt_bot = iso_point(longueur/2 + ratio * longueur/2, largeur, 0)
                c.line(*pt_top, *pt_bot)
            
            # Reflets lumineux (lignes blanches diagonales)
            c.setStrokeColor(colors.white)
            c.setLineWidth(1)
            c.setLineCap(1)
            
            for i in range(4):
                pt_ref_start = iso_point(longueur*0.65 + i*0.5, largeur*0.3, 0.3)
                pt_ref_end = iso_point(longueur*0.7 + i*0.5, largeur*0.4, 0.5)
                c.line(*pt_ref_start, *pt_ref_end)
        else:
            # Texture tuiles pan droit
            c.setStrokeColor(colors.HexColor('#654321'))
            c.setLineWidth(0.4)
            for i in range(1, 12):
                pt_start = iso_point(longueur/2 + longueur/2 * i/12, 0, hauteur_faitage * (1 - i/12))
                pt_end = iso_point(longueur/2 + longueur/2 * i/12, largeur, 0)
                c.line(*pt_start, *pt_end)
        
        # Faîtage (arête centrale)
        c.setStrokeColor(colors.HexColor('#5D4037'))
        c.setLineWidth(3)
        c.line(*p_faitage_avant, *p_faitage_arriere)
        
        # Cheminée (si applicable)
        cheminee_h = 1.5  # mètres
        cheminee_w = 0.6
        cheminee_x = longueur * 0.65
        cheminee_y = largeur * 0.4
        
        # Base cheminée
        ch_p1 = iso_point(cheminee_x, cheminee_y, hauteur_faitage * 0.6)
        ch_p2 = iso_point(cheminee_x + cheminee_w, cheminee_y, hauteur_faitage * 0.6)
        ch_p3 = iso_point(cheminee_x + cheminee_w, cheminee_y + cheminee_w, hauteur_faitage * 0.6)
        ch_p4 = iso_point(cheminee_x, cheminee_y + cheminee_w, hauteur_faitage * 0.6)
        
        # Top cheminée
        ch_t1 = iso_point(cheminee_x, cheminee_y, hauteur_faitage * 0.6 + cheminee_h)
        ch_t2 = iso_point(cheminee_x + cheminee_w, cheminee_y, hauteur_faitage * 0.6 + cheminee_h)
        ch_t3 = iso_point(cheminee_x + cheminee_w, cheminee_y + cheminee_w, hauteur_faitage * 0.6 + cheminee_h)
        ch_t4 = iso_point(cheminee_x, cheminee_y + cheminee_w, hauteur_faitage * 0.6 + cheminee_h)
        
        # Face avant cheminée
        c.setFillColor(colors.HexColor('#8D6E63'))
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        
        face_avant = c.beginPath()
        face_avant.moveTo(*ch_p2)
        face_avant.lineTo(*ch_t2)
        face_avant.lineTo(*ch_t3)
        face_avant.lineTo(*ch_p3)
        face_avant.close()
        c.drawPath(face_avant, fill=1, stroke=1)
        
        # Face gauche cheminée
        c.setFillColor(colors.HexColor('#6D4C41'))
        face_gauche = c.beginPath()
        face_gauche.moveTo(*ch_p1)
        face_gauche.lineTo(*ch_t1)
        face_gauche.lineTo(*ch_t2)
        face_gauche.lineTo(*ch_p2)
        face_gauche.close()
        c.drawPath(face_gauche, fill=1, stroke=1)
        
        # Couronnement cheminée
        c.setFillColor(colors.HexColor('#5D4037'))
        top_cheminee = c.beginPath()
        top_cheminee.moveTo(*ch_t1)
        top_cheminee.lineTo(*ch_t2)
        top_cheminee.lineTo(*ch_t3)
        top_cheminee.lineTo(*ch_t4)
        top_cheminee.close()
        c.drawPath(top_cheminee, fill=1, stroke=1)
        
        # Annotations dimensions
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor('#D32F2F'))
        
        # Longueur toiture
        c.drawString(center_x + echelle * longueur / 2, center_y - echelle * 2, f"L = {longueur:.1f} m")
        
        # Largeur toiture
        c.drawString(center_x - echelle * largeur * ratio_iso - 1*cm, center_y + echelle * largeur / 2, f"l = {largeur:.1f} m")
        
        # Hauteur faîtage
        c.drawString(center_x - echelle * largeur * ratio_iso / 2 - 1.5*cm, 
                    center_y + echelle * hauteur_faitage * 2, 
                    f"H = {hauteur_faitage:.1f} m")
        
        # Surface panneaux (si avec panneaux)
        if avec_panneaux:
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8)
            surface_pv = self._get_surface_panneaux()
            c.drawString(center_x + echelle * longueur * 0.3, center_y + echelle * 3, f"Surface PV: {surface_pv:.1f} m²")
    
    def _draw_coupe_transversale(self, c, x, y, width, height, avec_panneaux=False, titre=""):
        """Dessine une coupe transversale du bâtiment montrant la structure et les panneaux"""
        
        # Titre
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y + height + 0.3*cm, titre)
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(x, y, width, height)
        
        # Sol/terrain
        c.setFillColor(colors.HexColor('#A5D6A7'))
        c.rect(x, y, width, height * 0.15, fill=1, stroke=0)
        
        # Ligne de sol
        c.setStrokeColor(colors.HexColor('#795548'))
        c.setLineWidth(2)
        c.line(x, y + height * 0.15, x + width, y + height * 0.15)
        
        # Dimensions bâtiment
        largeur_bat = self.data.get('largeur_batiment_m', 10)
        hauteur_mur = self.data.get('hauteur_murs_m', 3) or 3
        hauteur_faitage = self.data.get('hauteur_faitage_m', 2.5) or 2.5
        pente_deg = self.data.get('pente_toiture_deg', 30) or 30
        
        # Échelle
        echelle = min(width * 0.7 / largeur_bat, height * 0.6 / (hauteur_mur + hauteur_faitage))
        
        # Centre
        center_x = x + width / 2
        sol_y = y + height * 0.15
        
        # Murs (coupe)
        mur_w = largeur_bat * echelle
        mur_h = hauteur_mur * echelle
        
        mur_x_gauche = center_x - mur_w / 2
        mur_x_droit = center_x + mur_w / 2
        
        # Mur gauche (coupe - hachures)
        c.setFillColor(colors.HexColor('#FFF8DC'))
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(mur_x_gauche - 0.3*cm, sol_y, 0.3*cm, mur_h, fill=1, stroke=1)
        
        # Hachures mur gauche
        c.setStrokeColor(colors.HexColor('#8D6E63'))
        c.setLineWidth(0.3)
        for i in range(int(mur_h / (0.2*cm))):
            y_hach = sol_y + i * 0.2*cm
            c.line(mur_x_gauche - 0.3*cm, y_hach, mur_x_gauche, y_hach + 0.2*cm)
        
        # Mur droit (coupe - hachures)
        c.setFillColor(colors.HexColor('#FFF8DC'))
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(mur_x_droit, sol_y, 0.3*cm, mur_h, fill=1, stroke=1)
        
        # Hachures mur droit
        c.setStrokeColor(colors.HexColor('#8D6E63'))
        c.setLineWidth(0.3)
        for i in range(int(mur_h / (0.2*cm))):
            y_hach = sol_y + i * 0.2*cm
            c.line(mur_x_droit, y_hach, mur_x_droit + 0.3*cm, y_hach + 0.2*cm)
        
        # Charpente (chevrons)
        faitage_y = sol_y + mur_h + hauteur_faitage * echelle
        faitage_x = center_x
        
        c.setStrokeColor(colors.HexColor('#795548'))
        c.setLineWidth(3)
        
        # Chevron gauche
        c.line(mur_x_gauche, sol_y + mur_h, faitage_x, faitage_y)
        
        # Chevron droit
        c.line(mur_x_droit + 0.3*cm, sol_y + mur_h, faitage_x, faitage_y)
        
        # Panne faîtière
        c.setFillColor(colors.HexColor('#6D4C41'))
        c.circle(faitage_x, faitage_y, 0.15*cm, fill=1, stroke=1)
        
        # Couverture toiture
        debord = 0.5*cm
        
        if avec_panneaux:
            # Toiture avec panneaux
            # Sous-toiture (isolant + tuiles)
            c.setStrokeColor(colors.HexColor('#8B4513'))
            c.setLineWidth(1)
            c.line(mur_x_gauche - debord, sol_y + mur_h, faitage_x, faitage_y)
            c.line(faitage_x, faitage_y, mur_x_droit + 0.3*cm + debord, sol_y + mur_h)
            
            # Panneaux PV en surimposition (côté droit - sud)
            c.setStrokeColor(colors.HexColor('#0D47A1'))
            c.setLineWidth(4)
            c.line(faitage_x, faitage_y + 0.15*cm, mur_x_droit + 0.3*cm + debord, sol_y + mur_h + 0.15*cm)
            
            # Détail fixation (crochets)
            nb_crochets = 4
            for i in range(nb_crochets):
                progress = (i + 1) / (nb_crochets + 1)
                crochet_x = faitage_x + (mur_x_droit + debord - faitage_x) * progress
                crochet_y_base = faitage_y + (sol_y + mur_h - faitage_y) * progress
                crochet_y_panneau = crochet_y_base + 0.15*cm
                
                c.setStrokeColor(colors.HexColor('#757575'))
                c.setLineWidth(1.5)
                c.line(crochet_x, crochet_y_base, crochet_x, crochet_y_panneau)
                c.circle(crochet_x, crochet_y_panneau, 0.08*cm, fill=1, stroke=1)
        else:
            # Toiture simple (tuiles)
            c.setStrokeColor(colors.HexColor('#A0522D'))
            c.setLineWidth(2)
            c.line(mur_x_gauche - debord, sol_y + mur_h, faitage_x, faitage_y)
            c.line(faitage_x, faitage_y, mur_x_droit + 0.3*cm + debord, sol_y + mur_h)
        
        # Annotations cotations
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        c.setLineWidth(0.5)
        
        # Largeur bâtiment
        cote_y = sol_y - 0.5*cm
        c.line(mur_x_gauche, cote_y, mur_x_droit + 0.3*cm, cote_y)
        c.line(mur_x_gauche, cote_y - 0.1*cm, mur_x_gauche, cote_y + 0.1*cm)
        c.line(mur_x_droit + 0.3*cm, cote_y - 0.1*cm, mur_x_droit + 0.3*cm, cote_y + 0.1*cm)
        c.drawString(center_x - 0.5*cm, cote_y - 0.4*cm, f"{largeur_bat:.1f} m")
        
        # Hauteur murs
        cote_x = mur_x_gauche - 0.7*cm
        c.line(cote_x, sol_y, cote_x, sol_y + mur_h)
        c.line(cote_x - 0.1*cm, sol_y, cote_x + 0.1*cm, sol_y)
        c.line(cote_x - 0.1*cm, sol_y + mur_h, cote_x + 0.1*cm, sol_y + mur_h)
        c.drawString(cote_x - 0.6*cm, sol_y + mur_h/2, f"{hauteur_mur:.1f} m")
        
        # Hauteur totale (au faîtage)
        cote_x_total = mur_x_droit + 0.3*cm + debord + 0.7*cm
        c.line(cote_x_total, sol_y, cote_x_total, faitage_y)
        c.line(cote_x_total - 0.1*cm, sol_y, cote_x_total + 0.1*cm, sol_y)
        c.line(cote_x_total - 0.1*cm, faitage_y, cote_x_total + 0.1*cm, faitage_y)
        
        hauteur_totale = hauteur_mur + hauteur_faitage
        c.drawString(cote_x_total + 0.2*cm, sol_y + mur_h + hauteur_faitage * echelle / 2, f"{hauteur_totale:.1f} m")
        
        # Pente toiture
        c.setFillColor(colors.HexColor('#0066CC'))
        c.drawString(center_x + 1*cm, faitage_y - 1*cm, f"Pente: {pente_deg}°")
        
        # Hauteur panneaux (si avec panneaux)
        if avec_panneaux:
            c.setFillColor(colors.HexColor('#1565C0'))
            c.drawString(center_x + 1*cm, faitage_y - 1.5*cm, "Surimposition: ~15 cm")
    
    # ========== PLANS DP6, DP7, DP8 (INSERTION PAYSAGÈRE) ==========
    
    def generate_insertion_paysagere(self):
        """Génère le plan DP6 : Document graphique - Insertion paysagère (photo-montage)"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche
        self._draw_cartouche_plan(c, "DP6 - INSERTION PAYSAGÈRE - PHOTO-MONTAGE")
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        # Photo satellite haute résolution
        if lat and lon:
            photo_buffer = self._fetch_satellite_image(lat, lon, zoom=19, width=1000, height=700)
            
            if photo_buffer:
                # Superposer panneaux PV sur la photo
                photo_montage = self._create_photomontage(photo_buffer)
                
                # Image AVANT
                c.setFont("Helvetica-Bold", 11)
                c.drawString(2*cm, self.height - 3*cm, "ÉTAT ACTUEL (sans panneaux photovoltaïques)")
                
                img_avant = ImageReader(photo_buffer)
                c.drawImage(img_avant, 1.5*cm, self.height - 14*cm, width=18*cm, height=9*cm, preserveAspectRatio=True)
                
                # Image APRÈS
                c.setFont("Helvetica-Bold", 11)
                c.drawString(2*cm, self.height - 15.5*cm, "ÉTAT PROJETÉ (avec panneaux photovoltaïques)")
                
                img_apres = ImageReader(photo_montage)
                c.drawImage(img_apres, 1.5*cm, self.height - 26*cm, width=18*cm, height=9*cm, preserveAspectRatio=True)
                
                # Annotations
                c.setFont("Helvetica", 8)
                c.setFillColor(colors.HexColor('#0066CC'))
                c.drawString(2*cm, self.height - 27*cm, "Note : Les panneaux sont représentés en bleu foncé sur la toiture")
        else:
            # Message si pas de coordonnées
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.HexColor('#666666'))
            c.drawCentredString(self.width/2, self.height - 10*cm, "INSERTION PAYSAGÈRE")
            c.setFont("Helvetica", 10)
            c.drawCentredString(self.width/2, self.height - 11*cm, "Photo-montage à réaliser avec vue réelle du bâtiment")
            c.drawCentredString(self.width/2, self.height - 12*cm, "avant et après installation des panneaux photovoltaïques")
        
        # Caractéristiques visuelles
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(2*cm, 5*cm, "CARACTÉRISTIQUES VISUELLES :")
        
        c.setFont("Helvetica", 8)
        specs_visuelles = [
            "• Modules photovoltaïques : Couleur bleu foncé/noir (intégration discrète)",
            "• Finition : Surface anti-reflet (pas d'éblouissement)",
            "• Cadre aluminium : Anodisé noir",
            "• Pose : En surimposition, parallèle à la pente de toiture",
            "• Impact visuel : Minimal depuis la voie publique",
            "• Réversibilité : Installation démontable sans dommage au bâtiment",
        ]
        
        y_spec = 4.5*cm
        for spec in specs_visuelles:
            c.drawString(2.5*cm, y_spec, spec)
            y_spec -= 0.4*cm
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_photo_environnement_proche(self):
        """Génère le plan DP7 : Photo environnement proche"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche
        self._draw_cartouche_plan(c, "DP7 - PHOTOGRAPHIE - ENVIRONNEMENT PROCHE")
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if lat and lon:
            # Photo satellite zoom moyen (rayon ~100m)
            photo_buffer = self._fetch_satellite_image(lat, lon, zoom=18, width=900, height=900)
            
            if photo_buffer:
                c.setFont("Helvetica-Bold", 11)
                c.drawString(2*cm, self.height - 3*cm, "VUE AÉRIENNE - ENVIRONNEMENT PROCHE (rayon ~100m)")
                
                img = ImageReader(photo_buffer)
                c.drawImage(img, 1.5*cm, self.height - 20*cm, width=18*cm, height=15*cm, preserveAspectRatio=True)
                
                # Marqueur emplacement projet
                center_x = 1.5*cm + 9*cm
                center_y = self.height - 20*cm + 7.5*cm
                
                c.setStrokeColor(colors.HexColor('#FF0000'))
                c.setFillColor(colors.HexColor('#FF0000'))
                c.setLineWidth(2.5)
                c.circle(center_x, center_y, 0.4*cm, fill=0, stroke=1)
                
                c.setFont("Helvetica-Bold", 9)
                c.setFillColor(colors.white)
                c.rect(center_x - 1.2*cm, center_y + 0.6*cm, 2.4*cm, 0.4*cm, fill=1, stroke=1)
                c.setFillColor(colors.HexColor('#FF0000'))
                c.drawCentredString(center_x, center_y + 0.75*cm, "PROJET")
        else:
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.HexColor('#666666'))
            c.drawCentredString(self.width/2, self.height - 10*cm, "ENVIRONNEMENT PROCHE")
            c.setFont("Helvetica", 10)
            c.drawCentredString(self.width/2, self.height - 11*cm, "À compléter avec photo réelle montrant")
            c.drawCentredString(self.width/2, self.height - 12*cm, "le terrain et les constructions voisines")
        
        # Description
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(2*cm, self.height - 22*cm, "DESCRIPTION DE L'ENVIRONNEMENT PROCHE :")
        
        c.setFont("Helvetica", 8)
        commune = self.data.get('commune', 'N/A')
        c.drawString(2*cm, self.height - 23*cm, f"• Commune : {commune}")
        c.drawString(2*cm, self.height - 23.5*cm, "• Zone : Résidentielle / Agricole")
        c.drawString(2*cm, self.height - 24*cm, "• Bâtiments voisins : Habitations individuelles similaires")
        c.drawString(2*cm, self.height - 24.5*cm, "• Voirie : Accès depuis rue résidentielle")
        c.drawString(2*cm, self.height - 25*cm, "• Espaces verts : Jardins privatifs")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_photo_environnement_lointain(self):
        """Génère le plan DP8 : Photo environnement lointain"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Cartouche
        self._draw_cartouche_plan(c, "DP8 - PHOTOGRAPHIE - ENVIRONNEMENT LOINTAIN")
        
        lat = self.data.get('latitude')
        lon = self.data.get('longitude')
        
        if lat and lon:
            # Photo satellite zoom large (rayon ~500m)
            photo_buffer = self._fetch_satellite_image(lat, lon, zoom=16, width=900, height=900)
            
            if photo_buffer:
                c.setFont("Helvetica-Bold", 11)
                c.drawString(2*cm, self.height - 3*cm, "VUE AÉRIENNE - ENVIRONNEMENT LOINTAIN (rayon ~500m)")
                
                img = ImageReader(photo_buffer)
                c.drawImage(img, 1.5*cm, self.height - 20*cm, width=18*cm, height=15*cm, preserveAspectRatio=True)
                
                # Marqueur emplacement projet
                center_x = 1.5*cm + 9*cm
                center_y = self.height - 20*cm + 7.5*cm
                
                c.setStrokeColor(colors.HexColor('#FF0000'))
                c.setFillColor(colors.HexColor('#FF0000'))
                c.setLineWidth(2.5)
                c.circle(center_x, center_y, 0.3*cm, fill=0, stroke=1)
                
                c.setFont("Helvetica-Bold", 8)
                c.setFillColor(colors.white)
                c.rect(center_x - 1*cm, center_y + 0.5*cm, 2*cm, 0.35*cm, fill=1, stroke=1)
                c.setFillColor(colors.HexColor('#FF0000'))
                c.drawCentredString(center_x, center_y + 0.65*cm, "PROJET")
        else:
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(colors.HexColor('#666666'))
            c.drawCentredString(self.width/2, self.height - 10*cm, "ENVIRONNEMENT LOINTAIN")
            c.setFont("Helvetica", 10)
            c.drawCentredString(self.width/2, self.height - 11*cm, "À compléter avec photo réelle montrant")
            c.drawCentredString(self.width/2, self.height - 12*cm, "le paysage et le contexte urbain général")
        
        # Description
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(2*cm, self.height - 22*cm, "DESCRIPTION DE L'ENVIRONNEMENT LOINTAIN :")
        
        c.setFont("Helvetica", 8)
        commune = self.data.get('commune', 'N/A')
        c.drawString(2*cm, self.height - 23*cm, f"• Commune : {commune}")
        c.drawString(2*cm, self.height - 23.5*cm, "• Type de zone : Urbaine / Péri-urbaine / Rurale")
        c.drawString(2*cm, self.height - 24*cm, "• Contexte paysager : Plaine / Collines / Vallée")
        c.drawString(2*cm, self.height - 24.5*cm, "• Patrimoine visible : Aucun monument historique à proximité")
        c.drawString(2*cm, self.height - 25*cm, "• Impact visuel du projet : Très faible (invisible depuis loin)")
        c.drawString(2*cm, self.height - 25.5*cm, "• Intégration paysagère : Bonne (cohérente avec l'habitat existant)")
        
        c.save()
        buffer.seek(0)
        return buffer
    
    # ========== HELPERS IMAGES SATELLITE ==========
    
    def _fetch_map_image(self, lat, lon, zoom=13, width=600, height=600):
        """Récupère une image de carte OpenStreetMap"""
        try:
            # API OpenStreetMap via StaticMap
            url = f"https://staticmap.openstreetmap.de/staticmap.php"
            params = {
                'center': f"{lat},{lon}",
                'zoom': zoom,
                'size': f"{width}x{height}",
                'maptype': 'mapnik',
                'markers': f"{lat},{lon},red"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return io.BytesIO(response.content)
            
        except Exception as e:
            print(f"Erreur fetch_map_image: {e}")
        
        return None
    
    def _fetch_satellite_image(self, lat, lon, zoom=18, width=800, height=800):
        """Récupère une image satellite via API (Google Maps, Mapbox ou OpenStreetMap)"""
        try:
            # Option 1 : Google Maps Static API (nécessite API key)
            # Pour démo, utiliser une alternative gratuite : OpenStreetMap satellite tile
            
            # Calculer tile coordinates
            import math
            lat_rad = math.radians(lat)
            n = 2.0 ** zoom
            x_tile = int((lon + 180.0) / 360.0 * n)
            y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            
            # URL tuile satellite (exemple Esri)
            tile_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y_tile}/{x_tile}"
            
            response = requests.get(tile_url, timeout=10)
            
            if response.status_code == 200:
                # Redimensionner si besoin
                img = PILImage.open(io.BytesIO(response.content))
                img = img.resize((width, height), PILImage.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                return buffer
                
        except Exception as e:
            print(f"Erreur fetch_satellite_image: {e}")
        
        return None
    
    def _create_photomontage(self, photo_buffer):
        """Crée un photo-montage avec panneaux PV superposés"""
        try:
            # Charger l'image
            photo_buffer.seek(0)
            img = PILImage.open(photo_buffer).convert('RGBA')
            width, height = img.size
            
            # Créer overlay panneaux PV (zone centrale)
            overlay = PILImage.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Zone panneaux (60% largeur, 40% hauteur, centré)
            panel_w = int(width * 0.6)
            panel_h = int(height * 0.4)
            panel_x = (width - panel_w) // 2
            panel_y = int(height * 0.3)
            
            # Rectangle bleu foncé semi-transparent (panneaux)
            draw.rectangle(
                [panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                fill=(28, 55, 92, 180)  # Bleu foncé avec alpha=180
            )
            
            # Grille modules (lignes blanches)
            nb_rows = 5
            nb_cols = 7
            
            # Lignes horizontales
            for i in range(1, nb_rows):
                y = panel_y + int(panel_h * i / nb_rows)
                draw.line([(panel_x, y), (panel_x + panel_w, y)], fill=(200, 220, 255, 200), width=2)
            
            # Lignes verticales
            for i in range(1, nb_cols):
                x = panel_x + int(panel_w * i / nb_cols)
                draw.line([(x, panel_y), (x, panel_y + panel_h)], fill=(200, 220, 255, 200), width=2)
            
            # Combiner image originale et overlay
            combined = PILImage.alpha_composite(img, overlay)
            
            # Convertir en RGB pour PDF
            combined = combined.convert('RGB')
            
            buffer = io.BytesIO()
            combined.save(buffer, format='PNG')
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            print(f"Erreur create_photomontage: {e}")
            # Retourner image originale en cas d'erreur
            photo_buffer.seek(0)
            return photo_buffer
    
    def _draw_legende_panneaux_enrichie(self, c, x, y):
        """Dessine une légende enrichie avec détails techniques"""
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "LÉGENDE ET CARACTÉRISTIQUES")
        
        y -= 0.6*cm
        c.setFont("Helvetica", 8)
        
        # Panneau PV
        c.setFillColor(colors.HexColor('#1565C0'))
        c.rect(x, y - 0.3*cm, 1*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Panneaux photovoltaïques (silicium monocristallin)")
        
        y -= 0.6*cm
        
        # Toiture existante
        c.setFillColor(colors.HexColor('#A0522D'))
        c.rect(x, y - 0.3*cm, 1*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Couverture existante (tuiles terre cuite)")
        
        y -= 0.6*cm
        
        # Structure
        c.setFillColor(colors.HexColor('#795548'))
        c.rect(x, y - 0.3*cm, 1*cm, 0.4*cm, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.drawString(x + 1.3*cm, y - 0.15*cm, "Charpente et structure bois")
        
        # Caractéristiques techniques
        y -= 1*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y, "CARACTÉRISTIQUES TECHNIQUES :")
        
        y -= 0.5*cm
        c.setFont("Helvetica", 7.5)
        
        specs = [
            f"• Puissance installée : {self._get_puissance():.2f} kWc",
            f"• Surface panneaux : {self._get_surface_panneaux():.1f} m²",
            f"• Nombre modules estimé : {int(self._get_surface_panneaux() / 2)}",
            f"• Type de pose : Surimposition (GSE, K2, Schletter ou équivalent)",
            f"• Hauteur modules : 150-200 mm au-dessus de la couverture",
            f"• Fixation : Rails aluminium + crochets acier inox sur chevrons",
            f"• Étanchéité : Préservée (pas de percement tuiles)",
            f"• Garantie étanchéité : 10 ans minimum",
            f"• Résistance au vent : Calcul selon NV65 modifiée + Eurocode 1",
            f"• Résistance neige : Selon zone géographique + altitude",
            f"• Conformité électrique : NF C 15-100, NF C 15-712",
            f"• Protection foudre : Parafoudre DC Type 2 + AC Type 2",
        ]
        
        for spec in specs:
            c.drawString(x + 0.3*cm, y, spec)
            y -= 0.35*cm
    
    def _draw_tableau_conformite(self, c, x, y):
        """Dessine un tableau de conformité réglementaire"""
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y + 0.5*cm, "CONFORMITÉ RÉGLEMENTAIRE")
        
        # Tableau
        data = [
            ['Critère', 'Valeur', 'Conformité'],
            ['Emprise au sol', '0 m² (toiture)', '✓ Conforme'],
            ['Surface plancher créée', '0 m²', '✓ Conforme'],
            ['Hauteur max.', f"{self.data.get('hauteur_batiment_m', 0) + 0.15:.2f} m", '✓ Conforme PLU'],
            ['Aspect extérieur', 'Modules sombres', '✓ Intégration'],
            ['Distance limites', 'Pas de modification', '✓ Conforme'],
        ]
        
        table = Table(data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#E3F2FD')])
        ]))
        
        table.wrapOn(c, 10*cm, 10*cm)
        table.drawOn(c, x, y - 3*cm)
    
    
    def _fetch_cadastre_data(self):
        """Récupère les données cadastrales via l'API IGN Cadastre"""
        try:
            lat = float(self.data.get('latitude', 0))
            lon = float(self.data.get('longitude', 0))
            
            if lat == 0 or lon == 0:
                print("Coordonnées GPS manquantes, impossible de récupérer les données cadastrales")
                return None
            
            # API Cadastre IGN
            url = "https://apicarto.ign.fr/api/cadastre/parcelle"
            point_geojson = {
                "type": "Point",
                "coordinates": [lon, lat]
            }
            
            params = {
                "geom": json.dumps(point_geojson),
                "_limit": 1,
                "source_ign": "PCI"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('features') and len(data['features']) > 0:
                    feature = data['features'][0]
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    
                    cadastre_info = {
                        'section': props.get('section', ''),
                        'numero': props.get('numero', ''),
                        'commune': props.get('commune', ''),
                        'code_com': props.get('code_com', ''),
                        'contenance': props.get('contenance', 0),
                        'geometry': geom,  # GeoJSON geometry avec coordinates
                        'success': True
                    }
                    
                    print(f"✓ Données cadastrales récupérées: {cadastre_info['section']}{cadastre_info['numero']}")
                    return cadastre_info
                else:
                    print("Aucune parcelle cadastrale trouvée à ces coordonnées")
                    return None
            else:
                print(f"Erreur API Cadastre: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erreur récupération cadastre: {e}")
            return None
    
    
    def _get_parcelle_bounds(self):
        """Calcule les limites géographiques de la parcelle cadastrale"""
        if not self.cadastre_data or not self.cadastre_data.get('geometry'):
            return None
        
        try:
            geom = self.cadastre_data['geometry']
            coords = geom.get('coordinates', [])
            
            if geom.get('type') == 'Polygon':
                # Polygon: coordinates[0] est le contour extérieur
                points = coords[0]
            elif geom.get('type') == 'MultiPolygon':
                # MultiPolygon: prendre le premier polygone
                points = coords[0][0]
            else:
                return None
            
            # Trouver min/max lat/lon
            lons = [p[0] for p in points]
            lats = [p[1] for p in points]
            
            return {
                'min_lon': min(lons),
                'max_lon': max(lons),
                'min_lat': min(lats),
                'max_lat': max(lats),
                'center_lon': sum(lons) / len(lons),
                'center_lat': sum(lats) / len(lats)
            }
            
        except Exception as e:
            print(f"Erreur calcul bounds: {e}")
            return None
    
    
    def _draw_parcelle_cadastrale(self, c, center_x, center_y, lat, lon, zoom=18):
        """Dessine les vraies délimitations cadastrales sur le plan"""
        if not self.cadastre_data or not self.cadastre_data.get('geometry'):
            return
        
        try:
            geom = self.cadastre_data['geometry']
            coords = geom.get('coordinates', [])
            
            # Extraire les points
            if geom.get('type') == 'Polygon':
                points = coords[0]  # Premier anneau (contour extérieur)
            elif geom.get('type') == 'MultiPolygon':
                points = coords[0][0]  # Premier polygone, premier anneau
            else:
                return
            
            # Conversion lat/lon vers pixels sur le plan
            # Calculer le facteur d'échelle basé sur le zoom
            # À zoom 18: 1 pixel = ~0.597m
            # Échelle approximative: 156543.03 * cos(lat) / (2^zoom) mètres/pixel
            
            lat_rad = math.radians(lat)
            meters_per_pixel = 156543.03 * math.cos(lat_rad) / (2 ** zoom)
            
            # 1cm sur le PDF = combien de pixels sur la carte satellite ?
            # Si image est 800x800px pour 18cm, alors ~44px/cm
            pixels_per_cm = 800 / 18
            
            # Mètres par cm sur le plan
            meters_per_cm = meters_per_pixel * pixels_per_cm
            
            # Échelle: 1cm sur plan = meters_per_cm mètres dans la réalité
            # Pour dessiner, on convertit les coordonnées GPS en offset depuis le centre
            
            # Calculer les offsets de chaque point par rapport au centre (lat, lon)
            pdf_points = []
            
            for point in points:
                point_lon, point_lat = point[0], point[1]
                
                # Différence en degrés
                delta_lon = point_lon - lon
                delta_lat = point_lat - lat
                
                # Conversion en mètres (approximation locale)
                delta_x_m = delta_lon * 111320 * math.cos(lat_rad)  # lon vers mètres
                delta_y_m = delta_lat * 111320  # lat vers mètres
                
                # Conversion mètres vers cm sur le plan
                delta_x_cm = delta_x_m / meters_per_cm
                delta_y_cm = delta_y_m / meters_per_cm
                
                # Position sur le PDF (ajouter au centre)
                pdf_x = center_x + delta_x_cm * cm
                pdf_y = center_y + delta_y_cm * cm
                
                pdf_points.append((pdf_x, pdf_y))
            
            # Dessiner le polygone
            if len(pdf_points) >= 3:
                c.setStrokeColor(colors.HexColor('#FF00FF'))
                c.setLineWidth(3)
                c.setDash(6, 3)
                
                # Créer le path
                path = c.beginPath()
                path.moveTo(pdf_points[0][0], pdf_points[0][1])
                
                for px, py in pdf_points[1:]:
                    path.lineTo(px, py)
                
                path.close()
                c.drawPath(path, stroke=1, fill=0)
                c.setDash()  # Reset dash
                
                print(f"✓ Délimitations cadastrales dessinées ({len(pdf_points)} points)")
            
        except Exception as e:
            print(f"Erreur dessin parcelle cadastrale: {e}")
            import traceback
            traceback.print_exc()
    
    
    def _extract_calpinage_info(self):
        """Extrait les informations utiles du calpinage pour les plans"""
        if not self.calpinage:
            # Valeurs par défaut si pas de calpinage
            self.module_longueur = 2.28  # m (dimensions standard)
            self.module_largeur = 1.13   # m
            self.module_puissance = 560  # Wc
            self.module_orientation = 'paysage'
            self.total_modules = 0
            self.total_puissance_kw = 0
            self.nb_cols = 10
            self.nb_rows = 6
            return
        
        # Récupérer les infos du module
        module = self.calpinage.get('module', {})
        self.module_longueur = module.get('longueur_mm', 2278) / 1000  # mm → m
        self.module_largeur = module.get('largeur_mm', 1134) / 1000    # mm → m
        self.module_puissance = module.get('puissance_wc', 560)        # Wc
        
        # Calculer totaux depuis toutes les zones
        zones = self.calpinage.get('zones', [])
        self.total_modules = sum(z.get('nbModules', 0) for z in zones)
        self.total_puissance_kw = sum(z.get('puissanceKw', 0) for z in zones)
        
        # Prendre l'orientation de la première zone (ou majoritaire)
        if zones:
            self.module_orientation = zones[0].get('moduleOrientation', 'paysage')
        else:
            self.module_orientation = 'paysage'
        
        # Stocker nbCols et nbRows de la zone principale pour les plans
        if zones:
            zone_principale = max(zones, key=lambda z: z.get('nbModules', 0))
            self.nb_cols = zone_principale.get('nbCols', 10)
            self.nb_rows = zone_principale.get('nbRows', 6)
        else:
            self.nb_cols = 10
            self.nb_rows = 6
        
        print(f"✓ Calpinage intégré: {self.total_modules} modules {self.module_orientation} ({self.nb_cols}x{self.nb_rows})")
    
    
    def _draw_cartouche_plan(self, c, titre_plan):
        """Dessine le cartouche standard pour les plans"""
        
        # Position cartouche (bas droit)
        cart_x = self.width - 8*cm - 1*cm
        cart_y = 1*cm
        cart_width = 8*cm
        cart_height = 3*cm
        
        # Cadre principal
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        c.rect(cart_x, cart_y, cart_width, cart_height)
        
        # Titre plan
        c.setFont("Helvetica-Bold", 10)
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 0.6*cm, titre_plan)
        
        # Séparateur
        c.setLineWidth(0.5)
        c.line(cart_x, cart_y + cart_height - 1*cm, cart_x + cart_width, cart_y + cart_height - 1*cm)
        
        # Informations projet
        c.setFont("Helvetica", 8)
        y = cart_y + cart_height - 1.4*cm
        
        commune = self.data.get('commune', '')
        c.drawString(cart_x + 0.3*cm, y, f"Commune : {commune}")
        
        y -= 0.4*cm
        adresse = self.data.get('adresse', '')
        if len(adresse) > 40:
            adresse = adresse[:37] + "..."
        c.drawString(cart_x + 0.3*cm, y, f"Adresse : {adresse}")
        
        y -= 0.4*cm
        c.drawString(cart_x + 0.3*cm, y, f"Échelle : 1/100")
        
        y -= 0.4*cm
        date_str = datetime.now().strftime('%d/%m/%Y')
        c.drawString(cart_x + 0.3*cm, y, f"Date : {date_str}")
    
    # ========== HELPERS ==========
    
    def _draw_footer(self, c, page):
        """Pied de page standard"""
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.grey)
        c.drawString(2*cm, 0.8*cm, f"CERFA 13703*09 - Déclaration Préalable de Travaux - Installation photovoltaïque - Page {page}/4")
    
    def _checkbox(self, c, x, y, checked=False):
        """Dessine une case à cocher"""
        size = 0.35*cm
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.rect(x, y - size, size, size)
        
        if checked:
            c.setLineWidth(2)
            c.setStrokeColor(colors.HexColor('#0066CC'))
            # Croix
            c.line(x + 0.05*cm, y - size + 0.05*cm, x + size - 0.05*cm, y - 0.05*cm)
            c.line(x + 0.05*cm, y - 0.05*cm, x + size - 0.05*cm, y - size + 0.05*cm)
            c.setStrokeColor(colors.black)
    
    def _field_labeled(self, c, x, y, label, value, width=8*cm):
        """Dessine un champ avec label et valeur"""
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#666666'))
        c.drawString(x, y + 0.15*cm, label)
        
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(x, y - 0.25*cm, str(value) if value else '')
        
        # Ligne de soulignement
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.3)
        c.line(x, y - 0.35*cm, x + width, y - 0.35*cm)
        c.setStrokeColor(colors.black)
    
    def _extract_parcelles(self):
        """Extrait les parcelles cadastrales"""
        parcelles_data = self.data.get('parcelles_cadastrales', '')
        
        if isinstance(parcelles_data, list):
            return parcelles_data
        
        if isinstance(parcelles_data, str) and parcelles_data:
            try:
                import json
                return json.loads(parcelles_data)
            except:
                # Format simple "Section Numéro"
                return [{'section': '', 'numero': parcelles_data, 'surface': ''}]
        
        return []
    
    def _get_puissance(self):
        """Calcule la puissance kWc"""
        surface_m2 = float(self.data.get('surface_m2', 0) or 0)
        surface_ha = float(self.data.get('surface_ha', 0) or 0)
        if surface_ha > 0:
            surface_m2 = surface_ha * 10000
        
        return round(surface_m2 * 0.15, 2) if surface_m2 > 0 else 0
    
    def _get_surface_panneaux(self):
        """Retourne la surface des panneaux"""
        surface_m2 = float(self.data.get('surface_m2', 0) or 0)
        surface_ha = float(self.data.get('surface_ha', 0) or 0)
        if surface_ha > 0:
            surface_m2 = surface_ha * 10000
        
        return round(surface_m2, 2)


# ========== FONCTIONS HELPER ==========

def generate_declaration_prealable_complete(prospect_data, calpinage_data=None):
    """
    Génère un dossier de Déclaration Préalable complet
    
    Args:
        prospect_data: dict avec les données du prospect
        calpinage_data: dict optionnel avec données du calpinage (zones, modules, orientation)
        
    Returns:
        dict avec les buffers PDF : {'formulaire': BytesIO, 'plan_dp1-8': BytesIO, ...}
    """
    generator = DeclarationPrealableGenerator(prospect_data, calpinage_data)
    return generator.generate_complete_dossier()


def generate_formulaire_cerfa_only(prospect_data):
    """Génère uniquement le formulaire CERFA 13703*09"""
    generator = DeclarationPrealableGenerator(prospect_data)
    return generator.generate_formulaire_cerfa()
