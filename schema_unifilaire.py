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
        
        # Type de raccordement (3 cas possibles)
        # 'autoconso_injection' : Autoconsommation avec vente du surplus (bidirectionnel)
        # 'autoconso_sans_injection' : Autoconsommation sans injection (unidirectionnel - soutirage uniquement)
        # 'injection_totale' : Vente totale (production uniquement vers réseau)
        self.type_raccordement = calpinage_data.get('type_raccordement', 'autoconso_injection')
        
        # Batterie de stockage (optionnel - NF C 15-712-2)
        equipments = calpinage_data.get('equipments', {})
        self.batterie = equipments.get('batterie', None)
        self.avec_batterie = self.batterie is not None
        
        # Vérifier si une configuration électrique existe déjà (sauvegardée)
        saved_config = calpinage_data.get('configuration_electrique', {})
        
        # Calculer le nombre de modules actuel du calepinage
        nb_modules_actuel = sum(zone.get('nbModules', 0) for zone in self.zones)
        
        # Vérifier si la config sauvegardée correspond au calepinage actuel
        config_valide = False
        if saved_config and saved_config.get('date_maj'):
            nb_modules_saved = saved_config.get('nb_modules', 0)
            # Comparer le nombre de modules (pas la puissance, car le module peut avoir changé)
            if nb_modules_actuel == nb_modules_saved:
                config_valide = True
                puissance_saved = saved_config.get('puissance_totale_kwc', 0)
                print(f"✅ [SCHEMA] Restauration configuration électrique ({nb_modules_saved} modules, {puissance_saved:.1f}kWc)")
            else:
                print(f"⚠️ [SCHEMA] Calepinage modifié ({nb_modules_saved} → {nb_modules_actuel} modules), recalcul nécessaire")
        
        if config_valide:
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
            # FIX #5: utiliser les valeurs v_min/v_max réelles sauvegardées (ou chercher dans ONDULEURS_DATABASE)
            ond_v_min = ond.get('tension_min') or ond.get('v_dc_min', 150)
            ond_v_max = ond.get('tension_max') or ond.get('v_dc_max', 1000)
            # Si jamais les deux champs sont absents, chercher dans la DB par modèle
            if ond_v_min == 150 and ond_v_max == 1000:
                try:
                    from equipements_database import ONDULEURS_DATABASE
                    ref = next((k for k, v in ONDULEURS_DATABASE.items()
                                if v.get('modele') == ond.get('modele')), None)
                    if ref:
                        ond_v_min = ONDULEURS_DATABASE[ref]['v_dc_min']
                        ond_v_max = ONDULEURS_DATABASE[ref]['v_dc_max']
                except Exception:
                    pass
            self.onduleur = {
                'marque': ond.get('marque', 'Onduleur'),
                'modele': ond.get('modele', 'Generic'),
                'p_ac': ond.get('puissance_ac', int(self.puissance_totale_kwc * 1000)),
                'p_dc_max': ond.get('puissance_dc_max', int(self.puissance_totale_kwc * 1000 * 1.2)),
                'mppt': ond.get('nb_mppt', 2),
                'v_min': ond_v_min,
                'v_max': ond_v_max,
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
        
        # Type réseau (AVANT calcul courant_max_ac)
        equipments = calpinage_data.get('equipments', {})
        injection_saved = equipments.get('injection', {})
        self.type_reseau = injection_saved.get('type_reseau', '230V Monophasé')
        
        # Restaurer les distances
        distances = calpinage_data.get('distances', {})
        self.longueur_dc = distances.get('dc_strings', 25)
        self.longueur_ac_onduleur_tgbt = distances.get('ac_onduleur_tgbt', 15)
        self.longueur_ac_tgbt_injection = distances.get('ac_tgbt_injection', 10)
        
        # Calculer courant max AC depuis l'onduleur
        puissance_ac = self.onduleur.get('p_ac', self.puissance_totale_kwc * 1000)
        if '230V' in self.type_reseau or 'Mono' in self.type_reseau:
            self.courant_max_ac = (puissance_ac / 230) * 1.25
        else:
            self.courant_max_ac = (puissance_ac / (400 * math.sqrt(3))) * 1.25
        
        # Restaurer les chutes de tension
        self.chute_tension_dc_pct = saved_config.get('chute_tension_dc_pct') or 1.5
        self.chute_tension_ac_pct = saved_config.get('chute_tension_ac_pct') or 1.0
        
        # Restaurer les protections DC
        self.calibre_sectionneur_dc = saved_config.get('sectionneur_dc') or '63A'
        self.tension_sectionneur_dc = '1000V DC'
        self.fusibles_strings = saved_config.get('fusibles_strings', 'Non requis')
        self.parafoudre_dc = saved_config.get('parafoudre_dc') or 'Type 2 - 1000V DC - 20A'
        
        # Restaurer les protections AC
        agcp_saved = saved_config.get('agcp')
        self.calibre_agcp = agcp_saved or '63A'
        self.courbe_agcp = 'C'
        self.pouvoir_coupure_agcp = '10kA'
        
        disj_saved = saved_config.get('disjoncteur_ac')
        self.calibre_disjoncteur_ac = disj_saved or '40A'
        self.courbe_disjoncteur_ac = 'C'
        self.pouvoir_coupure_ac = '10kA'
        
        # Sectionneur AC
        self.calibre_sectionneur_ac = saved_config.get('sectionneur_ac') or self.calibre_disjoncteur_ac
        self.type_sectionneur_ac = 'Sectionneur AC cadenassable'
        
        diff_saved = saved_config.get('differentiel_ac')
        self.type_differentiel = diff_saved or 'Type A 30mA'
        self.sensibilite_differentiel = 30
        
        # Parafoudre AC
        self.parafoudre_ac = saved_config.get('parafoudre_ac') or 'Type 2 - 275V AC - 20kA'
        
        # Restaurer les IP
        self.ip_boite_dc = saved_config.get('ip_boite_dc', 'IP65')
        self.ip_onduleur = saved_config.get('ip_onduleur', 'IP65')
        
        # Restaurer terre
        self.resistance_terre_max = saved_config.get('resistance_terre', '≤100Ω')
        
        # Restaurer Consuel
        self.num_consuel = saved_config.get('num_consuel', '')
        self.numero_consuel = saved_config.get('numero_consuel', '')
        
        # Métadonnées document
        self.indice_revision = saved_config.get('indice_revision', 'A')
        self.date_edition = saved_config.get('date_edition', datetime.now().strftime('%d/%m/%Y'))
        self.coupure_generale_dc = saved_config.get('coupure_generale_dc', True)
        
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
        
        # Métadonnées document
        self.indice_revision = 'A'
        self.date_edition = datetime.now().strftime('%d/%m/%Y')
        self.numero_consuel = ''
        self.coupure_generale_dc = True
        
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
            
            # FIX #4: correction température NF C 15-712 §7 avec coeff_temp_voc réel du module
            # coeff_temp_voc en %/°C (négatif), ex: -0.27 %/°C pour P-PERC, -0.24 pour N-TOPCon
            coeff_temp_v = float(self.module.get('coeff_temp_voc', -0.27))  # %/°C
            T_min = -10.0   # °C — pire cas hiver France hors montagne (NF C 15-712 zone H1b/H2b)
            T_max = 70.0    # °C — pire cas été (module en plein soleil)
            T_STC = 25.0    # °C — conditions standard de test
            # Voc monte quand T descend → v_oc_max à T_min
            v_oc_max  = v_oc_zone  * (1.0 + coeff_temp_v / 100.0 * (T_min - T_STC))
            # Vmpp descend quand T monte → v_mpp_min à T_max
            v_mpp_min = v_mpp_zone * (1.0 + coeff_temp_v / 100.0 * (T_max - T_STC))
            
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
        
        # 2. CÂBLES PAR STRING (calcul avec chute de tension selon distance réelle)
        i_max_string = max(s['i_sc'] * 1.25 for s in self.configuration_strings)
        
        # Section minimale selon courant admissible
        section_string_min_courant = 4  # Section minimale NF C 15-712 pour extérieur
        for i, courant_adm in enumerate(courants_admissibles):
            if courant_adm >= i_max_string:
                section_string_min_courant = max(sections_normalisees[i], 4)  # Min 4mm² recommandé extérieur
                break
        
        # Chute de tension sur câbles strings (longueur réelle du calepinage)
        # Chaque string a sa propre longueur depuis les modules jusqu'à la boîte DC
        section_string_chute_tension = (2 * rho_cuivre * longueur_dc_strings * i_max_string) / (0.02 * v_mpp_moyenne)
        
        # Prendre le max des deux contraintes
        section_string_calculee = max(section_string_min_courant, section_string_chute_tension)
        sections_valides_string = [s for s in sections_normalisees if s >= section_string_calculee]
        self.section_cable_string = min(sections_valides_string) if sections_valides_string else sections_normalisees[-1]
        
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
        
        # Type différentiel: Type A (onduleurs seuls) ou Type B (onduleurs + batteries)
        # NF C 15-712-2: Type B obligatoire si batterie (courants DC résiduels)
        if self.avec_batterie:
            self.type_differentiel = 'Type B 30mA'
        else:
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
        # PE selon NF C 15-100 art. 543.1 : PE = phase si ≤16mm², PE = phase/2 si >16mm²
        self.section_pe_dc = self.section_cable_dc if self.section_cable_dc <= 16 else self.section_cable_dc / 2
        self.section_pe_ac = self.section_cable_ac if self.section_cable_ac <= 16 else self.section_cable_ac / 2
        
        # 2. PROTECTION DC (sectionneurs + parafoudres)
        # Sectionneur DC: 1.5 × Isc total (NF C 15-712 art. 7.12.3.1)
        isc_total = sum(s['i_sc'] for s in self.configuration_strings)
        calibre_sectionneur_dc_min = isc_total * 1.5  # Facteur 1.5 sécurité
        
        calibres_sectionneurs_dc = [16, 25, 32, 40, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800]
        calibres_valides_sect = [c for c in calibres_sectionneurs_dc if c >= calibre_sectionneur_dc_min]
        self.calibre_sectionneur_dc = min(calibres_valides_sect) if calibres_valides_sect else calibres_sectionneurs_dc[-1]
        
        # Tension nominale sectionneur DC
        v_oc_max = max(s['v_oc'] * 1.25 for s in self.configuration_strings)  # Facteur température
        self.tension_sectionneur_dc = '1000V DC' if v_oc_max < 900 else '1500V DC'
        
        # 3. PARAFOUDRES (obligatoires selon NF C 15-712 art. 7.12.3.4)
        # Type 2 minimum (Type 1+2 si paratonnerre)
        self.parafoudre_dc = f'Type 2 - {self.tension_sectionneur_dc} - {int(isc_total * 1.5)}A'
        self.parafoudre_ac = 'Type 2 - 275V AC - 20kA'
        
        # 4. FUSIBLES PAR STRING (NF C 15-712 art. 7.12.2.2.1)
        # Fusibles obligatoires si >= 3 strings par entrée MPPT
        nb_mppt = self.onduleur.get('mppt', 2)
        strings_par_mppt = math.ceil(len(self.configuration_strings) / nb_mppt)
        if strings_par_mppt >= 3:
            isc_string_max = max(s['i_sc'] for s in self.configuration_strings)
            # Calibre fusible : 1.5 × Isc < In_fusible < 2.4 × Isc (NF C 15-712)
            calibre_fusible_min = isc_string_max * 1.5
            calibre_fusible_max = isc_string_max * 2.4
            calibres_fusibles = [10, 12, 15, 16, 20, 25, 32]
            calibres_valides_fus = [c for c in calibres_fusibles if calibre_fusible_min <= c <= calibre_fusible_max]
            if not calibres_valides_fus:
                calibres_valides_fus = [c for c in calibres_fusibles if c >= calibre_fusible_min]
            calibre_fusible = min(calibres_valides_fus) if calibres_valides_fus else calibres_fusibles[-1]
            self.fusibles_strings = f'{calibre_fusible}A gPV ({self.tension_sectionneur_dc})'
        else:
            self.fusibles_strings = f'Non requis ({strings_par_mppt} strings/MPPT, seuil=3)'
        
        # 5. MISE À LA TERRE (NF C 15-712 art. 7.13)
        self.resistance_terre_max = '100Ω'  # Valeur maximale
        self.liaison_equipotentielle = 'Liaison équipotentielle principale (LEP)'
        self.section_terre_principal = '16mm²'  # Section minimale conducteur principal de terre
        
        # 6. CHUTES DE TENSION (NF C 15-712 art. 7.12.1.1)
        # DC aller-retour : ΔU = 2 × ρ × L × I / S (avec ρ cuivre = 0.0225 Ω·mm²/m à 70°C)
        rho_cuivre = 0.0225  # Résistivité cuivre à 70°C
        i_mpp_total = sum(s['i_mpp'] for s in self.configuration_strings)
        self.chute_tension_dc = (2 * rho_cuivre * self.longueur_dc * i_mpp_total / self.section_cable_dc) if self.section_cable_dc > 0 else 0
        v_mpp_moyen = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
        self.chute_tension_dc_pct = (self.chute_tension_dc / v_mpp_moyen) * 100 if v_mpp_moyen > 0 else 0
        
        # AC : ΔU = 2 × ρ × L × I × cos(φ) / S (mono) ou √3 × ρ × L × I × cos(φ) / S (tri)
        cos_phi = 0.98  # Facteur de puissance onduleur
        v_ac = 230 if 'Mono' in self.type_reseau else 400
        if 'Mono' in self.type_reseau:
            self.chute_tension_ac = (2 * rho_cuivre * self.longueur_ac_onduleur_tgbt * self.courant_max_ac * cos_phi / self.section_cable_ac) if self.section_cable_ac > 0 else 0
        else:
            self.chute_tension_ac = (math.sqrt(3) * rho_cuivre * self.longueur_ac_onduleur_tgbt * self.courant_max_ac * cos_phi / self.section_cable_ac) if self.section_cable_ac > 0 else 0
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
        
        # Créer le canvas PDF (A3 portrait pour schéma vertical traditionnel)
        from reportlab.lib.pagesizes import A3
        page_width, page_height = A3
        
        c = canvas.Canvas(output_path, pagesize=A3)
        
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
        # Calculer les données du calepinage pour validation ultérieure
        nb_modules_total = sum(zone.get('nbModules', 0) for zone in self.zones)
        module_puissance = float(self.module.get('puissance', 550))
        puissance_totale = nb_modules_total * module_puissance / 1000
        
        # FIX #1a: résumé strings par zone (pour plans_strings.py)
        strings_par_zone = {}
        for s in self.configuration_strings:
            key = str(s['zone'])
            if key not in strings_par_zone:
                strings_par_zone[key] = {'nb_serie': s['nb_modules'], 'nb_strings': 0,
                                         'v_mpp': round(s['v_mpp'], 1), 'v_oc': round(s['v_oc'], 1)}
            strings_par_zone[key]['nb_strings'] += 1

        return {
            # Données calepinage (pour validation)
            'nb_modules': nb_modules_total,
            'puissance_totale_kwc': round(puissance_totale, 2),

            # FIX #1a: paramètres onduleur pour plans_strings.py
            'onduleur_v_min': self.onduleur.get('v_min', 150),
            'onduleur_v_max': self.onduleur.get('v_max', 1000),
            'onduleur_modele': f"{self.onduleur.get('marque','')} {self.onduleur.get('modele','')}".strip(),
            'strings_par_zone': strings_par_zone,

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
        """Dessine le cartouche professionnel ingénieur avec grille alignée"""
        
        # ── Dimensions cartouche principal (haut de page) ──
        margin = 1.5*cm
        cart_w = width - 2 * margin
        cart_h = 4.8*cm
        cart_x = margin
        cart_y = height - cart_h - 0.5*cm
        
        # Séparateur vertical entre col gauche et col droite
        col_split_x = cart_x + cart_w * 0.52
        
        # ── Cadre extérieur épais ──
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        c.rect(cart_x, cart_y, cart_w, cart_h)
        
        # ── Bandeau titre (noir, sobre) ──
        bandeau_h = 1.1*cm
        bandeau_y = cart_y + cart_h - bandeau_h
        c.setFillColor(colors.HexColor('#1a1a2e'))
        c.rect(cart_x, bandeau_y, cart_w, bandeau_h, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(cart_x + 0.6*cm, bandeau_y + 0.55*cm,
                     "AgriWeb Pro  —  SCHEMA UNIFILAIRE NF C 15-712")
        c.setFont("Helvetica", 8)
        c.drawString(cart_x + 0.6*cm, bandeau_y + 0.15*cm,
                     "Installation photovoltaique raccordee au reseau  |  Conforme NF C 03-201")
        c.setFillColor(colors.black)
        
        # ── Zone infos sous le bandeau ──
        info_top = bandeau_y  # top de la zone infos = bas du bandeau
        info_bot = cart_y     # bas = bas du cartouche
        info_h = info_top - info_bot
        
        # Trait séparateur vertical entre les 2 colonnes
        c.setLineWidth(1)
        c.line(col_split_x, info_bot, col_split_x, info_top)
        
        # ── COLONNE GAUCHE ──
        lx = cart_x + 0.5*cm
        row_h = info_h / 4  # 4 lignes
        
        # Lignes horizontales internes gauche
        for i in range(1, 4):
            ly = info_top - i * row_h
            c.setLineWidth(0.5)
            c.line(cart_x, ly, col_split_x, ly)
        
        # Ligne 1 : CLIENT
        y1 = info_top - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(lx, y1, "CLIENT")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        nom = self.prospect.get('nom', '').strip()
        prenom = self.prospect.get('prenom', '').strip()
        nom_client = f"{nom} {prenom}".strip() if nom else "Non renseigne"
        c.drawString(lx + 2.2*cm, y1, nom_client[:40])
        
        # Ligne 2 : ADRESSE
        y2 = info_top - row_h - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(lx, y2, "ADRESSE")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        adresse = self.prospect.get('adresse', 'Non disponible')
        c.drawString(lx + 2.2*cm, y2, adresse[:45])
        
        # Ligne 3 : COMMUNE
        y3 = info_top - 2 * row_h - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(lx, y3, "COMMUNE")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        code_postal = self.prospect.get('code_postal', '').strip()
        commune = self.prospect.get('commune', '').strip()
        if not code_postal and commune:
            import re
            match = re.match(r'^(\d{5})\s+(.+)$', commune)
            if match:
                code_postal = match.group(1)
                commune = match.group(2)
        ville = f"{code_postal} {commune}".strip() or "Non disponible"
        c.drawString(lx + 2.2*cm, y3, ville[:45])
        
        # Ligne 4 : DATE D'EDITION
        y4 = info_top - 3 * row_h - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(lx, y4, "DATE")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawString(lx + 2.2*cm, y4, datetime.now().strftime("%d/%m/%Y"))
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(lx + 5*cm, y4, "IND.")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawString(lx + 6*cm, y4, self.indice_revision)
        
        # ── COLONNE DROITE ──
        rx = col_split_x + 0.5*cm
        
        # Lignes horizontales internes droite (5 lignes)
        row_h_r = info_h / 5
        for i in range(1, 5):
            ly = info_top - i * row_h_r
            c.setLineWidth(0.5)
            c.line(col_split_x, ly, cart_x + cart_w, ly)
        
        # Ligne 1 : PARCELLES CADASTRALES
        yr1 = info_top - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(rx, yr1, "PARCELLES")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        parcelles_display = self._format_parcelles()
        c.drawString(rx + 2.5*cm, yr1, parcelles_display[:35])
        
        # Ligne 2 : PUISSANCE INSTALLATION
        yr2 = info_top - row_h_r - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(rx, yr2, "PUISSANCE")
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(rx + 2.5*cm, yr2,
                     f"{self.puissance_totale_kwc:.2f} kWc  ({self.nb_modules_total} modules)")
        
        # Ligne 3 : ONDULEUR
        yr3 = info_top - 2 * row_h_r - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(rx, yr3, "ONDULEUR")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawString(rx + 2.5*cm, yr3,
                     f"{self.onduleur['marque']} {self.onduleur['modele']}  ({self.onduleur['p_ac']/1000:.1f} kW AC)")
        
        # Ligne 4 : POSTE RACCORDEMENT
        yr4 = info_top - 3 * row_h_r - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(rx, yr4, "RACCORD.")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        poste_info = self._get_poste_info()
        c.drawString(rx + 2.5*cm, yr4, poste_info[:40])
        
        # Ligne 5 : CONSUEL / NORME
        yr5 = info_top - 4 * row_h_r - 0.35*cm
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(rx, yr5, "NORME")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        norme = "NF C 15-712-1 & 15-712-2" if self.avec_batterie else "NF C 15-712-1:2017"
        c.drawString(rx + 2.5*cm, yr5, norme)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(rx + 8*cm, yr5, "CONSUEL")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        c.drawString(rx + 10*cm, yr5, self.numero_consuel or "A completer")
        
        # ── Cartouche bas de page (petit, coin bas-droit) ──
        cb_w = 7*cm
        cb_h = 1.8*cm
        cb_x = width - margin - cb_w
        cb_y = 0.8*cm
        
        c.setLineWidth(1.5)
        c.rect(cb_x, cb_y, cb_w, cb_h)
        
        # Ligne séparatrice interne
        c.setLineWidth(0.5)
        c.line(cb_x, cb_y + cb_h / 2, cb_x + cb_w, cb_y + cb_h / 2)
        c.line(cb_x + cb_w / 2, cb_y, cb_x + cb_w / 2, cb_y + cb_h / 2)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawString(cb_x + 0.2*cm, cb_y + cb_h - 0.4*cm, "SCHEMA UNIFILAIRE NF C 15-712")
        c.setFont("Helvetica", 7)
        c.drawString(cb_x + 0.2*cm, cb_y + cb_h - 0.8*cm, f"AgriWeb Pro — {datetime.now().strftime('%d/%m/%Y')}")
        
        c.setFont("Helvetica", 7)
        c.drawString(cb_x + 0.2*cm, cb_y + 0.25*cm, f"Ind. {self.indice_revision}")
        c.drawString(cb_x + cb_w / 2 + 0.2*cm, cb_y + 0.25*cm, "Page 1/2")
        
        # ── Plan de situation (si injection réseau) ──
        if self.type_raccordement in ['autoconso_injection', 'injection_totale']:
            self._dessiner_plan_situation(c, width, height)
    
    def _format_parcelles(self):
        """Formatte les parcelles cadastrales pour affichage cartouche"""
        parcelles_raw = self.prospect.get('references_cadastrales', '')
        if not parcelles_raw:
            return 'Non renseignees'
        
        parcelles_list = []
        if isinstance(parcelles_raw, str):
            import json
            try:
                parcelles_obj = json.loads(parcelles_raw)
                if isinstance(parcelles_obj, list):
                    for p in parcelles_obj[:3]:
                        if isinstance(p, dict):
                            ref = ' '.join(filter(None, [p.get('prefixe'), p.get('section'), p.get('numero')]))
                            parcelles_list.append(ref or str(p))
                        else:
                            parcelles_list.append(str(p))
                elif isinstance(parcelles_obj, dict):
                    ref = ' '.join(filter(None, [parcelles_obj.get('prefixe'), parcelles_obj.get('section'), parcelles_obj.get('numero')]))
                    parcelles_list.append(ref or str(parcelles_obj))
                else:
                    parcelles_list.append(str(parcelles_obj))
            except Exception:
                parcelles_list.append(parcelles_raw)
        elif isinstance(parcelles_raw, list):
            for p in parcelles_raw[:3]:
                if isinstance(p, dict):
                    ref = ' '.join(filter(None, [p.get('prefixe'), p.get('section'), p.get('numero')]))
                    parcelles_list.append(ref or str(p))
                else:
                    parcelles_list.append(str(p))
        else:
            parcelles_list.append(str(parcelles_raw))
        
        return ', '.join(parcelles_list) if parcelles_list else 'Non renseignees'
    
    def _get_poste_info(self):
        """Retourne les infos du poste de raccordement pour le cartouche"""
        if self.puissance_totale_kwc < 1000:
            poste_nom = self.prospect.get('poste_bt_nom', '')
            poste_distance = self.prospect.get('poste_bt_distance_m', None)
            poste_type = 'BT'
        else:
            poste_nom = self.prospect.get('poste_hta_nom', '')
            poste_distance = self.prospect.get('poste_hta_distance_m', None)
            poste_type = 'HTA'
        
        parts = [f"Poste {poste_type}"]
        if poste_nom:
            parts.append(poste_nom[:20])
        if poste_distance:
            parts.append(f"({int(poste_distance)}m)")
        return ' — '.join(parts) if len(parts) > 1 else 'Non renseigne'
    
    def _dessiner_plan_situation(self, c, width, height):
        """Dessine un plan de situation simplifié montrant l'emplacement du poste de raccordement"""
        # Déterminer quel poste afficher (<1MWc = BT, ≥1MWc = HTA)
        if self.puissance_totale_kwc < 1000:
            poste_nom = self.prospect.get('poste_bt_nom', '')
            poste_distance = self.prospect.get('poste_bt_distance_m', None)
            poste_puissance = self.prospect.get('poste_bt_puissance', None)
            poste_etat = self.prospect.get('poste_bt_etat', '')
            poste_lat = self.prospect.get('poste_bt_lat', None)
            poste_lon = self.prospect.get('poste_bt_lon', None)
            poste_type = 'BT'
        else:
            poste_nom = self.prospect.get('poste_hta_nom', '')
            poste_distance = self.prospect.get('poste_hta_distance_m', None)
            poste_puissance = self.prospect.get('poste_hta_puissance', None)
            poste_etat = self.prospect.get('poste_hta_etat', '')
            poste_lat = self.prospect.get('poste_hta_lat', None)
            poste_lon = self.prospect.get('poste_hta_lon', None)
            poste_type = 'HTA'
            poste_lat = self.prospect.get('poste_hta_lat', None)
            poste_lon = self.prospect.get('poste_hta_lon', None)
            poste_type = 'HTA'
        
        # Ne dessiner que si on a au moins la distance
        if not (poste_nom or poste_distance):
            return
        
        # Position du plan (coin bas gauche)
        plan_x = 1.5*cm
        plan_y = 1*cm
        plan_width = 6*cm
        plan_height = 3*cm
        
        # Cadre du plan
        c.setLineWidth(1.5)
        c.rect(plan_x, plan_y, plan_width, plan_height)
        
        # Titre
        c.setFont("Helvetica-Bold", 8)
        c.drawString(plan_x + 0.3*cm, plan_y + plan_height - 0.5*cm, f"PLAN DE SITUATION - Poste {poste_type}")
        
        # Dessiner l'installation (rectangle au centre)
        install_width = 1.2*cm
        install_height = 0.8*cm
        install_x = plan_x + plan_width/2 - install_width/2
        install_y = plan_y + plan_height/2 - install_height/2
        
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(install_x, install_y, install_width, install_height, fill=1, stroke=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 6)
        c.drawCentredString(install_x + install_width/2, install_y + install_height/2 - 0.1*cm, "Installation PV")
        
        # Dessiner le poste (symbole électrique)
        if poste_distance:
            # Calculer position du poste (on le met à gauche de l'installation)
            # Échelle approximative : 100m = 2cm
            distance_cm = min(poste_distance / 100 * 2, plan_width - 2)
            poste_x = install_x - distance_cm
            poste_y = install_y + install_height/2
            
            # Limiter le poste dans le cadre
            if poste_x < plan_x + 0.5*cm:
                poste_x = plan_x + 0.5*cm
            
            # Symbole poste (cercle avec croix)
            c.setFillColorRGB(1, 0.8, 0)
            c.circle(poste_x, poste_y, 0.25*cm, fill=1, stroke=1)
            c.setFillColorRGB(0, 0, 0)
            c.setLineWidth(0.5)
            c.line(poste_x - 0.15*cm, poste_y, poste_x + 0.15*cm, poste_y)
            c.line(poste_x, poste_y - 0.15*cm, poste_x, poste_y + 0.15*cm)
            
            # Ligne de liaison
            c.setStrokeColorRGB(1, 0, 0)
            c.setLineWidth(0.5)
            c.setDash(3, 2)
            c.line(poste_x + 0.25*cm, poste_y, install_x, install_y + install_height/2)
            c.setDash()  # Reset dash
            c.setStrokeColorRGB(0, 0, 0)
            
            # Label distance
            c.setFont("Helvetica-Bold", 7)
            label_x = (poste_x + install_x) / 2
            label_y = poste_y + 0.3*cm
            c.drawCentredString(label_x, label_y, f"{int(poste_distance)}m")
            
            # Nom du poste et infos
            info_y = poste_y - 0.5*cm
            if poste_nom:
                c.setFont("Helvetica-Bold", 6)
                c.drawCentredString(poste_x, info_y, poste_nom[:20])
                info_y -= 0.25*cm
            
            # Puissance et statut
            c.setFont("Helvetica", 5)
            if poste_puissance:
                c.drawCentredString(poste_x, info_y, f"{poste_puissance} kVA")
                info_y -= 0.2*cm
            if poste_etat:
                c.drawCentredString(poste_x, info_y, poste_etat)
        
        # Coordonnées GPS si disponibles
        if poste_lat and poste_lon:
            c.setFont("Helvetica", 6)
            c.drawString(plan_x + 0.2*cm, plan_y + 0.2*cm, f"GPS: {poste_lat:.5f}, {poste_lon:.5f}")
    
    def _dessiner_schema_principal(self, c, width, height):
        """Dessine le schéma unifilaire principal avec symboles normalisés NF C 03-201"""
        
        # Zone de dessin (éviter cartouche et marges) - OPTIMISÉ
        schema_x_start = 1*cm
        schema_x_end = width - 1*cm
        schema_y_start = 4*cm
        schema_y_end = height - 7*cm  # Espace pour le titre
        
        schema_width = schema_x_end - schema_x_start
        schema_height = schema_y_end - schema_y_start
        
        # === CADRE GLOBAL SCHÉMA ===
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(schema_x_start, schema_y_start, schema_width, schema_height)
        
        # === COORDONNÉES LAYOUT VERTICAL (disposition traditionnelle) ===
        # Schéma unifilaire vertical classique : HAUT → BAS
        # Champ PV (haut) → Protections DC → Onduleur → Protections AC → Réseau (bas)
        
        # Axe central vertical du schéma
        center_x = schema_x_start + schema_width / 2
        
        # === ZONE 1: CHAMP PV (tout en haut) ===
        strings_x = center_x - 6*cm
        strings_y = schema_y_end - 3*cm
        
        # === ZONE 2: BOÎTE DC + PROTECTIONS (haut-milieu) ===
        boite_dc_x = center_x  # Aligné avec onduleur
        boite_dc_y = schema_y_end - 7*cm
        
        # === ZONE 3: ONDULEUR (centre) ===
        onduleur_x = center_x
        onduleur_y = schema_y_end - 12*cm
        
        # === ZONE 4: PROTECTIONS AC (bas-milieu) ===
        prot_ac_x = center_x
        prot_ac_y = schema_y_end - 18*cm
        
        # === ZONE 5: POINT INJECTION RÉSEAU (tout en bas) ===
        injection_x = center_x
        injection_y = schema_y_start + 3*cm
        
        # === TITRE SECTIONS (disposées verticalement à gauche) ===
        titre_x = schema_x_start + 0.8*cm
        
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.HexColor('#1a1a2e'))
        c.drawString(titre_x, strings_y + 0.3*cm, "CHAMP PV")
        
        c.setFillColor(colors.HexColor('#333333'))
        c.drawString(titre_x, boite_dc_y + 0.3*cm, "PROTECTION DC")
        
        c.setFillColor(colors.HexColor('#333333'))
        c.drawString(titre_x, onduleur_y + 0.3*cm, "CONVERSION")
        
        c.setFillColor(colors.HexColor('#333333'))
        c.drawString(titre_x, prot_ac_y + 1.5*cm, "PROTECTION AC")
        
        # Section réseau : libellé différencié selon le type de raccordement
        if self.type_raccordement in ('autoconso_injection', 'autoconso_sans_injection'):
            reseau_label = "TGBT / AUTOCONSOMMATION"
        else:
            reseau_label = "RÉSEAU / INJECTION TOTALE"
        c.setFillColor(colors.HexColor('#333333'))
        c.drawString(titre_x, injection_y + 0.3*cm, reseau_label)
        
        c.setFillColor(colors.black)
        
        # === 1. CHAMP PHOTOVOLTAÏQUE — GROUPES DE STRINGS SIMILAIRES ===
        # Conformément à la pratique de schéma unifilaire, on regroupe les strings
        # ayant le même nombre de modules et on indique le compteur symbolique (×N)
        
        nb_strings_total = len(self.configuration_strings)
        puissance_totale_strings = sum(s['puissance_wc'] for s in self.configuration_strings) / 1000
        
        # --- Grouper les strings par nombre de modules ---
        from collections import Counter
        groupes_compteur = Counter(s['nb_modules'] for s in self.configuration_strings)
        # groupes = liste de (nb_modules, count) triée par nb_modules décroissant
        groupes = sorted(groupes_compteur.items(), key=lambda x: -x[0])
        nb_groupes = len(groupes)
        
        # Espacement dynamique selon nombre de groupes distincts
        largeur_disponible = schema_width - 8*cm
        if nb_groupes > 1:
            espacement_strings = min(3*cm, largeur_disponible / (nb_groupes - 1))
        else:
            espacement_strings = 3*cm
        
        start_x = strings_x - ((nb_groupes - 1) * espacement_strings / 2)
        last_string_x = start_x + (nb_groupes - 1) * espacement_strings
        texte_info_x = max(strings_x + 3*cm, last_string_x + 1.5*cm)
        
        # Résumé global à droite
        c.setFont("Helvetica-Bold", 7)
        c.drawString(texte_info_x, strings_y + 0.8*cm,
                    f"{nb_strings_total} Strings en parallèle")
        c.setFont("Helvetica", 6)
        c.drawString(texte_info_x, strings_y + 0.3*cm,
                    f"{self.nb_modules_total}×{int(self.module_puissance)}Wc = {puissance_totale_strings:.2f}kWc")
        if self.configuration_strings:
            v_mpp_moy = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
            i_sc_total = sum(s['i_sc'] for s in self.configuration_strings)
            c.drawString(texte_info_x, strings_y - 0.2*cm, f"Vmpp:{v_mpp_moy:.1f}V")
            c.drawString(texte_info_x, strings_y - 0.7*cm, f"Isc:{i_sc_total:.1f}A")
        
        # Dessiner un symbole représentatif par groupe de strings similaires
        strings_y_bottom = []
        for gi, (nb_mod, nb_count) in enumerate(groupes):
            string_x = start_x + gi * espacement_strings
            
            # Symbole string (module PV)
            SymbolesElectriques.string_pv(c, string_x, strings_y,
                                          nb_modules=nb_mod,
                                          compact=True)
            
            # ×N modules au-dessus (italic petit)
            c.setFont("Helvetica-Bold", 6)
            c.setFillColor(colors.HexColor('#333333'))
            c.drawCentredString(string_x, strings_y + 1.5*cm, f"×{nb_mod}")
            c.setFillColor(colors.black)
            
            # Compteur de strings similaires en dessous du symbole (encadré)
            if nb_count > 1:
                badge_x = string_x - 0.35*cm
                badge_y = strings_y - 0.6*cm
                c.setFillColor(colors.HexColor('#1a1a2e'))
                c.roundRect(badge_x, badge_y, 0.7*cm, 0.35*cm, 2*mm, fill=1, stroke=0)
                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 5.5)
                c.drawCentredString(string_x, badge_y + 0.1*cm, f"×{nb_count} str.")
                c.setFillColor(colors.black)
            
            # Fusible sous chaque groupe (si requis)
            if 'Non requis' not in self.fusibles_strings:
                fusible_y = strings_y - 1.8*cm
                SymbolesElectriques.fusible(c, string_x, fusible_y, orientation='vertical')
                calibre_fusible = self.fusibles_strings.split('A')[0].strip()
                c.setFont("Helvetica", 5)
                c.drawString(string_x + 5*mm, fusible_y, f"{calibre_fusible}A")
                c.setStrokeColor(colors.red)
                c.setLineWidth(1.5)
                c.line(string_x, strings_y - 0.8*cm, string_x, fusible_y + 6*mm)
                c.line(string_x, fusible_y - 8*mm, string_x, fusible_y - 1.2*cm)
                strings_y_bottom.append((string_x, fusible_y - 1.2*cm))
            else:
                c.setStrokeColor(colors.red)
                c.setLineWidth(1.5)
                c.line(string_x, strings_y - 0.8*cm, string_x, strings_y - 2*cm)
                strings_y_bottom.append((string_x, strings_y - 2*cm))
        
        # Regroupement des strings vers la boîte DC (collecteur horizontal)
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        
        # Point de convergence (milieu)
        convergence_y = strings_y - 3*cm
        convergence_x = strings_x
        
        # Lignes verticales depuis chaque string vers le collecteur
        c.setLineWidth(1.5)
        for x, y in strings_y_bottom:
            c.line(x, y, x, convergence_y)
        
        # Ligne horizontale collecteur
        c.setLineWidth(2.5)
        min_x = min(x for x, _ in strings_y_bottom)
        max_x = max(x for x, _ in strings_y_bottom)
        c.line(min_x, convergence_y, max_x, convergence_y)
        
        # Ligne principale vers boîte DC
        cable_start_x = convergence_x
        cable_start_y = convergence_y
        
        c.setStrokeColor(colors.black)
        
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
        
        # Boîte de jonction (rectangle compact)
        c.setLineWidth(1.5)
        c.rect(boite_dc_x - 1*cm, boite_dc_y - 1*cm, 2*cm, 2*cm)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(boite_dc_x, boite_dc_y + 2*mm, "BOITE DC")
        c.setFont("Helvetica", 5)
        c.drawCentredString(boite_dc_x, boite_dc_y - 3*mm, f"{self.ip_boite_dc}")
        
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
        
        # Ligne verticale boîte → onduleur (sortie boîte bas vers entrée onduleur haut)
        c.setStrokeColor(colors.red)
        c.setLineWidth(2.5)
        c.line(boite_dc_x, boite_dc_y - 1*cm, boite_dc_x, onduleur_y + 1*cm)
        c.setStrokeColor(colors.black)
        
        # Annotation câble DC principal + type + PE (à gauche du câble)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.red)
        mid_dc_y = (boite_dc_y + onduleur_y) / 2
        c.drawString(boite_dc_x - 5*cm, mid_dc_y + 0.8*cm, 
                           f"DC: {self.section_cable_dc}mm²+PE {self.section_pe_dc}mm² Cu")
        c.setFont("Helvetica", 6)
        c.drawString(boite_dc_x - 5*cm, mid_dc_y + 0.3*cm, 
                           f"{self.type_cable_dc} ou équivalent PV - L={self.longueur_dc:.1f}m")
        c.drawString(boite_dc_x - 5*cm, mid_dc_y - 0.2*cm, 
                           f"ΔU={self.chute_tension_dc_pct:.2f}%")
        c.setFillColor(colors.black)
        
        # === 4. ONDULEURS (un par zone/pan de toiture) ===
        # Conformément à la réalité terrain : si plusieurs zones, plusieurs onduleurs
        # Le schéma indique chaque onduleur avec ses caractéristiques propres
        
        zones_actives = [z for z in self.zones if z.get('nbModules', 0) > 0]
        nb_onduleurs = max(1, len(zones_actives))
        
        # Si un seul onduleur → position centrale classique
        # Si plusieurs → répartis horizontalement autour du centre
        ond_espacement = min(3*cm, (schema_width - 8*cm) / max(nb_onduleurs, 1))
        ond_start_x = onduleur_x - ((nb_onduleurs - 1) * ond_espacement / 2)
        
        # Liste des positions d'onduleurs et de leurs sorties AC (pour convergence)
        ond_positions = []
        
        for oi in range(nb_onduleurs):
            ox = ond_start_x + oi * ond_espacement
            oy = onduleur_y
            
            SymbolesElectriques.onduleur(c, ox, oy, width=2*cm, height=2*cm)
            ond_positions.append((ox, oy))
            
            # Numérotation si plusieurs onduleurs
            if nb_onduleurs > 1:
                c.setFont("Helvetica-Bold", 6)
                c.setFillColor(colors.HexColor('#1a1a2e'))
                c.drawCentredString(ox, oy + 1.3*cm, f"ONd {oi+1}")
                c.setFillColor(colors.black)
                # Zone associée
                if oi < len(zones_actives):
                    z = zones_actives[oi]
                    c.setFont("Helvetica", 5)
                    orient = z.get('orientation', 180)
                    incl = z.get('inclinaison', 30)
                    c.drawCentredString(ox, oy - 1.4*cm, f"Pan {oi+1} ({orient}° / {incl}°)")
            
            # Infos techniques (sur le premier onduleur ou si seul)
            if oi == 0:
                info_x = ox + 2.2*cm if nb_onduleurs == 1 else ox + 1.2*cm
                c.setFont("Helvetica-Bold", 7 if nb_onduleurs == 1 else 6)
                c.drawString(info_x, oy + 0.8*cm,
                             f"{self.onduleur['marque']} {self.onduleur['modele']}")
                c.setFont("Helvetica", 6 if nb_onduleurs == 1 else 5)
                c.drawString(info_x, oy + 0.3*cm,
                             f"P AC: {self.onduleur['p_ac']/1000:.1f}kW | P DC: {self.onduleur['p_dc_max']/1000:.1f}kW")
                c.drawString(info_x, oy - 0.2*cm,
                             f"{self.onduleur['mppt']} MPPT | η={self.onduleur.get('rendement_max', 97)}% | {self.ip_onduleur}")
        
        # Câble AC de sortie des onduleurs : convergence vers un collecteur AC horizontal
        # puis descente vers sectionneur AC
        ond_sortie_y = onduleur_y - 1.1*cm
        
        if nb_onduleurs > 1:
            # Collecteur AC horizontal sous les onduleurs
            collecteur_ac_y = onduleur_y - 2.2*cm
            c.setStrokeColor(colors.black)
            c.setLineWidth(1.5)
            min_ox = ond_start_x
            max_ox = ond_start_x + (nb_onduleurs - 1) * ond_espacement
            c.line(min_ox, collecteur_ac_y, max_ox, collecteur_ac_y)
            for ox, oy in ond_positions:
                c.line(ox, oy - 1*cm, ox, collecteur_ac_y)
            # Câble principal AC depuis centre du collecteur
            collecteur_center_x = (min_ox + max_ox) / 2
            c.setLineWidth(2.5)
            c.line(collecteur_center_x, collecteur_ac_y, onduleur_x, onduleur_y - 3*cm)
            # Décaler le point de sortie AC pour la suite du schéma
            ond_sortie_y = onduleur_y - 3*cm
        
        # === 4.bis BATTERIE DE STOCKAGE (si présente - NF C 15-712-2) ===
        
        if self.avec_batterie:
            batterie_x = onduleur_x + 5*cm
            batterie_y = onduleur_y
            # Symbole batterie
            c.setLineWidth(1.5)
            c.rect(batterie_x - 0.8*cm, batterie_y - 0.8*cm, 1.6*cm, 1.6*cm)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(batterie_x, batterie_y + 2*mm, "BAT")
            c.setFont("Helvetica", 5)
            c.drawCentredString(batterie_x, batterie_y - 3*mm, "BMS")
            
            # Infos batterie (à droite)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(batterie_x + 1.2*cm, batterie_y + 0.6*cm, 
                        f"{self.batterie.get('marque', 'Batterie')} {self.batterie.get('modele', '')}")
            c.setFont("Helvetica", 6)
            capacite_kwh = self.batterie.get('capacite_kwh', 0)
            tension_v = self.batterie.get('tension_nominale', 48)
            c.drawString(batterie_x + 1.2*cm, batterie_y + 0.1*cm, 
                        f"{capacite_kwh:.1f}kWh | {tension_v}V DC")
            c.drawString(batterie_x + 1.2*cm, batterie_y - 0.4*cm, 
                        f"BMS intégré | Li-Ion")
            
            # Connexion onduleur ↔ batterie (liaison DC bidirectionnelle)
            c.setStrokeColor(colors.HexColor('#9400D3'))  # Violet pour batterie
            c.setLineWidth(2)
            c.line(onduleur_x + 1*cm, onduleur_y, batterie_x - 0.8*cm, batterie_y)
            
            # Annotations liaison batterie
            c.setFont("Helvetica", 5)
            c.setFillColor(colors.HexColor('#9400D3'))
            c.drawString(onduleur_x + 2*cm, onduleur_y - 0.8*cm, "DC Batterie")
            c.setFillColor(colors.black)
            c.setStrokeColor(colors.black)
            
            # Protection batterie (fusible/disjoncteur DC)
            fusible_bat_x = (onduleur_x + batterie_x) / 2
            fusible_bat_y = onduleur_y
            SymbolesElectriques.fusible(c, fusible_bat_x, fusible_bat_y, orientation='horizontal')
            calibre_fusible_bat = int(capacite_kwh * 1000 / tension_v * 1.5) if capacite_kwh > 0 else 50
            c.setFont("Helvetica", 5)
            c.drawString(fusible_bat_x - 0.5*cm, fusible_bat_y + 5*mm, f"{calibre_fusible_bat}A")
            
            # Parafoudre DC batterie (en dessous)
            para_bat_y = batterie_y - 2*cm
            SymbolesElectriques.parafoudre(c, batterie_x, para_bat_y, orientation='vertical')
            c.setFont("Helvetica", 5)
            c.drawString(batterie_x + 5*mm, para_bat_y - 5*mm, "SPD Type 2")
            
            # Terre batterie
            terre_bat_y = para_bat_y - 15*mm
            SymbolesElectriques.terre(c, batterie_x, terre_bat_y)
        
        # === 5. CÂBLE AC ONDULEUR(S) → PROTECTIONS ===
        
        nb_phases = 3 if '400V' in self.type_reseau else 1
        
        # Ligne verticale onduleur → sectionneur AC
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        sect_ac_x = onduleur_x
        sect_ac_y = prot_ac_y + 3.5*cm
        c.line(onduleur_x, ond_sortie_y, sect_ac_x, sect_ac_y + 8*mm)
        
        # Sectionneur AC (entre onduleur et AGCP)
        SymbolesElectriques.sectionneur(c, sect_ac_x, sect_ac_y, orientation='vertical')
        
        # Ligne verticale Sectionneur AC → AGCP
        agcp_x = prot_ac_x
        agcp_y = prot_ac_y + 4*cm
        c.line(sect_ac_x, sect_ac_y - 8*mm, agcp_x, agcp_y + 8*mm)
        
        # Annotation câble AC + distance + type + PE (à gauche du câble)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(colors.blue)
        mid_ac_y = (onduleur_y + prot_ac_y) / 2
        phases_str = f"{nb_phases}P+N+" if nb_phases > 1 else "Ph+N+"
        c.drawString(onduleur_x - 5*cm, mid_ac_y + 0.8*cm, 
                           f"AC: {phases_str}PE {self.section_cable_ac}mm²")
        c.setFont("Helvetica", 6)
        c.drawString(onduleur_x - 5*cm, mid_ac_y + 0.3*cm, 
                           f"{self.type_cable_ac} - L={self.longueur_ac_onduleur_tgbt:.1f}m")
        c.drawString(onduleur_x - 5*cm, mid_ac_y - 0.2*cm, 
                           f"ΔU={self.chute_tension_ac_pct:.2f}%")
        c.setFillColor(colors.black)
        
        # === 6. PROTECTIONS AC (TGBT) ===
        
        # AGCP - Appareil Général de Commande et Protection (au dessus TGBT)
        SymbolesElectriques.disjoncteur(c, agcp_x, agcp_y, orientation='vertical')
        c.setFont("Helvetica-Bold", 7)
        c.drawString(agcp_x + 2.5*cm, agcp_y + 8*mm, "AGCP")
        c.setFont("Helvetica", 6)
        c.drawString(agcp_x + 2.5*cm, agcp_y + 3*mm, f"{self.calibre_agcp}A courbe {self.courbe_agcp}")
        c.drawString(agcp_x + 2.5*cm, agcp_y - 3*mm, f"PdC: {self.pouvoir_coupure_agcp}")
        
        # Ligne verticale AGCP → Disjoncteur différentiel
        disj_y = prot_ac_y + 2*cm
        c.line(agcp_x, agcp_y - 8*mm, agcp_x, disj_y + 8*mm)
        # Disjoncteur différentiel (entre AGCP et TGBT)
        SymbolesElectriques.differentiel(c, prot_ac_x, disj_y, orientation='vertical')
        c.setFont("Helvetica", 6)
        c.drawString(prot_ac_x + 2.5*cm, disj_y + 3*mm, 
                   f"{self.type_differentiel}")
        c.drawString(prot_ac_x + 2.5*cm, disj_y - 3*mm, 
                   f"Type A 30mA")
        c.drawString(prot_ac_x + 2.5*cm, disj_y - 8*mm, 
                   f"PdC: {self.pouvoir_coupure_ac}")
        
        # Ligne verticale disjoncteur → TGBT
        c.line(prot_ac_x, disj_y - 8*mm, prot_ac_x, prot_ac_y + 1.25*cm)
        
        # Boîte TGBT (rectangle compact) — libellé selon type raccordement
        c.setLineWidth(1.5)
        c.rect(prot_ac_x - 0.75*cm, prot_ac_y - 0.75*cm, 1.5*cm, 1.5*cm)
        c.setFont("Helvetica-Bold", 6)
        if self.type_raccordement in ('autoconso_injection', 'autoconso_sans_injection'):
            c.drawCentredString(prot_ac_x, prot_ac_y + 1*mm, "TGBT")
            c.setFont("Helvetica", 4.5)
            c.drawCentredString(prot_ac_x, prot_ac_y - 3*mm, "Tableau bâtiment")
        else:
            c.drawCentredString(prot_ac_x, prot_ac_y + 1*mm, "PDL")
            c.setFont("Helvetica", 4.5)
            c.drawCentredString(prot_ac_x, prot_ac_y - 3*mm, "Pt livraison")
        
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
        
        # === 7. POINT D'INJECTION / RACCORDEMENT RÉSEAU ===
        # Conformément à C15-712 Complémentaire Jan.2025 §14.6 :
        # - Autoconsommation (avec ou sans vente surplus) → schéma passe par le TGBT
        #   Le TGBT est déjà l'élément central du tableau électrique existant.
        #   L'onduleur s'y raccorde via un disjoncteur dédié (AGCP).
        # - Injection totale (vente totale) → raccordement direct au poste de transformation
        #   ou au point de livraison réseau, sans passer par le TGBT habitant.
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2.5)
        
        if self.type_raccordement in ('autoconso_injection', 'autoconso_sans_injection'):
            # ── CAS AUTOCONSOMMATION : Onduleur → TGBT → Réseau (bidirectionnel) ──
            # Le TGBT est le nœud central : il alimente les charges ET reçoit la production PV
            
            # Ligne TGBT → Réseau (câble de soutirage / injection)
            c.line(prot_ac_x, prot_ac_y - 0.75*cm, injection_x, injection_y + 0.65*cm)
            
            # Annotation câble TGBT → réseau
            mid_inj_y = (prot_ac_y + injection_y) / 2
            c.setFont("Helvetica", 6)
            c.setFillColor(colors.HexColor('#28a745'))
            c.drawString(prot_ac_x - 3.5*cm, mid_inj_y + 0.5*cm, "▼ Injection surplus")
            c.setFillColor(colors.HexColor('#ffc107'))
            c.drawString(prot_ac_x - 3.5*cm, mid_inj_y - 0.5*cm, "▲ Soutirage réseau")
            c.setFillColor(colors.black)
            c.drawString(prot_ac_x - 3.5*cm, mid_inj_y,
                         f"L={self.longueur_ac_tgbt_injection:.1f}m")
            
            # Symbole compteur bidirectionnel
            SymbolesElectriques.compteur(c, injection_x, injection_y, size=1.3*cm)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(injection_x + 1*cm, injection_y + 0.3*cm, self.type_reseau)
            c.setFont("Helvetica", 6)
            c.drawString(injection_x + 1*cm, injection_y - 0.2*cm, "Compteur Linky bidirectionnel")
            c.setFont("Helvetica", 6)
            c.drawString(injection_x + 1*cm, injection_y - 0.6*cm, "RÉSEAU PUBLIC (BT)")
            
            # Flèche réseau → départ vers charges (vers le bas)
            charges_y = injection_y - 1.5*cm
            c.setLineWidth(1.5)
            c.setDash(4, 3)
            c.line(injection_x, injection_y - 0.65*cm, injection_x, charges_y)
            c.setDash()
            c.setFont("Helvetica", 5.5)
            c.setFillColor(colors.HexColor('#6c757d'))
            c.drawCentredString(injection_x, charges_y - 0.3*cm, "Vers charges bâtiment")
            c.setFillColor(colors.black)
            
            if self.type_raccordement == 'autoconso_sans_injection':
                # Surcharge textuelle : pas d'injection
                c.setFont("Helvetica-Bold", 6)
                c.setFillColor(colors.HexColor('#dc3545'))
                c.drawString(prot_ac_x - 3.5*cm, mid_inj_y - 1*cm, "(Sans injection réseau)")
                c.setFillColor(colors.black)
        
        else:
            # ── CAS INJECTION TOTALE : Onduleur → Compteur → Poste de transformation ──
            # Pas de TGBT habitant : raccordement direct au poste livraison réseau.
            # Le TGBT représente ici le PDL (Point De Livraison) ou coffret de comptage.
            
            # Ligne TGBT/PDL → compteur
            c.line(prot_ac_x, prot_ac_y - 0.75*cm, injection_x, injection_y + 0.65*cm)
            
            # Annotation câble production → réseau
            mid_inj_y = (prot_ac_y + injection_y) / 2
            c.setFont("Helvetica", 6)
            c.setFillColor(colors.HexColor('#28a745'))
            c.drawString(prot_ac_x - 3.5*cm, mid_inj_y + 0.2*cm, "▼ Injection totale")
            c.setFillColor(colors.HexColor('#0d6efd'))
            c.drawString(prot_ac_x - 3.5*cm, mid_inj_y - 0.3*cm, "(Vente totale production)")
            c.setFillColor(colors.black)
            c.drawString(prot_ac_x - 3.5*cm, mid_inj_y - 0.7*cm,
                         f"L={self.longueur_ac_tgbt_injection:.1f}m")
            
            # Symbole compteur de production
            SymbolesElectriques.compteur(c, injection_x, injection_y, size=1.3*cm)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(injection_x + 1*cm, injection_y + 0.3*cm, self.type_reseau)
            c.setFont("Helvetica", 6)
            c.drawString(injection_x + 1*cm, injection_y - 0.2*cm, "Compteur production")
            
            # Ligne vers poste de transformation (en bas)
            poste_y = injection_y - 2*cm
            c.setLineWidth(2.5)
            c.line(injection_x, injection_y - 0.65*cm, injection_x, poste_y + 0.5*cm)
            
            # Symbole poste de transformation (rectangle + T)
            c.setLineWidth(1.5)
            c.rect(injection_x - 1.2*cm, poste_y - 0.8*cm, 2.4*cm, 1.3*cm)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(injection_x, poste_y + 0.1*cm, "POSTE DE TRANSFO")
            c.setFont("Helvetica", 5)
            poste_nom = self.prospect.get('poste_bt_nom', '') or self.prospect.get('poste_hta_nom', '')
            poste_dist = self.prospect.get('poste_bt_distance_m') or self.prospect.get('poste_hta_distance_m', '')
            info_poste = poste_nom[:20] if poste_nom else 'ERDF / Enedis'
            if poste_dist:
                info_poste += f"  ({int(poste_dist)}m)"
            c.drawCentredString(injection_x, poste_y - 0.4*cm, info_poste)
            c.setFont("Helvetica", 5)
            c.drawCentredString(injection_x, poste_y - 0.7*cm, "RÉSEAU PUBLIC (BT/HTA)")
        
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
        """Dessine la page des notes de calculs — style ingenieur"""
        
        margin = 1.5*cm
        
        # ── Cartouche bas page 2 ──
        cb_w = 7*cm
        cb_h = 1.5*cm
        cb_x = width - margin - cb_w
        cb_y = 0.8*cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.rect(cb_x, cb_y, cb_w, cb_h)
        c.setLineWidth(0.5)
        c.line(cb_x + cb_w / 2, cb_y, cb_x + cb_w / 2, cb_y + cb_h)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawString(cb_x + 0.2*cm, cb_y + cb_h - 0.4*cm, "NOTES DE CALCULS")
        c.setFont("Helvetica", 7)
        c.drawString(cb_x + 0.2*cm, cb_y + 0.25*cm, f"Ind. {self.indice_revision}")
        c.drawString(cb_x + cb_w / 2 + 0.2*cm, cb_y + cb_h - 0.4*cm, "Page 2/2")
        c.drawString(cb_x + cb_w / 2 + 0.2*cm, cb_y + 0.25*cm, datetime.now().strftime('%d/%m/%Y'))
        
        # ── Bandeau titre sobre ──
        y_titre = height - 2*cm
        c.setFillColor(colors.HexColor('#1a1a2e'))
        c.rect(margin, y_titre - 0.3*cm, width - 2 * margin, 1*cm, fill=1, stroke=1)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(margin + 0.5*cm, y_titre, "NOTES DE CALCULS ET VERIFICATIONS DE CONFORMITE")
        c.setFillColor(colors.black)
        
        y = height - 4*cm
        
        # ── Couleurs neutres pour tableaux ──
        header_bg = colors.HexColor('#2d2d3f')
        header_fg = colors.whitesmoke
        row_even = colors.HexColor('#f5f5f8')
        row_odd = colors.white
        border_color = colors.HexColor('#cccccc')
        
        # === 1. CONFIGURATION ELECTRIQUE ===
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y, "1.  CONFIGURATION ELECTRIQUE")
        y -= 0.7*cm
        
        table_data = [
            ['Parametre', 'Valeur', 'Reference norme'],
            ['Puissance totale installee', f"{self.puissance_totale_kwc:.2f} kWc", 'NF C 15-712 art. 3.1'],
            ['Nombre total de modules', f"{self.nb_modules_total}", ''],
            ['Module photovoltaique', f"{self.module_puissance}Wc ({self.module.get('longueur')}x{self.module.get('largeur')}mm)", ''],
            ['Nombre de strings', f"{len(self.configuration_strings)}", ''],
            ['Modules par string (moy.)', f"{self.nb_modules_total / len(self.configuration_strings):.1f}", ''],
            ['Onduleur', f"{self.onduleur['marque']} {self.onduleur['modele']}", ''],
            ['Puissance onduleur AC', f"{self.onduleur['p_ac']/1000:.1f} kW", ''],
            ['Ratio DC/AC', f"{(self.puissance_totale_kwc * 1000 / self.onduleur['p_ac']):.2f}", 'Optimal : 1.2 - 1.3'],
            ['Type raccordement',
             'Autoconsommation (TGBT)' if self.type_raccordement in ('autoconso_injection','autoconso_sans_injection')
             else 'Injection totale (Poste transfo)',
             'C15-712 Compl. 2025 §14.6'],
            ['Nombre de pans / onduleurs', f"{max(1, len([z for z in self.zones if z.get('nbModules',0)>0]))}", ''],
        ]
        
        table = Table(table_data, colWidths=[7.5*cm, 5.5*cm, 5.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), header_fg),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_odd, row_even]),
        ]))
        
        table.wrapOn(c, width, height)
        table.drawOn(c, 2*cm, y - 6.5*cm)
        
        y -= 8*cm
        
        # === 2. DIMENSIONNEMENT CABLES ===
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y, "2.  DIMENSIONNEMENT DES CABLES")
        y -= 0.7*cm
        
        # Calculer chute de tension par string pour affichage
        rho_70 = 0.0225
        i_string_max = max(s['i_mpp'] for s in self.configuration_strings)
        v_string_moy = sum(s['v_mpp'] for s in self.configuration_strings) / len(self.configuration_strings)
        delta_u_string = (2 * rho_70 * self.longueur_dc * i_string_max / self.section_cable_string) if self.section_cable_string > 0 else 0
        delta_u_string_pct = (delta_u_string / v_string_moy) * 100 if v_string_moy > 0 else 0
        
        table_data2 = [
            ['Type cable', 'Section (mm2)', 'I max (A)', 'DeltaU calc.', 'Ref. norme'],
            ['Cables strings DC', f"{self.section_cable_string} mm2 Cu", 
             f"{max(s['i_sc'] * 1.25 for s in self.configuration_strings):.1f}", 
             f"{delta_u_string_pct:.2f}% (< 2%)", 'NF C 15-712 art. 7.12.1.1'],
            ['Cable principal DC', f"{self.section_cable_dc} mm2 Cu", 
             f"{sum(s['i_sc'] * 1.25 for s in self.configuration_strings):.1f}", 
             f"{self.chute_tension_dc_pct:.2f}% (< 2%)", 'NF C 15-712 art. 7.12.1.1'],
            ['Cable onduleur AC', f"{self.section_cable_ac} mm2 Cu", 
             f"{self.courant_max_ac:.1f}", 
             f"{self.chute_tension_ac_pct:.2f}% (< 2%)", 'NF C 15-100'],
            ['Longueur DC', f"{self.longueur_dc:.1f} m", '', '', ''],
            ['Longueur AC ond.-TGBT', f"{self.longueur_ac_onduleur_tgbt:.1f} m", '', '', ''],
            ['Longueur AC TGBT-inj.', f"{self.longueur_ac_tgbt_injection:.1f} m", '', '', ''],
        ]
        
        table2 = Table(table_data2, colWidths=[5*cm, 3*cm, 3*cm, 3*cm, 4.5*cm])
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), header_fg),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_odd, row_even]),
        ]))
        
        table2.wrapOn(c, width, height)
        table2.drawOn(c, 2*cm, y - 5.5*cm)
        
        y -= 7*cm
        
        # === 3. PROTECTIONS ELECTRIQUES ===
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y, "3.  PROTECTIONS ELECTRIQUES")
        y -= 0.7*cm
        
        sectionneur_ac_info = f"{self.calibre_sectionneur_ac}A - Cadenassable" if hasattr(self, 'calibre_sectionneur_ac') else ''
        table_data3 = [
            ['Protection', 'Caracteristiques', 'Ref. norme'],
            ['Sectionneur DC general', f"{self.calibre_sectionneur_dc}A - {self.tension_sectionneur_dc}", 'NF C 15-712 art. 7.12.3.1'],
            ['Parafoudre DC', self.parafoudre_dc, 'NF C 15-712 art. 7.12.3.4'],
            ['Fusibles strings', self.fusibles_strings, 'NF C 15-712 art. 7.12.2.2.1'],
            ['Sectionneur AC', sectionneur_ac_info, 'NF C 15-712 art. 7.12.3.2'],
            ['AGCP', f"{self.calibre_agcp}A courbe {self.courbe_agcp} - PdC {self.pouvoir_coupure_agcp}", 'NF C 15-712'],
            ['Disj. differentiel AC', f"{self.calibre_disjoncteur_ac}A courbe C - {self.type_differentiel}", 'NF C 15-100'],
            ['Parafoudre AC', self.parafoudre_ac, 'NF C 15-712 art. 7.12.3.4'],
            ['Conducteur PE DC', f"{self.section_pe_dc} mm2 Cu", 'NF C 15-100 art. 543.1'],
            ['Conducteur PE AC', f"{self.section_pe_ac} mm2 Cu", 'NF C 15-100 art. 543.1'],
            ['Mise a la terre', f"R < {self.resistance_terre_max} - LEP {self.section_terre_principal}", 'NF C 15-712 art. 7.13'],
        ]
        
        table3 = Table(table_data3, colWidths=[5*cm, 8*cm, 5.5*cm])
        table3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), header_fg),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_odd, row_even]),
        ]))
        
        table3.wrapOn(c, width, height)
        table3.drawOn(c, 2*cm, y - 8*cm)
        
        y -= 9.5*cm
        
        # === 4. VERIFICATIONS CONFORMITE ===
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y, "4.  VERIFICATIONS DE CONFORMITE NF C 15-712")
        y -= 0.6*cm
        
        c.setFont("Helvetica", 8)
        
        # Vérifications dynamiques basées sur les valeurs calculées
        v_oc_max_calc = max(s['v_oc'] * 1.25 for s in self.configuration_strings)  # -10°C
        v_mpp_min_calc = min(s['v_mpp'] * 0.85 for s in self.configuration_strings)  # +70°C
        i_sc_total_calc = sum(s['i_sc'] for s in self.configuration_strings)
        i_max_ond = self.onduleur.get('i_max', 30) * self.onduleur.get('mppt', 2)
        ratio_dc_ac = self.puissance_totale_kwc * 1000 / self.onduleur['p_ac'] if self.onduleur['p_ac'] > 0 else 0
        
        chk_voc = 'OK' if v_oc_max_calc < self.onduleur['v_max'] else 'NOK'
        chk_vmpp = 'OK' if v_mpp_min_calc > self.onduleur['v_min'] else 'NOK'
        chk_idc = 'OK' if i_sc_total_calc < i_max_ond else 'NOK'
        chk_du = 'OK' if self.chute_tension_dc_pct < 2 and self.chute_tension_ac_pct < 2 else 'NOK'
        chk_ratio = 'OK' if 0.9 <= ratio_dc_ac <= 1.5 else 'WARN'
        
        checks = [
            f"[{chk_voc}]  Voc max (-10C) = {v_oc_max_calc:.0f}V < Vmax onduleur {self.onduleur['v_max']}V",
            f"[{chk_vmpp}]  Vmpp min (+70C) = {v_mpp_min_calc:.0f}V > Vmin MPPT {self.onduleur['v_min']}V",
            f"[{chk_idc}]  Isc total = {i_sc_total_calc:.1f}A < Imax onduleur {i_max_ond}A",
            f"[{chk_du}]  DeltaU DC = {self.chute_tension_dc_pct:.2f}% | DeltaU AC = {self.chute_tension_ac_pct:.2f}% (seuil 2%)",
            "[OK]  Sections cables >= courants admissibles NF C 15-100",
            f"[OK]  Protection differentielle : {self.type_differentiel}",
            "[OK]  Parafoudres DC et AC Type 2 (obligatoire NF C 15-712)",
            f"[OK]  Sectionneur DC {self.calibre_sectionneur_dc}A avec coupure visible",
            f"[OK]  Mise a la terre R < {self.resistance_terre_max} + LEP",
            f"[{chk_ratio}]  Ratio DC/AC = {ratio_dc_ac:.2f} (plage 1.0 - 1.5)",
        ]
        
        for check in checks:
            c.drawString(2.5*cm, y, check)
            y -= 0.45*cm
        
        # Conclusion
        y -= 0.4*cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, y, "CONCLUSION :  Installation conforme NF C 15-712-1")
        if self.avec_batterie:
            y -= 0.4*cm
            c.drawString(2*cm, y, "               Stockage conforme NF C 15-712-2")
        
        # Avertissement
        y -= 1.2*cm
        c.setLineWidth(1)
        c.rect(2*cm, y - 2*cm, width - 4*cm, 2.3*cm)
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(2.3*cm, y, "AVERTISSEMENT")
        c.setFont("Helvetica", 7)
        y -= 0.4*cm
        c.drawString(2.3*cm, y, "Ce schema unifilaire est genere automatiquement a partir du calepinage. Les calculs sont conformes aux normes")
        y -= 0.3*cm
        c.drawString(2.3*cm, y, "en vigueur, mais doivent etre verifies par un professionnel qualifie avant mise en oeuvre. Les longueurs de")
        y -= 0.3*cm
        c.drawString(2.3*cm, y, "cables sont estimees et doivent etre mesurees sur site. Le choix du materiel doit tenir compte des contraintes")
        y -= 0.3*cm
        c.drawString(2.3*cm, y, "locales (temperature, altitude, environnement corrosif, etc.).")
