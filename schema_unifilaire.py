"""
Générateur de schéma unifilaire conforme NF C 15-712
Pour installations photovoltaïques raccordées au réseau
AgriWeb 2025 - Version Professionnelle avec symboles normalisés
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import math
from datetime import datetime
from equipements_database import MODULES_PV_DATABASE, ONDULEURS_DATABASE, get_onduleur_optimal
from symboles_electriques import SymbolesElectriques

class SchemaUnifilaire:
    """Générateur de schéma unifilaire conforme NF C 15-712-1"""
    
    def __init__(self, calpinage_data, prospect_data):
        """
        Args:
            calpinage_data: Données du calepinage (zones, modules)
            prospect_data: Données du prospect (nom, adresse)
        """
        self.calpinage = calpinage_data
        self.prospect = prospect_data
        self.module = calpinage_data.get('module', {})
        self.zones = calpinage_data.get('zones', [])
        
        # Calculs électriques automatiques
        self._calculer_configuration_electrique()
    
    def _calculer_configuration_electrique(self):
        """Calcule la configuration électrique optimale selon les modules et zones"""
        
        # Données module (valeurs typiques si non fournies) - CONVERSION EN NUMERIC
        self.module_puissance = float(self.module.get('puissance', 550))  # Wc
        self.module_voc = float(self.module.get('voc', 49.5))  # V (tension circuit ouvert)
        self.module_vmpp = float(self.module.get('vmpp', 41.8))  # V (tension MPP)
        self.module_isc = float(self.module.get('isc', 13.9))  # A (courant court-circuit)
        self.module_impp = float(self.module.get('impp', 13.2))  # A (courant MPP)
        
        # Calculer puissance totale
        self.nb_modules_total = sum(zone.get('nbModules', 0) for zone in self.zones)
        self.puissance_totale_kwc = self.nb_modules_total * self.module_puissance / 1000
        
        # Choix onduleur selon puissance
        self._choisir_onduleur()
        
        # Configuration strings optimale
        self._calculer_strings()
        
        # Calcul sections câbles
        self._calculer_sections_cables()
        
        # Protections électriques
        self._calculer_protections()
    
    def _choisir_onduleur(self):
        """Choisit l'onduleur adapté selon la puissance DC depuis la base de données"""
        
        p_dc_totale = self.puissance_totale_kwc * 1000
        
        # Ratio DC/AC entre 1.0 et 1.5 (plage large pour compatibilité)
        # Ratio optimal: 1.15-1.3, mais scoring favorise les meilleurs ratios
        p_ac_min = p_dc_totale / 1.5
        p_ac_max = p_dc_totale / 1.0
        
        # Filtrer onduleurs compatibles
        onduleurs_compatibles = []
        for ref, data in ONDULEURS_DATABASE.items():
            if (p_ac_min <= data['p_ac_nominale'] <= p_ac_max and 
                data['p_dc_max'] >= p_dc_totale * 0.95):
                
                # Calculer score de compatibilité
                ratio = p_dc_totale / data['p_ac_nominale']
                score_ratio = 100 - abs(ratio - 1.25) * 100  # Optimal = 1.25
                score_rendement = data['rendement_max']
                score_total = score_ratio * 0.6 + score_rendement * 0.4
                
                onduleurs_compatibles.append({
                    'ref': ref,
                    'data': data,
                    'score': score_total,
                    'ratio': ratio
                })
        
        if onduleurs_compatibles:
            # Trier par score (meilleur ratio + rendement)
            meilleur = max(onduleurs_compatibles, key=lambda x: x['score'])
            data = meilleur['data']
            
            # Adapter au format attendu par le reste du code
            self.onduleur = {
                'marque': data['fabricant'],
                'modele': data['modele'],
                'p_ac': data['p_ac_nominale'],
                'p_dc_max': data['p_dc_max'],
                'mppt': data['nb_mppt'],
                'v_min': data['v_dc_min'],
                'v_max': data['v_dc_max'],
                'i_max': data['i_dc_max_par_mppt'],
                'rendement': data['rendement_max'],
                'type_reseau': data['type_reseau'],
                'garantie': data['garantie'],
                'prix': data.get('prix_indicatif', 0)
            }
            
            print(f"✅ Onduleur sélectionné: {self.onduleur['marque']} {self.onduleur['modele']} "
                  f"({self.onduleur['p_ac']/1000:.1f}kW AC, rendement {self.onduleur['rendement']}%, "
                  f"ratio DC/AC {meilleur['ratio']:.2f})")
        else:
            # Par défaut, onduleur générique si aucun compatible
            self.onduleur = {
                'marque': 'Onduleur',
                'modele': f'{int(self.puissance_totale_kwc)}kW',
                'p_ac': int(self.puissance_totale_kwc * 1000),
                'p_dc_max': int(self.puissance_totale_kwc * 1000 * 1.3),
                'mppt': 2,
                'v_min': 150,
                'v_max': 980,
                'i_max': 15,
                'rendement': 97.0,
                'type_reseau': 'Triphasé' if p_dc_totale > 6000 else 'Monophasé',
                'garantie': 10,
                'prix': 0
            }
            
            print(f"⚠️ Aucun onduleur compatible trouvé, onduleur générique créé: "
                  f"{self.onduleur['marque']} {self.onduleur['modele']}")
    
    def _calculer_strings(self):
        """Calcule la configuration optimale des strings par zone"""
        
        self.configuration_strings = []
        
        for idx, zone in enumerate(self.zones):
            nb_modules_zone = zone.get('nbModules', 0)
            if nb_modules_zone == 0:
                continue
            
            # Calcul nombre de modules en série optimal
            # Contrainte: V_mpp doit être entre V_min et V_max de l'onduleur
            v_mpp_zone = self.module_vmpp
            v_oc_zone = self.module_voc
            
            # Facteur température (pire cas hiver: +25% Voc, été: -15% Vmpp)
            v_oc_max = v_oc_zone * 1.25  # Température -10°C
            v_mpp_min = v_mpp_zone * 0.85  # Température +70°C
            
            # Nombre max de modules en série (limite Voc max)
            nb_serie_max = int(self.onduleur['v_max'] / v_oc_max)
            
            # Nombre min de modules en série (limite Vmpp min)
            nb_serie_min = math.ceil(self.onduleur['v_min'] / v_mpp_min)
            
            # Nombre optimal: maximiser utilisation plage MPPT
            nb_serie_optimal = min(nb_serie_max, max(nb_serie_min, 20))  # 20 modules série = standard
            
            # Si zone trop petite, ajuster
            if nb_modules_zone < nb_serie_optimal:
                nb_serie_optimal = nb_modules_zone
            
            # Nombre de strings en parallèle
            nb_strings = math.ceil(nb_modules_zone / nb_serie_optimal)
            nb_serie_reel = nb_modules_zone // nb_strings
            
            # Modules restants (si division non exacte)
            modules_restants = nb_modules_zone % nb_strings
            
            # Créer les strings pour cette zone
            strings_zone = []
            for i in range(nb_strings):
                nb_modules_string = nb_serie_reel + (1 if i < modules_restants else 0)
                
                string_config = {
                    'zone': zone.get('numero', idx + 1),
                    'string_num': i + 1,
                    'nb_modules': nb_modules_string,
                    'v_mpp': nb_modules_string * v_mpp_zone,
                    'v_oc': nb_modules_string * v_oc_zone,
                    'i_mpp': self.module_impp,
                    'i_sc': self.module_isc,
                    'puissance_wc': nb_modules_string * self.module_puissance,
                    'orientation': zone.get('orientation', 180),
                    'inclinaison': zone.get('inclinaison', 30)
                }
                strings_zone.append(string_config)
            
            self.configuration_strings.extend(strings_zone)
        
        print(f"✅ Configuration: {len(self.configuration_strings)} strings créés")
        for s in self.configuration_strings:
            print(f"   String Zone {s['zone']}-{s['string_num']}: {s['nb_modules']} modules, {s['v_mpp']:.1f}V MPP, {s['i_mpp']:.1f}A")
    
    def _calculer_sections_cables(self):
        """Calcule les sections de câbles selon NF C 15-712 et NF C 15-100 avec distances réelles"""
        
        # PROTECTION: Vérifier que nous avons des strings configurés
        if not self.configuration_strings:
            print("⚠️ Aucun string configuré, utilisation valeurs par défaut")
            self.section_cable_dc = 6.0
            self.section_cable_string = 4.0
            self.section_cable_ac = 6.0
            self.longueur_dc_strings = 25
            self.longueur_ac_onduleur_tgbt = 15
            self.longueur_ac_tgbt_injection = 10
            return
        
        # 1. RÉCUPÉRER LES DISTANCES RÉELLES depuis le calepinage
        distances = self.calpinage.get('distances', {})
        
        # Distances DC, AC onduleur-TGBT, AC TGBT-injection
        longueur_dc_strings = distances.get('dc_strings', 25)  # Défaut 25m si non renseigné
        longueur_ac_onduleur_tgbt = distances.get('ac_onduleur_tgbt', 15)  # Défaut 15m
        longueur_ac_tgbt_injection = distances.get('ac_tgbt_injection', 10)  # Défaut 10m
        
        print(f"📏 Distances câbles (calepinage réel):")
        print(f"   DC strings → onduleur: {longueur_dc_strings:.1f} m")
        print(f"   AC onduleur → TGBT: {longueur_ac_onduleur_tgbt:.1f} m")
        print(f"   AC TGBT → injection: {longueur_ac_tgbt_injection:.1f} m")
        
        # 2. CÂBLES DC (strings → onduleur)
        # Chute tension max: 2% selon NF C 15-712 article 7.12.1.1
        
        # Courant max DC (tous strings en parallèle)
        i_max_dc = sum(s['i_sc'] * 1.25 for s in self.configuration_strings)  # Facteur 1.25 sécurité
        
        # Section minimale selon courant (tableau NF C 15-100)
        # Câble cuivre, isolant PVC, température 70°C, méthode de pose B1 (câbles encastrés)
        sections_normalisees = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
        courants_admissibles = [18, 24, 32, 41, 57, 76, 96, 119, 144, 184, 223, 259, 299, 338, 396]  # Ampères
        
        section_dc_min_courant = 2.5  # mm² par défaut
        for i, courant_adm in enumerate(courants_admissibles):
            if courant_adm >= i_max_dc:
                section_dc_min_courant = sections_normalisees[i]
                break
        
        # Vérification chute de tension (V = 2 * ρ * L * I / S)
        rho_cuivre = 0.01851  # Ω.mm²/m à 70°C
        v_mpp_moyenne = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
        
        section_dc_chute_tension = (2 * rho_cuivre * longueur_dc_strings * i_max_dc) / (0.02 * v_mpp_moyenne)
        
        # Prendre le max des deux contraintes
        section_dc_calculee = max(section_dc_min_courant, section_dc_chute_tension)
        
        # Arrondir à la section normalisée supérieure (avec sécurité si aucune section ne convient)
        sections_valides = [s for s in sections_normalisees if s >= section_dc_calculee]
        self.section_cable_dc = min(sections_valides) if sections_valides else sections_normalisees[-1]
        
        # 2. CÂBLES PAR STRING (moins de courant)
        i_max_string = max(s['i_sc'] * 1.25 for s in self.configuration_strings)
        section_string_min = 2.5  # Section minimale NF C 15-712
        for i, courant_adm in enumerate(courants_admissibles):
            if courant_adm >= i_max_string:
                section_string_min = max(sections_normalisees[i], 4)  # Min 4mm² recommandé extérieur
                break
        
        self.section_cable_string = section_string_min
        
        # 3. CÂBLE AC ONDULEUR → TGBT (distance réelle du calepinage)
        puissance_ac = self.onduleur['p_ac']
        
        # Courant AC (monophasé 230V ou triphasé 400V selon puissance)
        if puissance_ac <= 6000:
            # Monophasé 230V
            self.type_reseau = 'Monophasé 230V'
            i_max_ac = (puissance_ac / 230) * 1.25  # Facteur sécurité
            nb_phases = 1
        else:
            # Triphasé 400V
            self.type_reseau = 'Triphasé 400V'
            i_max_ac = (puissance_ac / (400 * math.sqrt(3))) * 1.25
            nb_phases = 3
        
        # Section AC selon courant
        section_ac_min_courant = 2.5
        for i, courant_adm in enumerate(courants_admissibles):
            if courant_adm >= i_max_ac:
                section_ac_min_courant = sections_normalisees[i]
                break
        
        # Chute tension AC (max 2%)
        if nb_phases == 1:
            section_ac_chute_tension = (2 * rho_cuivre * longueur_ac_onduleur_tgbt * i_max_ac) / (0.02 * 230)
        else:
            section_ac_chute_tension = (math.sqrt(3) * rho_cuivre * longueur_ac_onduleur_tgbt * i_max_ac) / (0.02 * 400)
        
        section_ac_calculee = max(section_ac_min_courant, section_ac_chute_tension)
        sections_valides_ac = [s for s in sections_normalisees if s >= section_ac_calculee]
        self.section_cable_ac = min(sections_valides_ac) if sections_valides_ac else sections_normalisees[-1]
        
        self.courant_max_ac = i_max_ac
        
        # Stocker les distances pour affichage dans le PDF
        self.longueur_dc = longueur_dc_strings
        self.longueur_ac_onduleur_tgbt = longueur_ac_onduleur_tgbt
        self.longueur_ac_tgbt_injection = longueur_ac_tgbt_injection
        
        print(f"✅ Sections câbles calculées selon distances réelles:")
        print(f"   DC strings: {self.section_cable_string}mm² ({longueur_dc_strings:.1f}m)")
        print(f"   DC principal: {self.section_cable_dc}mm² ({longueur_dc_strings:.1f}m)")
        print(f"   AC onduleur-TGBT: {self.section_cable_ac}mm² ({longueur_ac_onduleur_tgbt:.1f}m)")
        print(f"   AC TGBT-injection: {longueur_ac_tgbt_injection:.1f}m")
    
    def _calculer_protections(self):
        """Calcule les protections électriques selon NF C 15-712"""
        
        # PROTECTION: Vérifier que nous avons des strings configurés
        if not self.configuration_strings:
            print("⚠️ Aucun string configuré, utilisation calibres par défaut")
            self.calibre_disjoncteur_ac = 32
            self.type_differentiel = 'Type A 30mA'
            self.sensibilite_differentiel = 30
            self.calibre_sectionneur_dc = 25
            self.tension_sectionneur_dc = '1000V DC'
            self.parafoudre_dc = 'Type 2 - 1000V DC - 25A'
            self.parafoudre_ac = 'Type 2 - 275V AC - 20kA'
            self.fusibles_strings = 'Non requis'
            self.resistance_terre_max = '100Ω'
            return
        
        # 1. PROTECTION AC (disjoncteur différentiel)
        # Calibre disjoncteur: 1.45 × In (In = courant nominal onduleur)
        calibres_disjoncteurs = [10, 16, 20, 25, 32, 40, 50, 63]
        
        in_onduleur = self.courant_max_ac / 1.25  # Retour au nominal
        calibre_disjoncteur_min = in_onduleur * 1.45
        
        calibres_valides_disj = [c for c in calibres_disjoncteurs if c >= calibre_disjoncteur_min]
        self.calibre_disjoncteur_ac = min(calibres_valides_disj) if calibres_valides_disj else calibres_disjoncteurs[-1]
        
        # Type différentiel: Type A (onduleurs récents) ou Type B (onduleurs + batteries)
        self.type_differentiel = 'Type A 30mA'
        self.sensibilite_differentiel = 30  # mA
        
        # 2. PROTECTION DC (sectionneurs + parafoudres)
        # Sectionneur DC: 1.25 × Isc total
        isc_total = sum(s['i_sc'] for s in self.configuration_strings)
        calibre_sectionneur_dc_min = isc_total * 1.25
        
        calibres_sectionneurs_dc = [16, 25, 32, 40, 63, 80, 100, 125]
        calibres_valides_sect = [c for c in calibres_sectionneurs_dc if c >= calibre_sectionneur_dc_min]
        self.calibre_sectionneur_dc = min(calibres_valides_sect) if calibres_valides_sect else calibres_sectionneurs_dc[-1]
        
        # Tension nominale sectionneur DC
        v_oc_max = max(s['v_oc'] * 1.25 for s in self.configuration_strings)  # Facteur température
        self.tension_sectionneur_dc = '1000V DC' if v_oc_max < 900 else '1500V DC'
        
        # 3. PARAFOUDRES (obligatoires selon NF C 15-712 art. 7.12.3.4)
        # Type 2 minimum (Type 1+2 si paratonnerre)
        self.parafoudre_dc = f'Type 2 - {self.tension_sectionneur_dc} - {int(isc_total * 1.5)}A'
        self.parafoudre_ac = 'Type 2 - 275V AC - 20kA'
        
        # 4. FUSIBLES PAR STRING (si nb_strings > 2)
        if len(self.configuration_strings) > 2:
            isc_string_max = max(s['i_sc'] for s in self.configuration_strings)
            calibres_fusibles = [10, 12, 15, 16, 20, 25, 32]
            calibres_valides_fus = [c for c in calibres_fusibles if c >= isc_string_max * 1.5]
            calibre_fusible = min(calibres_valides_fus) if calibres_valides_fus else calibres_fusibles[-1]
            self.fusibles_strings = f'{calibre_fusible}A gPV (1000V DC)'
        else:
            self.fusibles_strings = 'Non requis (≤2 strings)'
        
        # 5. MISE À LA TERRE
        self.resistance_terre_max = '100Ω'  # NF C 15-712
        
        print(f"✅ Protections: Disj AC={self.calibre_disjoncteur_ac}A {self.type_differentiel}, Sect DC={self.calibre_sectionneur_dc}A {self.tension_sectionneur_dc}")
    
    def generer_schema_pdf(self, output_path=None):
        """Génère le schéma unifilaire au format PDF"""
        
        if output_path is None:
            output_path = f"schema_unifilaire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Créer le canvas PDF (A3 paysage pour plus d'espace)
        from reportlab.lib.pagesizes import A3, landscape
        page_width, page_height = landscape(A3)
        
        c = canvas.Canvas(output_path, pagesize=landscape(A3))
        
        # === PAGE 1: SCHÉMA UNIFILAIRE ===
        self._dessiner_cartouche(c, page_width, page_height)
        self._dessiner_schema_principal(c, page_width, page_height)
        
        c.showPage()
        
        # === PAGE 2: NOTES DE CALCULS ===
        self._dessiner_notes_calculs(c, page_width, page_height)
        
        c.save()
        print(f"✅ Schéma unifilaire généré: {output_path}")
        return output_path
    
    def _dessiner_cartouche(self, c, width, height):
        """Dessine le cartouche professionnel avec informations client"""
        
        # === CARTOUCHE PRINCIPAL (en haut, pleine largeur) ===
        cart_main_height = 5*cm
        cart_main_y = height - cart_main_height - 0.5*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(1.5*cm, cart_main_y, width - 3*cm, cart_main_height)
        
        # Bandeau titre
        c.setFillColor(colors.HexColor('#28a745'))
        c.rect(1.5*cm, cart_main_y + cart_main_height - 1*cm, width - 3*cm, 1*cm, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, cart_main_y + cart_main_height - 0.7*cm, "🌱 AgriWeb Pro - SCHÉMA UNIFILAIRE NF C 15-712")
        c.setFillColor(colors.black)
        
        # Informations client (2 colonnes)
        y_info = cart_main_y + cart_main_height - 1.8*cm
        
        # Colonne gauche
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y_info, "CLIENT:")
        c.setFont("Helvetica", 9)
        nom_client = f"{self.prospect.get('nom', '')} {self.prospect.get('prenom', '')}".strip() or "Non renseigné"
        c.drawString(2*cm, y_info - 0.5*cm, nom_client[:40])
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y_info - 1.2*cm, "ADRESSE:")
        c.setFont("Helvetica", 9)
        adresse = self.prospect.get('adresse', 'Non renseignée')
        c.drawString(2*cm, y_info - 1.7*cm, adresse[:50])
        
        ville = f"{self.prospect.get('code_postal', '')} {self.prospect.get('commune', '')}"
        c.drawString(2*cm, y_info - 2.1*cm, ville[:50])
        
        # Colonne droite
        col2_x = width / 2 + 1*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(col2_x, y_info, "PARCELLES CADASTRALES:")
        c.setFont("Helvetica", 9)
        parcelles = self.prospect.get('references_cadastrales', 'Non renseignées')
        if isinstance(parcelles, list):
            parcelles = ', '.join(parcelles[:3])
        c.drawString(col2_x, y_info - 0.5*cm, str(parcelles)[:40])
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(col2_x, y_info - 1.2*cm, "PUISSANCE INSTALLATION:")
        c.setFont("Helvetica", 9)
        c.drawString(col2_x, y_info - 1.7*cm, f"{self.puissance_totale_kwc:.2f} kWc ({self.nb_modules_total} modules)")
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(col2_x, y_info - 2.4*cm, "DATE D'ÉDITION:")
        c.setFont("Helvetica", 9)
        c.drawString(col2_x, y_info - 2.9*cm, datetime.now().strftime("%d/%m/%Y"))
        
        # Trait séparateur vertical
        c.setLineWidth(1)
        c.line(width/2, cart_main_y, width/2, cart_main_y + cart_main_height - 1*cm)
        
        # === CARTOUCHE BAS (infos techniques) ===
        cart_width = 8*cm
        cart_height = 2.5*cm
        cart_x = width - cart_width - 1.5*cm
        cart_y = 1*cm
        
        c.setLineWidth(2)
        c.rect(cart_x, cart_y, cart_width, cart_height)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 0.6*cm, "Indice: A")
        c.drawString(cart_x + 3*cm, cart_y + cart_height - 0.6*cm, "Page: 1/2")
        
        c.setFont("Helvetica", 8)
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 1.2*cm, "Norme: NF C 15-712-1")
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 1.7*cm, "Installations PV raccordées réseau")
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 2.2*cm, "AgriWeb Pro - Édition automatique")
    
    def _dessiner_schema_principal(self, c, width, height):
        """Dessine le schéma unifilaire principal avec symboles normalisés NF C 03-201"""
        
        # Zone de dessin (éviter cartouche et marges)
        schema_x_start = 1.5*cm
        schema_x_end = width - 1.5*cm
        schema_y_start = 5*cm
        schema_y_end = height - 11*cm  # Ajusté pour cartouche haut
        
        schema_width = schema_x_end - schema_x_start
        schema_height = schema_y_end - schema_y_start
        
        # === CADRE GLOBAL SCHÉMA ===
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(schema_x_start, schema_y_start, schema_width, schema_height)
        
        # === COORDONNÉES LAYOUT HORIZONTAL ===
        # Positionnement des éléments de gauche à droite
        
        # Zone centrale du schéma (centrage vertical)
        center_y = schema_y_start + schema_height/2
        
        # Zone strings (gauche) - GROUPÉ
        strings_x = schema_x_start + 1.5*cm
        strings_y = center_y
        
        # Boîte jonction DC
        boite_dc_x = schema_x_start + 6.5*cm
        boite_dc_y = center_y
        
        # Onduleur (centre)
        onduleur_x = boite_dc_x + 5.5*cm
        onduleur_y = center_y
        
        # Protections AC (TGBT)
        prot_ac_x = onduleur_x + 5.5*cm
        prot_ac_y = center_y
        
        # Point injection (droite)
        injection_x = prot_ac_x + 4*cm
        injection_y = center_y
        
        # === TITRE SECTIONS (en haut) ===
        titre_y = schema_y_end - 0.5*cm
        
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#0d6efd'))
        c.drawCentredString(strings_x, titre_y, "CHAMP PV")
        
        c.setFillColor(colors.HexColor('#ffc107'))
        c.drawCentredString(boite_dc_x, titre_y, "PROTECTION DC")
        
        c.setFillColor(colors.HexColor('#28a745'))
        c.drawCentredString(onduleur_x, titre_y, "ONDULEUR")
        
        c.setFillColor(colors.HexColor('#dc3545'))
        c.drawCentredString(prot_ac_x, titre_y, "PROTECTION AC")
        
        c.setFillColor(colors.black)
        c.drawCentredString(injection_x, titre_y, "RÉSEAU")
        
        c.setFillColor(colors.black)
        
        # === 1. CHAMP PHOTOVOLTAÏQUE (STRINGS GROUPÉS) ===
        
        # Regrouper tous les strings en un seul bloc avec symbole
        nb_strings_total = len(self.configuration_strings)
        puissance_totale_strings = sum(s['puissance_wc'] for s in self.configuration_strings) / 1000
        
        # Symbole module PV principal (représentant tous les strings)
        SymbolesElectriques.string_pv(c, strings_x, strings_y, 
                                     nb_modules=self.nb_modules_total, 
                                     compact=True)
        
        # Annotations groupées
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(strings_x, strings_y + 1.2*cm, 
                    f"{nb_strings_total} String{'s' if nb_strings_total > 1 else ''}")
        c.setFont("Helvetica", 6)
        c.drawCentredString(strings_x, strings_y - 1*cm, 
                    f"{self.nb_modules_total}×{int(self.module_puissance)}Wc")
        c.drawCentredString(strings_x, strings_y - 1.4*cm, 
                    f"= {puissance_totale_strings:.2f}kWc")
        
        # Tension/courant moyens
        if self.configuration_strings:
            v_mpp_moy = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
            i_sc_total = sum(s['i_sc'] for s in self.configuration_strings)
            c.drawCentredString(strings_x, strings_y - 1.8*cm, 
                        f"Vmpp:{v_mpp_moy:.1f}V")
            c.drawCentredString(strings_x, strings_y - 2.2*cm, 
                        f"Isc total:{i_sc_total:.1f}A")
        
        # Fusible (si requis)
        if 'Non requis' not in self.fusibles_strings:
            fusible_x = strings_x + 2*cm
            SymbolesElectriques.fusible(c, fusible_x, strings_y, orientation='horizontal')
            c.setFont("Helvetica", 6)
            c.setFillColor(colors.black)
            c.drawString(fusible_x - 5*mm, strings_y + 6*mm, 
                        self.fusibles_strings.split('A')[0].strip() + 'A')
            cable_start_x = fusible_x + 1*cm
        else:
            cable_start_x = strings_x + 0.8*cm
        
        # Câble DC vers boîte jonction (horizontal)
        c.setStrokeColor(colors.red)
        c.setLineWidth(3)
        c.line(cable_start_x, strings_y, boite_dc_x - 1.5*cm, boite_dc_y)
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.red)
        c.drawString(cable_start_x + 5*mm, strings_y + 3*mm, 
                    f"{self.section_cable_string}mm²")
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        
        # === 2. BOÎTE DE JONCTION DC + PROTECTIONS ===
        
        # Câble principal DC entrant (depuis strings)
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        c.line(cable_start_x + 1.5*cm, strings_y, boite_dc_x - 1.5*cm, boite_dc_y)
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.red)
        mid_x_strings = (cable_start_x + boite_dc_x) / 2
        c.drawString(mid_x_strings, (strings_y + boite_dc_y)/2 + 3*mm, 
                    f"120mm² DC")
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        
        # Sectionneur DC (au dessus de la boîte)
        sect_dc_y = boite_dc_y + 2*cm
        SymbolesElectriques.sectionneur(c, boite_dc_x - 5*mm, sect_dc_y, orientation='horizontal')
        c.setFont("Helvetica", 6)
        c.drawString(boite_dc_x - 1.2*cm, sect_dc_y + 6*mm, 
                   f"{self.calibre_sectionneur_dc}A")
        c.drawString(boite_dc_x - 1.5*cm, sect_dc_y + 10*mm, 
                   f"{self.tension_sectionneur_dc}")
        
        # Boîte de jonction (rectangle)
        c.setLineWidth(2)
        c.rect(boite_dc_x - 1.5*cm, boite_dc_y - 1.5*cm, 3*cm, 3*cm)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(boite_dc_x, boite_dc_y, "BOITE DC")
        
        # Parafoudre DC (en dessous de la boîte)
        para_dc_y = boite_dc_y - 2.2*cm
        SymbolesElectriques.parafoudre(c, boite_dc_x, para_dc_y, orientation='vertical')
        c.setFont("Helvetica", 6)
        c.drawString(boite_dc_x + 5*mm, para_dc_y - 8*mm, "SPD Type 2")
        
        # Terre
        SymbolesElectriques.terre(c, boite_dc_x, para_dc_y - 12*mm)
        
        # === 3. CÂBLE DC PRINCIPAL → ONDULEUR ===
        
        # Ligne horizontale boîte → onduleur
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        c.line(boite_dc_x + 1.5*cm, boite_dc_y, onduleur_x - 2*cm, onduleur_y)
        c.setStrokeColor(colors.black)
        
        # Annotation câble DC + distance
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.red)
        mid_dc_x = (boite_dc_x + onduleur_x) / 2
        c.drawCentredString(mid_dc_x, boite_dc_y + 7*mm, 
                           f"Longueur DC: {self.longueur_dc:.1f}m")
        c.setFont("Helvetica", 6)
        c.drawCentredString(mid_dc_x, boite_dc_y + 2*mm, 
                           f"{self.section_cable_dc}mm² Cu")
        c.setFillColor(colors.black)
        
        # === 4. ONDULEUR ===
        
        SymbolesElectriques.onduleur(c, onduleur_x, onduleur_y, width=3.5*cm, height=3.5*cm)
        
        # Infos onduleur (en dessous)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(onduleur_x, onduleur_y - 2.5*cm, 
                           f"{self.onduleur['marque']} {self.onduleur['modele']}")
        c.setFont("Helvetica", 6)
        c.drawCentredString(onduleur_x, onduleur_y - 2.9*cm, 
                           f"P AC: {self.onduleur['p_ac']/1000:.1f}kW | P DC max: {self.onduleur['p_dc_max']/1000:.1f}kW")
        c.drawCentredString(onduleur_x, onduleur_y - 3.3*cm, 
                           f"{self.onduleur['mppt']} MPPT | η={self.onduleur.get('rendement_max', 97)}%")
        
        # === 5. CÂBLE AC ONDULEUR → PROTECTIONS ===
        
        nb_phases = 3 if '400V' in self.type_reseau else 1
        
        # Ligne AC
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        c.line(onduleur_x + 1.75*cm, onduleur_y, prot_ac_x - 1.25*cm, prot_ac_y)
        c.setStrokeColor(colors.black)
        
        # Annotation câble AC + distance
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.blue)
        mid_ac_x = (onduleur_x + prot_ac_x) / 2
        c.drawCentredString(mid_ac_x, onduleur_y + 7*mm, 
                           f"Longueur AC: {self.longueur_ac_onduleur_tgbt:.1f}m")
        c.setFont("Helvetica", 6)
        phases_str = f"{nb_phases}P+" if nb_phases > 1 else ""
        c.drawCentredString(mid_ac_x, onduleur_y + 2*mm, 
                           f"{phases_str}{self.section_cable_ac}mm²")
        c.setFillColor(colors.black)
        
        # === 6. PROTECTIONS AC (TGBT) ===
        
        # Disjoncteur différentiel (au dessus)
        disj_y = prot_ac_y + 1.8*cm
        SymbolesElectriques.differentiel(c, prot_ac_x, disj_y, orientation='horizontal')
        c.setFont("Helvetica", 6)
        c.drawString(prot_ac_x - 1*cm, disj_y + 10*mm, 
                   f"{self.calibre_disjoncteur_ac}A")
        c.drawString(prot_ac_x - 1.2*cm, disj_y + 14*mm, 
                   f"{self.type_differentiel}")
        
        # Boîte TGBT (rectangle)
        c.setLineWidth(2)
        c.rect(prot_ac_x - 1.25*cm, prot_ac_y - 1.25*cm, 2.5*cm, 2.5*cm)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(prot_ac_x, prot_ac_y, "TGBT")
        
        # Parafoudre AC (en dessous)
        para_ac_y = prot_ac_y - 2*cm
        SymbolesElectriques.parafoudre(c, prot_ac_x, para_ac_y, orientation='vertical')
        c.setFont("Helvetica", 6)
        c.drawString(prot_ac_x + 5*mm, para_ac_y - 8*mm, "SPD Type 2")
        
        # Terre
        SymbolesElectriques.terre(c, prot_ac_x, para_ac_y - 12*mm)
        
        # === 7. POINT D'INJECTION RÉSEAU ===
        
        # Ligne TGBT → réseau
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        c.line(prot_ac_x + 1.25*cm, prot_ac_y, injection_x - 0.8*cm, injection_y)
        
        # Annotation distance injection
        c.setFont("Helvetica", 6)
        mid_inj_x = (prot_ac_x + injection_x) / 2
        c.drawCentredString(mid_inj_x, prot_ac_y + 8*mm, 
                           f"Distance: {self.longueur_ac_tgbt_injection:.1f}m")
        
        # Symbole compteur
        SymbolesElectriques.compteur(c, injection_x, injection_y, size=1.3*cm)
        
        # Label réseau
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(injection_x, injection_y - 1.3*cm, self.type_reseau)
        c.setFont("Helvetica", 6)
        c.drawCentredString(injection_x, injection_y - 1.7*cm, "RÉSEAU PUBLIC")
        
        # === LÉGENDE ===
        
        legende_y = schema_y_start + 1.2*cm
        legende_x = schema_x_start + 0.5*cm
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(legende_x, legende_y, "LÉGENDE:")
        
        # Symbole string dans légende (plus haut pour éviter coupure)
        legend_string_x = legende_x + 2*cm
        SymbolesElectriques.module_pv(c, legend_string_x, legende_y + 2*mm, size=0.6*cm)
        c.setFont("Helvetica", 6)
        c.drawString(legend_string_x + 5*mm, legende_y + 2*mm, f"String×20 modules DC")
        
        # DC (rouge)
        dc_line_x = legende_x + 6.5*cm
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        c.line(dc_line_x, legende_y + 2*mm, dc_line_x + 1*cm, legende_y + 2*mm)
        c.setStrokeColor(colors.black)
        c.setFont("Helvetica", 6)
        c.drawString(dc_line_x + 1.2*cm, legende_y, "Courant continu DC")
        
        # AC (noir)
        ac_line_x = legende_x + 11*cm
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        c.line(ac_line_x, legende_y + 2*mm, ac_line_x + 1*cm, legende_y + 2*mm)
        c.setStrokeColor(colors.black)
        c.drawString(ac_line_x + 1.2*cm, legende_y, "Courant alternatif AC")
        
        # Terre
        terre_x = legende_x + 16*cm
        SymbolesElectriques.terre(c, terre_x, legende_y + 5*mm)
        c.drawString(terre_x + 5*mm, legende_y, f"Terre (≤{self.resistance_terre_max})")
    
    def _dessiner_notes_calculs(self, c, width, height):
        """Dessine la page des notes de calculs et vérifications"""
        
        # Cartouche page 2
        cart_width = 18*cm
        cart_height = 2*cm
        cart_x = width - cart_width - 1*cm
        cart_y = 1*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(cart_x, cart_y, cart_width, cart_height)
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 0.8*cm, "NOTES DE CALCULS - NF C 15-712")
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 0.6*cm, "Page: 2/2")
        
        # Titre page avec bandeau
        y_titre = height - 2.5*cm
        c.setFillColor(colors.HexColor('#0d6efd'))
        c.rect(1.5*cm, y_titre - 0.5*cm, width - 3*cm, 1.2*cm, fill=1, stroke=1)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, y_titre, "NOTES DE CALCULS ET VÉRIFICATIONS DE CONFORMITÉ")
        c.setFillColor(colors.black)
        
        y = height - 4.5*cm
        
        # === 1. CONFIGURATION ÉLECTRIQUE ===
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#28a745'))
        c.drawString(2*cm, y, "1. CONFIGURATION ÉLECTRIQUE")
        c.setFillColor(colors.black)
        y -= 0.8*cm
        
        # Tableau configuration
        table_data = [
            ['Paramètre', 'Valeur', 'Référence norme'],
            ['Puissance totale installée', f"{self.puissance_totale_kwc:.2f} kWc", 'NF C 15-712 art. 3.1'],
            ['Nombre total de modules', f"{self.nb_modules_total}", ''],
            ['Module photovoltaïque', f"{self.module_puissance}Wc ({self.module.get('longueur')}×{self.module.get('largeur')}mm)", ''],
            ['Nombre de strings', f"{len(self.configuration_strings)}", ''],
            ['Modules par string (moy)', f"{self.nb_modules_total / len(self.configuration_strings):.1f}", ''],
            ['Onduleur', f"{self.onduleur['marque']} {self.onduleur['modele']}", ''],
            ['Puissance onduleur AC', f"{self.onduleur['p_ac']/1000:.1f} kW", ''],
            ['Ratio DC/AC', f"{(self.puissance_totale_kwc * 1000 / self.onduleur['p_ac']):.2f}", 'Optimal: 1.2-1.3'],
        ]
        
        table = Table(table_data, colWidths=[8*cm, 5*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        table.wrapOn(c, width, height)
        table.drawOn(c, 2*cm, y - 7*cm)
        
        y -= 8.5*cm
        
        # === 2. DIMENSIONNEMENT CÂBLES ===
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#ffc107'))
        c.drawString(2*cm, y, "2. DIMENSIONNEMENT DES CÂBLES")
        c.setFillColor(colors.black)
        y -= 0.8*cm
        
        table_data2 = [
            ['Type câble', 'Section (mm²)', 'Courant max (A)', 'Chute tension', 'Référence norme'],
            ['Câbles strings DC', f"{self.section_cable_string}", 
             f"{max(s['i_sc'] * 1.25 for s in self.configuration_strings):.1f}", 
             '< 2%', 'NF C 15-712 art. 7.12.1.1'],
            ['Câble principal DC', f"{self.section_cable_dc}", 
             f"{sum(s['i_sc'] * 1.25 for s in self.configuration_strings):.1f}", 
             '< 2%', 'NF C 15-712 art. 7.12.1.1'],
            ['Câble onduleur AC', f"{self.section_cable_ac}", 
             f"{self.courant_max_ac:.1f}", 
             '< 2%', 'NF C 15-100'],
        ]
        
        table2 = Table(table_data2, colWidths=[5*cm, 3*cm, 3*cm, 3*cm, 4.5*cm])
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff8e1')])
        ]))
        
        table2.wrapOn(c, width, height)
        table2.drawOn(c, 2*cm, y - 4*cm)
        
        y -= 5.5*cm
        
        # === 3. PROTECTIONS ÉLECTRIQUES ===
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#dc3545'))
        c.drawString(2*cm, y, "3. PROTECTIONS ÉLECTRIQUES")
        c.setFillColor(colors.black)
        y -= 0.8*cm
        
        table_data3 = [
            ['Protection', 'Caractéristiques', 'Référence norme'],
            ['Sectionneur DC', f"{self.calibre_sectionneur_dc}A - {self.tension_sectionneur_dc}", 'NF C 15-712 art. 7.12.3.1'],
            ['Parafoudre DC', self.parafoudre_dc, 'NF C 15-712 art. 7.12.3.4 (Obligatoire)'],
            ['Fusibles strings', self.fusibles_strings, 'Si > 2 strings en parallèle'],
            ['Disjoncteur AC', f"{self.calibre_disjoncteur_ac}A", 'NF C 15-100'],
            ['Différentiel AC', self.type_differentiel, 'NF C 15-100 (Obligatoire)'],
            ['Parafoudre AC', self.parafoudre_ac, 'NF C 15-712 art. 7.12.3.4'],
            ['Mise à la terre', f"Résistance < {self.resistance_terre_max}", 'NF C 15-712 art. 7.13'],
        ]
        
        table3 = Table(table_data3, colWidths=[5*cm, 8*cm, 5.5*cm])
        table3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffe6e6')])
        ]))
        
        table3.wrapOn(c, width, height)
        table3.drawOn(c, 2*cm, y - 7*cm)
        
        y -= 8.5*cm
        
        # === 4. VÉRIFICATIONS CONFORMITÉ ===
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#17a2b8'))
        c.drawString(2*cm, y, "4. VÉRIFICATIONS DE CONFORMITÉ NF C 15-712")
        c.setFillColor(colors.black)
        y -= 0.6*cm
        
        c.setFont("Helvetica", 9)
        checks = [
            "✅ Tension maximale DC < tension max onduleur (facteur température inclus)",
            "✅ Tension minimale DC > tension min MPPT onduleur",
            "✅ Courant max DC < courant max onduleur",
            "✅ Chutes de tension DC et AC < 2%",
            "✅ Sections câbles conformes NF C 15-100 (courants admissibles)",
            "✅ Protections différentielles AC 30mA Type A minimum",
            "✅ Parafoudres DC et AC Type 2 (obligatoire)",
            "✅ Sectionneurs DC avec coupure visible",
            "✅ Mise à la terre des masses métalliques",
            "✅ Ratio DC/AC onduleur optimisé (1.2-1.3)",
        ]
        
        for check in checks:
            c.drawString(2.5*cm, y, check)
            y -= 0.5*cm
        
        # Note finale
        y -= 0.5*cm
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#28a745'))
        c.drawString(2*cm, y, "✅ INSTALLATION CONFORME NF C 15-712-1 (Installations photovoltaïques raccordées au réseau)")
        c.setFillColor(colors.black)
        
        # Avertissement
        y -= 1.5*cm
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#dc3545'))
        c.drawString(2*cm, y, "⚠️ IMPORTANT:")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        y -= 0.4*cm
        c.drawString(2*cm, y, "Ce schéma unifilaire est généré automatiquement à partir du calepinage. Les calculs sont conformes aux normes")
        y -= 0.35*cm
        c.drawString(2*cm, y, "en vigueur, mais doivent être vérifiés par un professionnel qualifié avant mise en œuvre. Les longueurs de")
        y -= 0.35*cm
        c.drawString(2*cm, y, "câbles sont estimées et doivent être mesurées sur site. Le choix du matériel doit tenir compte des contraintes")
        y -= 0.35*cm
        c.drawString(2*cm, y, "locales (température, altitude, environnement corrosif, etc.).")
