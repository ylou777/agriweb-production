"""
Bases de données techniques - Modules PV et Onduleurs
AgriWeb 2025 - Catalogue professionnel
"""

# ============================================================================
# BASE DE DONNÉES MODULES PHOTOVOLTAÏQUES
# ============================================================================

MODULES_PV_DATABASE = {
    # =========================================================================
    # CANADIAN SOLAR (Leader mondial, rapport qualité/prix)
    # =========================================================================
    'CS-550W': {
        'fabricant': 'Canadian Solar',
        'modele': 'HiKu6 CS6W-550MS',
        'puissance': 550,
        'voc': 49.5, 'vmpp': 41.8, 'isc': 13.9, 'impp': 13.2,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 35,
        'poids': 27.5, 'rendement': 21.2,
        'technologie': 'Monocristallin PERC',
        'tech_cellule': 'P-PERC', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 180, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34, 'coeff_temp_voc': -0.27, 'coeff_temp_isc': 0.048,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },
    'CS-450W': {
        'fabricant': 'Canadian Solar',
        'modele': 'HiKu CS3W-450MS',
        'puissance': 450,
        'voc': 49.1, 'vmpp': 41.2, 'isc': 11.53, 'impp': 10.93,
        'longueur': 2108, 'largeur': 1048, 'epaisseur': 35,
        'poids': 24.0, 'rendement': 20.4,
        'technologie': 'Monocristallin PERC',
        'tech_cellule': 'P-PERC', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 150, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.35, 'coeff_temp_voc': -0.27, 'coeff_temp_isc': 0.048,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },
    'CS-580W-BIFACIAL': {
        'fabricant': 'Canadian Solar',
        'modele': 'BiHiKu7 CS7N-580TB-AG',
        'puissance': 580,
        'voc': 51.80, 'vmpp': 43.60, 'isc': 14.20, 'impp': 13.30,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 35,
        'poids': 31.5, 'rendement': 22.4,
        'technologie': 'Monocristallin N-type Bifacial',
        'tech_cellule': 'N-TOPCon', 'biverre': True,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 220, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'bifacial': True, 'bifaciality': 70,
        'coeff_temp_pmax': -0.30, 'coeff_temp_voc': -0.25, 'coeff_temp_isc': 0.045,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },

    # =========================================================================
    # JINKO SOLAR (Top 3 mondial)
    # =========================================================================
    'JKM-575W': {
        'fabricant': 'Jinko Solar',
        'modele': 'Tiger Neo JKM575N-72HL4-BDV',
        'puissance': 575,
        'voc': 51.45, 'vmpp': 43.30, 'isc': 14.10, 'impp': 13.28,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 30,
        'poids': 28.6, 'rendement': 22.2,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': True,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 200, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°029-2024_002', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-12',
    },
    'JKM-590N-72HL4-BDV': {
        'fabricant': 'Jinko Solar',
        'modele': 'Tiger Neo JKM590N-72HL4-BDV',
        'puissance': 590,
        'voc': 52.20, 'vmpp': 44.10, 'isc': 14.50, 'impp': 13.38,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 30,
        'poids': 29.6, 'rendement': 22.8,
        'technologie': 'Monocristallin N-type TOPCon Bifacial',
        'tech_cellule': 'N-TOPCon', 'biverre': True,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 205, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°029-2024_002', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-12',
    },
    'JKM-455N-54HL4R': {
        'fabricant': 'Jinko Solar',
        'modele': 'Tiger Neo JKM455N-54HL4R-B',
        'puissance': 455,
        'voc': 49.65, 'vmpp': 41.80, 'isc': 11.88, 'impp': 10.89,
        'longueur': 1762, 'largeur': 1134, 'epaisseur': 30,
        'poids': 21.7, 'rendement': 21.6,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 160, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°029-2024_004', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-12',
    },
    'JKM-460W': {
        'fabricant': 'Jinko Solar',
        'modele': 'Tiger Pro JKM460M-60HL4-V',
        'puissance': 460,
        'voc': 49.75, 'vmpp': 41.85, 'isc': 11.65, 'impp': 10.99,
        'longueur': 1903, 'largeur': 1134, 'epaisseur': 30,
        'poids': 24.5, 'rendement': 21.3,
        'technologie': 'Monocristallin PERC',
        'tech_cellule': 'P-PERC', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 155, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34, 'coeff_temp_voc': -0.26, 'coeff_temp_isc': 0.048,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },

    # =========================================================================
    # JA SOLAR (DeepBlue 4.0 Pro N-TOPCon)
    # =========================================================================
    'JAM72S30': {
        'fabricant': 'JA Solar',
        'modele': 'JAM72S30 560W',
        'puissance': 560,
        'voc': 49.85, 'vmpp': 42.05, 'isc': 14.10, 'impp': 13.32,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 35,
        'poids': 28.0, 'rendement': 21.6,
        'technologie': 'Monocristallin PERC Half-cell',
        'tech_cellule': 'P-PERC', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 185, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.35, 'coeff_temp_voc': -0.27, 'coeff_temp_isc': 0.050,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },
    'JAM66D45-635': {
        'fabricant': 'JA Solar',
        'modele': 'DeepBlue 4.0 Pro JAM66D45/LB 635W',
        'puissance': 635,
        'voc': 47.60, 'vmpp': 39.88, 'isc': 17.49, 'impp': 15.93,
        'longueur': 2465, 'largeur': 1134, 'epaisseur': 35,
        'poids': 34.8, 'rendement': 22.7,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 215, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°022-2025_002', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-04',
    },
    'JAM54D40-455': {
        'fabricant': 'JA Solar',
        'modele': 'DeepBlue 4.0 Pro JAM54D40/LB 455W',
        'puissance': 455,
        'voc': 40.35, 'vmpp': 33.95, 'isc': 14.78, 'impp': 13.40,
        'longueur': 1762, 'largeur': 1134, 'epaisseur': 30,
        'poids': 22.5, 'rendement': 22.8,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 165, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°022-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-04',
    },

    # =========================================================================
    # LONGI SOLAR (Back Contact Hi-MO 7)
    # =========================================================================
    'LR5-72HBD': {
        'fabricant': 'LONGi Solar',
        'modele': 'Hi-MO 5 LR5-72HBD-565M',
        'puissance': 565,
        'voc': 49.95, 'vmpp': 42.10, 'isc': 14.26, 'impp': 13.42,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 35,
        'poids': 28.3, 'rendement': 21.8,
        'technologie': 'Monocristallin PERC',
        'tech_cellule': 'P-PERC', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 195, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34, 'coeff_temp_voc': -0.26, 'coeff_temp_isc': 0.048,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },
    'LR7-72HVD-645BC': {
        'fabricant': 'LONGi Solar',
        'modele': 'Hi-MO 7 LR7-72HVD-645M (Back Contact)',
        'puissance': 645,
        'voc': 51.85, 'vmpp': 44.40, 'isc': 14.98, 'impp': 14.53,
        'longueur': 2382, 'largeur': 1134, 'epaisseur': 35,
        'poids': 32.5, 'rendement': 23.8,
        'technologie': 'Monocristallin Back Contact N-type',
        'tech_cellule': 'Back Contact', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 230, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.040,
        'certisolis_cert': 'PPE2_V2 N°026-2025_003', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-12',
    },
    'LR7-54HVH-480BC': {
        'fabricant': 'LONGi Solar',
        'modele': 'Hi-MO X LR7-54HVH-480M (Back Contact)',
        'puissance': 480,
        'voc': 40.20, 'vmpp': 33.90, 'isc': 14.91, 'impp': 14.16,
        'longueur': 1722, 'largeur': 1134, 'epaisseur': 30,
        'poids': 23.0, 'rendement': 23.0,
        'technologie': 'Monocristallin Back Contact N-type',
        'tech_cellule': 'Back Contact', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 175, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.040,
        'certisolis_cert': 'PPE2_V2 N°026-2025_003', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-12',
    },
    'LR8-66HYD-640BC': {
        'fabricant': 'LONGi Solar',
        'modele': 'Hi-MO LR8-66HYD-640M (Back Contact Bifacial)',
        'puissance': 640,
        'voc': 51.23, 'vmpp': 43.65, 'isc': 15.18, 'impp': 14.66,
        'longueur': 2384, 'largeur': 1096, 'epaisseur': 35,
        'poids': 34.0, 'rendement': 24.5,
        'technologie': 'Monocristallin Back Contact N-type Bifacial',
        'tech_cellule': 'Back Contact', 'biverre': True,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 250, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'bifacial': True, 'bifaciality': 75,
        'coeff_temp_pmax': -0.24, 'coeff_temp_voc': -0.22, 'coeff_temp_isc': 0.040,
        'certisolis_cert': 'PPE2_V2 N°026-2025_005', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-12',
    },

    # =========================================================================
    # TRINA SOLAR (Vertex S+ N-TOPCon)
    # =========================================================================
    'TSM-DEG21C': {
        'fabricant': 'Trina Solar',
        'modele': 'Vertex S TSM-DEG21C.20 550W',
        'puissance': 550,
        'voc': 49.60, 'vmpp': 41.90, 'isc': 13.95, 'impp': 13.13,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 30,
        'poids': 27.8, 'rendement': 21.2,
        'technologie': 'Monocristallin PERC',
        'tech_cellule': 'P-PERC', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 178, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.34, 'coeff_temp_voc': -0.26, 'coeff_temp_isc': 0.048,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },
    'TSM-NEG9R-450': {
        'fabricant': 'Trina Solar',
        'modele': 'Vertex S+ TSM-NEG9R.28 450W',
        'puissance': 450,
        'voc': 37.73, 'vmpp': 31.64, 'isc': 15.30, 'impp': 14.22,
        'longueur': 1762, 'largeur': 1134, 'epaisseur': 30,
        'poids': 21.5, 'rendement': 22.6,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 165, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°006-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-03',
    },
    'TSM-NEG18R-505': {
        'fabricant': 'Trina Solar',
        'modele': 'Vertex S+ TSM-NEG18R.28 505W',
        'puissance': 505,
        'voc': 42.04, 'vmpp': 35.30, 'isc': 15.38, 'impp': 14.31,
        'longueur': 1903, 'largeur': 1134, 'epaisseur': 30,
        'poids': 24.0, 'rendement': 23.4,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 185, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°006-2025_002', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-03',
    },

    # =========================================================================
    # RISEN ENERGY (Titan Pro N-TOPCon)
    # =========================================================================
    'RSM108-11-510': {
        'fabricant': 'Risen Energy',
        'modele': 'Titan Pro RSM108-11-510BNDG',
        'puissance': 510,
        'voc': 42.35, 'vmpp': 35.55, 'isc': 15.28, 'impp': 14.35,
        'longueur': 1903, 'largeur': 1134, 'epaisseur': 30,
        'poids': 24.5, 'rendement': 23.6,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 180, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.30, 'coeff_temp_voc': -0.25, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°035-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-06',
    },
    'RSM96-11-450': {
        'fabricant': 'Risen Energy',
        'modele': 'Risen Evolution RSM96-11-450BNDG',
        'puissance': 450,
        'voc': 37.40, 'vmpp': 31.50, 'isc': 15.25, 'impp': 14.26,
        'longueur': 1722, 'largeur': 1134, 'epaisseur': 30,
        'poids': 21.5, 'rendement': 23.0,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 162, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.30, 'coeff_temp_voc': -0.25, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°035-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-06',
    },

    # =========================================================================
    # AIKO SOLAR (Neon N+ ABC — meilleur rendement marché)
    # =========================================================================
    'AIKO-A460-MAH54M': {
        'fabricant': 'AIKO Solar',
        'modele': 'Neon N+ AIKO-A460-MAH54Mw',
        'puissance': 460,
        'voc': 37.80, 'vmpp': 31.82, 'isc': 15.21, 'impp': 14.46,
        'longueur': 1722, 'largeur': 1134, 'epaisseur': 30,
        'poids': 22.0, 'rendement': 23.6,
        'technologie': 'Monocristallin N-type ABC (Back Contact)',
        'tech_cellule': 'N-ABC', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 195, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.27, 'coeff_temp_voc': -0.23, 'coeff_temp_isc': 0.040,
        'certisolis_cert': 'PPE2_V2 N°069-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-10',
    },
    'AIKO-A480-MAH54D': {
        'fabricant': 'AIKO Solar',
        'modele': 'Neon N+ AIKO-A480-MAH54Dw (Bifacial)',
        'puissance': 480,
        'voc': 38.90, 'vmpp': 32.72, 'isc': 15.47, 'impp': 14.67,
        'longueur': 1722, 'largeur': 1134, 'epaisseur': 30,
        'poids': 24.5, 'rendement': 24.6,
        'technologie': 'Monocristallin N-type ABC Bifacial',
        'tech_cellule': 'N-ABC', 'biverre': True,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 210, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'bifacial': True, 'bifaciality': 80,
        'coeff_temp_pmax': -0.27, 'coeff_temp_voc': -0.23, 'coeff_temp_isc': 0.040,
        'certisolis_cert': 'PPE2_V2 N°069-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-10',
    },

    # =========================================================================
    # VOLTEC SOLAR (Fabrication française — meilleur score carbone AO)
    # =========================================================================
    'VOLTEC-430': {
        'fabricant': 'Voltec Solar',
        'modele': 'VS-430-M6-PERC (ancienne génération)',
        'puissance': 430,
        'voc': 49.20, 'vmpp': 41.50, 'isc': 10.98, 'impp': 10.36,
        'longueur': 1755, 'largeur': 1038, 'epaisseur': 35,
        'poids': 22.0, 'rendement': 23.5,
        'technologie': 'Monocristallin PERC',
        'tech_cellule': 'P-PERC', 'biverre': False,
        'pays_module': 'France', 'pays_cellule': 'Asie', 'pays_wafer': 'Asie',
        'garantie_produit': 20, 'garantie_performance': 30,
        'prix_indicatif': 280, 'disponibilite': 'stock France', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.35, 'coeff_temp_voc': -0.28, 'coeff_temp_isc': 0.050,
        'made_in_france': True,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },
    'VOLTEC-TARKA110-450': {
        'fabricant': 'Voltec Solar',
        'modele': 'TARKA 110 VSMP 450W (Made in France)',
        'puissance': 450,
        'voc': 38.05, 'vmpp': 32.00, 'isc': 14.72, 'impp': 14.06,
        'longueur': 1722, 'largeur': 1038, 'epaisseur': 30,
        'poids': 21.5, 'rendement': 25.2,
        'technologie': 'Monocristallin N-type TOPCon (Assemblage France)',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'France', 'pays_cellule': 'Asie', 'pays_wafer': 'Asie',
        'garantie_produit': 20, 'garantie_performance': 30,
        'prix_indicatif': 310, 'disponibilite': 'stock France', 'classe_feu': 'Classe C',
        'made_in_france': True,
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°005-2025_007', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 530, 'certisolis_expiry': '2026-10',
    },
    'VOLTEC-TARKA120-490': {
        'fabricant': 'Voltec Solar',
        'modele': 'TARKA 120 VSMP 490W (Made in France)',
        'puissance': 490,
        'voc': 41.07, 'vmpp': 34.54, 'isc': 14.89, 'impp': 14.19,
        'longueur': 1903, 'largeur': 1038, 'epaisseur': 30,
        'poids': 23.5, 'rendement': 24.8,
        'technologie': 'Monocristallin N-type TOPCon (Assemblage France)',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'France', 'pays_cellule': 'Asie', 'pays_wafer': 'Asie',
        'garantie_produit': 20, 'garantie_performance': 30,
        'prix_indicatif': 330, 'disponibilite': 'stock France', 'classe_feu': 'Classe C',
        'made_in_france': True,
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°005-2025_007', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 530, 'certisolis_expiry': '2026-10',
    },

    # =========================================================================
    # TONGWEI (N-TOPCon, bon rapport qualité/prix)
    # =========================================================================
    'TWMNH-54HD-505': {
        'fabricant': 'Tongwei Solar',
        'modele': 'TWMNH-54HD 505W',
        'puissance': 505,
        'voc': 41.95, 'vmpp': 35.24, 'isc': 15.32, 'impp': 14.33,
        'longueur': 1903, 'largeur': 1134, 'epaisseur': 30,
        'poids': 24.3, 'rendement': 23.4,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 172, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.30, 'coeff_temp_voc': -0.25, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°036-2024_003', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-07',
    },
    'TWMNH-66HD-620': {
        'fabricant': 'Tongwei Solar',
        'modele': 'TWMNH-66HD 620W',
        'puissance': 620,
        'voc': 51.70, 'vmpp': 43.45, 'isc': 15.42, 'impp': 14.27,
        'longueur': 2384, 'largeur': 1096, 'epaisseur': 30,
        'poids': 32.8, 'rendement': 23.7,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 200, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.30, 'coeff_temp_voc': -0.25, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°036-2024_003', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-07',
    },

    # =========================================================================
    # QCELLS (Hanwha, qualité premium)
    # =========================================================================
    'QCELLS-QTRON-445': {
        'fabricant': 'Qcells (Hanwha)',
        'modele': 'Q.TRON S-G3R.12+ 445W',
        'puissance': 445,
        'voc': 37.38, 'vmpp': 31.45, 'isc': 15.13, 'impp': 14.15,
        'longueur': 1722, 'largeur': 1134, 'epaisseur': 30,
        'poids': 21.8, 'rendement': 22.8,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Corée/Malaisie', 'pays_cellule': 'Corée', 'pays_wafer': 'Asie',
        'garantie_produit': 15, 'garantie_performance': 25,
        'prix_indicatif': 185, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°009-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-07',
    },

    # =========================================================================
    # GCL SOLAR (N-TOPCon, compétitif)
    # =========================================================================
    'GCL-NT12R-520': {
        'fabricant': 'GCL Solar',
        'modele': 'NT12R/54GDF 520W',
        'puissance': 520,
        'voc': 43.25, 'vmpp': 36.35, 'isc': 15.36, 'impp': 14.31,
        'longueur': 1903, 'largeur': 1134, 'epaisseur': 30,
        'poids': 24.8, 'rendement': 24.1,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 12, 'garantie_performance': 25,
        'prix_indicatif': 168, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.30, 'coeff_temp_voc': -0.25, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°025-2024_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-06',
    },

    # =========================================================================
    # JOLYWOOD (N-TOPCon bifacial, spécialiste cellules)
    # =========================================================================
    'JW-HD96N-460': {
        'fabricant': 'Jolywood',
        'modele': 'JW-HD96N-R2-460 (Bifacial)',
        'puissance': 460,
        'voc': 38.54, 'vmpp': 32.44, 'isc': 15.12, 'impp': 14.18,
        'longueur': 1722, 'largeur': 1134, 'epaisseur': 30,
        'poids': 22.5, 'rendement': 23.6,
        'technologie': 'Monocristallin N-type TOPCon Bifacial',
        'tech_cellule': 'N-TOPCon', 'biverre': True,
        'pays_module': 'Chine', 'pays_cellule': 'Chine', 'pays_wafer': 'Chine',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 178, 'disponibilite': 'stock', 'classe_feu': 'Classe C',
        'bifacial': True, 'bifaciality': 75,
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.040,
        'certisolis_cert': 'PPE2_V2 N°032-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 630, 'certisolis_expiry': '2026-06',
    },

    # =========================================================================
    # 3SUN / ENEL (HJT — Fabrication Italie, point Europe)
    # =========================================================================
    '3SUN-HJT-565': {
        'fabricant': '3SUN (Enel)',
        'modele': '3SHBGH-AA 565W HJT',
        'puissance': 565,
        'voc': 48.77, 'vmpp': 41.12, 'isc': 14.38, 'impp': 13.74,
        'longueur': 2278, 'largeur': 1134, 'epaisseur': 30,
        'poids': 28.5, 'rendement': 21.9,
        'technologie': 'Monocristallin N-type HJT (Hétérojonction)',
        'tech_cellule': 'HJT', 'biverre': False,
        'pays_module': 'Italie', 'pays_cellule': 'Italie', 'pays_wafer': 'Asie',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 260, 'disponibilite': 'sur commande', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.24, 'coeff_temp_voc': -0.21, 'coeff_temp_isc': 0.040,
        'certisolis_cert': 'PPE2_V2 N°092-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-04',
    },

    # =========================================================================
    # SUNPOWER / MAXEON (IBC premium)
    # =========================================================================
    'SUNPOWER-400': {
        'fabricant': 'SunPower (Maxeon)',
        'modele': 'Maxeon 3 SPR-MAX3-400',
        'puissance': 400,
        'voc': 67.8, 'vmpp': 57.3, 'isc': 7.12, 'impp': 6.98,
        'longueur': 1690, 'largeur': 1046, 'epaisseur': 40,
        'poids': 19.0, 'rendement': 22.6,
        'technologie': 'Monocristallin IBC (Interdigitated Back Contact)',
        'tech_cellule': 'IBC', 'biverre': False,
        'pays_module': 'Malaisie', 'pays_cellule': 'Philippines', 'pays_wafer': 'Asie',
        'garantie_produit': 25, 'garantie_performance': 40,
        'prix_indicatif': 350, 'disponibilite': 'sur commande', 'classe_feu': 'Classe A',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.27, 'coeff_temp_isc': 0.035,
        'certisolis_cert': None, 'certisolis_methode': None,
        'certisolis_ecs_seuil': None, 'certisolis_expiry': None,
    },
    'SUNPOWER-HSM-ND-450': {
        'fabricant': 'SunPower / Maxeon',
        'modele': 'HSM-ND48-DR 450W N-TopCon',
        'puissance': 450,
        'voc': 37.65, 'vmpp': 31.62, 'isc': 15.23, 'impp': 14.23,
        'longueur': 1722, 'largeur': 1134, 'epaisseur': 30,
        'poids': 22.0, 'rendement': 23.0,
        'technologie': 'Monocristallin N-type TOPCon',
        'tech_cellule': 'N-TOPCon', 'biverre': False,
        'pays_module': 'Malaisie', 'pays_cellule': 'Asie', 'pays_wafer': 'Asie',
        'garantie_produit': 15, 'garantie_performance': 30,
        'prix_indicatif': 220, 'disponibilite': 'sur commande', 'classe_feu': 'Classe C',
        'coeff_temp_pmax': -0.29, 'coeff_temp_voc': -0.24, 'coeff_temp_isc': 0.045,
        'certisolis_cert': 'PPE2_V2 N°002-2025_001', 'certisolis_methode': 'PPE2-V2',
        'certisolis_ecs_seuil': 740, 'certisolis_expiry': '2026-06',
    },
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

def get_modules_certisolis_eligibles(seuil_max=740, methode='PPE2-V2'):
    """
    Retourne les modules ayant un certificat Certisolis valide.

    Args:
        seuil_max: Seuil ECS maximum (530, 630 ou 740 kg CO2/kWc).
                   Ex: 530 → uniquement les modules <530 kg CO2/kWc.
        methode: Méthode Certisolis ciblée ('PPE2-V2' ou 'PPE2').

    Returns:
        dict {ref: data} des modules certifiés répondant au seuil.
    """
    eligible = {}
    for ref, data in MODULES_PV_DATABASE.items():
        cert = data.get('certisolis_cert')
        m = data.get('certisolis_methode')
        seuil = data.get('certisolis_ecs_seuil')
        if cert and m == methode and seuil is not None and seuil <= seuil_max:
            eligible[ref] = data
    return eligible

def get_modules_par_tech(tech_cellule):
    """
    Filtre les modules par technologie de cellule.

    Args:
        tech_cellule: 'N-TOPCon', 'P-PERC', 'HJT', 'IBC', 'N-ABC', 'Back Contact'

    Returns:
        dict {ref: data}
    """
    return {
        ref: data for ref, data in MODULES_PV_DATABASE.items()
        if data.get('tech_cellule', '').upper() == tech_cellule.upper()
    }

def get_modules_pays_fabrication(pays='France'):
    """
    Filtre les modules assemblés dans un pays donné (pour score carbone AO).

    Args:
        pays: 'France', 'Italie', 'Europe', 'Chine', etc.

    Returns:
        dict {ref: data}
    """
    return {
        ref: data for ref, data in MODULES_PV_DATABASE.items()
        if pays.lower() in data.get('pays_module', '').lower()
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
