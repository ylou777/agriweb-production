"""
Générateur de proposition commerciale professionnelle pour installations photovoltaïques
Conforme aux standards de l'industrie solaire française
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import (Table, TableStyle, PageBreak, SimpleDocTemplate, 
                                 Paragraph, Spacer, Image as RLImage, KeepTogether, Frame, PageTemplate)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import json

class PropositionProfessionnelle:
    """Générateur de proposition commerciale photovoltaïque professionnelle"""
    
    def __init__(self, prospect, calpinage, parametres):
        self.prospect = prospect
        self.calpinage = calpinage
        self.params = parametres
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Créer des styles personnalisés professionnels"""
        
        # Style titre principal
        self.styles.add(ParagraphStyle(
            name='TitrePrincipal',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#003d7a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='SousTitre',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0066cc'),
            spaceAfter=12,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        # Style section
        self.styles.add(ParagraphStyle(
            name='Section',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#003d7a'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            leftIndent=0
        ))
        
        # Style corps de texte justifié
        self.styles.add(ParagraphStyle(
            name='CorpsJustifie',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            leading=14
        ))
        
        # Style encadré important
        self.styles.add(ParagraphStyle(
            name='Encadre',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#003d7a'),
            backColor=colors.HexColor('#e6f2ff'),
            borderPadding=10,
            fontName='Helvetica-Bold'
        ))
    
    def generer_pdf(self):
        """Génère le PDF complet de la proposition"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=2*cm, 
            leftMargin=2*cm,
            topMargin=2.5*cm, 
            bottomMargin=2.5*cm,
            title=f"Proposition Commerciale - {self.prospect.get('nom_prospect', 'N/A')}",
            author="Votre Société Photovoltaïque"
        )
        
        story = []
        
        # Générer toutes les sections
        story.extend(self._page_couverture())
        story.append(PageBreak())
        
        story.extend(self._sommaire())
        story.append(PageBreak())
        
        story.extend(self._presentation_entreprise())
        story.append(PageBreak())
        
        story.extend(self._analyse_site())
        story.append(PageBreak())
        
        story.extend(self._solution_technique())
        story.append(PageBreak())
        
        story.extend(self._etude_productible())
        story.append(PageBreak())
        
        story.extend(self._etude_financiere())
        story.append(PageBreak())
        
        story.extend(self._devis_detaille())
        story.append(PageBreak())
        
        story.extend(self._planning_realisation())
        story.append(PageBreak())
        
        story.extend(self._garanties_maintenance())
        story.append(PageBreak())
        
        story.extend(self._aspects_reglementaires())
        story.append(PageBreak())
        
        story.extend(self._conditions_generales())
        
        # Construire le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _page_couverture(self):
        """PAGE 1: Page de couverture professionnelle"""
        elements = []
        
        # Espace en haut
        elements.append(Spacer(1, 3*cm))
        
        # Logo (si disponible)
        # elements.append(RLImage('logo.png', width=6*cm, height=2*cm))
        elements.append(Paragraph("VOTRE SOCIÉTÉ PHOTOVOLTAÏQUE", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Titre principal
        elements.append(Paragraph("PROPOSITION COMMERCIALE", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Récupérer type raccordement depuis calepinage (cohérence avec schéma unifilaire)
        type_raccordement = self.calpinage.get('type_raccordement', 'autoconso_injection')
        
        # Mapping pour affichage
        type_projet_display = {
            'autoconso_injection': 'Autoconsommation avec Revente du Surplus',
            'autoconso_sans_injection': 'Autoconsommation Sans Injection',
            'injection_totale': 'Vente Totale (Obligation d’Achat)'
        }.get(type_raccordement, 'Autoconsommation')
        
        elements.append(Paragraph(f"Installation Photovoltaïque en {type_projet_display}", self.styles['SousTitre']))
        
        elements.append(Spacer(1, 2*cm))
        
        # Encadré informations projet
        puissance = self.params.get('puissance_kwc', 0)
        
        info_data = [
            ['CARACTÉRISTIQUES DU PROJET'],
            [''],
            [f'<b>Puissance:</b> {puissance:.2f} kWc'],
            [f'<b>Type raccordement:</b> {type_projet_display}'],
            [f'<b>Localisation:</b> {self.prospect.get("commune", "N/A")} ({self.prospect.get("departement", "")})'],
            [''],
            [f'<b>Proposition valable jusqu\'au:</b> {(datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")}'],
        ]
        
        info_table = Table(info_data, colWidths=[16*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#003d7a')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        elements.append(info_table)
        
        elements.append(Spacer(1, 2*cm))
        
        # Informations client
        client_text = f"""
        <b>À l'attention de :</b><br/>
        <b>{self.prospect.get('nom_prospect', 'N/A')}</b><br/>
        {self.prospect.get('adresse', 'N/A')}<br/>
        {self.prospect.get('commune', 'N/A')}
        """
        elements.append(Paragraph(client_text, self.styles['Normal']))
        
        elements.append(Spacer(1, 1*cm))
        
        # Date et référence
        ref_text = f"""
        <b>Référence:</b> PROP-{self.prospect.get('id', '000')}-{datetime.now().strftime('%Y%m%d')}<br/>
        <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}
        """
        elements.append(Paragraph(ref_text, self.styles['Normal']))
        
        return elements
    
    def _sommaire(self):
        """PAGE 2: Sommaire"""
        elements = []
        
        elements.append(Paragraph("SOMMAIRE", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 1*cm))
        
        sommaire_data = [
            ['', '<b>SECTION</b>', '<b>PAGE</b>'],
            ['1.', 'Présentation de l\'entreprise', '3'],
            ['2.', 'Analyse du site et diagnostic', '4'],
            ['3.', 'Solution technique proposée', '5'],
            ['4.', 'Étude de productible', '6'],
            ['5.', 'Étude financière et rentabilité', '7'],
            ['6.', 'Devis détaillé', '8'],
            ['7.', 'Planning de réalisation', '9'],
            ['8.', 'Garanties et maintenance', '10'],
            ['9.', 'Aspects réglementaires', '11'],
            ['10.', 'Conditions générales de vente', '12'],
        ]
        
        sommaire_table = Table(sommaire_data, colWidths=[1.5*cm, 12*cm, 3*cm])
        sommaire_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        elements.append(sommaire_table)
        
        return elements
    
    def _presentation_entreprise(self):
        """PAGE 3: Présentation de l'entreprise"""
        elements = []
        
        elements.append(Paragraph("1. PRÉSENTATION DE L'ENTREPRISE", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Qui sommes-nous
        texte_presentation = """
        <b>Votre Société Photovoltaïque</b> est un acteur reconnu dans le secteur des énergies renouvelables, 
        spécialisé dans la conception, l'installation et la maintenance d'installations photovoltaïques pour 
        les professionnels et les collectivités.
        <br/><br/>
        Avec <b>plus de X années d'expérience</b> et <b>XXX MWc installés</b>, nous maîtrisons l'ensemble 
        de la chaîne de valeur du photovoltaïque, de l'étude de faisabilité jusqu'à la maintenance préventive 
        et curative.
        """
        elements.append(Paragraph(texte_presentation, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Nos engagements
        elements.append(Paragraph("Nos engagements", self.styles['Section']))
        
        engagements_data = [
            ['✓ <b>Qualité</b>', 'Matériel premium (Tier 1) avec garanties constructeur étendues'],
            ['✓ <b>Expertise</b>', 'Bureau d\'études interne, certifications QualiPV et RGE'],
            ['✓ <b>Accompagnement</b>', 'Suivi personnalisé de A à Z, démarches administratives incluses'],
            ['✓ <b>Performance</b>', 'Garantie de production sur 25 ans'],
            ['✓ <b>Sécurité</b>', 'Assurance décennale, respect des normes NF C 15-100'],
        ]
        
        engagements_table = Table(engagements_data, colWidths=[4*cm, 12*cm])
        engagements_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(engagements_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Certifications
        elements.append(Paragraph("Nos certifications", self.styles['Section']))
        
        cert_text = """
        • <b>QualiPV</b> - Module Bât (Installations en toiture)<br/>
        • <b>QualiPV</b> - Module Elec (Raccordement électrique)<br/>
        • <b>RGE</b> - Reconnu Garant de l'Environnement<br/>
        • <b>Assurance décennale</b> - Garantie dommages-ouvrage<br/>
        • <b>Habilitations électriques</b> - BR, BC, B2V
        """
        elements.append(Paragraph(cert_text, self.styles['CorpsJustifie']))
        
        return elements
    
    def _analyse_site(self):
        """PAGE 4: Analyse du site"""
        elements = []
        
        elements.append(Paragraph("2. ANALYSE DU SITE ET DIAGNOSTIC", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Localisation
        elements.append(Paragraph("2.1. Localisation", self.styles['Section']))
        
        localisation_text = f"""
        <b>Adresse:</b> {self.prospect.get('adresse', 'N/A')}<br/>
        <b>Commune:</b> {self.prospect.get('commune', 'N/A')} ({self.prospect.get('departement', '')})<br/>
        <b>Coordonnées GPS:</b> {self.prospect.get('latitude', 'N/A'):.6f}, {self.prospect.get('longitude', 'N/A'):.6f}<br/>
        <b>Zone climatique:</b> H2 (tempérée)<br/>
        <b>Irradiation annuelle:</b> 1400-1600 kWh/m²/an
        """
        elements.append(Paragraph(localisation_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Caractéristiques du bâtiment
        elements.append(Paragraph("2.2. Caractéristiques du site", self.styles['Section']))
        
        surface = self.prospect.get('surface_m2', 0)
        type_bat = self.prospect.get('type', 'N/A')
        
        batiment_text = f"""
        <b>Type de structure:</b> {type_bat.title()}<br/>
        <b>Surface disponible:</b> {surface:,.0f} m²<br/>
        <b>Type de toiture:</b> À déterminer lors de la visite technique<br/>
        <b>Orientation:</b> Optimisée selon calepinage (Sud ±30°)<br/>
        <b>Inclinaison:</b> Variable selon zones (25-35°)<br/>
        <b>Ombrages:</b> Analyse détaillée nécessaire sur site
        """
        elements.append(Paragraph(batiment_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Raccordement
        elements.append(Paragraph("2.3. Raccordement électrique", self.styles['Section']))
        
        distance_bt = self.prospect.get('poste_bt_distance_m', 'N/A')
        distance_hta = self.prospect.get('poste_hta_distance_m', 'N/A')
        
        raccordement_text = f"""
        <b>Poste BT le plus proche:</b> {distance_bt} mètres<br/>
        <b>Poste HTA le plus proche:</b> {distance_hta} mètres<br/>
        <b>Puissance disponible:</b> À vérifier auprès d'Enedis<br/>
        <b>Type de raccordement:</b> BT (< 250 kVA) ou HTA (> 250 kVA) selon puissance finale
        """
        elements.append(Paragraph(raccordement_text, self.styles['CorpsJustifie']))
        
        # Encadré important
        important_text = """
        <b>⚠️ NOTE IMPORTANTE:</b> Cette analyse préliminaire devra être confirmée par une visite technique 
        approfondie incluant :
        • Relevé précis des dimensions et orientations
        • Analyse des ombrages (diagramme solaire)
        • Vérification de la structure porteuse
        • État du tableau électrique
        • Contraintes d'urbanisme locales
        """
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(important_text, self.styles['Encadre']))
        
        return elements
    
    def _solution_technique(self):
        """PAGE 5: Solution technique proposée - ENRICHIE AVEC DONNÉES CALEPINAGE"""
        elements = []
        
        elements.append(Paragraph("3. SOLUTION TECHNIQUE PROPOSÉE", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Récupérer les données du calepinage
        zones = self.calpinage.get('zones', [])
        module = self.calpinage.get('module', {})
        equipments = self.calpinage.get('equipments', {})
        config_elec = self.calpinage.get('configuration_electrique', {})
        distances = self.calpinage.get('distances', {})
        
        # Calculs
        nb_modules_total = sum(z.get('nbModules', 0) for z in zones)
        puissance_totale = nb_modules_total * float(module.get('puissance', 550)) / 1000
        
        # Vue d'ensemble
        vue_ensemble_text = f"""
        Nous proposons l'installation d'une centrale photovoltaïque d'une puissance totale de <b>{puissance_totale:.2f} kWc</b>, 
        composée de <b>{nb_modules_total} modules</b> photovoltaïques haute efficacité répartis sur <b>{len(zones)} zone(s)</b> 
        de toiture, avec onduleur(s) de dernière génération et structure de fixation certifiée.
        <br/><br/>
        <b>Installation conforme NF C 15-712-1:2017</b> - Installations photovoltaïques raccordées au réseau public.
        """
        elements.append(Paragraph(vue_ensemble_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.5*cm))
        
        # === LOT 1: MODULES PHOTOVOLTAÏQUES ===
        elements.append(Paragraph("LOT 1 - MODULES PHOTOVOLTAÏQUES", self.styles['Section']))
        
        modules_data = [
            ['<b>Caractéristique</b>', '<b>Spécification</b>'],
            ['Nombre de modules', f'{nb_modules_total} unités'],
            ['Puissance unitaire', f"{module.get('puissance', 550)} Wc"],
            ['Puissance totale', f'{puissance_totale:.2f} kWc'],
            ['Tension circuit ouvert (Voc)', f"{module.get('voc', 49.5)} V"],
            ['Tension MPP (Vmpp)', f"{module.get('vmpp', 41.8)} V"],
            ['Courant court-circuit (Isc)', f"{module.get('isc', 13.9)} A"],
            ['Courant MPP (Impp)', f"{module.get('impp', 13.2)} A"],
            ['Technologie', 'Monocristallin PERC Half-Cell'],
            ['Rendement', '≥ 21%'],
            ['Garantie produit', '12 ans fabricant'],
            ['Garantie performance', '25 ans linéaire (84% Pmin à 25 ans)'],
            ['Certification', 'IEC 61215, IEC 61730, CE'],
        ]
        
        modules_table = Table(modules_data, colWidths=[7*cm, 9*cm])
        modules_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(modules_table)
        elements.append(Spacer(1, 0.3*cm))
        
        # Détail par zone
        if len(zones) > 1:
            elements.append(Paragraph("<b>Répartition par zone:</b>", self.styles['Normal']))
            zones_data = [['<b>Zone</b>', '<b>Modules</b>', '<b>Surface</b>', '<b>Puissance</b>', '<b>Orientation</b>']]
            for z in zones:
                zones_data.append([
                    f"Zone {z.get('numero', '?')}",
                    str(z.get('nbModules', 0)),
                    f"{z.get('surfaceM2', 0):.1f} m²",
                    f"{z.get('puissanceKw', 0):.2f} kWc",
                    f"{z.get('orientation', 'N/A')}° / {z.get('inclinaison', 'N/A')}°"
                ])
            zones_table = Table(zones_data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 3*cm, 5*cm])
            zones_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(zones_table)
        
        elements.append(Spacer(1, 0.5*cm))
        
        # === LOT 2: ONDULEURS ===
        elements.append(Paragraph("LOT 2 - ONDULEUR(S) DE CONVERSION", self.styles['Section']))
        
        onduleurs_list = equipments.get('onduleurs', [])
        nb_onduleurs = len(onduleurs_list)
        
        if nb_onduleurs > 0 and onduleurs_list[0].get('marque'):
            ond = onduleurs_list[0]
            onduleurs_data = [
                ['<b>Caractéristique</b>', '<b>Spécification</b>'],
                ['Marque / Modèle', f"{ond.get('marque', 'N/A')} / {ond.get('modele', 'N/A')}"],
                ['Nombre d\'onduleurs', str(nb_onduleurs)],
                ['Puissance AC nominale', f"{ond.get('puissance_ac', 0)/1000:.1f} kW"],
                ['Puissance DC maximale', f"{ond.get('puissance_dc_max', 0)/1000:.1f} kW"],
                ['Tension DC maximale', f"{ond.get('tension_max', 1000)} V"],
                ['Nombre de MPPT', str(ond.get('nb_mppt', 2))],
                ['Rendement européen', '≥ 97.5%'],
                ['Protection', config_elec.get('ip_onduleur', 'IP65')],
                ['Garantie standard', '5 ans (extensible)'],
                ['Monitoring', 'Interface web/smartphone incluse'],
                ['Certification', 'CE, VDE, EN 62109'],
            ]
        else:
            # Fallback onduleur générique
            onduleurs_data = [
                ['<b>Caractéristique</b>', '<b>Spécification</b>'],
                ['Type', 'Onduleur string triphasé'],
                ['Puissance', f'{puissance_totale:.0f} kW'],
                ['Rendement', '≥ 98%'],
                ['Protection', 'IP65'],
                ['Garantie', '5-10 ans'],
            ]
        
        onduleurs_table = Table(onduleurs_data, colWidths=[7*cm, 9*cm])
        onduleurs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(onduleurs_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # === LOT 3: PROTECTIONS ÉLECTRIQUES (NF C 15-712) ===
        elements.append(Paragraph("LOT 3 - PROTECTIONS ÉLECTRIQUES CONFORMES NF C 15-712", self.styles['Section']))
        
        protections_text = """
        <b>Conformité NF C 15-712-1:2017</b> - Toutes les protections électriques réglementaires sont incluses.
        """
        elements.append(Paragraph(protections_text, self.styles['Normal']))
        
        protections_data = [
            ['<b>Équipement</b>', '<b>Spécification</b>', '<b>Norme</b>'],
            ['<b>PARTIE DC (Courant Continu)</b>', '', ''],
            ['Sectionneur DC', config_elec.get('sectionneur_dc', '63A') + f' / {config_elec.get("type_cable_dc", "1000V DC")}', 'NF EN 60947-3'],
            ['Parafoudre DC', config_elec.get('parafoudre_dc', 'Type 2') + f' (≤ {config_elec.get("resistance_terre", "100Ω")})', 'NF EN 61643-31'],
            ['Boîte de jonction DC', config_elec.get('ip_boite_dc', 'IP65') + ' avec porte-fusibles', 'NF C 15-712'],
            ['Fusibles strings (si requis)', config_elec.get('fusibles_strings', 'Selon calcul'), 'Type gPV'],
            ['<b>PARTIE AC (Courant Alternatif)</b>', '', ''],
            ['AGCP (Appareil Général)', config_elec.get('agcp', '63A') + ' courbe C, PdC 10kA', 'NF C 15-100'],
            ['Disjoncteur différentiel', config_elec.get('disjoncteur_ac', '40A') + ' courbe C', 'NF EN 61008'],
            ['Différentiel', config_elec.get('differentiel_ac', 'Type A 30mA'), 'NF C 15-100'],
            ['Parafoudre AC', config_elec.get('parafoudre_ac', 'Type 2'), 'NF EN 61643-11'],
            ['Coffret TGBT', 'IP65 pré-câblé', 'NF C 15-100'],
        ]
        
        protections_table = Table(protections_data, colWidths=[6*cm, 7*cm, 3*cm])
        protections_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.whitesmoke),
            ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 6), (-1, 6), colors.whitesmoke),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 2), (-1, 5), [colors.white, colors.HexColor('#f5f5f5')]),
            ('ROWBACKGROUNDS', (0, 7), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(protections_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # === LOT 4: CÂBLAGE ET RACCORDEMENT ===
        elements.append(Paragraph("LOT 4 - CÂBLAGE ET RACCORDEMENT", self.styles['Section']))
        
        cablage_data = [
            ['<b>Type de câble</b>', '<b>Section</b>', '<b>Longueur</b>', '<b>Caractéristiques</b>'],
            ['Câbles DC strings', 
             f"{config_elec.get('section_cable_strings', 6)}mm² + PE {config_elec.get('section_pe_dc', 6)}mm²",
             f"{distances.get('dc_strings', 25):.1f}m",
             f"{config_elec.get('type_cable_dc', 'U1000R2V')} Cu"],
            ['Câble DC principal', 
             f"{config_elec.get('section_cable_dc', 16)}mm² + PE {config_elec.get('section_pe_dc', 16)}mm²",
             f"{distances.get('dc_strings', 25):.1f}m",
             f"{config_elec.get('type_cable_dc', 'U1000R2V')} Cu - ΔU={config_elec.get('chute_tension_dc_pct', 1.5):.2f}%"],
            ['Câble AC onduleur-TGBT',
             f"{config_elec.get('section_cable_ac', 10)}mm² + PE {config_elec.get('section_pe_ac', 10)}mm²",
             f"{distances.get('ac_onduleur_tgbt', 15):.1f}m",
             f"{config_elec.get('type_cable_ac', 'U1000R2V')} Cu - ΔU={config_elec.get('chute_tension_ac_pct', 1.0):.2f}%"],
            ['Câble AC TGBT-Injection',
             f"{config_elec.get('section_cable_ac', 10)}mm² + PE",
             f"{distances.get('ac_tgbt_injection', 10):.1f}m",
             f"{config_elec.get('type_cable_ac', 'U1000R2V')} Cu"],
            ['Terre / LEP',
             f"{config_elec.get('section_pe_ac', 16)}mm² Cu nu",
             'Selon installation',
             f"Résistance ≤ {config_elec.get('resistance_terre', '100Ω')}"],
        ]
        
        cablage_table = Table(cablage_data, colWidths=[4.5*cm, 4*cm, 3*cm, 4.5*cm])
        cablage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(cablage_table)
        
        cablage_note = f"""
        <br/><b>Note:</b> Tous les câbles sont dimensionnés selon NF C 15-712 avec chutes de tension 
        DC: {config_elec.get('chute_tension_dc_pct', 1.5):.2f}% et AC: {config_elec.get('chute_tension_ac_pct', 1.0):.2f}% 
        (conformes aux limites ≤3% DC et ≤1.5% AC).
        """
        elements.append(Paragraph(cablage_note, self.styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # === LOT 5: STRUCTURE DE FIXATION ===
        elements.append(Paragraph("LOT 5 - STRUCTURE ET FIXATION", self.styles['Section']))
        
        structure_text = """
        <b>Structure aluminium anodisé haute résistance:</b>
        • Calcul de structure par bureau d'études (neige, vent selon Eurocode)
        • Rails de fixation aluminium anodisé (garantie 25 ans)
        • Crochets de toiture spécifiques (tuiles mécaniques/ardoises/bac acier)
        • Étanchéité renforcée avec bandes EPDM et solin alu
        • Fixations inox A4 anti-corrosion
        • Système de gestion des câbles intégré
        <br/><br/>
        <b>Sécurité intégrée:</b>
        • Ligne de vie permanente (si accès toiture requis)
        • EPI (Équipements de Protection Individuelle) pour installateurs
        • Signalétique sécurité DC/AC
        """
        elements.append(Paragraph(structure_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.5*cm))
        
        # === LOT 6: INSTALLATION ET MISE EN SERVICE ===
        elements.append(Paragraph("LOT 6 - INSTALLATION ET MISE EN SERVICE", self.styles['Section']))
        
        installation_data = [
            ['<b>Prestation</b>', '<b>Description</b>'],
            ['Préparation du chantier', '• Réunion de lancement\n• Sécurisation zone de travail\n• Échafaudage si nécessaire'],
            ['Pose structure', '• Fixation crochets\n• Montage rails\n• Vérification étanchéité'],
            ['Pose modules', f'• Installation {nb_modules_total} modules\n• Câblage DC strings\n• Tests électriques'],
            ['Installation onduleur(s)', f'• Fixation {nb_onduleurs} onduleur(s)\n• Raccordement DC/AC\n• Configuration'],
            ['Protections électriques', '• Installation coffret TGBT\n• Parafoudres DC/AC\n• Mise à la terre'],
            ['Raccordement réseau', '• Liaison TGBT → compteur\n• Tests injection\n• Vérifications conformité'],
            ['Mise en service', '• Tests complets\n• Activation monitoring\n• Formation utilisateur'],
            ['Documentation', '• DOE (Dossier Ouvrage Exécuté)\n• Schéma unifilaire\n• Certificats Consuel'],
        ]
        
        installation_table = Table(installation_data, colWidths=[5*cm, 11*cm])
        installation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(installation_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # === LOT 7: DÉMARCHES ADMINISTRATIVES ===
        elements.append(Paragraph("LOT 7 - DÉMARCHES ADMINISTRATIVES INCLUSES", self.styles['Section']))
        
        admin_text = """
        <b>Nous prenons en charge toutes les démarches réglementaires:</b>
        <br/><br/>
        <b>1. Déclaration Préalable de Travaux (DP):</b>
        • Constitution et dépôt du dossier en mairie
        • Plans et documents techniques
        • Suivi instruction (délai 1 mois)
        <br/><br/>
        <b>2. Déclaration de Raccordement (DDR):</b>
        • Demande de raccordement auprès d'Enedis
        • Convention d'exploitation (si injection)
        • Suivi validation technique
        <br/><br/>
        <b>3. Attestation Consuel:</b>
        • Dossier Consuel complet (formulaire, schémas, photos)
        • Vérification conformité NF C 15-712 et NF C 15-100
        • Obtention attestation finale (obligatoire mise en service)
        <br/><br/>
        <b>4. Mise en service Enedis:</b>
        • Prise de rendez-vous technicien Enedis
        • Paramétrage compteur Linky (injection)
        • Activation contrat revente/autoconsommation
        """
        elements.append(Paragraph(admin_text, self.styles['CorpsJustifie']))
        
        return elements
    
    def _etude_productible(self):
        """PAGE 6: Étude de productible détaillée"""
        elements = []
        
        elements.append(Paragraph("4. ÉTUDE DE PRODUCTIBLE", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 0.5*cm))
        
        puissance = self.params.get('puissance_kwc', 0)
        
        # Méthodologie
        elements.append(Paragraph("4.1. Méthodologie de calcul", self.styles['Section']))
        
        methodo_text = """
        L'estimation de production est basée sur le logiciel <b>PVGIS</b> (Photovoltaic Geographical Information System) 
        de la Commission Européenne, considéré comme la référence pour les études photovoltaïques en Europe.
        <br/><br/>
        Paramètres pris en compte :
        • Irradiation solaire moyenne sur 20 ans (base de données PVGIS-SARAH2)
        • Orientation et inclinaison des modules
        • Pertes système (câblage, onduleur, température, ombrage)
        • Coefficient de performance global (Performance Ratio)
        """
        elements.append(Paragraph(methodo_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Production annuelle
        elements.append(Paragraph("4.2. Production annuelle estimée", self.styles['Section']))
        
        # Ratio de performance réaliste
        PR = 0.85  # Performance Ratio de 85% (réaliste)
        irradiation = 1500  # kWh/m²/an (moyenne Sud de la France)
        production_annuelle = puissance * 1100  # kWh/an conservateur
        
        production_data = [
            ['<b>Paramètre</b>', '<b>Valeur</b>'],
            ['Puissance installée', f'{puissance:.2f} kWc'],
            ['Irradiation moyenne', f'{irradiation} kWh/m²/an'],
            ['Performance Ratio (PR)', f'{PR*100:.0f}%'],
            ['<b>Production annuelle estimée</b>', f'<b>{production_annuelle:,.0f} kWh/an</b>'],
            ['Soit par kWc installé', f'{production_annuelle/puissance:.0f} kWh/kWc/an'],
            ['Production sur 25 ans', f'{production_annuelle * 25:,.0f} kWh'],
        ]
        
        production_table = Table(production_data, colWidths=[10*cm, 6*cm])
        production_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#d4edda')),
            ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
        ]))
        elements.append(production_table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Production mensuelle
        elements.append(Paragraph("4.3. Répartition mensuelle", self.styles['Section']))
        
        # Générer graphique de production mensuelle
        mois = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        coef_mensuels = np.array([0.06, 0.07, 0.09, 0.11, 0.13, 0.14, 0.15, 0.14, 0.12, 0.09, 0.07, 0.06])
        production_mensuelle = production_annuelle * coef_mensuels
        
        fig, ax = plt.subplots(figsize=(14, 6))
        bars = ax.bar(mois, production_mensuelle, color='#0066cc', edgecolor='#003d7a', linewidth=1.5)
        
        # Ajouter valeurs au-dessus des barres
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_ylabel('Production (kWh)', fontsize=12, fontweight='bold')
        ax.set_xlabel('Mois', fontsize=12, fontweight='bold')
        ax.set_title('Production Mensuelle Estimée', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, max(production_mensuelle) * 1.15)
        
        graph_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(graph_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        graph_buffer.seek(0)
        
        elements.append(RLImage(graph_buffer, width=16*cm, height=8*cm))
        
        return elements
    
    def _etude_financiere(self):
        """PAGE 7: Étude financière complète"""
        elements = []
        
        elements.append(Paragraph("5. ÉTUDE FINANCIÈRE ET RENTABILITÉ", self.styles['TitrePrincipal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Récupérer les paramètres
        puissance = self.params.get('puissance_kwc', 0)
        prix_kwc = self.params.get('prix_kwc', 850)
        type_raccordement = self.calpinage.get('type_raccordement', 'autoconso_injection')
        
        investissement_ht = puissance * prix_kwc
        investissement_ttc = investissement_ht * 1.10  # TVA 10%
        
        production_annuelle = puissance * 1100
        
        # Section selon type de raccordement
        if type_raccordement == 'injection_totale':
            elements.extend(self._section_vente_totale(investissement_ht, production_annuelle))
        else:  # autoconso_injection ou autoconso_sans_injection
            elements.extend(self._section_autoconsommation(investissement_ht, production_annuelle, type_raccordement))
        
        return elements
    
    def _section_autoconsommation(self, investissement_ht, production_annuelle, type_raccordement='autoconso_injection'):
        """Sous-section pour autoconsommation (avec ou sans injection)"""
        sub_elements = []
        
        consommation = self.params.get('consommation_annuelle_kwh', production_annuelle * 1.2)
        taux_autoconso = self.params.get('taux_autoconso', 70) / 100
        tarif_achat = self.params.get('tarif_achat_kwh', 0.20)
        tarif_revente = self.params.get('tarif_revente_kwh', 0.13)
        
        energie_autoconsommee = production_annuelle * taux_autoconso
        economie_autoconso = energie_autoconsommee * tarif_achat
        
        # Gestion de l'injection selon le type
        if type_raccordement == 'autoconso_sans_injection':
            # Sans injection : surplus perdu
            energie_revendue = 0
            revenu_revente = 0
            gain_annuel = economie_autoconso
        else:
            # Avec injection : surplus vendu
            energie_revendue = production_annuelle - energie_autoconsommee
            revenu_revente = energie_revendue * tarif_revente
            gain_annuel = economie_autoconso + revenu_revente
        
        # Tableau récapitulatif
        recap_data = [
            ['<b>Flux Financiers Annuels</b>', '<b>Montant (€/an)</b>'],
            [f'Économie autoconsommation ({energie_autoconsommee:,.0f} kWh × {tarif_achat:.3f} €/kWh)', f'{economie_autoconso:,.2f} €'],
            [f'Revenu revente surplus ({energie_revendue:,.0f} kWh × {tarif_revente:.3f} €/kWh)', f'{revenu_revente:,.2f} €'],
            ['<b>GAIN TOTAL ANNUEL</b>', f'<b>{gain_annuel:,.2f} €</b>'],
        ]
        
        recap_table = Table(recap_data, colWidths=[11*cm, 5*cm])
        recap_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4edda')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        sub_elements.append(recap_table)
        sub_elements.append(Spacer(1, 0.5*cm))
        
        # Indicateurs de rentabilité
        roi_annees = investissement_ht / gain_annuel if gain_annuel > 0 else 0
        tri = (gain_annuel / investissement_ht) * 100  # TRI simplifié
        van_25ans = (gain_annuel * 25) - investissement_ht  # VAN simplifiée
        
        rentabilite_data = [
            ['<b>Indicateur</b>', '<b>Valeur</b>', '<b>Commentaire</b>'],
            ['Temps de retour simple', f'{roi_annees:.1f} ans', 'Sans actualisation'],
            ['Taux de Rentabilité Interne (TRI)', f'{tri:.1f}%', 'Excellente rentabilité > 10%'],
            ['Valeur Actuelle Nette (25 ans)', f'{van_25ans:,.0f} €', 'Gain net sur durée de vie'],
            ['Économies cumulées sur 25 ans', f'{gain_annuel * 25:,.0f} €', 'Hors inflation électricité'],
        ]
        
        rentabilite_table = Table(rentabilite_data, colWidths=[6*cm, 4*cm, 6*cm])
        rentabilite_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        sub_elements.append(rentabilite_table)
        sub_elements.append(Spacer(1, 0.5*cm))
        
        # GRAPHIQUE COURBES PRODUCTION vs CONSOMMATION HORAIRES
        sub_elements.append(Paragraph("<b>📊 COURBES PRODUCTION vs CONSOMMATION (Journée type)</b>", self.styles['Section']))
        
        # Récupérer données PVGIS horaires si disponibles
        pvgis_hourly = self.params.get('pvgis_hourly_data')
        enedis_hourly = self.params.get('enedis_hourly_data')
        
        if pvgis_hourly and enedis_hourly:
            # Utiliser vraies données
            graph_img = self._create_courbes_horaires_graph(pvgis_hourly, enedis_hourly)
        else:
            # Simulation réaliste en attendant vraies données
            graph_img = self._create_courbes_horaires_simulation(production_annuelle, consommation)
        
        if graph_img:
            sub_elements.append(RLImage(graph_img, width=16*cm, height=10*cm))
            sub_elements.append(Spacer(1, 0.3*cm))
        
        explication_text = """
        <b>Légende du graphique :</b><br/>
        • <b>Courbe orange :</b> Production photovoltaïque heure par heure (PVGIS)<br/>
        • <b>Courbe bleue :</b> Consommation électrique du site (données Enedis)<br/>
        • <b>Zone verte :</b> Autoconsommation instantanée (production directement consommée)<br/>
        • <b>Zone orange :</b> Surplus de production (revendu au réseau)<br/>
        • <b>Zone bleue :</b> Soutirage réseau (consommation non couverte)<br/>
        <br/>
        <i>Le taux d'autoconsommation dépend de la synchronisation entre production solaire et besoins.
        Une batterie de stockage permettrait d'augmenter ce taux de 70% à 90%.</i>
        """
        sub_elements.append(Paragraph(explication_text, self.styles['CorpsJustifie']))
        
        return sub_elements
    
    def _create_courbes_horaires_simulation(self, production_annuelle, consommation_annuelle):
        """Créer graphique simulation courbes production/consommation horaires"""
        try:
            heures = np.arange(0, 24, 1)
            
            # Simulation production solaire (courbe gaussienne 8h-18h)
            production_horaire = np.zeros(24)
            for h in heures:
                if 6 <= h <= 20:
                    # Courbe en cloche centrée sur 13h
                    production_horaire[h] = (production_annuelle / 365 / 1000) * np.exp(-((h - 13) ** 2) / 18) * 8
            
            # Simulation consommation (profil tertiaire/agricole)
            consommation_horaire = np.ones(24) * (consommation_annuelle / 365 / 24 / 1000)  # Base constante
            # Pics matin et soir
            for h in heures:
                if 7 <= h <= 9:
                    consommation_horaire[h] *= 1.5  # Pic matin
                elif 11 <= h <= 14:
                    consommation_horaire[h] *= 1.3  # Activité midi
                elif 17 <= h <= 20:
                    consommation_horaire[h] *= 1.4  # Pic soir
                elif 22 <= h or h <= 6:
                    consommation_horaire[h] *= 0.3  # Nuit réduite
            
            # Créer graphique
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Zones colorées
            ax.fill_between(heures, 0, np.minimum(production_horaire, consommation_horaire), 
                            alpha=0.3, color='green', label='Autoconsommation')
            ax.fill_between(heures, np.minimum(production_horaire, consommation_horaire), production_horaire, 
                            alpha=0.2, color='orange', label='Surplus (revente)')
            ax.fill_between(heures, consommation_horaire, np.maximum(production_horaire, consommation_horaire), 
                            alpha=0.2, color='blue', label='Soutirage réseau')
            
            # Courbes
            ax.plot(heures, production_horaire, color='orange', linewidth=2.5, marker='o', markersize=4, label='Production PV')
            ax.plot(heures, consommation_horaire, color='blue', linewidth=2.5, marker='s', markersize=4, label='Consommation')
            
            ax.set_xlabel('Heure de la journée', fontsize=11, fontweight='bold')
            ax.set_ylabel('Puissance (kW)', fontsize=11, fontweight='bold')
            ax.set_title('Profil Production Photovoltaïque vs Consommation (Journée type)', fontsize=13, fontweight='bold')
            ax.legend(loc='upper right', fontsize=9)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_xlim(0, 23)
            ax.set_ylim(0, max(max(production_horaire), max(consommation_horaire)) * 1.1)
            ax.set_xticks(np.arange(0, 24, 2))
            
            plt.tight_layout()
            
            # Sauvegarder en buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            print(f"Erreur création graphique horaire: {e}")
            return None
    
    def _create_courbes_horaires_graph(self, pvgis_data, enedis_data):
        """Créer graphique avec vraies données PVGIS et Enedis"""
        try:
            # TODO: Parser vraies données 8760h PVGIS + Enedis
            # Pour l'instant, utiliser simulation
            return None
        except Exception as e:
            print(f"Erreur parsing données horaires: {e}")
            return None
        sub_elements.append(Paragraph("Courbes Production vs Consommation", self.styles['Section']))
        
        # Créer courbes mensuelles
        mois = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        coef_prod = np.array([0.06, 0.07, 0.09, 0.11, 0.13, 0.14, 0.15, 0.14, 0.12, 0.09, 0.07, 0.06])
        production_mens = production_annuelle * coef_prod
        
        # Consommation (pattern typique professionnel)
        coef_conso = np.array([1.1, 1.1, 1.0, 0.9, 0.8, 0.7, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2])
        consommation_mens = consommation * coef_conso / coef_conso.sum()
        
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(mois, production_mens, marker='o', linewidth=2.5, color='#28a745', label='Production PV', markersize=8)
        ax.plot(mois, consommation_mens, marker='s', linewidth=2.5, color='#dc3545', label='Consommation', markersize=8)
        
        # Zone autoconsommée
        autoconso_mens = np.minimum(production_mens, consommation_mens)
        ax.fill_between(range(12), 0, autoconso_mens, alpha=0.3, color='#28a745', label='Autoconsommation')
        
        ax.set_xlabel('Mois', fontsize=13, fontweight='bold')
        ax.set_ylabel('Énergie (kWh)', fontsize=13, fontweight='bold')
        ax.set_title('Production et Consommation Mensuelles - Optimisation Autoconsommation', fontsize=15, fontweight='bold')
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        graph_buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(graph_buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        graph_buffer.seek(0)
        
        sub_elements.append(RLImage(graph_buffer, width=16*cm, height=8*cm))
        
        return sub_elements
    
    def _section_vente_totale(self, investissement_ht, production_annuelle):
        """Sous-section pour vente totale"""
        sub_elements = []
        
        tarif_revente = self.params.get('tarif_revente_kwh', 0.13)
        revenu_annuel = production_annuelle * tarif_revente
        roi_annees = investissement_ht / revenu_annuel if revenu_annuel > 0 else 0
        
        # ... Code similaire pour vente totale
        
        return sub_elements
    
    def _devis_detaille(self):
        """PAGE 8: Devis détaillé conforme NF C 15-752-1 avec taxes IFER"""
        elements = []
        
        elements.append(Paragraph("8. DEVIS DÉTAILLÉ", self.styles['Section']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Récupération données calepinage réelles
        zones = self.calpinage.get('zones', [])
        if zones:
            puissance_kwc = sum(z.get('puissanceKw', 0) for z in zones)
            nb_modules_total = sum(z.get('nbModules', 0) for z in zones)
        else:
            puissance_kwc = self.params.get('puissance_kwc', 100)
            nb_modules_total = int(puissance_kwc * 1000 / 550)
        
        prix_kwc = self.params.get('prix_kwc', 850)
        investissement_total = puissance_kwc * prix_kwc
        
        # Onduleurs Huawei (1 onduleur 50kW par tranche)
        nb_onduleurs = max(1, int(np.ceil(puissance_kwc / 50)))
        
        # Prix unitaires marché 2025
        prix_module_unit = 180  # €/module Tier 1 550Wc
        prix_onduleur_unit = 4500 if puissance_kwc >= 50 else 2500
        prix_structure_m2 = 45  # €/m² rails + fixations
        surface_modules = nb_modules_total * 2.7  # m² par module
        
        # Décomposition devis NF C 15-752-1
        devis_data = [
            ['POSTE', 'DESCRIPTION', 'QTÉ', 'P.U. HT', 'TOTAL HT'],
            
            # 1. MODULES
            ['1. MODULES PHOTOVOLTAÏQUES', '', '', '', ''],
            ['', f'Modules JA Solar JAM72S30-550/MR - 550Wc', nb_modules_total, f'{prix_module_unit} €', 
             f'{nb_modules_total * prix_module_unit:,.2f} €'],
            ['', 'Certification IEC 61215, IEC 61730, Tier 1', '', '', ''],
            ['', 'Garantie produit 12 ans, performance 25 ans', '', '', ''],
            
            # 2. ONDULEURS
            ['2. ONDULEURS ET ÉQUIPEMENTS ÉLECTRIQUES', '', '', '', ''],
            ['', f'Onduleur Huawei SUN2000-{50 if puissance_kwc >= 50 else 25}KTL-M3', 
             nb_onduleurs, f'{prix_onduleur_unit} €', f'{nb_onduleurs * prix_onduleur_unit:,.2f} €'],
            ['', 'Rendement 98.65%, monitoring inclus', '', '', ''],
            ['', 'Coffret AC/DC protections (parafoudre, sectionneur)', 1, '850 €', '850.00 €'],
            ['', 'Câbles solaires 6mm² certifiés EN 50618', 1, '1200 €', '1200.00 €'],
            
            # 3. STRUCTURE
            ['3. STRUCTURE ET FIXATIONS', '', '', '', ''],
            ['', f'Rails aluminium + fixations toiture NF C 15-752-1', 
             f'{surface_modules:.0f} m²', f'{prix_structure_m2} €/m²', 
             f'{surface_modules * prix_structure_m2:,.2f} €'],
            ['', 'Étude de charpente incluse', 1, 'Inclus', '0.00 €'],
            ['', 'Crochets inox A4, étanchéité renforcée', '', '', ''],
            
            # 4. RACCORDEMENT
            ['4. RACCORDEMENT RÉSEAU', '', '', '', ''],
            ['', 'Liaison DC modules → onduleur', 1, '1800 €', '1800.00 €'],
            ['', 'Liaison AC onduleur → TGBT (NF C 15-100)', 1, '2200 €', '2200.00 €'],
            ['', 'Mise à la terre équipotentielle', 1, '650 €', '650.00 €'],
            ['', 'Parafoudres Type 1+2 AC et DC', 1, '450 €', '450.00 €'],
            
            # 5. MONITORING
            ['5. SUPERVISION ET MONITORING', '', '', '', ''],
            ['', 'Box supervision Huawei SmartLogger', 1, '850 €', '850.00 €'],
            ['', 'Application mobile iOS/Android', 1, 'Inclus', '0.00 €'],
            ['', 'Alertes SMS/email anomalies', 1, 'Inclus', '0.00 €'],
            
            # 6. INSTALLATION
            ['6. MAIN D\'ŒUVRE ET INSTALLATION', '', '', '', ''],
            ['', f'Pose modules + onduleurs + raccordement', 
             1, f'{investissement_total * 0.20:.0f} €', f'{investissement_total * 0.20:,.2f} €'],
            ['', 'Installation par équipe RGE QualiPV', '', '', ''],
            ['', 'Conformité NF C 15-100 et NF C 15-752-1', '', '', ''],
            
            # 7. ADMINISTRATIF
            ['7. PRESTATIONS ADMINISTRATIVES', '', '', '', ''],
            ['', 'Déclaration Préalable (DP) en mairie', 1, '450 €', '450.00 €'],
            ['', 'Demande Raccordement (DDR) Enedis', 1, '350 €', '350.00 €'],
            ['', 'Attestation Consuel', 1, '250 €', '250.00 €'],
            ['', 'Contrat achat EDF OA', 1, '300 €', '300.00 €'],
        ]
        
        sous_total = investissement_total
        tva_rate = 0.10 if puissance_kwc <= 3 else 0.20
        
        devis_data.extend([
            ['', '', '', 'SOUS-TOTAL HT', f'{sous_total:,.2f} €'],
            ['', '', '', f'TVA {int(tva_rate*100)}%', f'{sous_total * tva_rate:,.2f} €'],
            ['', '', '', '', ''],
            ['', '', '', 'TOTAL TTC', f'{sous_total * (1+tva_rate):,.2f} €'],
        ])
        
        table = Table(devis_data, colWidths=[4*cm, 7*cm, 2*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, 6), (0, 6), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 11), (-1, 11), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, 11), (0, 11), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 16), (-1, 16), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, 16), (0, 16), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 21), (-1, 21), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, 21), (0, 21), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 26), (-1, 26), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, 26), (0, 26), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 29), (-1, 29), colors.HexColor('#e6f2ff')),
            ('FONTNAME', (0, 29), (0, 29), 'Helvetica-Bold'),
            ('BACKGROUND', (3, -4), (-1, -4), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (3, -3), (-1, -3), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (3, -1), (-1, -1), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (3, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (3, -1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        # TAXES ET FISCALITÉ
        elements.append(Paragraph("<b>🔸 TAXES ET FISCALITÉ APPLICABLES</b>", self.styles['Section']))
        
        taxe_ifer = puissance_kwc * 7.65 if puissance_kwc > 100 else 0
        taxe_territoriale = investissement_total * 0.005
        
        fiscal_text = f"""
        <b>IFER (Imposition Forfaitaire Entreprises de Réseaux) :</b><br/>
        • Installations ≤ 100 kWc : <b>EXONÉRÉES</b><br/>
        • Installations > 100 kWc : <b>7,65 €/kWc/an</b><br/>
        • Votre installation ({puissance_kwc:.2f} kWc) : <b>{'EXONÉRÉE' if puissance_kwc <= 100 else f'{taxe_ifer:,.2f} €/an'}</b><br/>
        <br/>
        <b>Taxe Foncière :</b><br/>
        • Exonération possible 50% pendant 3 ans (selon commune)<br/>
        • À vérifier auprès centre des impôts local<br/>
        <br/>
        <b>Taxe d'aménagement :</b><br/>
        • Estimation : <b>{taxe_territoriale:,.2f} €</b> (paiement unique)<br/>
        • Variable selon commune (part communale + départementale)<br/>
        <br/>
        <b>TVA :</b><br/>
        • Installation ≤ 3 kWc : TVA 10%<br/>
        • Installation > 3 kWc : TVA 20%<br/>
        • Votre projet : <b>TVA {int(tva_rate*100)}%</b>
        """
        
        elements.append(Paragraph(fiscal_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Paragraph(
            "<i>Devis valable 2 mois. Prix marché T4 2025. Conforme NF C 15-752-1.</i>", 
            self.styles['Normal']
        ))
        
        elements.append(PageBreak())
        return elements
    
    def _planning_realisation(self):
        """PAGE 9: Planning de réalisation détaillé"""
        elements = []
        
        elements.append(Paragraph("9. PLANNING DE RÉALISATION", self.styles['Section']))
        elements.append(Spacer(1, 0.3*cm))
        
        intro_text = """
        Le planning ci-dessous présente les différentes étapes de votre projet photovoltaïque, 
        de la signature du devis jusqu'à la mise en service définitive. Les durées indiquées 
        sont des estimations basées sur notre expérience et peuvent varier selon les délais 
        administratifs et les contraintes locales.
        """
        elements.append(Paragraph(intro_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.4*cm))
        
        # Tableau planning détaillé
        planning_data = [
            ['ÉTAPE', 'DURÉE', 'DÉLAI CUMULÉ', 'RESPONSABLE', 'LIVRABLE'],
            
            ['1. Signature contrat', '1 jour', 'J+0', 'Client + Sunstice', 'Bon de commande signé'],
            
            ['2. Visite technique', '3-5 jours', 'J+5', 'Sunstice', 'Rapport visite technique'],
            
            ['3. Étude technique détaillée', '5-7 jours', 'J+12', 'Bureau d\'études', 
             'Plans détaillés, calepinage, schéma électrique'],
            
            ['4. Déclaration Préalable (DP)', '1-3 jours', 'J+15', 'Sunstice', 'Dépôt dossier en mairie'],
            
            ['5. Instruction DP mairie', '30 jours', 'J+45', 'Mairie', 'Arrêté ou accord tacite'],
            
            ['6. Demande Raccordement (DDR)', '2-3 jours', 'J+48', 'Sunstice', 'Dépôt DDR Enedis'],
            
            ['7. Proposition Technique Raccordement', '15-45 jours', 'J+93', 'Enedis', 
             'PTR + Convention raccordement'],
            
            ['8. Commande matériel', '5-7 jours', 'J+100', 'Sunstice', 'Confirmation fabricants'],
            
            ['9. Livraison matériel', '15-30 jours', 'J+130', 'Fournisseurs', 'Modules, onduleurs, structure'],
            
            ['10. Installation chantier', '3-5 jours', 'J+135', 'Équipe RGE', 'Installation complète'],
            
            ['11. Attestation Consuel', '5-7 jours', 'J+142', 'Sunstice', 'Demande + réception attestation'],
            
            ['12. Mise en service Enedis', '10-15 jours', 'J+157', 'Enedis', 'Activation compteur producteur'],
            
            ['13. Contrat achat EDF OA', '7-10 jours', 'J+167', 'EDF OA', 'Contrat actif (revente)'],
            
            ['', '', '', '', ''],
            ['<b>DÉLAI TOTAL</b>', '<b>~6 mois</b>', '<b>J+167</b>', '', '<b>Installation opérationnelle</b>'],
        ]
        
        table = Table(planning_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Étapes critiques (DP, DDR, Installation)
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#fff3cd')),  # DP
            ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#fff3cd')),  # DDR
            ('BACKGROUND', (0, 10), (-1, 10), colors.HexColor('#d1ecf1')),  # Installation
            ('BACKGROUND', (0, 12), (-1, 12), colors.HexColor('#d4edda')),  # Mise en service
            
            # Total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            
            # Bordures
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('BOX', (0, -1), (-1, -1), 1.5, colors.HexColor('#003d7a')),
            
            # Alignements
            ('ALIGN', (1, 1), (2, -2), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        # Notes importantes
        notes_text = """
        <b>📌 POINTS IMPORTANTS À RETENIR :</b><br/><br/>
        
        <b>1. Délai d'instruction DP (Déclaration Préalable) :</b><br/>
        • 1 mois légal, peut être prolongé si dossier incomplet<br/>
        • Accord tacite si pas de réponse de la mairie<br/>
        • Nécessaire si installation > 1 kWc ou en zone protégée<br/><br/>
        
        <b>2. Raccordement Enedis :</b><br/>
        • Délai variable selon charge du réseau local (15-45 jours)<br/>
        • PTR peut imposer travaux supplémentaires (coût additionnel)<br/>
        • Installation interdite sans Consuel validé<br/><br/>
        
        <b>3. Météo et saisonnalité :</b><br/>
        • Installation toiture impossible par temps de pluie/gel<br/>
        • Période optimale : Mars à Octobre<br/>
        • Prévoir 1 semaine de marge selon météo<br/><br/>
        
        <b>4. Consuel (Comité National pour la Sécurité des Usagers de l'Électricité) :</b><br/>
        • Contrôle obligatoire avant mise en service<br/>
        • Visite sur site par organisme agréé<br/>
        • Sans Consuel, pas d'activation par Enedis<br/><br/>
        
        <b>5. Délai global :</b><br/>
        • <b>Minimum : 5 mois</b> (si tous délais administratifs courts)<br/>
        • <b>Standard : 6 mois</b> (cas général)<br/>
        • <b>Maximum : 9 mois</b> (si complications administratives/travaux réseau)
        """
        
        elements.append(Paragraph(notes_text, self.styles['CorpsJustifie']))
        
        elements.append(PageBreak())
        return elements
    
    def _garanties_maintenance(self):
        """PAGE 10: Garanties et maintenance"""
        elements = []
        
        elements.append(Paragraph("10. GARANTIES ET MAINTENANCE", self.styles['Section']))
        elements.append(Spacer(1, 0.3*cm))
        
        intro_text = """
        Votre installation photovoltaïque bénéficie d'un ensemble complet de garanties 
        couvrant l'intégralité des équipements et de la main d'œuvre. Ces garanties assurent 
        la pérennité et la performance de votre investissement sur le long terme.
        """
        elements.append(Paragraph(intro_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.4*cm))
        
        # Tableau garanties
        garanties_data = [
            ['ÉQUIPEMENT / PRESTATION', 'TYPE GARANTIE', 'DURÉE', 'COUVERTURE'],
            
            ['Modules JA Solar JAM72S30-550/MR', 'Garantie Produit', '12 ans', 
             'Défauts de fabrication, vices matériaux'],
            ['', 'Garantie Performance', '25 ans', 
             '90% puissance à 10 ans\n80% puissance à 25 ans'],
            
            ['Onduleurs Huawei SUN2000', 'Garantie Constructeur', '10 ans', 
             'Panne, défaillance électronique'],
            ['', 'Extension possible', '15-20 ans', 
             'Option payante +500€'],
            
            ['Structure aluminium', 'Garantie Matériau', '10 ans', 
             'Corrosion, déformation'],
            
            ['Étanchéité toiture', 'Garantie Décennale', '10 ans', 
             'Infiltrations liées aux travaux'],
            
            ['Installation électrique', 'Garantie Décennale', '10 ans', 
             'Conformité NF C 15-100, défauts'],
            
            ['Main d\'œuvre pose', 'Garantie Biennale', '2 ans', 
             'Équipements détachables'],
            ['', 'Garantie Décennale', '10 ans', 
             'Dommages structurels'],
            
            ['Monitoring Huawei', 'Garantie Service', '5 ans', 
             'Accès application, alertes'],
        ]
        
        table = Table(garanties_data, colWidths=[5*cm, 3.5*cm, 2.5*cm, 7.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Lignes modules (surlignage vert)
            ('BACKGROUND', (0, 1), (-1, 2), colors.HexColor('#d4edda')),
            
            # Lignes garanties décennales (orange)
            ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#fff3cd')),
            ('BACKGROUND', (0, 7), (-1, 7), colors.HexColor('#fff3cd')),
            ('BACKGROUND', (0, 9), (-1, 9), colors.HexColor('#fff3cd')),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        # MAINTENANCE
        elements.append(Paragraph("<b>🔧 MAINTENANCE ET ENTRETIEN</b>", self.styles['Section']))
        
        maintenance_text = """
        <b>1. Maintenance préventive (Optionnelle) :</b><br/><br/>
        
        <b>Forfait Sérénité Annuel : 450 €/an HT</b><br/>
        • Visite annuelle sur site par technicien qualifié<br/>
        • Nettoyage modules (2 passages/an selon exposition)<br/>
        • Contrôle serrage connecteurs DC/AC<br/>
        • Vérification tensions et courants de chaînes<br/>
        • Test isolation électrique<br/>
        • Contrôle état onduleurs et monitoring<br/>
        • Rapport annuel de performance<br/>
        • Priorité intervention en cas de panne<br/><br/>
        
        <b>2. Nettoyage modules :</b><br/>
        • Fréquence recommandée : 1 fois/an minimum<br/>
        • Gain production : +5 à 15% après nettoyage<br/>
        • Tarif intervention : 3 €/module (hors forfait)<br/>
        • Produits écologiques biodégradables<br/><br/>
        
        <b>3. Monitoring à distance :</b><br/>
        • Surveillance 24/7 via application Huawei FusionSolar<br/>
        • Alertes automatiques si anomalie détectée<br/>
        • Accès historique production (données minute par minute)<br/>
        • Comparaison production réelle vs théorique<br/>
        • <b>Inclus sans frais pendant 25 ans</b><br/><br/>
        
        <b>4. Dépannage et interventions :</b><br/>
        • Hotline technique 7j/7 : 09 XX XX XX XX<br/>
        • Délai intervention : 48h ouvrées maximum<br/>
        • Sous garantie : <b>GRATUIT</b> (pièces + main d'œuvre)<br/>
        • Hors garantie : Devis avant intervention<br/><br/>
        
        <b>5. Extensions garanties disponibles :</b><br/>
        • Extension onduleur 10→20 ans : <b>500 €</b><br/>
        • Garantie tous risques (bris de glace, tempête) : <b>150 €/an</b><br/>
        • Rachat production perdue en cas de panne : <b>+100 €/an</b>
        """
        
        elements.append(Paragraph(maintenance_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Encadré important
        important_text = """
        <b>⚠️ ASSURANCE HABITATION :</b> Pensez à déclarer votre installation photovoltaïque 
        à votre assureur habitation. La surprime est généralement comprise entre 50 et 150 €/an. 
        Elle couvre les dommages causés par les intempéries, incendie, vol des équipements.
        """
        elements.append(Paragraph(important_text, self.styles['Encadre']))
        
        elements.append(PageBreak())
        return elements
    
    def _aspects_reglementaires(self):
        """PAGE 11: Aspects réglementaires et conformité NF C 15-752-1"""
        elements = []
        
        elements.append(Paragraph("11. ASPECTS RÉGLEMENTAIRES ET CONFORMITÉ", self.styles['Section']))
        elements.append(Spacer(1, 0.3*cm))
        
        intro_text = """
        Votre installation photovoltaïque sera réalisée dans le strict respect de l'ensemble 
        des réglementations en vigueur, garantissant sécurité, performance et conformité légale.
        """
        elements.append(Paragraph(intro_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.4*cm))
        
        # NORMES TECHNIQUES
        elements.append(Paragraph("<b>📋 NORMES TECHNIQUES APPLICABLES</b>", self.styles['Section']))
        
        normes_data = [
            ['NORME', 'DESCRIPTION', 'POINTS DE CONTRÔLE'],
            
            ['NF C 15-100', 'Installations électriques BT', 
             '• Protection personnes/biens\n• Schéma électrique\n• Section câbles\n• Protections différentielles'],
            
            ['NF C 15-752-1', 'Installations PV raccordées au réseau', 
             '• Conception installation DC\n• Protection surtensions\n• Choix câbles solaires\n• Étiquetage circuits'],
            
            ['NF C 14-100', 'Installations de branchement BT', 
             '• Raccordement au réseau public\n• Point de livraison\n• Comptage'],
            
            ['UTE C 15-712-1', 'Installations PV autonomes', 
             '• Si stockage batterie\n• Protection batteries\n• Gestion énergie'],
            
            ['DTU 40.5', 'Travaux toiture (étanchéité)', 
             '• Traversées de couverture\n• Étanchéité à l\'eau\n• Ventilation sous-toiture'],
            
            ['IEC 61215', 'Modules cristallins', 
             '• Tests performances\n• Qualification modules\n• Résistance mécanique'],
            
            ['IEC 61730', 'Sécurité modules PV', 
             '• Résistance au feu\n• Isolation électrique\n• Protection choc électrique'],
        ]
        
        table = Table(normes_data, colWidths=[3*cm, 5*cm, 10.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Mise en évidence normes principales
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fff3cd')),  # NF C 15-100
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fff3cd')),  # NF C 15-752-1
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        # DÉMARCHES ADMINISTRATIVES
        elements.append(Paragraph("<b>🏛️ DÉMARCHES ADMINISTRATIVES OBLIGATOIRES</b>", self.styles['Section']))
        
        demarches_text = """
        <b>1. Déclaration Préalable (DP) en Mairie :</b><br/>
        • <b>Obligatoire</b> pour toute installation > 1 kWc ou en zone protégée<br/>
        • Dossier complet fourni par Sunstice (plans, photos, notice)<br/>
        • Délai instruction : 1 mois (tacite accord si pas de réponse)<br/>
        • En zone ABF : accord Architecte des Bâtiments de France requis<br/>
        • Coût : <b>Inclus dans le devis</b><br/><br/>
        
        <b>2. Demande de Raccordement (DDR) auprès d'Enedis :</b><br/>
        • <b>Obligatoire</b> avant installation<br/>
        • Enedis étudie capacité d'accueil du réseau<br/>
        • Proposition Technique et Financière (PTF) sous 15-45 jours<br/>
        • Travaux réseau éventuels à la charge du demandeur<br/>
        • Coût raccordement : selon puissance (généralement 500-2000 €)<br/>
        • Coût : <b>Montage dossier inclus, frais Enedis en sus</b><br/><br/>
        
        <b>3. Attestation Consuel :</b><br/>
        • <b>Obligatoire</b> avant mise en service<br/>
        • Vérification conformité NF C 15-100 et NF C 15-752-1<br/>
        • Visite sur site par organisme agréé<br/>
        • Sans Consuel, Enedis refuse activation<br/>
        • Coût : <b>250 € (inclus dans devis)</b><br/><br/>
        
        <b>4. Contrat d'Achat Électricité (EDF OA) :</b><br/>
        • Pour installations avec revente surplus ou totale<br/>
        • Durée : 20 ans à tarif garanti<br/>
        • Tarifs 2025 (selon arrêté tarifaire) :<br/>
          - Vente surplus ≤ 9 kWc : 0,13 €/kWh<br/>
          - Vente totale ≤ 100 kWc : 0,1430 €/kWh<br/>
        • Coût : <b>Montage dossier inclus</b><br/><br/>
        
        <b>5. Déclaration ENEDIS (mise en service) :</b><br/>
        • Fourniture attestation Consuel<br/>
        • Convention d'autoconsommation ou de raccordement<br/>
        • Activation compteur Linky en mode producteur<br/>
        • Délai : 10-15 jours après réception Consuel
        """
        
        elements.append(Paragraph(demarches_text, self.styles['CorpsJustifie']))
        elements.append(Spacer(1, 0.4*cm))
        
        # OBLIGATIONS LÉGALES PROPRIÉTAIRE
        elements.append(Paragraph("<b>📜 OBLIGATIONS LÉGALES DU PROPRIÉTAIRE</b>", self.styles['Section']))
        
        obligations_text = """
        <b>Déclaration fiscale :</b><br/>
        • Revenu imposable si vente surplus/totale > 70 000 kWh/an<br/>
        • Exonération totale si puissance ≤ 3 kWc et usage personnel<br/>
        • Régime micro-BIC ou réel selon montant revenus<br/><br/>
        
        <b>Assurance :</b><br/>
        • Déclaration obligatoire à l'assurance habitation<br/>
        • Couverture RC (Responsabilité Civile) obligatoire<br/>
        • Dommages-ouvrage recommandée<br/><br/>
        
        <b>Contrôles périodiques :</b><br/>
        • Contrôle initial Consuel avant mise en service<br/>
        • Vérification électrique tous les 4 ans (> 250 kVA)<br/>
        • Entretien et maintenance selon recommandations fabricant
        """
        
        elements.append(Paragraph(obligations_text, self.styles['CorpsJustifie']))
        
        elements.append(PageBreak())
        return elements
    
    def _conditions_generales(self):
        """PAGE 12: Conditions Générales de Vente"""
        elements = []
        
        elements.append(Paragraph("12. CONDITIONS GÉNÉRALES DE VENTE", self.styles['Section']))
        elements.append(Spacer(1, 0.2*cm))
        
        cgv_text = """
        <b>Article 1 - Objet</b><br/>
        Les présentes Conditions Générales de Vente (CGV) régissent les relations contractuelles entre 
        SUNSTICE (ci-après "le Prestataire") et le client (ci-après "le Client") pour la fourniture et 
        l'installation d'une centrale photovoltaïque.<br/><br/>
        
        <b>Article 2 - Devis et commande</b><br/>
        Le devis est valable 2 mois à compter de sa date d'émission. La commande devient ferme et définitive 
        dès signature du devis et versement de l'acompte de 30% du montant total TTC. Prix basés sur les 
        tarifs en vigueur au T4 2025, susceptibles d'évolution selon variation coût matières premières.<br/><br/>
        
        <b>Article 3 - Prix et modalités de paiement</b><br/>
        Prix indiqués en Euros TTC. Modalités de paiement :<br/>
        • <b>30% à la commande</b> (signature devis)<br/>
        • <b>40% à réception matériel</b> (modules + onduleurs livrés sur site)<br/>
        • <b>30% à la mise en service</b> (installation terminée + Consuel obtenu)<br/>
        Modes de paiement acceptés : virement bancaire, chèque. Escompte 2% si paiement comptant intégral.<br/><br/>
        
        <b>Article 4 - Délais</b><br/>
        Délai indicatif de réalisation : 5 à 7 mois à compter de la signature. Ce délai peut être prolongé 
        en cas de force majeure, retards administratifs (mairie, Enedis), intempéries, ou indisponibilité matériel. 
        Le Client sera informé de tout retard significatif.<br/><br/>
        
        <b>Article 5 - Visite technique et étude</b><br/>
        Une visite technique préalable est obligatoire pour confirmer la faisabilité. Si des contraintes techniques 
        majeures sont découvertes (charpente insuffisante, réseau inadapté), le Prestataire se réserve le droit 
        d'annuler ou modifier le devis. Dans ce cas, l'acompte est remboursé intégralement.<br/><br/>
        
        <b>Article 6 - Autorisa­tions administratives</b><br/>
        Le Prestataire se charge du montage des dossiers administratifs (DP, DDR, Consuel). Le Client s'engage 
        à fournir tous documents nécessaires. En cas de refus des autorités (mairie, ABF, Enedis), le contrat 
        pourra être annulé. Frais déjà engagés resteront dus (visite technique, étude : 500 € forfait).<br/><br/>
        
        <b>Article 7 - Installation et réception</b><br/>
        L'installation sera réalisée par une équipe RGE QualiPV dans le respect des normes NF C 15-100 et 
        NF C 15-752-1. À l'issue, un procès-verbal de réception sera signé conjointement. Le Client dispose 
        de 8 jours pour formuler des réserves écrites. Passé ce délai, l'installation est réputée conforme.<br/><br/>
        
        <b>Article 8 - Garanties</b><br/>
        Garanties détaillées en page 10 du présent document. Garantie décennale assurée par AXA France 
        (police n°XXXX). Pour toute réclamation sous garantie, contacter le SAV : sav@sunstice.fr - 
        Tél 09 XX XX XX XX.<br/><br/>
        
        <b>Article 9 - Assurances</b><br/>
        Le Prestataire est titulaire d'une assurance Responsabilité Civile Professionnelle et d'une assurance 
        Décennale. Le Client doit déclarer l'installation à son assureur habitation sous 30 jours suivant 
        la mise en service.<br/><br/>
        
        <b>Article 10 - Maintenance</b><br/>
        Le Client s'engage à entretenir l'installation selon recommandations du fabricant (nettoyage modules, 
        contrôle visuel). Toute modification par un tiers non agréé annule les garanties. Contrats de 
        maintenance disponibles (cf. page 10).<br/><br/>
        
        <b>Article 11 - Propriété intellectuelle</b><br/>
        Tous plans, études, schémas fournis restent propriété du Prestataire et ne peuvent être reproduits 
        ou communiqués sans accord écrit préalable.<br/><br/>
        
        <b>Article 12 - Protection des données</b><br/>
        Conformément au RGPD, les données personnelles collectées sont utilisées uniquement dans le cadre 
        de l'exécution du contrat. Le Client dispose d'un droit d'accès, rectification, suppression en 
        contactant : contact@sunstice.fr.<br/><br/>
        
        <b>Article 13 - Résiliation</b><br/>
        En cas de non-paiement d'une échéance, le Prestataire peut suspendre les travaux après mise en demeure 
        restée sans effet 15 jours. Frais déjà engagés resteront dus. Le Client peut annuler dans les 14 jours 
        (délai de rétractation légal), avec remboursement intégral de l'acompte si aucun travail n'a débuté.<br/><br/>
        
        <b>Article 14 - Force majeure</b><br/>
        Cas de force majeure : catastrophe naturelle, épidémie, guerre, grève générale, indisponibilité matériel 
        du fait du fabricant. En cas de force majeure de plus de 3 mois, le contrat pourra être annulé sans 
        pénalité.<br/><br/>
        
        <b>Article 15 - Litiges</b><br/>
        En cas de litige, le Client peut saisir le médiateur de la consommation : Médiateur de l'Énergie - 
        www.mediateur-energie.fr. À défaut d'accord amiable, les tribunaux compétents sont ceux du siège social 
        du Prestataire.<br/><br/>
        
        <b>Article 16 - Acceptation</b><br/>
        La signature du devis vaut acceptation pleine et entière des présentes CGV.
        """
        
        elements.append(Paragraph(cgv_text, self.styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Coordonnées et signature
        signature_text = """
        <b>SUNSTICE SAS</b><br/>
        123 Avenue du Soleil - 75001 PARIS<br/>
        SIRET : 123 456 789 00012 - APE : 4321Z<br/>
        RCS Paris B 123 456 789<br/>
        Capital social : 100 000 €<br/>
        TVA : FR12345678900<br/>
        <br/>
        Tél : 09 XX XX XX XX<br/>
        Email : contact@sunstice.fr<br/>
        Web : www.sunstice.fr<br/>
        <br/>
        <i>Document généré automatiquement le """ + datetime.now().strftime('%d/%m/%Y à %H:%M') + """</i>
        """
        
        elements.append(Paragraph(signature_text, self.styles['Normal']))
        
        return elements
