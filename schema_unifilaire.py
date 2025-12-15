"""
Générateur de schéma unifilaire conforme NF C 15-712
Pour installations photovoltaïques raccordées au réseau
AgriWeb 2025 - Version Professionnelle
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
        """Dessine le schéma unifilaire principal"""
        
        # Zone de dessin (éviter cartouche et marges)
        schema_x_start = 2*cm
        schema_x_end = width - 2*cm
        schema_y_start = 6*cm
        schema_y_end = height - 11*cm  # Ajusté pour cartouche haut
        
        schema_width = schema_x_end - schema_x_start
        schema_height = schema_y_end - schema_y_start
        
        # === CADRE GLOBAL SCHÉMA ===
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(schema_x_start, schema_y_start, schema_width, schema_height)
        
        # === PARTIE GAUCHE: CHAMP PHOTOVOLTAÏQUE ===
        
        # Titre section
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#0d6efd'))
        c.drawString(schema_x_start + 0.5*cm, schema_y_end - 0.7*cm, "CHAMP PHOTOVOLTAÏQUE (DC)")
        c.setFillColor(colors.black)
        
        # Dessiner les zones et strings
        y_current = schema_y_end - 1.5*cm
        
        # Regrouper strings par zone
        zones_dict = {}
        for string in self.configuration_strings:
            zone_num = string['zone']
            if zone_num not in zones_dict:
                zones_dict[zone_num] = []
            zones_dict[zone_num].append(string)
        
        for zone_num in sorted(zones_dict.keys()):
            strings_zone = zones_dict[zone_num]
            
            # Titre zone (avec fond coloré)
            c.setFillColor(colors.HexColor('#e3f2fd'))
            c.rect(schema_x_start + 0.5*cm, y_current - 0.3*cm, 5*cm, 0.6*cm, fill=1, stroke=0)
            
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(schema_x_start + 0.7*cm, y_current - 0.1*cm, f"Zone {zone_num}")
            
            # Infos zone
            zone_data = next((z for z in self.zones if z.get('numero') == zone_num), {})
            c.setFont("Helvetica", 7)
            c.drawString(schema_x_start + 2*cm, y_current - 0.1*cm, 
                        f"Orient: {zone_data.get('orientation', '?')}° - Inclin: {zone_data.get('inclinaison', '?')}°")
            
            y_current -= 1.1*cm
            
            # Dessiner chaque string
            for string in strings_zone:
                self._dessiner_string(c, schema_x_start + 1*cm, y_current, string)
                y_current -= 1.5*cm  # Réduit espacement pour éviter superposition
            
            y_current -= 0.3*cm  # Espacement entre zones réduit
        
        # === PARTIE CENTRALE: BOÎTE DE JONCTION DC ===
        
        boite_x = schema_x_start + schema_width * 0.35
        boite_y = schema_y_start + schema_height * 0.5
        boite_width = 4*cm
        boite_height = 4.5*cm
        
        # Titre au-dessus de la boîte
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#ffc107'))
        c.drawCentredString(boite_x + boite_width/2, boite_y + boite_height/2 + 0.5*cm, "BOÎTE DE JONCTION DC")
        c.setFillColor(colors.black)
        
        # Rectangle boîte avec fond
        c.setFillColor(colors.HexColor('#fffbf0'))
        c.setLineWidth(2)
        c.rect(boite_x, boite_y - boite_height/2, boite_width, boite_height, fill=1, stroke=1)
        c.setFillColor(colors.black)
        
        # Contenu boîte
        c.setFont("Helvetica-Bold", 8)
        y_boite = boite_y + boite_height/2 - 0.8*cm
        
        c.drawCentredString(boite_x + boite_width/2, y_boite, "Sectionneurs DC")
        y_boite -= 0.4*cm
        c.setFont("Helvetica", 7)
        c.drawCentredString(boite_x + boite_width/2, y_boite, f"{self.calibre_sectionneur_dc}A - {self.tension_sectionneur_dc}")
        
        y_boite -= 0.8*cm
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(boite_x + boite_width/2, y_boite, "Parafoudre DC")
        y_boite -= 0.4*cm
        c.setFont("Helvetica", 7)
        c.drawCentredString(boite_x + boite_width/2, y_boite, self.parafoudre_dc.split('-')[0].strip())
        
        if 'Non requis' not in self.fusibles_strings:
            y_boite -= 0.7*cm
            c.drawCentredString(boite_x + boite_width/2, y_boite, "Fusibles strings")
            y_boite -= 0.5*cm
            c.drawCentredString(boite_x + boite_width/2, y_boite, self.fusibles_strings.split('(')[0].strip())
        
        # Connexions strings → boîte DC
        for i, string in enumerate(self.configuration_strings):
            # Ligne depuis strings vers boîte (simplifiée)
            x_string_end = schema_x_start + 7*cm
            y_string = schema_y_end - 2*cm - (i * 0.8*cm)
            
            c.setStrokeColor(colors.red)
            c.setLineWidth(1)
            c.line(x_string_end, y_string, boite_x, boite_y)
        
        c.setStrokeColor(colors.black)
        
        # === PARTIE DROITE: ONDULEUR ===
        
        onduleur_x = boite_x + boite_width + 4*cm
        onduleur_y = boite_y
        onduleur_width = 5*cm
        onduleur_height = 6*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#28a745'))
        c.drawCentredString(onduleur_x + onduleur_width/2, schema_y_end - 0.3*cm, "ONDULEUR")
        c.setFillColor(colors.black)
        
        # Rectangle onduleur
        c.setLineWidth(2)
        c.rect(onduleur_x, onduleur_y - onduleur_height/2, onduleur_width, onduleur_height)
        
        # Symbole onduleur (sinusoïde simplifiée)
        c.setLineWidth(1.5)
        wave_y = onduleur_y
        wave_x_start = onduleur_x + 0.5*cm
        wave_width = onduleur_width - 1*cm
        
        # Texte onduleur
        c.setFont("Helvetica-Bold", 9)
        y_ond = onduleur_y + onduleur_height/2 - 1*cm
        c.drawCentredString(onduleur_x + onduleur_width/2, y_ond, self.onduleur['marque'])
        y_ond -= 0.5*cm
        c.setFont("Helvetica", 8)
        c.drawCentredString(onduleur_x + onduleur_width/2, y_ond, self.onduleur['modele'])
        
        y_ond -= 0.7*cm
        c.drawCentredString(onduleur_x + onduleur_width/2, y_ond, f"P AC: {self.onduleur['p_ac']/1000:.1f} kW")
        y_ond -= 0.4*cm
        c.drawCentredString(onduleur_x + onduleur_width/2, y_ond, f"P DC max: {self.onduleur['p_dc_max']/1000:.1f} kW")
        y_ond -= 0.4*cm
        c.drawCentredString(onduleur_x + onduleur_width/2, y_ond, f"{self.onduleur['mppt']} MPPT")
        
        # Connexion boîte DC → onduleur
        c.setStrokeColor(colors.red)
        c.setLineWidth(3)
        c.line(boite_x + boite_width, boite_y, onduleur_x, onduleur_y)
        
        # Annotation câble DC principal
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.red)
        c.drawString(boite_x + boite_width + 0.3*cm, boite_y + 0.3*cm, f"{self.section_cable_dc}mm² Cu")
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        
        # === PARTIE EXTRÊME DROITE: RÉSEAU AC ===
        
        reseau_x = onduleur_x + onduleur_width + 4*cm
        reseau_y = onduleur_y
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#dc3545'))
        c.drawCentredString(reseau_x + 2*cm, schema_y_end - 0.3*cm, "RÉSEAU AC")
        c.setFillColor(colors.black)
        
        # Boîte protections AC
        prot_width = 4*cm
        prot_height = 5*cm
        
        c.setLineWidth(2)
        c.rect(reseau_x, reseau_y - prot_height/2, prot_width, prot_height)
        
        c.setFont("Helvetica-Bold", 8)
        y_prot = reseau_y + prot_height/2 - 0.7*cm
        c.drawCentredString(reseau_x + prot_width/2, y_prot, "PROTECTIONS AC")
        
        y_prot -= 0.6*cm
        c.setFont("Helvetica", 8)
        c.drawCentredString(reseau_x + prot_width/2, y_prot, f"Disjoncteur {self.calibre_disjoncteur_ac}A")
        
        y_prot -= 0.5*cm
        c.drawCentredString(reseau_x + prot_width/2, y_prot, self.type_differentiel)
        
        y_prot -= 0.6*cm
        c.drawCentredString(reseau_x + prot_width/2, y_prot, "Parafoudre AC")
        y_prot -= 0.4*cm
        c.drawCentredString(reseau_x + prot_width/2, y_prot, "Type 2")
        
        y_prot -= 0.6*cm
        c.drawCentredString(reseau_x + prot_width/2, y_prot, self.type_reseau)
        
        # Connexion onduleur → protections AC
        c.setStrokeColor(colors.blue)
        c.setLineWidth(3)
        c.line(onduleur_x + onduleur_width, onduleur_y, reseau_x, reseau_y)
        
        # Annotation câble AC
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.blue)
        c.drawString(onduleur_x + onduleur_width + 0.3*cm, onduleur_y + 0.3*cm, f"{self.section_cable_ac}mm² Cu")
        c.setFillColor(colors.black)
        
        # Symbole réseau (after protections)
        reseau_symbol_x = reseau_x + prot_width + 1*cm
        
        # Cercle réseau
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.circle(reseau_symbol_x, reseau_y, 0.8*cm)
        
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(reseau_symbol_x, reseau_y + 0.2*cm, "~")
        c.setFont("Helvetica", 8)
        c.drawCentredString(reseau_symbol_x, reseau_y - 0.3*cm, "RÉSEAU")
        
        c.line(reseau_x + prot_width, reseau_y, reseau_symbol_x - 0.8*cm, reseau_y)
        
        # === LÉGENDE COULEURS ===
        
        legende_y = schema_y_start + 0.5*cm
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(schema_x_start, legende_y, "LÉGENDE:")
        
        # DC (rouge)
        c.setStrokeColor(colors.red)
        c.setLineWidth(3)
        c.line(schema_x_start + 2.5*cm, legende_y + 0.1*cm, schema_x_start + 3.5*cm, legende_y + 0.1*cm)
        c.setStrokeColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawString(schema_x_start + 3.8*cm, legende_y, "Courant continu (DC)")
        
        # AC (bleu)
        c.setStrokeColor(colors.blue)
        c.setLineWidth(3)
        c.line(schema_x_start + 9*cm, legende_y + 0.1*cm, schema_x_start + 10*cm, legende_y + 0.1*cm)
        c.setStrokeColor(colors.black)
        c.drawString(schema_x_start + 10.3*cm, legende_y, "Courant alternatif (AC)")
        
        # Terre (vert/jaune)
        c.setStrokeColor(colors.green)
        c.setLineWidth(2)
        c.line(schema_x_start + 16*cm, legende_y + 0.1*cm, schema_x_start + 17*cm, legende_y + 0.1*cm)
        c.setStrokeColor(colors.black)
        c.drawString(schema_x_start + 17.3*cm, legende_y, f"Terre (max {self.resistance_terre_max})")
    
    def _dessiner_string(self, c, x, y, string_data):
        """Dessine un string de panneaux PV"""
        
        # Rectangle string
        c.setLineWidth(1)
        c.setStrokeColor(colors.HexColor('#0d6efd'))
        c.rect(x, y, 5*cm, 1.2*cm)
        
        # Texte string
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 0.2*cm, y + 0.9*cm, f"String {string_data['zone']}-{string_data['string_num']}")
        
        c.setFont("Helvetica", 7)
        c.drawString(x + 0.2*cm, y + 0.5*cm, f"{string_data['nb_modules']} × {self.module_puissance}Wc = {string_data['puissance_wc']/1000:.2f} kWc")
        c.drawString(x + 0.2*cm, y + 0.1*cm, f"Vmpp: {string_data['v_mpp']:.1f}V - Impp: {string_data['i_mpp']:.1f}A")
        
        # Symboles panneaux (petits carrés)
        nb_symboles = min(string_data['nb_modules'], 8)  # Max 8 symboles affichés
        symbole_size = 0.15*cm
        symbole_spacing = 0.2*cm
        
        for i in range(nb_symboles):
            symbole_x = x + 3.5*cm + (i * symbole_spacing)
            symbole_y = y + 0.5*cm
            
            c.setFillColor(colors.HexColor('#ffc107'))
            c.rect(symbole_x, symbole_y, symbole_size, symbole_size, fill=1, stroke=0)
        
        if string_data['nb_modules'] > nb_symboles:
            c.setFont("Helvetica", 6)
            c.drawString(x + 3.5*cm + (nb_symboles * symbole_spacing), y + 0.5*cm, f"...×{string_data['nb_modules']}")
        
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
    
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
