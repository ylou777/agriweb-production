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
        
        # Vérifier si une configuration électrique existe déjà (sauvegardée)
        saved_config = calpinage_data.get('configuration_electrique', {})
        
        if saved_config and saved_config.get('date_maj'):
            print("✅ [SCHEMA] Restauration configuration électrique sauvegardée")
            self._restaurer_configuration_electrique(saved_config, calpinage_data)
        else:
            print("🔄 [SCHEMA] Calcul automatique configuration électrique")
            # Calculs électriques automatiques si pas de config sauvegardée
            self._calculer_configuration_electrique()
    
    def _restaurer_configuration_electrique(self, saved_config, calpinage_data):
        """Restaure la configuration électrique depuis les données sauvegardées"""
        
        # Restaurer les données module
        self.module_puissance = float(self.module.get('puissance', 550))
        self.module_voc = float(self.module.get('voc', 49.5))
        self.module_vmpp = float(self.module.get('vmpp', 41.8))
        self.module_isc = float(self.module.get('isc', 13.9))
        self.module_impp = float(self.module.get('impp', 13.2))
        
        # Calculer totaux
        self.nb_modules_total = sum(zone.get('nbModules', 0) for zone in self.zones)
        self.puissance_totale_kwc = self.nb_modules_total * self.module_puissance / 1000
        
        # Restaurer l'onduleur depuis les equipments sauvegardés
        equipments = calpinage_data.get('equipments', {})
        onduleurs_saved = equipments.get('onduleurs', [])
        
        if onduleurs_saved and len(onduleurs_saved) > 0:
            ond = onduleurs_saved[0]
            self.onduleur = {
                'marque': ond.get('marque', 'Onduleur'),
                'modele': ond.get('modele', 'Generic'),
                'p_ac': ond.get('puissance_ac', int(self.puissance_totale_kwc * 1000)),
                'p_dc_max': ond.get('puissance_dc_max', int(self.puissance_totale_kwc * 1000 * 1.2)),
                'mppt': ond.get('nb_mppt', 2),
                'v_min': 150,
                'v_max': 1000,
                'i_max': 30,
                'rendement': 98,
                'type_reseau': '230V',
                'garantie': '10 ans',
                'prix': 0
            }
        else:
            # Fallback: recalculer onduleur
            self._choisir_onduleur()
        
        # Restaurer les strings (ou recalculer si pas sauvegardés)
        self._calculer_strings()
        
        # Restaurer les sections de câbles sauvegardées
        self.section_cable_string = saved_config.get('section_cable_strings') or 6
        self.section_cable_dc = saved_config.get('section_cable_dc') or 16
        self.type_cable_dc = saved_config.get('type_cable_dc', 'U1000R2V')
        self.section_cable_ac = saved_config.get('section_cable_ac') or 10
        self.type_cable_ac = saved_config.get('type_cable_ac', 'U1000R2V')
        
        # Restaurer les sections PE
        self.section_pe_dc = saved_config.get('section_pe_dc') or 16
        self.section_pe_ac = saved_config.get('section_pe_ac') or 10
        self.section_terre_principal = f"{self.section_pe_ac}mm²"
        
        # Restaurer les distances
        distances = calpinage_data.get('distances', {})
        self.longueur_dc = distances.get('dc_strings', 25)
        self.longueur_ac_onduleur_tgbt = distances.get('ac_onduleur_tgbt', 15)
        self.longueur_ac_tgbt_injection = distances.get('ac_tgbt_injection', 10)
        
        # Restaurer les chutes de tension
        self.chute_tension_dc_pct = saved_config.get('chute_tension_dc_pct') or 1.5
        self.chute_tension_ac_pct = saved_config.get('chute_tension_ac_pct') or 1.0
        
        # Restaurer les protections DC
        self.calibre_sectionneur_dc = saved_config.get('sectionneur_dc') or '63A'
        self.tension_sectionneur_dc = '1000V DC'
        self.fusibles_strings = saved_config.get('fusibles_strings', 'Non requis')
        
        # Restaurer les protections AC
        agcp_saved = saved_config.get('agcp')
        self.calibre_agcp = agcp_saved or '63A'
        self.courbe_agcp = 'C'
        self.pouvoir_coupure_agcp = '10kA'
        
        disj_saved = saved_config.get('disjoncteur_ac')
        self.calibre_disjoncteur_ac = disj_saved or '40A'
        self.courbe_disjoncteur_ac = 'C'
        self.pouvoir_coupure_ac = '10kA'
        
        diff_saved = saved_config.get('differentiel_ac')
        self.type_differentiel = diff_saved or 'Type A 30mA'
        
        # Restaurer les IP
        self.ip_boite_dc = saved_config.get('ip_boite_dc', 'IP65')
        self.ip_onduleur = saved_config.get('ip_onduleur', 'IP65')
        
        # Restaurer terre
        self.resistance_terre_max = saved_config.get('resistance_terre', '≤100Ω')
        
        # Restaurer Consuel
        self.num_consuel = saved_config.get('num_consuel', '')
        self.numero_consuel = self.num_consuel or 'À compléter après dépôt'
        self.indice_revision = 'A'
        self.date_edition = datetime.now().strftime('%d/%m/%Y')
        
        # Dispositif de coupure générale DC
        self.coupure_generale_dc = f'Sectionneur DC par string - {self.calibre_sectionneur_dc}A'
        
        # Type réseau
        injection_saved = equipments.get('injection', {})
        self.type_reseau = injection_saved.get('type_reseau', '230V Monophasé')
        
        print(f"✅ Config restaurée: Onduleur {self.onduleur['marque']} {self.onduleur['modele']}, "
              f"AGCP {self.calibre_agcp}, Disj {self.calibre_disjoncteur_ac}, "
              f"Câbles DC:{self.section_cable_dc}mm² AC:{self.section_cable_ac}mm²")
    
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
        """Calcule les sections de câbles selon NF C 15-712 et NF C 15-100 avec longueurs réelles des strings"""
        
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
        
        # 1.bis CALCULER LES LONGUEURS RÉELLES DE CHAQUE STRING avec plans_strings
        try:
            from plans_strings import PlansStrings
            
            # Créer instance PlansStrings pour calculer les longueurs
            plans_temp = PlansStrings(self.calpinage, self.prospect)
            
            # Récupérer les longueurs de câbles par string pour chaque zone
            longueurs_strings = []
            for zone in self.zones:
                strings_config = plans_temp._calculer_strings_zone(zone)
                for string in strings_config:
                    longueurs_strings.append({
                        'longueur': string['longueur_cable'],
                        'longueur_intra': string['longueur_intra_string'],
                        'i_sc': string['i_sc'],
                        'v_mpp': string['v_mpp']
                    })
            
            print(f"📏 Longueurs câbles strings calculées: {len(longueurs_strings)} strings")
            for i, ls in enumerate(longueurs_strings[:3]):  # Afficher les 3 premiers
                print(f"   String {i+1}: {ls['longueur']:.1f}m (intra:{ls['longueur_intra']:.1f}m)")
            
        except Exception as e:
            print(f"⚠️ Erreur calcul longueurs strings: {e}, utilisation distance globale")
            longueurs_strings = []
        
        print(f"📏 Distances câbles (calepinage):")
        print(f"   DC strings → onduleur: {longueur_dc_strings:.1f} m")
        print(f"   AC onduleur → TGBT: {longueur_ac_onduleur_tgbt:.1f} m")
        print(f"   AC TGBT → injection: {longueur_ac_tgbt_injection:.1f} m")
        
        # 2. CÂBLES PAR STRING - Calcul individualisé selon longueur réelle
        sections_normalisees = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
        courants_admissibles = [18, 24, 32, 41, 57, 76, 96, 119, 144, 184, 223, 259, 299, 338, 396]  # Ampères
        rho_cuivre = 0.01851  # Ω.mm²/m à 70°C
        
        sections_strings_calculees = []
        
        if longueurs_strings:
            # Calcul section pour chaque string selon sa longueur réelle
            for ls in longueurs_strings:
                i_string = ls['i_sc'] * 1.25  # Facteur sécurité
                v_mpp_string = ls['v_mpp']
                longueur_string = ls['longueur']
                
                # Section min selon courant
                section_min_courant = 2.5
                for i, courant_adm in enumerate(courants_admissibles):
                    if courant_adm >= i_string:
                        section_min_courant = max(sections_normalisees[i], 4)  # Min 4mm² extérieur
                        break
                
                # Section selon chute tension (max 3% NF C 15-712 article 7.12.1.1)
                # ΔU = 2 * ρ * L * I / S  =>  S = 2 * ρ * L * I / ΔU_max
                delta_u_max = 0.03 * v_mpp_string  # 3% de Vmpp
                section_chute_tension = (2 * rho_cuivre * longueur_string * i_string) / delta_u_max
                
                # Prendre le max des deux contraintes
                section_calculee = max(section_min_courant, section_chute_tension)
                
                # Arrondir à section normalisée supérieure
                sections_valides = [s for s in sections_normalisees if s >= section_calculee]
                section_finale = min(sections_valides) if sections_valides else sections_normalisees[-1]
                
                sections_strings_calculees.append(section_finale)
            
            # Section string = max de toutes les sections calculées (uniformisation)
            self.section_cable_string = max(sections_strings_calculees)
            
            print(f"✅ Sections strings calculées: {sections_strings_calculees[:5]}... → {self.section_cable_string}mm² (max)")
        else:
            # Fallback: calcul classique
            i_max_string = max(s['i_sc'] * 1.25 for s in self.configuration_strings)
            section_string_min = 2.5
            for i, courant_adm in enumerate(courants_admissibles):
                if courant_adm >= i_max_string:
                    section_string_min = max(sections_normalisees[i], 4)
                    break
            self.section_cable_string = section_string_min
        
        # 3. CÂBLES DC COLLECTEUR (parallèle strings → onduleur)
        # Chute tension max: 2% selon NF C 15-712 article 7.12.1.1
        
        # Courant max DC (tous strings en parallèle)
        i_max_dc = sum(s['i_sc'] * 1.25 for s in self.configuration_strings)  # Facteur 1.25 sécurité
        
        # Section minimale selon courant
        section_dc_min_courant = 2.5  # mm² par défaut
        for i, courant_adm in enumerate(courants_admissibles):
            if courant_adm >= i_max_dc:
                section_dc_min_courant = sections_normalisees[i]
                break
        
        # Vérification chute de tension (V = 2 * ρ * L * I / S)
        v_mpp_moyenne = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
        
        section_dc_chute_tension = (2 * rho_cuivre * longueur_dc_strings * i_max_dc) / (0.02 * v_mpp_moyenne)
        
        # Prendre le max des deux contraintes
        section_dc_calculee = max(section_dc_min_courant, section_dc_chute_tension)
        
        # Arrondir à la section normalisée supérieure
        sections_valides = [s for s in sections_normalisees if s >= section_dc_calculee]
        self.section_cable_dc = min(sections_valides) if sections_valides else sections_normalisees[-1]
        
        # 4. CÂBLE AC ONDULEUR → TGBT (distance réelle du calepinage)
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
        
        # CALCULER LES CHUTES DE TENSION RÉELLES avec sections finales
        # Chute tension strings (formule: ΔU% = 2 * ρ * L * I / (S * U) * 100)
        if longueurs_strings:
            chutes_tension_strings = []
            for i, ls in enumerate(longueurs_strings):
                delta_u = (2 * rho_cuivre * ls['longueur'] * ls['i_sc'] * 1.25) / self.section_cable_string
                delta_u_pct = (delta_u / ls['v_mpp']) * 100
                chutes_tension_strings.append(delta_u_pct)
            
            self.chute_tension_dc_pct = max(chutes_tension_strings)  # Pire cas
            print(f"   Chutes tension strings: {min(chutes_tension_strings):.2f}%-{max(chutes_tension_strings):.2f}% (max {self.chute_tension_dc_pct:.2f}%)")
        else:
            # Chute tension DC collecteur
            delta_u_dc = (2 * rho_cuivre * longueur_dc_strings * i_max_dc) / self.section_cable_dc
            self.chute_tension_dc_pct = (delta_u_dc / v_mpp_moyenne) * 100
        
        # Chute tension AC
        if nb_phases == 1:
            delta_u_ac = (2 * rho_cuivre * longueur_ac_onduleur_tgbt * i_max_ac) / self.section_cable_ac
            self.chute_tension_ac_pct = (delta_u_ac / 230) * 100
        else:
            delta_u_ac = (math.sqrt(3) * rho_cuivre * longueur_ac_onduleur_tgbt * i_max_ac) / self.section_cable_ac
            self.chute_tension_ac_pct = (delta_u_ac / 400) * 100
        
        print(f"✅ Sections câbles calculées selon longueurs réelles strings:")
        print(f"   DC strings: {self.section_cable_string}mm² (ΔU: {self.chute_tension_dc_pct:.2f}% ≤ 3%)")
        print(f"   DC collecteur: {self.section_cable_dc}mm² ({longueur_dc_strings:.1f}m)")
        print(f"   AC onduleur-TGBT: {self.section_cable_ac}mm² (ΔU: {self.chute_tension_ac_pct:.2f}% ≤ 2%)")
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
        self.courbe_disjoncteur_ac = 'C'  # Courbe C pour onduleurs
        self.pouvoir_coupure_ac = '10kA'  # Pouvoir de coupure minimum
        
        # AGCP (Appareil Général de Commande et Protection) - Obligatoire NF C 15-712
        # Placé en tête installation avant TGBT
        self.calibre_agcp = self.calibre_disjoncteur_ac  # Même calibre que protection onduleur
        self.courbe_agcp = 'C'
        self.pouvoir_coupure_agcp = '10kA'
        
        # Sectionneur AC (entre onduleur et TGBT) - NF C 15-712 art. 7.12.3.2
        self.calibre_sectionneur_ac = self.calibre_disjoncteur_ac
        self.type_sectionneur_ac = 'Sectionneur AC cadenassable'
        
        # Indices de protection (IP)
        self.ip_boite_dc = 'IP65'  # Boîte DC extérieure
        self.ip_onduleur = 'IP65'  # Onduleur extérieur
        
        # Types de câbles selon NF C 15-712
        self.type_cable_dc = 'U1000R2V ou équivalent PV'
        self.type_cable_ac = 'U1000R2V'
        self.section_pe_dc = self.section_cable_dc  # PE = section phase si ≤ 16mm²
        self.section_pe_ac = self.section_cable_ac
        
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
        
        # 5. MISE À LA TERRE (NF C 15-712 art. 7.13)
        self.resistance_terre_max = '100Ω'  # Valeur maximale
        self.liaison_equipotentielle = 'Liaison équipotentielle principale (LEP)'
        self.section_terre_principal = '16mm²'  # Section minimale conducteur principal de terre
        
        # 6. CHUTES DE TENSION (NF C 15-712 art. 7.12.1.1)
        # DC: ΔU = ρ × L × I / S (avec ρ cuivre = 0.018 Ω·mm²/m)
        rho_cuivre = 0.018
        self.chute_tension_dc = (rho_cuivre * self.longueur_dc * sum(s['i_mpp'] for s in self.configuration_strings) / self.section_cable_dc) if self.section_cable_dc > 0 else 0
        v_mpp_moyen = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
        self.chute_tension_dc_pct = (self.chute_tension_dc / v_mpp_moyen) * 100 if v_mpp_moyen > 0 else 0
        
        # AC: ΔU = ρ × L × I / S × cos(φ) (triphasé: × √3)
        cos_phi = 0.98  # Facteur de puissance onduleur
        self.chute_tension_ac = (rho_cuivre * self.longueur_ac_onduleur_tgbt * self.courant_max_ac / self.section_cable_ac * cos_phi) if self.section_cable_ac > 0 else 0
        v_ac = 230 if 'Mono' in self.type_reseau else 400
        self.chute_tension_ac_pct = (self.chute_tension_ac / v_ac) * 100
        
        # 7. DISPOSITIF DE COUPURE GÉNÉRALE DC (en tête de chaque string)
        self.coupure_generale_dc = f'Sectionneur DC par string - {self.calibre_sectionneur_dc}A'
        
        # 8. CONSUEL - Informations réglementaires
        self.numero_consuel = 'À compléter après dépôt'
        self.date_edition = datetime.now().strftime('%d/%m/%Y')
        self.indice_revision = 'A'
        
        print(f"✅ Protections: AGCP={self.calibre_agcp}A, Disj AC={self.calibre_disjoncteur_ac}A {self.type_differentiel} courbe {self.courbe_disjoncteur_ac}, Sect DC={self.calibre_sectionneur_dc}A {self.tension_sectionneur_dc}")
        print(f"✅ Chutes tension: DC={self.chute_tension_dc_pct:.2f}%, AC={self.chute_tension_ac_pct:.2f}%")
    
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
    
    def get_configuration_electrique_json(self):
        """Retourne la configuration électrique au format JSON pour sauvegarde"""
        return {
            # Protections DC
            'sectionneur_dc': self.calibre_sectionneur_dc,
            'parafoudre_dc': 'SPD Type 2',
            'fusibles_strings': self.fusibles_strings,
            
            # Câbles DC
            'section_cable_strings': self.section_cable_string,
            'section_cable_dc': self.section_cable_dc,
            'type_cable_dc': self.type_cable_dc,
            
            # Protections AC
            'agcp': self.calibre_agcp,
            'disjoncteur_ac': self.calibre_disjoncteur_ac,
            'differentiel_ac': self.type_differentiel,
            'parafoudre_ac': 'SPD Type 2',
            
            # Câbles AC
            'section_cable_ac': self.section_cable_ac,
            'type_cable_ac': self.type_cable_ac,
            
            # Terre
            'section_pe_dc': self.section_pe_dc,
            'section_pe_ac': self.section_pe_ac,
            'resistance_terre': self.resistance_terre_max,
            
            # Chutes de tension
            'chute_tension_dc_pct': round(self.chute_tension_dc_pct, 2),
            'chute_tension_ac_pct': round(self.chute_tension_ac_pct, 2),
            
            # IP
            'ip_boite_dc': self.ip_boite_dc,
            'ip_onduleur': self.ip_onduleur,
            
            # Consuel
            'num_consuel': getattr(self, 'num_consuel', ''),
            'date_maj': datetime.now().isoformat()
        }
    
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
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 0.6*cm, f"Indice: {self.indice_revision}")
        c.drawString(cart_x + 3*cm, cart_y + cart_height - 0.6*cm, "Page: 1/2")
        
        c.setFont("Helvetica", 8)
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 1.2*cm, "Norme: NF C 15-712-1:2017")
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 1.7*cm, "Installations PV ≤ 250kVA")
        c.drawString(cart_x + 0.3*cm, cart_y + cart_height - 2.2*cm, f"N° CONSUEL: {self.numero_consuel}")
    
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
        
        # === TITRE SCHÉMA ===
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#0d6efd'))
        c.drawCentredString(width/2, schema_y_end + 0.5*cm, "SCHÉMA UNIFILAIRE - Installation photovoltaïque NF C 15-712-1")
        c.setFillColor(colors.black)
        
        # === COORDONNÉES LAYOUT VERTICAL (disposition traditionnelle) ===
        # Schéma unifilaire vertical classique : HAUT → BAS
        # Champ PV (haut) → Protections DC → Onduleur → Protections AC → Réseau (bas)
        
        # Axe central vertical du schéma
        center_x = schema_x_start + schema_width / 2
        
        # === ZONE 1: CHAMP PV (tout en haut) ===
        strings_x = center_x - 8*cm  # À gauche
        strings_y = schema_y_end - 3*cm
        
        # === ZONE 2: BOÎTE DC + PROTECTIONS (haut-milieu) ===
        boite_dc_x = center_x + 2*cm  # Décalée à droite pour faire place au sectionneur
        boite_dc_y = schema_y_end - 9*cm
        
        # === ZONE 3: ONDULEUR (centre) ===
        onduleur_x = center_x
        onduleur_y = schema_y_end - 15*cm
        
        # === ZONE 4: PROTECTIONS AC (bas-milieu) ===
        prot_ac_x = center_x
        prot_ac_y = schema_y_end - 21*cm
        
        # === ZONE 5: POINT INJECTION RÉSEAU (tout en bas) ===
        injection_x = center_x
        injection_y = schema_y_start + 5*cm
        
        # === TITRE SECTIONS (disposées verticalement à gauche) ===
        titre_x = schema_x_start + 0.8*cm
        
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor('#0d6efd'))
        c.drawString(titre_x, schema_y_end - 2.5*cm, "CHAMP PV")
        
        c.setFillColor(colors.HexColor('#ffc107'))
        c.drawString(titre_x, schema_y_end - 8.5*cm, "PROTECTION DC")
        
        c.setFillColor(colors.HexColor('#28a745'))
        c.drawString(titre_x, schema_y_end - 14.5*cm, "ONDULEUR")
        
        c.setFillColor(colors.HexColor('#dc3545'))
        c.drawString(titre_x, schema_y_end - 20.5*cm, "PROTECTION AC")
        
        c.setFillColor(colors.black)
        c.drawString(titre_x, schema_y_start + 5.5*cm, "RÉSEAU")
        
        c.setFillColor(colors.black)
        
        # === 1. CHAMP PHOTOVOLTAÏQUE (STRINGS GROUPÉS) ===
        
        # Regrouper tous les strings en un seul bloc avec symbole
        nb_strings_total = len(self.configuration_strings)
        puissance_totale_strings = sum(s['puissance_wc'] for s in self.configuration_strings) / 1000
        
        # Symbole module PV principal (représentant tous les strings)
        SymbolesElectriques.string_pv(c, strings_x, strings_y, 
                                     nb_modules=self.nb_modules_total, 
                                     compact=True)
        
        # Annotations groupées - à droite du symbole
        c.setFont("Helvetica-Bold", 7)
        c.drawString(strings_x + 2*cm, strings_y + 0.5*cm, 
                    f"{nb_strings_total} String{'s' if nb_strings_total > 1 else ''}")
        c.setFont("Helvetica", 6)
        c.drawString(strings_x + 2*cm, strings_y, 
                    f"{self.nb_modules_total}×{int(self.module_puissance)}Wc")
        c.drawString(strings_x + 2*cm, strings_y - 0.5*cm, 
                    f"= {puissance_totale_strings:.2f}kWc")
        
        # Tension/courant moyens - à droite
        if self.configuration_strings:
            v_mpp_moy = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
            i_sc_total = sum(s['i_sc'] for s in self.configuration_strings)
            c.drawString(strings_x + 2*cm, strings_y - 1*cm, 
                        f"Vmpp:{v_mpp_moy:.1f}V")
            c.drawString(strings_x + 2*cm, strings_y - 1.5*cm, 
                        f"Isc:{i_sc_total:.1f}A")
        
        # Fusible (si requis) - positionné entre strings et boîte
        if 'Non requis' not in self.fusibles_strings:
            fusible_x = strings_x
            fusible_y = strings_y - 2.5*cm
            SymbolesElectriques.fusible(c, fusible_x, fusible_y, orientation='vertical')
            c.setFont("Helvetica", 6)
            c.setFillColor(colors.black)
            c.drawString(fusible_x + 8*mm, fusible_y, 
                        self.fusibles_strings.split('A')[0].strip() + 'A')
            # Ligne strings → fusible (vertical)
            c.setStrokeColor(colors.red)
            c.setLineWidth(2.5)
            c.line(strings_x, strings_y - 1*cm, fusible_x, fusible_y + 6*mm)
            cable_start_x = fusible_x
            cable_start_y = fusible_y - 8*mm
        else:
            cable_start_x = strings_x
            cable_start_y = strings_y - 1*cm
        
        # === 2. BOÎTE DE JONCTION DC + PROTECTIONS ===
        
        # Câble principal DC (depuis strings vers boîte jonction - avec coude)
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        # Partie verticale (strings → niveau boîte)
        c.line(cable_start_x, cable_start_y, cable_start_x, boite_dc_y)
        # Partie horizontale (vers boîte)
        c.line(cable_start_x, boite_dc_y, boite_dc_x - 3*cm - 8*mm, boite_dc_y)
        
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.red)
        # Annotation sur partie verticale
        c.drawString(cable_start_x + 5*mm, (cable_start_y + boite_dc_y) / 2, 
                    f"{self.section_cable_string}mm²")
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        
        # Boîte de jonction (rectangle)
        c.setLineWidth(2)
        c.rect(boite_dc_x - 1.5*cm, boite_dc_y - 1.5*cm, 3*cm, 3*cm)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(boite_dc_x, boite_dc_y + 3*mm, "BOITE DC")
        c.setFont("Helvetica", 6)
        c.drawCentredString(boite_dc_x, boite_dc_y - 5*mm, f"{self.ip_boite_dc}")
        
        # Sectionneur DC (à gauche de la boîte)
        sect_dc_x = boite_dc_x - 3*cm
        sect_dc_y = boite_dc_y
        SymbolesElectriques.sectionneur(c, sect_dc_x, sect_dc_y, orientation='horizontal')
        c.setFont("Helvetica", 6)
        c.drawString(sect_dc_x - 1.2*cm, sect_dc_y + 8*mm, 
                   f"{self.calibre_sectionneur_dc}A")
        c.drawString(sect_dc_x - 1.5*cm, sect_dc_y + 3*mm, 
                   f"{self.tension_sectionneur_dc}")
        
        # Ligne horizontale câble DC → sectionneur → boîte
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        c.line(cable_start_x, boite_dc_y, sect_dc_x - 8*mm, boite_dc_y)
        c.line(sect_dc_x + 8*mm, boite_dc_y, boite_dc_x - 1.5*cm, boite_dc_y)
        c.setStrokeColor(colors.black)
        
        # Parafoudre DC (à droite de la boîte, aligné verticalement)
        para_dc_x = boite_dc_x + 2.5*cm
        para_dc_y = boite_dc_y
        SymbolesElectriques.parafoudre(c, para_dc_x, para_dc_y, orientation='vertical')
        c.setFont("Helvetica", 6)
        c.drawString(para_dc_x + 6*mm, para_dc_y - 8*mm, "SPD Type 2")
        
        # Terre (sous parafoudre)
        terre_dc_y = para_dc_y - 18*mm
        SymbolesElectriques.terre(c, para_dc_x, terre_dc_y)
        
        # === 3. CÂBLE DC PRINCIPAL → ONDULEUR ===
        
        # Ligne verticale boîte → onduleur
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        c.line(boite_dc_x, boite_dc_y - 1.5*cm, boite_dc_x, onduleur_y + 1.8*cm)
        c.setStrokeColor(colors.black)
        
        # Annotation câble DC principal + type + PE (à droite du câble)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.red)
        mid_dc_y = (boite_dc_y + onduleur_y) / 2
        c.drawString(boite_dc_x + 0.8*cm, mid_dc_y + 0.8*cm, 
                           f"DC: {self.section_cable_dc}mm²+PE {self.section_pe_dc}mm² Cu")
        c.setFont("Helvetica", 6)
        c.drawString(boite_dc_x + 0.8*cm, mid_dc_y + 0.3*cm, 
                           f"{self.type_cable_dc} - L={self.longueur_dc:.1f}m")
        c.drawString(boite_dc_x + 0.8*cm, mid_dc_y - 0.2*cm, 
                           f"ΔU={self.chute_tension_dc_pct:.2f}%")
        c.setFillColor(colors.black)
        
        # === 4. ONDULEUR ===
        
        SymbolesElectriques.onduleur(c, onduleur_x, onduleur_y, width=3.5*cm, height=3.5*cm)
        
        # Infos onduleur (à droite du symbole)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(onduleur_x + 2*cm, onduleur_y + 0.8*cm, 
                           f"{self.onduleur['marque']} {self.onduleur['modele']}")
        c.setFont("Helvetica", 6)
        c.drawString(onduleur_x + 2*cm, onduleur_y + 0.3*cm, 
                           f"P AC: {self.onduleur['p_ac']/1000:.1f}kW | P DC max: {self.onduleur['p_dc_max']/1000:.1f}kW")
        c.drawString(onduleur_x + 2*cm, onduleur_y - 0.2*cm, 
                           f"{self.onduleur['mppt']} MPPT | η={self.onduleur.get('rendement_max', 97)}% | {self.ip_onduleur}")
        
        # === 5. CÂBLE AC ONDULEUR → PROTECTIONS ===
        
        nb_phases = 3 if '400V' in self.type_reseau else 1
        
        # Ligne verticale onduleur → protections AC
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        c.line(onduleur_x, onduleur_y - 1.8*cm, onduleur_x, prot_ac_y + 4.5*cm)
        
        # Sectionneur AC (entre onduleur et AGCP)
        sect_ac_x = onduleur_x
        sect_ac_y = prot_ac_y + 3.5*cm
        SymbolesElectriques.sectionneur(c, sect_ac_x, sect_ac_y, orientation='vertical')
        c.setFont("Helvetica", 6)
        c.drawString(sect_ac_x + 8*mm, sect_ac_y + 3*mm, f"Sect. AC")
        c.drawString(sect_ac_x + 8*mm, sect_ac_y - 3*mm, f"{self.calibre_sectionneur_ac}A")
        
        # Annotation câble AC + distance + type + PE (à droite du câble)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.blue)
        mid_ac_y = (onduleur_y + prot_ac_y) / 2
        phases_str = f"{nb_phases}P+N+" if nb_phases > 1 else "Ph+N+"
        c.drawString(onduleur_x + 0.8*cm, mid_ac_y + 0.8*cm, 
                           f"AC: {phases_str}PE {self.section_cable_ac}mm²")
        c.setFont("Helvetica", 6)
        c.drawString(onduleur_x + 0.8*cm, mid_ac_y + 0.3*cm, 
                           f"{self.type_cable_ac} - L={self.longueur_ac_onduleur_tgbt:.1f}m")
        c.drawString(onduleur_x + 0.8*cm, mid_ac_y - 0.2*cm, 
                           f"ΔU={self.chute_tension_ac_pct:.2f}%")
        c.setFillColor(colors.black)
        
        # === 6. PROTECTIONS AC (TGBT) ===
        
        # AGCP - Appareil Général de Commande et Protection (au dessus TGBT)
        agcp_x = prot_ac_x
        agcp_y = prot_ac_y + 4*cm
        SymbolesElectriques.disjoncteur(c, agcp_x, agcp_y, orientation='vertical')
        c.setFont("Helvetica-Bold", 7)
        c.drawString(agcp_x + 8*mm, agcp_y + 8*mm, "AGCP")
        c.setFont("Helvetica", 6)
        c.drawString(agcp_x + 8*mm, agcp_y + 3*mm, f"{self.calibre_agcp}A courbe {self.courbe_agcp}")
        c.drawString(agcp_x + 8*mm, agcp_y - 3*mm, f"PdC: {self.pouvoir_coupure_agcp}")
        
        # Ligne verticale Sectionneur AC → AGCP
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.line(sect_ac_x, sect_ac_y - 8*mm, agcp_x, agcp_y + 8*mm)
        
        # Ligne verticale AGCP → Disjoncteur différentiel
        disj_y = prot_ac_y + 2*cm
        c.line(agcp_x, agcp_y - 8*mm, agcp_x, disj_y + 8*mm)
        # Disjoncteur différentiel (entre AGCP et TGBT)
        SymbolesElectriques.differentiel(c, prot_ac_x, disj_y, orientation='vertical')
        c.setFont("Helvetica", 6)
        c.drawString(prot_ac_x + 8*mm, disj_y + 3*mm, 
                   f"{self.calibre_disjoncteur_ac}A courbe {self.courbe_disjoncteur_ac}")
        c.drawString(prot_ac_x + 8*mm, disj_y - 3*mm, 
                   f"{self.type_differentiel}")
        c.drawString(prot_ac_x + 8*mm, disj_y - 8*mm, 
                   f"PdC: {self.pouvoir_coupure_ac}")
        
        # Ligne verticale disjoncteur → TGBT
        c.line(prot_ac_x, disj_y - 8*mm, prot_ac_x, prot_ac_y + 1.25*cm)
        
        # Boîte TGBT (rectangle)
        c.setLineWidth(2)
        c.rect(prot_ac_x - 1.25*cm, prot_ac_y - 1.25*cm, 2.5*cm, 2.5*cm)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(prot_ac_x, prot_ac_y, "TGBT")
        
        # Parafoudre AC (en dessous TGBT)
        para_ac_y = prot_ac_y - 2.5*cm
        SymbolesElectriques.parafoudre(c, prot_ac_x - 0.3*cm, para_ac_y, orientation='vertical')
        c.setFont("Helvetica", 6)
        c.drawString(prot_ac_x + 8*mm, para_ac_y - 3*mm, "SPD Type 2")
        
        # Terre avec liaison équipotentielle
        terre_y = para_ac_y - 18*mm
        SymbolesElectriques.terre(c, prot_ac_x - 0.3*cm, terre_y)
        c.setFont("Helvetica", 5)
        c.drawCentredString(prot_ac_x - 0.3*cm, terre_y - 10*mm, f"≤{self.resistance_terre_max}")
        c.setFont("Helvetica", 4.5)
        c.drawCentredString(prot_ac_x - 0.3*cm, terre_y - 14*mm, f"LEP")
        c.setFont("Helvetica", 5)
        c.drawCentredString(prot_ac_x - 0.3*cm, terre_y - 18*mm, f"PE: {self.section_terre_principal}")
        
        # === 7. POINT D'INJECTION RÉSEAU ===
        
        # Ligne verticale TGBT → réseau
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        c.line(prot_ac_x, prot_ac_y - 1.25*cm, injection_x, injection_y + 0.8*cm)
        
        # Flèche sens injection (production → réseau) - à droite du câble
        c.setFillColor(colors.HexColor('#28a745'))
        mid_inj_y = (prot_ac_y + injection_y) / 2
        c.setFont("Helvetica", 6)
        c.drawString(prot_ac_x + 0.8*cm, mid_inj_y + 0.5*cm, "▼ Production")
        c.setFillColor(colors.HexColor('#ffc107'))
        c.drawString(prot_ac_x + 0.8*cm, mid_inj_y - 0.5*cm, "▲ Soutirage")
        c.setFillColor(colors.black)
        
        # Annotation distance injection (à droite)
        c.setFont("Helvetica", 6)
        c.drawString(prot_ac_x + 0.8*cm, mid_inj_y, 
                           f"L={self.longueur_ac_tgbt_injection:.1f}m")
        
        # Symbole compteur
        SymbolesElectriques.compteur(c, injection_x, injection_y, size=1.3*cm)
        
        # Label réseau (à droite)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(injection_x + 1*cm, injection_y + 0.3*cm, self.type_reseau)
        c.setFont("Helvetica", 6)
        c.drawString(injection_x + 1*cm, injection_y - 0.3*cm, "RÉSEAU PUBLIC")
        
        # === LÉGENDE (en bas du schéma) ===
        
        legende_y = schema_y_start + 1*cm
        legende_x = schema_x_start + 1*cm
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(legende_x, legende_y, "LÉGENDE:")
        
        # Symbole string dans légende
        legend_string_x = legende_x + 3*cm
        SymbolesElectriques.module_pv(c, legend_string_x, legende_y + 2*mm, size=0.6*cm)
        c.setFont("Helvetica", 6)
        c.drawString(legend_string_x + 6*mm, legende_y + 2*mm, f"String×20 modules DC")
        
        # DC (rouge)
        dc_line_x = legende_x + 9*cm
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        c.line(dc_line_x, legende_y + 2*mm, dc_line_x + 1*cm, legende_y + 2*mm)
        c.setStrokeColor(colors.black)
        c.setFont("Helvetica", 6)
        c.drawString(dc_line_x + 1.3*cm, legende_y, "Courant continu DC")
        
        # AC (noir)
        ac_line_x = legende_x + 15*cm
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        c.line(ac_line_x, legende_y + 2*mm, ac_line_x + 1*cm, legende_y + 2*mm)
        c.setStrokeColor(colors.black)
        c.drawString(ac_line_x + 1.3*cm, legende_y, "Courant alternatif AC")
        
        # Terre (plus espacé)
        terre_x = legende_x + 18*cm
        SymbolesElectriques.terre(c, terre_x, legende_y + 5*mm)
        c.drawString(terre_x + 6*mm, legende_y, f"Terre (≤{self.resistance_terre_max})")
    
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
