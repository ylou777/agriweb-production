"""
Bases de données techniques - Modules PV et Onduleurs
AgriWeb 2025 - Catalogue professionnel
"""

# ============================================================================
# BASE DE DONNÉES MODULES PHOTOVOLTAÏQUES
# ============================================================================

MODULES_PV_DATABASE = {
    # CANADIAN SOLAR (Leader mondial, excellent rapport qualité/prix)
    'CS-550W': {
        'fabricant': 'Canadian Solar',
        'modele': 'HiKu6 CS6W-550MS',
        'puissance': 550,  # Wc
        'voc': 49.5,       # V (tension circuit ouvert)
        'vmpp': 41.8,      # V (tension point de puissance max)
        'isc': 13.9,       # A (courant court-circuit)
        'impp': 13.2,      # A (courant point de puissance max)
        'longueur': 2278,  # mm
        'largeur': 1134,   # mm
        'epaisseur': 35,   # mm
        'poids': 27.5,     # kg
        'rendement': 21.2, # %
        'technologie': 'Monocristallin PERC',
        'garantie_produit': 12,  # années
        'garantie_performance': 25,  # années
        'prix_indicatif': 180,  # € HT
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34,  # %/°C
        'coeff_temp_voc': -0.27,   # %/°C
        'coeff_temp_isc': 0.048    # %/°C
    },
    'CS-450W': {
        'fabricant': 'Canadian Solar',
        'modele': 'HiKu CS3W-450MS',
        'puissance': 450,
        'voc': 49.1,
        'vmpp': 41.2,
        'isc': 11.53,
        'impp': 10.93,
        'longueur': 2108,
        'largeur': 1048,
        'epaisseur': 35,
        'poids': 24.0,
        'rendement': 20.4,
        'technologie': 'Monocristallin PERC',
        'garantie_produit': 12,
        'garantie_performance': 25,
        'prix_indicatif': 150,
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.35,
        'coeff_temp_voc': -0.27,
        'coeff_temp_isc': 0.048
    },
    
    # JINKO SOLAR (Top 3 mondial, très performant)
    'JKM-575W': {
        'fabricant': 'Jinko Solar',
        'modele': 'Tiger Neo N-type JKM575N-72HL4-BDV',
        'puissance': 575,
        'voc': 51.45,
        'vmpp': 43.30,
        'isc': 14.10,
        'impp': 13.28,
        'longueur': 2278,
        'largeur': 1134,
        'epaisseur': 30,
        'poids': 28.6,
        'rendement': 22.2,
        'technologie': 'Monocristallin N-type TOPCon',
        'garantie_produit': 15,
        'garantie_performance': 30,
        'prix_indicatif': 200,
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29,  # Meilleur coeff température (N-type)
        'coeff_temp_voc': -0.24,
        'coeff_temp_isc': 0.045
    },
    'JKM-460W': {
        'fabricant': 'Jinko Solar',
        'modele': 'Tiger Pro JKM460M-60HL4-V',
        'puissance': 460,
        'voc': 49.75,
        'vmpp': 41.85,
        'isc': 11.65,
        'impp': 10.99,
        'longueur': 1903,
        'largeur': 1134,
        'epaisseur': 30,
        'poids': 24.5,
        'rendement': 21.3,
        'technologie': 'Monocristallin PERC',
        'garantie_produit': 12,
        'garantie_performance': 25,
        'prix_indicatif': 155,
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34,
        'coeff_temp_voc': -0.26,
        'coeff_temp_isc': 0.048
    },
    
    # JA SOLAR (Innovant, excellent rendement)
    'JAM72S30': {
        'fabricant': 'JA Solar',
        'modele': 'JAM72S30 560W',
        'puissance': 560,
        'voc': 49.85,
        'vmpp': 42.05,
        'isc': 14.10,
        'impp': 13.32,
        'longueur': 2278,
        'largeur': 1134,
        'epaisseur': 35,
        'poids': 28.0,
        'rendement': 21.6,
        'technologie': 'Monocristallin PERC Half-cell',
        'garantie_produit': 12,
        'garantie_performance': 25,
        'prix_indicatif': 185,
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.35,
        'coeff_temp_voc': -0.27,
        'coeff_temp_isc': 0.050
    },
    
    # LONGI SOLAR (Premium, leader technologie)
    'LR5-72HBD': {
        'fabricant': 'LONGi Solar',
        'modele': 'Hi-MO 5 LR5-72HBD-565M',
        'puissance': 565,
        'voc': 49.95,
        'vmpp': 42.10,
        'isc': 14.26,
        'impp': 13.42,
        'longueur': 2278,
        'largeur': 1134,
        'epaisseur': 35,
        'poids': 28.3,
        'rendement': 21.8,
        'technologie': 'Monocristallin PERC',
        'garantie_produit': 12,
        'garantie_performance': 25,
        'prix_indicatif': 195,
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34,
        'coeff_temp_voc': -0.26,
        'coeff_temp_isc': 0.048
    },
    
    # TRINA SOLAR (Très populaire France)
    'TSM-DEG21C': {
        'fabricant': 'Trina Solar',
        'modele': 'Vertex S TSM-DEG21C.20 550W',
        'puissance': 550,
        'voc': 49.60,
        'vmpp': 41.90,
        'isc': 13.95,
        'impp': 13.13,
        'longueur': 2278,
        'largeur': 1134,
        'epaisseur': 30,
        'poids': 27.8,
        'rendement': 21.2,
        'technologie': 'Monocristallin PERC',
        'garantie_produit': 12,
        'garantie_performance': 25,
        'prix_indicatif': 178,
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34,
        'coeff_temp_voc': -0.26,
        'coeff_temp_isc': 0.048
    },
    
    # MODULES PREMIUM (Fabrication européenne)
    'SUNPOWER-400': {
        'fabricant': 'SunPower (Maxeon)',
        'modele': 'Maxeon 3 SPR-MAX3-400',
        'puissance': 400,
        'voc': 67.8,
        'vmpp': 57.3,
        'isc': 7.12,
        'impp': 6.98,
        'longueur': 1690,
        'largeur': 1046,
        'epaisseur': 40,
        'poids': 19.0,
        'rendement': 22.6,  # Excellent rendement
        'technologie': 'Monocristallin IBC (Interdigitated Back Contact)',
        'garantie_produit': 25,  # Garantie exceptionnelle
        'garantie_performance': 40,
        'prix_indicatif': 350,  # Premium
        'disponibilite': 'sur commande',
        'classe_feu': 'Classe A',
        'coeff_temp_pmax': -0.29,  # Meilleur du marché
        'coeff_temp_voc': -0.27,
        'coeff_temp_isc': 0.035
    },
    
    # MODULES FRANÇAIS (Made in France)
    'VOLTEC-430': {
        'fabricant': 'Voltec Solar (France)',
        'modele': 'VS-430-M6-PERC',
        'puissance': 430,
        'voc': 49.20,
        'vmpp': 41.50,
        'isc': 10.98,
        'impp': 10.36,
        'longueur': 1755,
        'largeur': 1038,
        'epaisseur': 35,
        'poids': 22.0,
        'rendement': 23.5,  # Excellent rendement
        'technologie': 'Monocristallin PERC',
        'garantie_produit': 20,
        'garantie_performance': 30,
        'prix_indicatif': 280,
        'disponibilite': 'stock France',
        'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.35,
        'coeff_temp_voc': -0.28,
        'coeff_temp_isc': 0.050,
        'made_in_france': True
    },
    
    # MODULES BIFACIAUX (Production recto-verso)
    'CS-580W-BIFACIAL': {
        'fabricant': 'Canadian Solar',
        'modele': 'BiHiKu7 CS7N-580TB-AG',
        'puissance': 580,
        'voc': 51.80,
        'vmpp': 43.60,
        'isc': 14.20,
        'impp': 13.30,
        'longueur': 2278,
        'largeur': 1134,
        'epaisseur': 35,
        'poids': 31.5,
        'rendement': 22.4,
        'technologie': 'Monocristallin N-type Bifacial',
        'garantie_produit': 15,
        'garantie_performance': 30,
        'prix_indicatif': 220,
        'disponibilite': 'stock',
        'classe_feu': 'Classe C',
        'bifacial': True,
        'bifaciality': 70,  # % gain face arrière
        'coeff_temp_pmax': -0.30,
        'coeff_temp_voc': -0.25,
        'coeff_temp_isc': 0.045
    }
}

# ============================================================================
# BASE DE DONNÉES ONDULEURS
# ============================================================================

ONDULEURS_DATABASE = {
    # ========== HUAWEI (Leader France résidentiel/tertiaire) ==========
    
    # Série L1 (Monophasé 3-6kW)
    'HUAWEI-3KTL-L1': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-3KTL-L1',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 3000,      # W
        'p_dc_max': 4500,            # W
        'rendement_max': 97.6,       # %
        'rendement_euro': 97.0,      # %
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 90,              # V
        'v_dc_nominal': 360,         # V
        'v_dc_max': 560,             # V
        'i_dc_max_par_mppt': 12.5,   # A
        'i_ac_max': 13.6,            # A
        'v_ac_nominal': 230,         # V
        'frequence': '50/60',        # Hz
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '365×365×156', # mm (L×H×P)
        'poids': 10.5,               # kg
        'refroidissement': 'Convection naturelle',
        'ip': 'IP65',
        'garantie': 10,              # années (extensible 20)
        'prix_indicatif': 800,       # € HT
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True
    },
    'HUAWEI-5KTL-L1': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-5KTL-L1',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 5000,
        'p_dc_max': 7500,
        'rendement_max': 97.8,
        'rendement_euro': 97.3,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 90,
        'v_dc_nominal': 360,
        'v_dc_max': 560,
        'i_dc_max_par_mppt': 15.0,
        'i_ac_max': 22.7,
        'v_ac_nominal': 230,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '365×365×156',
        'poids': 11.0,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 950,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True
    },
    
    # Série M1 (Triphasé 6-12kW)
    'HUAWEI-6KTL-M1': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-6KTL-M1',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 6000,
        'p_dc_max': 9000,
        'rendement_max': 98.4,
        'rendement_euro': 98.0,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 12.5,
        'i_ac_max': 10.0,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '375×470×166',
        'poids': 17.0,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 1200,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    'HUAWEI-8KTL-M1': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-8KTL-M1',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 8000,
        'p_dc_max': 12000,
        'rendement_max': 98.4,
        'rendement_euro': 98.0,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 12.5,
        'i_ac_max': 13.3,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '375×470×166',
        'poids': 17.5,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 1400,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    'HUAWEI-10KTL-M1': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-10KTL-M1',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 10000,
        'p_dc_max': 15000,
        'rendement_max': 98.4,
        'rendement_euro': 98.0,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 12.5,
        'i_ac_max': 16.7,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '375×470×166',
        'poids': 18.0,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 1600,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    
    # Série M2 (Triphasé 12-20kW)
    'HUAWEI-12KTL-M2': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-12KTL-M2',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 12000,
        'p_dc_max': 18000,
        'rendement_max': 98.5,
        'rendement_euro': 98.1,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 15.0,
        'i_ac_max': 20.0,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '490×545×178',
        'poids': 26.0,
        'refroidissement': 'Ventilation forcée',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 2000,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    'HUAWEI-15KTL-M2': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-15KTL-M2',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 15000,
        'p_dc_max': 22500,
        'rendement_max': 98.5,
        'rendement_euro': 98.1,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 15.0,
        'i_ac_max': 25.0,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '490×545×178',
        'poids': 26.5,
        'refroidissement': 'Ventilation forcée',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 2300,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    'HUAWEI-20KTL-M2': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-20KTL-M2',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 20000,
        'p_dc_max': 30000,
        'rendement_max': 98.5,
        'rendement_euro': 98.2,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 22.0,
        'i_ac_max': 33.3,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '490×545×178',
        'poids': 27.0,
        'refroidissement': 'Ventilation forcée',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 2800,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    'HUAWEI-25KTL-M3': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-25KTL-M3',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 25000,
        'p_dc_max': 37500,
        'rendement_max': 98.6,
        'rendement_euro': 98.3,
        'nb_mppt': 3,
        'nb_strings_max': 3,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 20.0,
        'i_ac_max': 36.3,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '560×580×238',
        'poids': 32.0,
        'refroidissement': 'Ventilation forcée',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 3200,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    'HUAWEI-30KTL-M3': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-30KTL-M3',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 30000,
        'p_dc_max': 45000,
        'rendement_max': 98.6,
        'rendement_euro': 98.3,
        'nb_mppt': 3,
        'nb_strings_max': 3,
        'v_dc_min': 140,
        'v_dc_nominal': 600,
        'v_dc_max': 980,
        'i_dc_max_par_mppt': 25.0,
        'i_ac_max': 43.5,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD',
        'protection_ac': 'Type II SPD',
        'dimensions': '560×580×238',
        'poids': 34.0,
        'refroidissement': 'Ventilation forcée',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 3600,
        'disponibilite': 'stock',
        'smart_monitoring': True,
        'wifi_integre': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000'
    },
    
    # ========== FRONIUS (Premium Autriche) ==========
    
    'FRONIUS-PRIMO-3.0': {
        'fabricant': 'Fronius',
        'modele': 'Primo GEN24 3.0 Plus',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 3000,
        'p_dc_max': 4500,
        'rendement_max': 97.2,
        'rendement_euro': 96.8,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 80,
        'v_dc_nominal': 460,
        'v_dc_max': 1000,
        'i_dc_max_par_mppt': 16.0,
        'i_ac_max': 13.0,
        'v_ac_nominal': 230,
        'frequence': '50',
        'protection_dc': 'Type II SPD intégré',
        'protection_ac': 'Type II SPD intégré',
        'dimensions': '510×597×204',
        'poids': 20.3,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 1500,
        'disponibilite': 'stock',
        'compatible_batterie': True,
        'batterie_modele': 'BYD/LG',
        'monitoring': 'Fronius Solar.web',
        'made_in': 'Autriche'
    },
    'FRONIUS-PRIMO-5.0': {
        'fabricant': 'Fronius',
        'modele': 'Primo GEN24 5.0 Plus',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 5000,
        'p_dc_max': 7500,
        'rendement_max': 97.4,
        'rendement_euro': 97.0,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 80,
        'v_dc_nominal': 460,
        'v_dc_max': 1000,
        'i_dc_max_par_mppt': 16.0,
        'i_ac_max': 21.7,
        'v_ac_nominal': 230,
        'frequence': '50',
        'protection_dc': 'Type II SPD intégré',
        'protection_ac': 'Type II SPD intégré',
        'dimensions': '510×597×204',
        'poids': 20.8,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 1800,
        'disponibilite': 'stock',
        'compatible_batterie': True,
        'batterie_modele': 'BYD/LG',
        'monitoring': 'Fronius Solar.web',
        'made_in': 'Autriche'
    },
    'FRONIUS-SYMO-10.0': {
        'fabricant': 'Fronius',
        'modele': 'Symo GEN24 10.0 Plus',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 10000,
        'p_dc_max': 15000,
        'rendement_max': 98.0,
        'rendement_euro': 97.6,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 150,
        'v_dc_nominal': 580,
        'v_dc_max': 1000,
        'i_dc_max_par_mppt': 16.0,
        'i_ac_max': 14.5,
        'v_ac_nominal': 400,
        'frequence': '50',
        'protection_dc': 'Type II SPD intégré',
        'protection_ac': 'Type II SPD intégré',
        'dimensions': '645×431×204',
        'poids': 27.0,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 2500,
        'disponibilite': 'stock',
        'compatible_batterie': True,
        'batterie_modele': 'BYD/LG',
        'monitoring': 'Fronius Solar.web',
        'made_in': 'Autriche'
    },
    
    # ========== SMA (Leader allemand) ==========
    
    'SMA-SB-3.0': {
        'fabricant': 'SMA',
        'modele': 'Sunny Boy 3.0 Smart Energy',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 3000,
        'p_dc_max': 4500,
        'rendement_max': 97.0,
        'rendement_euro': 96.5,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 100,
        'v_dc_nominal': 400,
        'v_dc_max': 600,
        'i_dc_max_par_mppt': 15.0,
        'i_ac_max': 13.0,
        'v_ac_nominal': 230,
        'frequence': '50',
        'protection_dc': 'Sectionneur intégré',
        'protection_ac': 'Type II SPD en option',
        'dimensions': '460×460×180',
        'poids': 21.0,
        'refroidissement': 'OptiCool (convection)',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 1300,
        'disponibilite': 'stock',
        'compatible_batterie': True,
        'batterie_modele': 'SMA Home Storage',
        'monitoring': 'SMA Sunny Portal',
        'made_in': 'Allemagne'
    },
    'SMA-SB-5.0': {
        'fabricant': 'SMA',
        'modele': 'Sunny Boy 5.0 Smart Energy',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 5000,
        'p_dc_max': 7500,
        'rendement_max': 97.1,
        'rendement_euro': 96.7,
        'nb_mppt': 2,
        'nb_strings_max': 2,
        'v_dc_min': 100,
        'v_dc_nominal': 400,
        'v_dc_max': 600,
        'i_dc_max_par_mppt': 15.0,
        'i_ac_max': 21.7,
        'v_ac_nominal': 230,
        'frequence': '50',
        'protection_dc': 'Sectionneur intégré',
        'protection_ac': 'Type II SPD en option',
        'dimensions': '460×460×180',
        'poids': 21.5,
        'refroidissement': 'OptiCool (convection)',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 1600,
        'disponibilite': 'stock',
        'compatible_batterie': True,
        'batterie_modele': 'SMA Home Storage',
        'monitoring': 'SMA Sunny Portal',
        'made_in': 'Allemagne'
    },
    'SMA-STP-10.0': {
        'fabricant': 'SMA',
        'modele': 'Sunny Tripower 10.0',
        'type_reseau': 'Triphasé',
        'p_ac_nominale': 10000,
        'p_dc_max': 15000,
        'rendement_max': 98.3,
        'rendement_euro': 98.0,
        'nb_mppt': 2,
        'nb_strings_max': 5,
        'v_dc_min': 150,
        'v_dc_nominal': 530,
        'v_dc_max': 800,
        'i_dc_max_par_mppt': 20.0,
        'i_ac_max': 14.5,
        'v_ac_nominal': 400,
        'frequence': '50',
        'protection_dc': 'Sectionneur intégré',
        'protection_ac': 'Type II SPD en option',
        'dimensions': '665×682×264',
        'poids': 34.0,
        'refroidissement': 'OptiCool (convection)',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 2200,
        'disponibilite': 'stock',
        'monitoring': 'SMA Sunny Portal',
        'made_in': 'Allemagne'
    },
    
    # ========== SOLAREDGE (Optimiseurs de puissance) ==========
    
    'SOLAREDGE-SE5K': {
        'fabricant': 'SolarEdge',
        'modele': 'SE5K SetApp',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 5000,
        'p_dc_max': 7600,
        'rendement_max': 97.6,
        'rendement_euro': 97.1,
        'nb_mppt': 1,  # Optimiseurs = 1 MPPT par module
        'nb_strings_max': 1,
        'v_dc_min': 125,
        'v_dc_nominal': 350,
        'v_dc_max': 480,
        'i_dc_max_par_mppt': 15.0,
        'i_ac_max': 22.0,
        'v_ac_nominal': 230,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD en option',
        'protection_ac': 'Type II SPD en option',
        'dimensions': '350×460×156',
        'poids': 12.4,
        'refroidissement': 'Convection naturelle',
        'ip': 'IP65',
        'garantie': 12,
        'prix_indicatif': 1400,
        'disponibilite': 'stock',
        'technologie_specifique': 'Optimiseurs de puissance (1 par module)',
        'optimiseurs_requis': True,
        'optimiseur_modele': 'P370/P400/P505',
        'compatible_batterie': True,
        'batterie_modele': 'LG Chem/BYD',
        'monitoring': 'SolarEdge Monitoring',
        'monitoring_module': True  # Monitoring par module
    },
    
    # ========== ENPHASE (Micro-onduleurs) ==========
    
    'ENPHASE-IQ8PLUS': {
        'fabricant': 'Enphase',
        'modele': 'IQ8+ (Système 12 unités)',
        'type_reseau': 'Monophasé',
        'p_ac_nominale': 3360,  # 12 × 280W
        'p_dc_max': 5040,       # 12 × 420Wc
        'rendement_max': 97.0,
        'rendement_euro': 96.5,
        'nb_mppt': 12,  # 1 par micro-onduleur
        'nb_strings_max': 12,
        'v_dc_min': 16,
        'v_dc_nominal': 40,
        'v_dc_max': 60,
        'i_dc_max_par_mppt': 14.0,
        'i_ac_max': 14.6,
        'v_ac_nominal': 230,
        'frequence': '50',
        'protection_dc': 'Intégrée par unité',
        'protection_ac': 'Intégrée par unité',
        'dimensions': '211×175×30',  # Par unité
        'poids': 1.1,  # kg par unité
        'refroidissement': 'Convection naturelle',
        'ip': 'IP67',
        'garantie': 25,  # Exceptionnelle
        'prix_indicatif': 2400,  # 12 unités
        'disponibilite': 'stock',
        'technologie_specifique': 'Micro-onduleurs (1 par module)',
        'compatible_batterie': True,
        'batterie_modele': 'Enphase IQ Battery',
        'monitoring': 'Enphase Enlighten',
        'monitoring_module': True,
        'made_in': 'USA/Mexique'
    },
    
    # ========== ONDULEURS HAUTE PUISSANCE (Installations commerciales/industrielles) ==========
    
    'HUAWEI-50KTL-M0': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-50KTL-M0',
        'type_reseau': 'Triphasé 400V',
        'p_ac_nominale': 50000,
        'p_dc_max': 75000,
        'rendement_max': 98.7,
        'rendement_euro': 98.5,
        'nb_mppt': 4,
        'nb_strings_max': 8,
        'v_dc_min': 200,
        'v_dc_nominal': 820,
        'v_dc_max': 1100,
        'i_dc_max_par_mppt': 22.0,
        'i_ac_max': 75.0,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD + Sectionneurs',
        'protection_ac': 'Type II SPD',
        'dimensions': '860×640×310',
        'poids': 78.0,
        'refroidissement': 'Ventilation forcée',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 6500,
        'disponibilite': 'stock (1-2 semaines)',
        'smart_monitoring': True,
        'wifi_integre': True,
        'ethernet': True,
        '4G': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000',
        'monitoring': 'FusionSolar',
        'certification': 'CE, VDE-AR-N 4120',
        'made_in': 'Chine'
    },
    'HUAWEI-100KTL-M1': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-100KTL-M1',
        'type_reseau': 'Triphasé 400V',
        'p_ac_nominale': 100000,
        'p_dc_max': 150000,
        'rendement_max': 98.7,
        'rendement_euro': 98.5,
        'nb_mppt': 10,
        'nb_strings_max': 20,
        'v_dc_min': 200,
        'v_dc_nominal': 870,
        'v_dc_max': 1100,
        'i_dc_max_par_mppt': 26.0,
        'i_ac_max': 152.0,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type II SPD + Sectionneurs',
        'protection_ac': 'Type II SPD + Protection surcharge',
        'dimensions': '1035×700×365',
        'poids': 135.0,
        'refroidissement': 'Ventilation forcée intelligente',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 12000,
        'disponibilite': 'sur commande (2-4 semaines)',
        'smart_monitoring': True,
        'wifi_integre': True,
        'ethernet': True,
        '4G': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000 (jusqu\'à 5 unités)',
        'monitoring': 'FusionSolar Smart PV Management',
        'certification': 'CE, VDE-AR-N 4120, G98/99',
        'puissance_reactive': True,
        'q_on_demand': True,
        'made_in': 'Chine'
    },
    'SMA-CORE1-110': {
        'fabricant': 'SMA',
        'modele': 'Sunny Core1 110',
        'type_reseau': 'Triphasé 400V',
        'p_ac_nominale': 110000,
        'p_dc_max': 165000,
        'rendement_max': 98.5,
        'rendement_euro': 98.3,
        'nb_mppt': 6,
        'nb_strings_max': 30,
        'v_dc_min': 330,
        'v_dc_nominal': 795,
        'v_dc_max': 1100,
        'i_dc_max_par_mppt': 45.0,
        'i_ac_max': 159.0,
        'v_ac_nominal': 400,
        'frequence': '50/60',
        'protection_dc': 'Type I+II SPD intégré',
        'protection_ac': 'Type I+II SPD intégré',
        'dimensions': '1045×770×360',
        'poids': 148.0,
        'refroidissement': 'OptiCool ventilation intelligente',
        'ip': 'IP65',
        'garantie': 10,
        'prix_indicatif': 15000,
        'disponibilite': 'sur commande (3-6 semaines)',
        'ethernet': True,
        'rs485': True,
        'monitoring': 'SMA Sunny Portal / Data Manager',
        'certification': 'CE, VDE-AR-N 4120, EN 50549-1',
        'puissance_reactive': True,
        'q_on_demand': True,
        'cos_phi_reglable': True,
        'made_in': 'Allemagne'
    },
    'HUAWEI-215KTL-H1': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-215KTL-H1',
        'type_reseau': 'Triphasé 800V',
        'p_ac_nominale': 215000,
        'p_dc_max': 322500,
        'rendement_max': 98.8,
        'rendement_euro': 98.6,
        'nb_mppt': 24,
        'nb_strings_max': 48,
        'v_dc_min': 500,
        'v_dc_nominal': 1080,
        'v_dc_max': 1500,
        'i_dc_max_par_mppt': 30.0,
        'i_ac_max': 310.0,
        'v_ac_nominal': 800,
        'frequence': '50/60',
        'protection_dc': 'Type I+II SPD intégré + Arc Fault Detection',
        'protection_ac': 'Type I+II SPD intégré + Protection îlotage',
        'dimensions': '2245×1070×730',
        'poids': 450.0,
        'refroidissement': 'Ventilation forcée + Radiateur aluminium',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 35000,
        'disponibilite': 'sur commande (6-8 semaines)',
        'smart_monitoring': True,
        'wifi_integre': False,
        'ethernet': True,
        '4G': True,
        'rs485': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000 (jusqu\'à 20 unités)',
        'monitoring': 'FusionSolar Smart PV Management System',
        'certification': 'CE, VDE-AR-N 4120, IEC 62109, IEC 61727',
        'puissance_reactive': True,
        'q_on_demand': True,
        'cos_phi_reglable': True,
        'grid_support': True,
        'lvrt_hvrt': True,
        'anti_pid': True,
        'made_in': 'Chine'
    },
    'SMA-CENTRAL-250': {
        'fabricant': 'SMA',
        'modele': 'Sunny Central 250-EV',
        'type_reseau': 'Triphasé 800V',
        'p_ac_nominale': 250000,
        'p_dc_max': 375000,
        'rendement_max': 98.8,
        'rendement_euro': 98.6,
        'nb_mppt': 8,
        'nb_strings_max': 64,
        'v_dc_min': 585,
        'v_dc_nominal': 1080,
        'v_dc_max': 1500,
        'i_dc_max_par_mppt': 60.0,
        'i_ac_max': 361.0,
        'v_ac_nominal': 800,
        'frequence': '50/60',
        'protection_dc': 'Type I+II SPD intégré + DC Switch',
        'protection_ac': 'Type I+II SPD intégré + Q-on-demand',
        'dimensions': '2400×1200×800',
        'poids': 580.0,
        'refroidissement': 'Système de refroidissement actif OptiCool',
        'ip': 'IP54 (indoor) / IP65 (outdoor option)',
        'garantie': 10,
        'prix_indicatif': 45000,
        'disponibilite': 'sur commande (8-12 semaines)',
        'ethernet': True,
        'rs485': True,
        'profibus': True,
        'modbus': True,
        'monitoring': 'SMA Power Plant Controller',
        'certification': 'CE, VDE-AR-N 4120, IEC 62109-1/-2, IEEE 1547',
        'puissance_reactive': True,
        'q_on_demand': True,
        'cos_phi_reglable': True,
        'grid_support': True,
        'lvrt_hvrt': True,
        'frequency_support': True,
        'black_start': True,
        'scada_ready': True,
        'made_in': 'Allemagne'
    },
    'SMA-CENTRAL-500': {
        'fabricant': 'SMA',
        'modele': 'Sunny Central 500-EV',
        'type_reseau': 'Triphasé 800V',
        'p_ac_nominale': 500000,
        'p_dc_max': 750000,
        'rendement_max': 98.9,
        'rendement_euro': 98.7,
        'nb_mppt': 12,
        'nb_strings_max': 120,
        'v_dc_min': 585,
        'v_dc_nominal': 1080,
        'v_dc_max': 1500,
        'i_dc_max_par_mppt': 80.0,
        'i_ac_max': 722.0,
        'v_ac_nominal': 800,
        'frequence': '50/60',
        'protection_dc': 'Type I+II SPD intégré + DC Combiner Box',
        'protection_ac': 'Type I+II SPD intégré + Transformateur',
        'dimensions': '3500×1800×1200',
        'poids': 1800.0,
        'refroidissement': 'Système refroidissement liquide + air forcé',
        'ip': 'IP54 (container climatisé recommandé)',
        'garantie': 10,
        'prix_indicatif': 85000,
        'disponibilite': 'sur commande (12-16 semaines)',
        'ethernet': True,
        'rs485': True,
        'profibus': True,
        'modbus': True,
        'scada_integration': 'Full',
        'monitoring': 'SMA Power Plant Controller + SCADA',
        'certification': 'CE, VDE-AR-N 4120, IEC 62109-1/-2, IEEE 1547',
        'puissance_reactive': True,
        'q_on_demand': True,
        'cos_phi_reglable': True,
        'grid_support': True,
        'lvrt_hvrt': True,
        'frequency_support': True,
        'black_start': True,
        'scada_ready': True,
        'transformer_option': True,
        'mv_connection': '20kV option',
        'made_in': 'Allemagne'
    },
    'HUAWEI-300KTL-H3': {
        'fabricant': 'Huawei',
        'modele': 'SUN2000-300KTL-H3',
        'type_reseau': 'Triphasé 800V',
        'p_ac_nominale': 300000,
        'p_dc_max': 450000,
        'rendement_max': 98.9,
        'rendement_euro': 98.7,
        'nb_mppt': 30,
        'nb_strings_max': 60,
        'v_dc_min': 500,
        'v_dc_nominal': 1080,
        'v_dc_max': 1500,
        'i_dc_max_par_mppt': 30.0,
        'i_ac_max': 433.0,
        'v_ac_nominal': 800,
        'frequence': '50/60',
        'protection_dc': 'Type I+II SPD intégré + Arc Fault Detection',
        'protection_ac': 'Type I+II SPD intégré + Grid support',
        'dimensions': '2800×1200×850',
        'poids': 720.0,
        'refroidissement': 'Ventilation forcée intelligente + Radiateur',
        'ip': 'IP66',
        'garantie': 10,
        'prix_indicatif': 55000,
        'disponibilite': 'sur commande (8-12 semaines)',
        'smart_monitoring': True,
        'ethernet': True,
        '4G': True,
        'rs485': True,
        'compatible_batterie': True,
        'batterie_modele': 'LUNA2000 (jusqu\'à 30 unités)',
        'monitoring': 'FusionSolar Smart PV Management System',
        'certification': 'CE, VDE-AR-N 4120, IEC 62109, UL 1741',
        'puissance_reactive': True,
        'q_on_demand': True,
        'cos_phi_reglable': True,
        'grid_support': True,
        'lvrt_hvrt': True,
        'anti_pid': True,
        'scada_ready': True,
        'made_in': 'Chine'
    }
}

def get_module_par_puissance(puissance_min=400, puissance_max=600):
    """Filtre les modules par plage de puissance"""
    return {
        ref: data for ref, data in MODULES_PV_DATABASE.items()
        if puissance_min <= data['puissance'] <= puissance_max
    }

def get_onduleur_par_puissance(p_ac_min=0, p_ac_max=999999, type_reseau=None):
    """Filtre les onduleurs par puissance AC et type de réseau"""
    onduleurs = {
        ref: data for ref, data in ONDULEURS_DATABASE.items()
        if p_ac_min <= data['p_ac_nominale'] <= p_ac_max
    }
    
    if type_reseau:
        onduleurs = {
            ref: data for ref, data in onduleurs.items()
            if data['type_reseau'] == type_reseau
        }
    
    return onduleurs

def get_onduleur_optimal(puissance_dc_kwc, preference='rendement'):
    """
    Sélectionne l'onduleur optimal selon la puissance DC de l'installation
    
    Args:
        puissance_dc_kwc: Puissance DC totale en kWc (ex: 29.7)
        preference: 'rendement', 'prix', 'garantie'
    
    Returns:
        tuple (ref, data) ou None si aucun onduleur compatible
    """
    p_dc_totale = puissance_dc_kwc * 1000  # Conversion en W
    
    # Ratio DC/AC entre 1.0 et 1.5 (plage large pour couvrir toutes configurations)
    # Ratio optimal: 1.15-1.3, mais on accepte plus large pour compatibilité
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
    
    if not onduleurs_compatibles:
        return None
    
    # Trier selon préférence
    if preference == 'rendement':
        meilleur = max(onduleurs_compatibles, key=lambda x: x['score'])
    elif preference == 'prix':
        meilleur = min(onduleurs_compatibles, key=lambda x: x['data']['prix_indicatif'])
    elif preference == 'garantie':
        meilleur = max(onduleurs_compatibles, key=lambda x: x['data']['garantie'])
    else:
        meilleur = min(onduleurs_compatibles, key=lambda x: abs(x['ratio'] - 1.25))
    
    # Retourner tuple (ref, data) pour compatibilité avec .items()
    return (meilleur['ref'], meilleur['data'])
