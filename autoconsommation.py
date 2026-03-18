"""
Module Autoconsommation - HeliaPV AgriWeb
=========================================
Calcul et analyse de l'autoconsommation solaire à partir des données PVGIS 8760h
et des profils de consommation types Enedis (RES1, RES2, PRO1, PRO2, AGR, ENT).

Références :
  - PVGIS EU Science Hub (données 8760h)
  - Enedis Open Data : courbes de charge fictives résidentielles/professionnelles
  - https://openservices.enedis.fr/service/simulateur-courbes-de-charge/
  - Tarifs TRV EDF au 01/02/2025 : CRE / arrêtés tarifaires
  - TEMPO : arrêté du 28 juillet 2023, prix actualisés 01/08/2024
"""

from datetime import datetime, timedelta
import math


# ──────────────────────────────────────────────────────────────────────────────
# STRUCTURES TARIFAIRES  (TRV EDF au 01/02/2025, puissance 6 kVA référence)
# ──────────────────────────────────────────────────────────────────────────────

TARIFF_STRUCTURES = {
    # ── Tarif de Base ──────────────────────────────────────────────────────────
    'BASE': {
        'label'          : 'Tarif Base – Prix unique',
        'description'    : 'Un seul prix kWh toute la journée, toute l\'année (TRV Bleu EDF)',
        'abonnement_6kva': 103.56,   # €/an (abonnement 6 kVA hors taxes)
        'prix_kwh'       : 0.2516,   # €/kWh TTC (TRV au 01/02/2025)
    },

    # ── HP / HC : Heures Pleines / Heures Creuses ──────────────────────────────
    'HPHC': {
        'label'          : 'Heures Pleines / Heures Creuses',
        'description'    : 'HC la nuit (22h-6h), HP le reste de la journée',
        'abonnement_6kva': 130.08,   # €/an (option HC, abonnement un peu plus cher)
        'hp_kwh'         : 0.2700,   # €/kWh TTC HP
        'hc_kwh'         : 0.2068,   # €/kWh TTC HC
        # Plages HC par défaut (h_debut inclus, h_fin exclu) – 8h/jour
        # Possibilité de personnaliser : 'hc_plages': [(22, 6)] ou [(0, 8)] ou [(12.5, 14.5), (22.5, 6.5)]
        'hc_plages'      : [(22, 6)],  # nuit 22h → 6h
    },

    # ── HPHC avec créneau midi ─────────────────────────────────────────────────
    'HPHC_MIDI': {
        'label'          : 'HP/HC avec créneau midi',
        'description'    : 'HC nuit (23h-7h) + créneau midi (12h-14h) → 10h HC',
        'abonnement_6kva': 130.08,
        'hp_kwh'         : 0.2700,
        'hc_kwh'         : 0.2068,
        'hc_plages'      : [(23, 7), (12, 14)],  # nuit 23h→7h + midi 12h→14h
    },

    # ── Tarif TEMPO  ──────────────────────────────────────────────────────────
    'TEMPO': {
        'label'          : 'Tarif Tempo (EDF)',
        'description'    : '3 couleurs de jours : Bleu (300j/an), Blanc (43j/an), Rouge (22j/an). HC = 22h-6h.',
        'abonnement_6kva': 235.20,   # €/an
        # Prix par couleur (TTC, 01/08/2024)
        'bleu_hc_kwh'    : 0.1369,
        'bleu_hp_kwh'    : 0.1609,
        'blanc_hc_kwh'   : 0.1654,
        'blanc_hp_kwh'   : 0.2118,
        'rouge_hc_kwh'   : 0.1654,
        'rouge_hp_kwh'   : 0.7562,   # ← tarif pointe rouge HP très élevé
        # HC = 22h-6h comme HPHC
        'hc_plages'      : [(22, 6)],
        # Distribution annuelle (jours confirmés par EDF)
        'nb_jours_bleu'  : 300,
        'nb_jours_blanc' : 43,
        'nb_jours_rouge' : 22,
    },

    # ── EJP : Effacement Jours de Pointe  ─────────────────────────────────────
    'EJP': {
        'label'          : 'EJP – Effacement Jours de Pointe',
        'description'    : '22 jours de pointe/an (annoncés veille), tarif très élevé 7h-23h. 343j normaux.',
        'abonnement_6kva': 127.20,   # €/an (abonnement EJP)
        'hn_kwh'         : 0.1613,   # €/kWh HN (Heure Normale – 343 jours)
        'hp_kwh'         : 0.6797,   # €/kWh HP (Heure de Pointe – 22 jours, 7h-23h)
        'nb_jours_pointe': 22,
        # Plages horaires de pointe (sur les jours EJP uniquement)
        'heures_pointe'  : (7, 23),
    },

    # ── C4 : BT Professionnel 36-250 kVA – Horosaisonnier 4 périodes ──────────
    # Anciennement "Tarif Jaune" (supprimé 31/12/2021), remplacé par offres marché.
    # Structure horosaisonnière : Hiver=Nov-Mar / Été=Avr-Oct, HP=7h-23h, HC=23h-7h.
    # Prix estimés 2024 (offres marché avec TURPE C4 + CSPE + TVA).
    'C4_HORO': {
        'label'          : 'C4 Pro BT 36-250 kVA – Horosaisonnier',
        'description'    : ('Ex-Tarif Jaune (supprimé 2021). 4 périodes : HPH/HCH (Hiver: nov-mar) '
                            'et HPE/HCE (Été: avr-oct). HP=7h-23h, HC=23h-7h + WE.'),
        'abonnement_an'  : 800.0,    # €/an indicatif (varie selon puissance souscrite)
        # Hiver (Nov–Mar) ─ HP jours ouvrés / HC nuits + week-ends
        'hph_kwh'        : 0.2150,   # €/kWh HPH (Heures Pleines Hiver)
        'hch_kwh'        : 0.1450,   # €/kWh HCH (Heures Creuses Hiver)
        # Été (Avr–Oct) ─ HP jours ouvrés / HC nuits + week-ends
        'hpe_kwh'        : 0.1750,   # €/kWh HPE (Heures Pleines Été)
        'hce_kwh'        : 0.1250,   # €/kWh HCE (Heures Creuses Été)
        # Définition des périodes
        'hiver_mois'     : {10, 0, 1, 2, 11},   # indices mois (0=jan) → nov+déc+jan+fév+mar
        'hp_debut'       : 7,    # 7h
        'hp_fin'         : 23,   # 23h
    },

    # ── HTA : Industriel > 250 kVA – Horosaisonnier 5 périodes (TURPE 6 HTA) ─
    # Haute Tension A (1 kV < U ≤ 50 kV), mesure quotidienne (compteur communicant).
    # 5 périodes : Pointe(P) / HPH / HCH / HPE / HCE.
    # Prix indicatifs tout compris 2024 (TURPE 6 + offre marché + taxes).
    'HTA_HORO': {
        'label'          : 'HTA Industriel >250 kVA – 5 périodes TURPE',
        'description'    : ('Tarif Haute Tension A (TURPE 6 HTA). 5 périodes. '
                            'Pointe (P) : jours ouvrés hiver 9h-11h + 17h-19h (très cher). '
                            'HPH/HCH : reste hiver. HPE/HCE : été (avr-oct).'),
        'abonnement_an'  : 2500.0,   # €/an indicatif (varie beaucoup selon puissance)
        # Pointe : jours ouvrés, hiver (nov-mar), créneaux 9h-11h ET 17h-19h
        'p_kwh'          : 0.4500,   # €/kWh P (Pointe) – très élevé en hiver matin/soir
        # Hiver HP/HC hors pointe
        'hph_kwh'        : 0.2000,   # €/kWh HPH (Heures Pleines Hiver)
        'hch_kwh'        : 0.1350,   # €/kWh HCH (Heures Creuses Hiver)
        # Été HP/HC
        'hpe_kwh'        : 0.1650,   # €/kWh HPE (Heures Pleines Été)
        'hce_kwh'        : 0.1100,   # €/kWh HCE (Heures Creuses Été)
        # Définition des périodes
        'hiver_mois'     : {10, 0, 1, 2, 11},   # indices mois : nov(10)+déc(11)+jan(0)+fév(1)+mar(2)
        'hp_debut'       : 7,    # 7h
        'hp_fin'         : 23,   # 23h
        # Créneaux Pointe uniquement (jours ouvrés hiver)
        'pointe_plages'  : [(9, 11), (17, 19)],  # 9h-11h et 17h-19h
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# TARIFS S21 – Arrêté du 6 oct. 2021, mod. 26 mars 2025
# Tarification du surplus injecté (autoconsommation avec injection du surplus)
# Tranche 1 : P_totale ≤ 9 kWc  →  4,00 c€/kWh
# Tranche 2 : 9 < P_totale ≤ 100 kWc  →  5,36 c€/kWh
# (P = puissance crête modules + Q = puissance onduleur, ici approximé sur P seule)
# Mise à jour trimestrielle – ces valeurs sont valides pour T1 2026
# ──────────────────────────────────────────────────────────────────────────────

TARIFS_S21_SURPLUS = [
    (9.0,   0.0400),   # ≤ 9 kWc  → 4,00 c€/kWh
    (100.0, 0.0536),   # ≤ 100 kWc → 5,36 c€/kWh
]


def get_tarif_revente_s21(puissance_kwc: float) -> float:
    """
    Retourne le tarif d'achat du surplus S21 (€/kWh) selon la puissance totale.
    Source : Arrêté S21 modifié le 26/03/2025, valeurs T1 2026.
    """
    for seuil, tarif in TARIFS_S21_SURPLUS:
        if puissance_kwc <= seuil:
            return tarif
    # Au-delà de 100 kWc : pas d'obligation d'achat standard – on renvoie le
    # tarif 9-100 kWc comme approximation conservative.
    return TARIFS_S21_SURPLUS[-1][1]


# ──────────────────────────────────────────────────────────────────────────────
# GÉNÉRATION DU PLANNING TEMPO : attribution des couleurs aux 365 jours
# ──────────────────────────────────────────────────────────────────────────────

def _generate_tempo_colors() -> list:
    """
    Génère le planning TEMPO pour une année (8760h = 365j depuis le 01/01/2020).
    Retourne une liste de 365 strings : 'bleu' | 'blanc' | 'rouge'.

    Règles:
    - Pas de jours non-bleus en mai, juin, juillet, août, septembre.
    - Seuls les jours ouvrables (lundi-vendredi) peuvent être blanc/rouge.
    - 22 jours rouges répartis sur les semaines les plus froides (déc, jan, fév).
    - 43 jours blancs sur les semaines froides/intermédiaires (nov, déc, jan, fév, mar).
    - Référence 2020 : 1er janvier = mercredi.
    """
    # Nombre de jours par mois (année non-bissextile, PVGIS utilise 8760h)
    MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    # Score de froid par mois (0=jan, 11=déc) – plus grand = plus froid
    COLD_SCORE  = {0: 10, 1: 9, 11: 8, 2: 6, 10: 5, 3: 3, 9: 2}
    SUMMER_MONTHS = {4, 5, 6, 7, 8}  # mai-sep → toujours bleu

    # Jan 1, 2020 = mercredi → weekday index 2 (0=lun)
    JAN1_WEEKDAY = 2

    days_info = []
    month, day_in_month = 0, 0
    cum = 0
    for mi, nd in enumerate(MONTH_DAYS):
        for d in range(nd):
            idx = cum + d
            weekday = (JAN1_WEEKDAY + idx) % 7
            is_weekend = weekday >= 5
            cold = COLD_SCORE.get(mi, 0)
            days_info.append({
                'idx': idx, 'month': mi,
                'weekday': weekday, 'is_weekend': is_weekend,
                'cold': cold, 'is_summer': mi in SUMMER_MONTHS,
            })
        cum += nd

    # Candidats non-bleus : jours ouvrables hors été
    candidates = [d for d in days_info if not d['is_weekend'] and not d['is_summer']]
    # Trier par score de froid DESC, puis jour de l'année ASC (hiver début d'abord)
    candidates_sorted = sorted(candidates, key=lambda d: (-d['cold'], d['idx']))

    rouge_set = {d['idx'] for d in candidates_sorted[:22]}
    blanc_set = {d['idx'] for d in candidates_sorted[22:65]}

    colors = []
    for d in days_info:
        if d['idx'] in rouge_set:
            colors.append('rouge')
        elif d['idx'] in blanc_set:
            colors.append('blanc')
        else:
            colors.append('bleu')
    return colors


# ──────────────────────────────────────────────────────────────────────────────
# GÉNÉRATION DU PLANNING EJP : attribution des jours de pointe
# ──────────────────────────────────────────────────────────────────────────────

def _generate_ejp_pointe_days() -> set:
    """
    Retourne l'ensemble des indices de jours (0-364) considérés comme
    'jours de pointe' EJP (22 jours, ouvrables, hiver).
    Même logique que TEMPO rouge.
    """
    colors = _generate_tempo_colors()
    return {i for i, c in enumerate(colors) if c == 'rouge'}


# ──────────────────────────────────────────────────────────────────────────────
# GÉNÉRATION DES VECTEURS HOROSAISONNIERS (C4 et HTA)
# ──────────────────────────────────────────────────────────────────────────────

def _generate_horo_8760(tariff_type: str) -> list:
    """
    Génère le vecteur de 8760 prix horaires pour les tarifs horosaisonniers
    C4_HORO (BT 36-250 kVA) et HTA_HORO (>250 kVA, TURPE 6 HTA).

    Règles horosaisonnières (définition TURPE) :
    ┌───────────────┬────────────────────────────────────────────────────────┐
    │ Saison Hiver  │ Nov 1 → Mar 31   (mois : nov=10, déc=11, jan=0, fév=1,│
    │               │ mar=2 en indices Python)                               │
    │ Saison Été    │ Avr 1 → Oct 31   (mois : avr=3 … oct=9)               │
    ├───────────────┼────────────────────────────────────────────────────────┤
    │ HP            │ Jours ouvrés, 7h ≤ h < 23h                            │
    │ HC            │ Nuits (23h–7h) + week-ends + jours fériés              │
    ├───────────────┼────────────────────────────────────────────────────────┤
    │ Pointe P      │ HTA uniquement : jours ouvrés hiver                    │
    │ (HTA seulement│ créneaux 9h-11h  ET  17h-19h                          │
    └───────────────┴────────────────────────────────────────────────────────┘

    Année de référence : 2020 (non-bissextile, PVGIS) → jan 1 = mercredi (wd=2).
    """
    struct = TARIFF_STRUCTURES[tariff_type]
    MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    HIVER_MOIS = struct['hiver_mois']   # e.g. {10, 0, 1, 2, 11}
    HP_DEBUT   = struct['hp_debut']     # 7
    HP_FIN     = struct['hp_fin']       # 23
    JAN1_WEEKDAY = 2   # 2020-01-01 = mercredi (0=lun, 6=dim)

    is_hta = (tariff_type == 'HTA_HORO')
    if is_hta:
        POINTE_PLAGES = struct['pointe_plages']   # [(9, 11), (17, 19)]
        p_kwh   = struct['p_kwh']
        hph_kwh = struct['hph_kwh']
        hch_kwh = struct['hch_kwh']
        hpe_kwh = struct['hpe_kwh']
        hce_kwh = struct['hce_kwh']
    else:
        hph_kwh = struct['hph_kwh']
        hch_kwh = struct['hch_kwh']
        hpe_kwh = struct['hpe_kwh']
        hce_kwh = struct['hce_kwh']

    # Jours fériés fixes en France (hors Pâques/Ascension/Lundi Pentecôte)
    # Format : (mois_0indexed, jour)
    FERIES = {
        (0, 1),   # 1er janvier
        (4, 1),   # 1er mai
        (4, 8),   # 8 mai
        (6, 14),  # 14 juillet
        (7, 15),  # 15 août
        (10, 1),  # 1er novembre
        (10, 11), # 11 novembre
        (11, 25), # 25 décembre
    }

    prix = []
    global_day = 0

    for mi, nb_jours in enumerate(MONTH_DAYS):
        is_hiver = (mi in HIVER_MOIS)

        for d in range(nb_jours):
            weekday    = (JAN1_WEEKDAY + global_day) % 7   # 0=lun … 6=dim
            is_weekend = weekday >= 5
            is_ferie   = (mi, d) in FERIES
            is_ouvre   = not is_weekend and not is_ferie

            for h in range(24):
                # ── Déterminer la période tarifaire ──────────────────────────
                if HP_DEBUT <= h < HP_FIN:
                    # Créneau HP (7h-23h)
                    if is_ouvre:
                        if is_hiver:
                            # HTA : vérifier si c'est une heure de pointe
                            if is_hta:
                                in_pointe = any(ps <= h < pe for ps, pe in POINTE_PLAGES)
                                p = p_kwh if in_pointe else hph_kwh
                            else:
                                p = hph_kwh
                        else:
                            p = hpe_kwh   # Été HP ouvré
                    else:
                        # Week-end ou férié → HC même sur plage horaire HP
                        p = hch_kwh if is_hiver else hce_kwh
                else:
                    # Créneau HC nuit (h < 7 ou h >= 23)
                    p = hch_kwh if is_hiver else hce_kwh

                prix.append(p)

            global_day += 1

    return prix[:8760]


# ──────────────────────────────────────────────────────────────────────────────
# GÉNÉRATION DU VECTEUR DE PRIX HORAIRES (8760 valeurs)
# ──────────────────────────────────────────────────────────────────────────────

def get_hourly_tariff_schedule(
    tariff_type: str = 'BASE',
    hc_plages_custom: list = None,
) -> dict:
    """
    Retourne un dict avec :
      - 'prix_8760'  : liste de 8760 float (€/kWh à chaque heure)
      - 'label'      : nom lisible du tarif
      - 'abonnement' : abonnement annuel €/an
      - 'stats'      : {'hp_mean', 'hc_mean', 'min', 'max'} pour info
    """
    struct = TARIFF_STRUCTURES.get(tariff_type, TARIFF_STRUCTURES['BASE'])
    MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    def _is_hc(hour: int, plages: list) -> bool:
        """hour ∈ [0, 23], plages = [(start, end), ...] – end peut être < start (nuit)."""
        for start, end in plages:
            if end > start:
                if start <= hour < end:
                    return True
            else:  # chevauchement minuit
                if hour >= start or hour < end:
                    return True
        return False

    prix = []

    if tariff_type == 'BASE':
        p = struct['prix_kwh']
        prix = [p] * 8760

    elif tariff_type in ('HPHC', 'HPHC_MIDI'):
        plages = hc_plages_custom or struct['hc_plages']
        hp, hc = struct['hp_kwh'], struct['hc_kwh']
        for h in range(8760):
            hour = h % 24
            prix.append(hc if _is_hc(hour, plages) else hp)

    elif tariff_type == 'TEMPO':
        colors = _generate_tempo_colors()
        plages = hc_plages_custom or struct['hc_plages']
        # Construire le vecteur
        h = 0
        for day_idx, color in enumerate(colors):
            for hour in range(24):
                is_hc = _is_hc(hour, plages)
                if color == 'bleu':
                    p = struct['bleu_hc_kwh'] if is_hc else struct['bleu_hp_kwh']
                elif color == 'blanc':
                    p = struct['blanc_hc_kwh'] if is_hc else struct['blanc_hp_kwh']
                else:  # rouge
                    p = struct['rouge_hc_kwh'] if is_hc else struct['rouge_hp_kwh']
                prix.append(p)
                h += 1
        prix = prix[:8760]

    elif tariff_type == 'EJP':
        pointe_days = _generate_ejp_pointe_days()
        hp_start, hp_end = struct['heures_pointe']
        hn, hp = struct['hn_kwh'], struct['hp_kwh']
        h = 0
        for day_idx in range(365):
            is_pointe_day = day_idx in pointe_days
            for hour in range(24):
                if is_pointe_day and hp_start <= hour < hp_end:
                    prix.append(hp)
                else:
                    prix.append(hn)
                h += 1
        prix = prix[:8760]

    elif tariff_type in ('C4_HORO', 'HTA_HORO'):
        # Tarifs horosaisonniers industriels – délégation à _generate_horo_8760()
        prix = _generate_horo_8760(tariff_type)

    else:
        prix = [struct.get('prix_kwh', 0.2516)] * 8760

    return {
        'prix_8760'  : prix,
        'label'      : struct.get('label', tariff_type),
        'abonnement' : struct.get('abonnement_6kva', struct.get('abonnement_an', 130.0)),
        'stats': {
            'mean'   : round(sum(prix) / len(prix), 4),
            'min'    : round(min(prix), 4),
            'max'    : round(max(prix), 4),
        }
    }


TARIFF_LABELS = {k: v['label'] for k, v in TARIFF_STRUCTURES.items()}

# ──────────────────────────────────────────────────────────────────────────────
# PROFILS DE CONSOMMATION TYPES ENEDIS  (normalisés → somme = 1.0)
# ──────────────────────────────────────────────────────────────────────────────

def _make_hourly_profile(profile_type: str) -> list:
    """
    Génère un profil horaire normalisé sur 8760 heures (année non-bissextile).
    La somme des 8760 valeurs vaut 1.0.
    Les formes sont calées sur les profils de référence Enedis.

    profile_type : 'RES1', 'RES2', 'PRO1', 'PRO2', 'AGR', 'ENT'
    """

    # ── 1. FACTEURS MENSUELS ──────────────────────────────────────────────────
    # (relatifs à la moyenne ; seront normalisés)
    # Ordre : Jan … Déc
    MONTHLY = {
        'RES1': [1.30, 1.20, 1.05, 0.90, 0.80, 0.75, 0.72, 0.75, 0.85, 1.00, 1.15, 1.28],
        'RES2': [1.80, 1.60, 1.30, 0.90, 0.70, 0.60, 0.55, 0.60, 0.75, 1.00, 1.40, 1.75],
        'PRO1': [1.15, 1.10, 1.05, 0.95, 0.90, 0.85, 0.82, 0.85, 0.90, 1.00, 1.10, 1.13],
        'PRO2': [1.55, 1.40, 1.20, 0.95, 0.80, 0.70, 0.65, 0.70, 0.82, 1.00, 1.35, 1.50],
        'AGR' : [1.40, 1.30, 1.10, 0.95, 0.88, 0.80, 0.78, 0.82, 0.90, 1.00, 1.18, 1.35],
        'ENT' : [1.15, 1.10, 1.05, 0.97, 0.93, 0.88, 0.85, 0.88, 0.95, 1.02, 1.10, 1.12],
    }

    # ── 2. FORMES HORAIRES (facteurs pour chaque heure 0-23) ─────────────────
    # Weekday / Weekend × Saison (été vs hiver vs inter)
    # Indices : 0=hiver, 1=inter, 2=été

    HOURLY_SHAPES = {
        'RES1': {
            'wd': [  # weekday
                [0.30, 0.32, 0.28, 0.26, 0.28, 0.45, 0.75, 1.60, 1.55, 1.00, 0.85, 1.05,
                 1.15, 1.00, 0.75, 0.70, 0.85, 1.30, 1.80, 1.95, 1.70, 1.30, 0.90, 0.55],  # hiver
                [0.28, 0.25, 0.23, 0.22, 0.24, 0.38, 0.65, 1.20, 1.10, 0.85, 0.75, 0.90,
                 1.00, 0.88, 0.72, 0.70, 0.88, 1.20, 1.60, 1.75, 1.55, 1.20, 0.80, 0.50],  # inter
                [0.25, 0.22, 0.20, 0.20, 0.22, 0.32, 0.55, 0.95, 0.90, 0.78, 0.72, 0.88,
                 0.95, 0.85, 0.72, 0.72, 0.90, 1.15, 1.45, 1.65, 1.50, 1.15, 0.75, 0.48],  # été
            ],
            'we': [  # weekend/jours fériés
                [0.38, 0.35, 0.32, 0.30, 0.30, 0.35, 0.50, 0.80, 1.20, 1.35, 1.25, 1.20,
                 1.25, 1.20, 1.15, 1.10, 1.10, 1.35, 1.65, 1.80, 1.65, 1.35, 0.95, 0.60],  # hiver
                [0.35, 0.30, 0.28, 0.28, 0.28, 0.30, 0.45, 0.72, 1.05, 1.18, 1.12, 1.10,
                 1.12, 1.08, 1.00, 0.98, 1.05, 1.22, 1.48, 1.60, 1.48, 1.22, 0.88, 0.55],  # inter
                [0.30, 0.27, 0.25, 0.25, 0.25, 0.28, 0.42, 0.68, 0.98, 1.10, 1.08, 1.05,
                 1.05, 1.02, 0.98, 0.98, 1.05, 1.18, 1.40, 1.55, 1.42, 1.18, 0.82, 0.50],  # été
            ]
        },
        'RES2': {
            'wd': [
                [0.55, 0.52, 0.50, 0.50, 0.55, 0.90, 1.55, 2.50, 2.20, 1.30, 1.00, 1.05,
                 1.10, 1.00, 0.95, 1.10, 1.50, 2.30, 2.80, 2.75, 2.20, 1.55, 0.95, 0.65],  # hiver
                [0.32, 0.30, 0.28, 0.26, 0.28, 0.45, 0.75, 1.30, 1.20, 0.90, 0.80, 0.92,
                 1.00, 0.90, 0.75, 0.75, 0.95, 1.30, 1.70, 1.82, 1.62, 1.25, 0.82, 0.52],  # inter
                [0.26, 0.24, 0.22, 0.22, 0.24, 0.34, 0.58, 1.00, 0.92, 0.80, 0.74, 0.90,
                 0.98, 0.88, 0.74, 0.74, 0.92, 1.18, 1.50, 1.68, 1.52, 1.18, 0.78, 0.50],  # été
            ],
            'we': [
                [0.65, 0.60, 0.58, 0.55, 0.55, 0.65, 0.85, 1.20, 1.70, 1.85, 1.70, 1.55,
                 1.55, 1.50, 1.45, 1.55, 1.70, 2.10, 2.60, 2.75, 2.35, 1.70, 1.10, 0.75],  # hiver
                [0.38, 0.35, 0.32, 0.30, 0.30, 0.36, 0.52, 0.80, 1.12, 1.25, 1.18, 1.12,
                 1.15, 1.10, 1.05, 1.05, 1.12, 1.30, 1.58, 1.72, 1.56, 1.28, 0.90, 0.58],  # inter
                [0.32, 0.28, 0.26, 0.26, 0.26, 0.30, 0.45, 0.72, 1.02, 1.15, 1.10, 1.08,
                 1.08, 1.05, 1.00, 1.00, 1.08, 1.22, 1.45, 1.60, 1.45, 1.20, 0.84, 0.52],  # été
            ]
        },
        'PRO1': {
            'wd': [
                [0.06, 0.05, 0.05, 0.05, 0.06, 0.15, 0.55, 1.80, 2.35, 2.45, 2.40, 2.20,
                 1.80, 2.10, 2.38, 2.42, 2.10, 1.50, 0.45, 0.20, 0.12, 0.10, 0.08, 0.07],  # hiver
                [0.06, 0.05, 0.05, 0.05, 0.06, 0.12, 0.45, 1.60, 2.20, 2.35, 2.30, 2.10,
                 1.75, 2.00, 2.25, 2.32, 2.00, 1.35, 0.38, 0.18, 0.10, 0.08, 0.07, 0.06],  # inter
                [0.05, 0.05, 0.04, 0.04, 0.05, 0.10, 0.38, 1.40, 2.05, 2.20, 2.15, 1.98,
                 1.65, 1.88, 2.12, 2.18, 1.88, 1.22, 0.32, 0.15, 0.09, 0.07, 0.06, 0.05],  # été
            ],
            'we': [
                [0.05, 0.04, 0.04, 0.04, 0.04, 0.06, 0.10, 0.22, 0.38, 0.45, 0.42, 0.40,
                 0.38, 0.38, 0.38, 0.35, 0.30, 0.20, 0.12, 0.08, 0.06, 0.06, 0.05, 0.05],  # hiver
                [0.05, 0.04, 0.04, 0.04, 0.04, 0.05, 0.09, 0.18, 0.32, 0.38, 0.36, 0.34,
                 0.32, 0.32, 0.32, 0.30, 0.26, 0.16, 0.10, 0.07, 0.06, 0.05, 0.05, 0.04],  # inter
                [0.04, 0.04, 0.03, 0.03, 0.04, 0.05, 0.08, 0.16, 0.28, 0.34, 0.32, 0.30,
                 0.28, 0.28, 0.28, 0.26, 0.22, 0.14, 0.08, 0.06, 0.05, 0.04, 0.04, 0.04],  # été
            ]
        },
        'PRO2': {
            'wd': [
                [0.10, 0.08, 0.08, 0.08, 0.10, 0.25, 0.75, 2.00, 2.50, 2.55, 2.48, 2.25,
                 1.90, 2.15, 2.45, 2.52, 2.20, 1.60, 0.55, 0.28, 0.18, 0.15, 0.12, 0.10],  # hiver
                [0.07, 0.06, 0.06, 0.06, 0.07, 0.14, 0.50, 1.70, 2.25, 2.38, 2.32, 2.12,
                 1.78, 2.02, 2.28, 2.35, 2.02, 1.38, 0.40, 0.20, 0.12, 0.09, 0.08, 0.07],  # inter
                [0.05, 0.05, 0.04, 0.04, 0.05, 0.10, 0.38, 1.40, 2.05, 2.20, 2.15, 1.98,
                 1.65, 1.88, 2.12, 2.18, 1.88, 1.22, 0.32, 0.16, 0.10, 0.07, 0.06, 0.05],  # été
            ],
            'we': [
                [0.08, 0.07, 0.07, 0.07, 0.07, 0.10, 0.18, 0.32, 0.50, 0.58, 0.55, 0.52,
                 0.50, 0.50, 0.50, 0.48, 0.40, 0.28, 0.18, 0.12, 0.09, 0.08, 0.08, 0.08],  # hiver
                [0.06, 0.05, 0.05, 0.05, 0.05, 0.07, 0.12, 0.22, 0.36, 0.42, 0.40, 0.38,
                 0.36, 0.36, 0.36, 0.34, 0.28, 0.20, 0.12, 0.08, 0.06, 0.06, 0.05, 0.05],  # inter
                [0.04, 0.04, 0.03, 0.03, 0.04, 0.05, 0.08, 0.16, 0.28, 0.34, 0.32, 0.30,
                 0.28, 0.28, 0.28, 0.26, 0.22, 0.14, 0.08, 0.06, 0.05, 0.04, 0.04, 0.04],  # été
            ]
        },
        'AGR': {
            'wd': [
                [0.45, 0.42, 0.40, 0.42, 0.55, 1.00, 1.45, 1.65, 1.60, 1.45, 1.35, 1.20,
                 1.10, 1.20, 1.35, 1.40, 1.25, 1.10, 0.90, 0.80, 0.72, 0.65, 0.58, 0.50],  # hiver
                [0.38, 0.35, 0.33, 0.35, 0.48, 0.88, 1.28, 1.48, 1.45, 1.32, 1.22, 1.10,
                 1.02, 1.10, 1.22, 1.28, 1.15, 1.00, 0.82, 0.72, 0.65, 0.58, 0.52, 0.44],  # inter
                [0.32, 0.30, 0.28, 0.30, 0.45, 0.80, 1.15, 1.35, 1.32, 1.20, 1.12, 1.00,
                 0.95, 1.00, 1.12, 1.18, 1.08, 0.95, 0.78, 0.68, 0.62, 0.55, 0.48, 0.40],  # été
            ],
            'we': [
                [0.48, 0.44, 0.42, 0.44, 0.55, 0.90, 1.25, 1.42, 1.38, 1.28, 1.20, 1.12,
                 1.08, 1.12, 1.20, 1.25, 1.15, 1.02, 0.88, 0.78, 0.70, 0.62, 0.56, 0.52],  # hiver
                [0.40, 0.36, 0.34, 0.36, 0.48, 0.80, 1.10, 1.28, 1.25, 1.15, 1.08, 1.00,
                 0.98, 1.00, 1.08, 1.15, 1.05, 0.95, 0.80, 0.72, 0.64, 0.56, 0.50, 0.44],  # inter
                [0.34, 0.30, 0.28, 0.30, 0.44, 0.75, 1.02, 1.18, 1.15, 1.07, 1.00, 0.94,
                 0.92, 0.94, 1.00, 1.07, 0.98, 0.90, 0.76, 0.66, 0.60, 0.52, 0.46, 0.38],  # été
            ]
        },
        'ENT': {
            'wd': [
                [0.12, 0.10, 0.10, 0.10, 0.12, 0.28, 0.65, 1.70, 2.15, 2.25, 2.22, 2.05,
                 1.80, 2.00, 2.20, 2.22, 2.00, 1.55, 0.65, 0.35, 0.22, 0.18, 0.15, 0.12],  # hiver
                [0.10, 0.09, 0.09, 0.09, 0.10, 0.22, 0.55, 1.55, 2.00, 2.12, 2.08, 1.92,
                 1.70, 1.88, 2.06, 2.10, 1.88, 1.42, 0.55, 0.28, 0.18, 0.14, 0.12, 0.10],  # inter
                [0.09, 0.08, 0.08, 0.08, 0.09, 0.18, 0.48, 1.40, 1.85, 1.98, 1.95, 1.80,
                 1.58, 1.75, 1.92, 1.96, 1.75, 1.30, 0.48, 0.24, 0.15, 0.12, 0.10, 0.09],  # été
            ],
            'we': [
                [0.10, 0.09, 0.09, 0.09, 0.10, 0.14, 0.22, 0.40, 0.65, 0.78, 0.75, 0.70,
                 0.68, 0.70, 0.72, 0.68, 0.60, 0.40, 0.24, 0.16, 0.12, 0.10, 0.10, 0.10],  # hiver
                [0.08, 0.07, 0.07, 0.07, 0.08, 0.11, 0.18, 0.32, 0.52, 0.62, 0.60, 0.56,
                 0.54, 0.56, 0.58, 0.54, 0.48, 0.32, 0.19, 0.12, 0.09, 0.08, 0.07, 0.07],  # inter
                [0.07, 0.06, 0.06, 0.06, 0.07, 0.09, 0.14, 0.26, 0.44, 0.54, 0.52, 0.48,
                 0.46, 0.48, 0.50, 0.48, 0.40, 0.26, 0.16, 0.10, 0.07, 0.06, 0.06, 0.06],  # été
            ]
        },
    }

    if profile_type not in HOURLY_SHAPES:
        profile_type = 'RES1'

    monthly_factors = MONTHLY[profile_type]
    shapes = HOURLY_SHAPES[profile_type]

    # ── 3. GÉNÉRER LES 8760 VALEURS ──────────────────────────────────────────
    # Année de référence : 2023 (commence un dimanche)
    start = datetime(2023, 1, 1)
    profile = []

    MONTHS_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # 2023 non-bissextile

    hour_idx = 0
    for month_idx, n_days in enumerate(MONTHS_DAYS):
        mf = monthly_factors[month_idx]
        # Saison horaire : 0=hiver (oct-mars), 1=inter (avr,sep), 2=été (mai-aug)
        if month_idx in (0, 1, 2, 9, 10, 11):   # J, F, M, O, N, D
            season = 0
        elif month_idx in (3, 8):                # A, S
            season = 1
        else:                                     # M, J, J, A
            season = 2

        for day_in_month in range(n_days):
            dt = start + timedelta(hours=hour_idx)
            dow = dt.weekday()  # 0=lundi … 6=dimanche
            is_weekend = (dow >= 5)  # samedi ou dimanche
            day_shape = shapes['we'][season] if is_weekend else shapes['wd'][season]

            for h in range(24):
                raw_val = mf * day_shape[h]
                profile.append(raw_val)
            hour_idx += 24

    # ── 4. NORMALISER (somme = 1.0) ───────────────────────────────────────────
    total = sum(profile)
    profile = [v / total for v in profile]
    return profile


# Cache des profils générés (évite de recalculer à chaque requête)
_PROFILE_CACHE: dict = {}

def get_consumption_profile(profile_type: str) -> list:
    """Retourne le profil horaire normalisé (8760 valeurs, somme=1.0)."""
    global _PROFILE_CACHE
    if profile_type not in _PROFILE_CACHE:
        _PROFILE_CACHE[profile_type] = _make_hourly_profile(profile_type)
    return _PROFILE_CACHE[profile_type]


# ──────────────────────────────────────────────────────────────────────────────
# CALCUL AUTO-CONSOMMATION
# ──────────────────────────────────────────────────────────────────────────────

def compute_autoconsommation(
    hourly_production_wh: list,        # 8760 valeurs en Wh (production toutes zones)
    annual_consumption_kwh: float,     # Consommation annuelle saisie par l'utilisateur (kWh)
    profile_type: str = 'RES1',        # Profil de consommation Enedis
) -> dict:
    """
    Calcule les indicateurs d'autoconsommation heure par heure.

    Returns dict avec :
      - hourly_production  : liste 8760 Wh
      - hourly_consumption : liste 8760 Wh (profilée)
      - hourly_autoconso   : liste 8760 Wh (min(P,C))
      - hourly_surplus     : liste 8760 Wh (max(P-C, 0))
      - hourly_deficit     : liste 8760 Wh (max(C-P, 0))
      - monthly_*          : listes 12 valeurs kWh
      - kpis               : {taux_autoconso, taux_autosuffisance, ...}
    """
    profile = get_consumption_profile(profile_type)
    annual_consumption_wh = annual_consumption_kwh * 1000.0

    # Consommation horaire profilée
    hourly_consumption_wh = [annual_consumption_wh * v for v in profile]

    # Calcul heure par heure
    h_autoconso = [min(p, c) for p, c in zip(hourly_production_wh, hourly_consumption_wh)]
    h_surplus   = [max(p - c, 0.0) for p, c in zip(hourly_production_wh, hourly_consumption_wh)]
    h_deficit   = [max(c - p, 0.0) for p, c in zip(hourly_production_wh, hourly_consumption_wh)]

    total_prod   = sum(hourly_production_wh)
    total_conso  = sum(hourly_consumption_wh)
    total_auto   = sum(h_autoconso)
    total_surp   = sum(h_surplus)

    # KPIs globaux
    taux_autoconso     = (total_auto / total_prod  * 100) if total_prod  > 0 else 0.0
    taux_autosuffis    = (total_auto / total_conso * 100) if total_conso > 0 else 0.0

    # ── Agrégats mensuels ────────────────────────────────────────────────────
    MONTHS_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    monthly_prod   = []
    monthly_conso  = []
    monthly_auto   = []
    monthly_surp   = []
    monthly_acrate = []
    monthly_asrate = []

    idx = 0
    for n_days in MONTHS_DAYS:
        n_hours = n_days * 24
        mp = sum(hourly_production_wh[idx: idx+n_hours]) / 1000.0  # kWh
        mc = sum(hourly_consumption_wh[idx: idx+n_hours]) / 1000.0
        ma = sum(h_autoconso[idx: idx+n_hours]) / 1000.0
        ms = sum(h_surplus[idx: idx+n_hours]) / 1000.0

        monthly_prod.append(round(mp, 1))
        monthly_conso.append(round(mc, 1))
        monthly_auto.append(round(ma, 1))
        monthly_surp.append(round(ms, 1))
        monthly_acrate.append(round((ma / mp * 100) if mp > 0 else 0, 1))
        monthly_asrate.append(round((ma / mc * 100) if mc > 0 else 0, 1))
        idx += n_hours

    # ── Profil journalier moyen (24h) par saison ─────────────────────────────
    def _daily_avg(values_wh: list, month_indices: list):
        """Moyenne par heure du jour sur les mois demandés."""
        sums   = [0.0] * 24
        counts = [0]   * 24
        idx = 0
        for mi, n_days in enumerate(MONTHS_DAYS):
            for _d in range(n_days):
                for h in range(24):
                    if mi in month_indices:
                        sums[h]   += values_wh[idx]
                        counts[h] += 1
                    idx += 1
        return [round(s / c / 1000.0, 3) if c else 0.0 for s, c in zip(sums, counts)]  # kWh moyen

    winter_prod   = _daily_avg(hourly_production_wh,  [11, 0, 1])  # Déc, Jan, Fév
    winter_conso  = _daily_avg(hourly_consumption_wh, [11, 0, 1])
    summer_prod   = _daily_avg(hourly_production_wh,  [5, 6, 7])   # Jun, Jul, Aoû
    summer_conso  = _daily_avg(hourly_consumption_wh, [5, 6, 7])
    spring_prod   = _daily_avg(hourly_production_wh,  [3, 4])      # Avr, Mai
    spring_conso  = _daily_avg(hourly_consumption_wh, [3, 4])

    return {
        'hourly_production_wh' : hourly_production_wh,
        'hourly_consumption_wh': hourly_consumption_wh,
        'hourly_autoconso_wh'  : h_autoconso,
        'hourly_surplus_wh'    : h_surplus,
        'hourly_deficit_wh'    : h_deficit,
        'monthly': {
            'labels'       : ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'],
            'production'   : monthly_prod,
            'consommation' : monthly_conso,
            'autoconso'    : monthly_auto,
            'surplus'      : monthly_surp,
            'taux_ac'      : monthly_acrate,
            'taux_as'      : monthly_asrate,
        },
        'daily_profiles': {
            'hours'       : list(range(24)),
            'winter_prod' : winter_prod,
            'winter_conso': winter_conso,
            'summer_prod' : summer_prod,
            'summer_conso': summer_conso,
            'spring_prod' : spring_prod,
            'spring_conso': spring_conso,
        },
        'kpis': {
            'production_annuelle_kwh'  : round(total_prod / 1000.0, 1),
            'consommation_annuelle_kwh': round(total_conso / 1000.0, 1),
            'autoconso_kwh'            : round(total_auto / 1000.0, 1),
            'surplus_kwh'              : round(total_surp / 1000.0, 1),
            'deficit_kwh'              : round((total_conso - total_auto) / 1000.0, 1),
            'taux_autoconsommation'    : round(taux_autoconso, 1),
            'taux_autosuffisance'      : round(taux_autosuffis, 1),
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# CALCUL ÉCONOMIQUE
# ──────────────────────────────────────────────────────────────────────────────

def compute_economics(
    kpis: dict,
    tarif_achat_kwh: float = 0.2516,    # utilisé uniquement si tariff_type='BASE' ou non fourni
    prix_revente_kwh: float = 0.0536,   # Tarif S21 surplus 9-100 kWc (€/kWh, T1 2026) – à calculer via get_tarif_revente_s21()
    degradation_annuelle_pct: float = 0.5,
    duree_contrat_ans: int = 20,
    tariff_type: str = 'BASE',
    hourly_production_wh: list = None,       # 8760 Wh – nécessaire pour calcul HP/HC/TEMPO
    hourly_consumption_wh: list = None,      # 8760 Wh
    hourly_autoconso_wh: list = None,        # 8760 Wh
    hourly_surplus_wh: list = None,          # 8760 Wh
    hc_plages_custom: list = None,
) -> dict:
    """
    Calcul économique de l'autoconsommation sur la durée du contrat.
    Prend en compte les tarifs horaires (HP/HC, TEMPO, EJP) si les vecteurs
    horaires sont fournis, sinon utilise les KPIs agrégés avec tarif_achat_kwh.
    """
    # ── Calcul économies avec vecteur horaire (précis pour HP/HC/TEMPO/EJP) ──
    if tariff_type != 'BASE' and hourly_autoconso_wh and hourly_surplus_wh:
        tariff_schedule = get_hourly_tariff_schedule(tariff_type, hc_plages_custom)
        prix_h = tariff_schedule['prix_8760']

        # Économie annuelle = Σ autoconso[h] × prix_achat[h] (on évite d'acheter au réseau)
        economie_an1 = sum(
            a * p / 1000.0  # Wh → kWh × €/kWh
            for a, p in zip(hourly_autoconso_wh, prix_h)
        )
        # Revenu surplus = Σ surplus[h] × tarif_revente (fixe OA EDF)
        revenu_surplus_an1 = sum(s / 1000.0 * prix_revente_kwh for s in hourly_surplus_wh)

        # Prix moyen pondéré par la consommation (pour info)
        tarif_moyen_effectif = sum(
            c * p for c, p in zip(hourly_consumption_wh or [], prix_h)
        ) / max(sum(hourly_consumption_wh or [1]), 1) if hourly_consumption_wh else tarif_achat_kwh

        # Détail HP/HC sur l'autoconsommation
        detail_tariff = tariff_schedule['stats']
        abonnement = tariff_schedule['abonnement']

    else:
        # Fallback : tarif unique (BASE ou vecteurs non fournis)
        auto = kpis['autoconso_kwh']
        surp = kpis['surplus_kwh']
        economie_an1       = auto * tarif_achat_kwh
        revenu_surplus_an1 = surp * prix_revente_kwh
        tarif_moyen_effectif = tarif_achat_kwh
        detail_tariff = {'mean': tarif_achat_kwh, 'min': tarif_achat_kwh, 'max': tarif_achat_kwh}
        abonnement = TARIFF_STRUCTURES.get(tariff_type, {}).get('abonnement_6kva', 130.0)

    gain_total_an1 = economie_an1 + revenu_surplus_an1

    economies    = []
    revenus_surp = []
    total_ec     = 0.0
    total_rev    = 0.0

    for y in range(duree_contrat_ans):
        facto = (1 - degradation_annuelle_pct / 100) ** y
        eco   = economie_an1       * facto
        rev   = revenu_surplus_an1 * facto
        economies.append(round(eco, 0))
        revenus_surp.append(round(rev, 0))
        total_ec  += eco
        total_rev += rev

    return {
        'tariff_type'         : tariff_type,
        'tariff_label'        : TARIFF_STRUCTURES.get(tariff_type, {}).get('label', tariff_type),
        'tarif_achat'         : round(tarif_moyen_effectif, 4),
        'tarif_revente'       : prix_revente_kwh,
        'abonnement_an'       : abonnement,
        'detail_tariff'       : detail_tariff,
        'degradation_pct'     : degradation_annuelle_pct,
        'duree_ans'           : duree_contrat_ans,
        'economie_an1'        : round(economie_an1, 0),
        'revenu_surplus_an1'  : round(revenu_surplus_an1, 0),
        'gain_total_an1'      : round(gain_total_an1, 0),
        'cumul_economies'     : round(total_ec, 0),
        'cumul_revenus_surp'  : round(total_rev, 0),
        'cumul_total'         : round(total_ec + total_rev, 0),
        'economies_par_an'    : economies,
        'revenus_par_an'      : revenus_surp,
    }


# ──────────────────────────────────────────────────────────────────────────────
# NOMS / DESCRIPTIONS DES PROFILS
# ──────────────────────────────────────────────────────────────────────────────

PROFILE_LABELS = {
    'RES1': 'Résidentiel – Tarif Base/HC-HP (sans chauffage électrique)',
    'RES2': 'Résidentiel – Avec chauffage électrique',
    'PRO1': 'Professionnel – Tertiaire/Bureau (sans chauffage électrique)',
    'PRO2': 'Professionnel – Avec chauffage électrique',
    'AGR' : 'Agricole – Exploitation agricole',
    'ENT' : 'Entreprise / Industrie – Process continu',
}


# ──────────────────────────────────────────────────────────────────────────────
# ENEDIS DATA CONNECT – Courbes de charge réelles (compteur Linky)
# ──────────────────────────────────────────────────────────────────────────────
# Prérequis : inscription sur datahub-enedis.fr + consentement signé du client.
# Flux OAuth 2.0 Authorization Code :
#   1. Ton app redirige le client vers ENEDIS_AUTHORIZE_URL
#   2. Le client se connecte à son compte Enedis et donne son consentement
#   3. Enedis redirige vers ta redirect_uri avec un ?code=
#   4. Tu échanges ce code contre un access_token via /oauth2/v3/token
#   5. Tu appelles Metering v5 avec ce token pour récupérer les courbes 30min
# Doc : https://datahub-enedis.fr/services-api/data-connect/
# ──────────────────────────────────────────────────────────────────────────────

ENEDIS_SANDBOX_BASE  = "https://gw.ext.prod-sandbox.api.enedis.fr"
ENEDIS_PROD_BASE     = "https://gw.ext.prod.api.enedis.fr"
ENEDIS_AUTHORIZE_URL = "https://mon-compte-particulier.enedis.fr/dataconnect/v1/oauth2/authorize"
ENEDIS_TOKEN_PATH    = "/oauth2/v3/token"
ENEDIS_LOAD_CURVE_PATH = "/metering_data/v5/consumption_load_curve"


def get_enedis_authorize_url(client_id: str, redirect_uri: str, state: str = '') -> str:
    """
    Génère l'URL de consentement Enedis (OAuth 2.0 Authorization Code flow).
    Le client doit visiter cette URL pour autoriser l'accès à son compteur Linky.

    Args:
        client_id    : identifiant de ton application (fourni par Enedis)
        redirect_uri : URL de callback de ton app (doit être enregistrée chez Enedis)
        state        : valeur aléatoire anti-CSRF (recommandé)

    Returns:
        URL complète vers la page de consentement Enedis.
    """
    import urllib.parse
    params = {
        'client_id'    : client_id,
        'redirect_uri' : redirect_uri,
        'response_type': 'code',
    }
    if state:
        params['state'] = state
    return ENEDIS_AUTHORIZE_URL + '?' + urllib.parse.urlencode(params)


def exchange_enedis_code_for_token(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    sandbox: bool = False,
) -> dict:
    """
    Échange le code d'autorisation (reçu en callback) contre un access_token.
    Utilise le grant type Authorization Code (OAuth 2.0).

    Returns:
        dict Enedis : {access_token, token_type, expires_in,
                       refresh_token, usage_points_id, ...}
    Raises:
        ValueError si l'échange échoue (code expiré, credentials invalides, etc.)
    """
    import urllib.request
    import urllib.parse
    import json as _json

    base = ENEDIS_SANDBOX_BASE if sandbox else ENEDIS_PROD_BASE
    url  = base + ENEDIS_TOKEN_PATH
    body = urllib.parse.urlencode({
        'grant_type'   : 'authorization_code',
        'code'         : code,
        'client_id'    : client_id,
        'client_secret': client_secret,
        'redirect_uri' : redirect_uri,
    }).encode()
    req = urllib.request.Request(
        url, data=body, method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return _json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ValueError(f"Enedis token exchange HTTP {e.code}: {e.read().decode(errors='replace')}")
    except Exception as e:
        raise ValueError(f"Enedis token exchange failed: {e}")


def fetch_enedis_load_curve_30min(
    pdl: str,
    access_token: str,
    date_start: str,    # YYYY-MM-DD
    date_end: str,      # YYYY-MM-DD (max 24 mois d'écart)
    sandbox: bool = False,
) -> list:
    """
    Télécharge les données de consommation au pas 30 min via Metering v5.

    Returns:
        Liste d'intervalles : [{'date': 'YYYY-MM-DD HH:MM:SS', 'value': float (Wh)}, ...]
        La valeur est en Wh (puissance W × 0.5h convertie en énergie).

    Raises:
        ValueError si le PDL est inconnu, le consentement absent, ou l'API répond en erreur.
    """
    import urllib.request
    import urllib.parse
    import json as _json

    base   = ENEDIS_SANDBOX_BASE if sandbox else ENEDIS_PROD_BASE
    params = urllib.parse.urlencode({
        'usage_point_id': pdl,
        'start'         : date_start,
        'end'           : date_end,
    })
    url = base + ENEDIS_LOAD_CURVE_PATH + '?' + params
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {access_token}',
        'Accept'       : 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = _json.loads(r.read())
            # Format : {meter_reading: {interval_reading: [{date, value}, ...]}}
            readings = (
                resp.get('meter_reading', resp)
                    .get('interval_reading', [])
            )
            # Les valeurs sont en W (puissance), pas en Wh (énergie).
            # Sur 30 min : énergie (Wh) = puissance (W) × 0.5
            return [
                {
                    'date' : item['date'],
                    'value': float(item.get('value') or 0) * 0.5,
                }
                for item in readings
            ]
    except urllib.error.HTTPError as e:
        raise ValueError(f"Enedis Metering API HTTP {e.code}: {e.read().decode(errors='replace')}")
    except Exception as e:
        raise ValueError(f"Enedis Metering API error: {e}")


def build_8760h_profile_from_enedis(intervals: list) -> list:
    """
    Convertit les données 30min Enedis en profil horaire normalisé 8760h (somme = 1.0).

    Étapes :
      1. Agréger les deux créneaux 30min → valeur horaire (Wh)
      2. Mapper sur le calendrier 8760h d'une année non-bissextile de référence (jan-déc)
      3. Interpoler les heures manquantes (forward/backward fill)
      4. Normaliser pour que la somme = 1.0 (compatible avec get_consumption_profile)

    Returns:
        Liste de 8760 floats normalisés, ou [] si les données sont insuffisantes.
    """
    # ── Étape 1 : construire un dict (mois, jour, heure) → énergie Wh ────────
    hourly: dict = {}
    for item in intervals:
        raw_date = item.get('date', '')
        try:
            # Accepter 'YYYY-MM-DD HH:MM:SS' et 'YYYY-MM-DDTHH:MM:SS'
            raw_date = raw_date.replace('T', ' ').split('+')[0].strip()
            parts = raw_date.split(' ')
            day_parts  = parts[0].split('-')
            time_parts = parts[1].split(':')
            month = int(day_parts[1])
            day   = int(day_parts[2])
            hour  = int(time_parts[0])
        except (IndexError, ValueError):
            continue
        key = (month, day, hour)
        hourly[key] = hourly.get(key, 0.0) + item.get('value', 0.0)

    if not hourly:
        return []

    # ── Étape 2 : mapper sur 8760h (année référence non-bissextile) ──────────
    MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    profile = []
    for mi, nd in enumerate(MONTH_DAYS):
        month = mi + 1
        for d in range(1, nd + 1):
            for h in range(24):
                profile.append(hourly.get((month, d, h), None))

    # ── Étape 3 : interpoler les valeurs manquantes ───────────────────────────
    filled = list(profile)
    last = None
    for i, v in enumerate(filled):
        if v is not None:
            last = v
        elif last is not None:
            filled[i] = last
    last = None
    for i in range(len(filled) - 1, -1, -1):
        if filled[i] is not None:
            last = filled[i]
        elif last is not None:
            filled[i] = last
    filled = [v if v is not None else 0.0 for v in filled]

    # ── Étape 4 : normaliser ──────────────────────────────────────────────────
    total = sum(filled)
    if total <= 0:
        return []
    return [v / total for v in filled]


def get_enedis_dataconnect_profile(
    pdl: str,
    access_token: str,
    date_start: str = None,   # YYYY-MM-DD, défaut : il y a 365 jours
    date_end: str   = None,   # YYYY-MM-DD, défaut : aujourd'hui
    sandbox: bool   = False,
) -> list:
    """
    Télécharge la courbe de charge réelle depuis l'API Enedis Data Connect (Metering v5)
    et retourne un profil normalisé 8760h (somme = 1.0) directement utilisable dans
    compute_autoconsommation() à la place des profils types synthétiques.

    Args:
        pdl          : Numéro de Point De Livraison (14 chiffres)
        access_token : Token OAuth 2.0 obtenu avec consentement du client
        date_start   : début de la période de mesure (défaut : J-365)
        date_end     : fin de la période de mesure   (défaut : aujourd'hui)
        sandbox      : True pour utiliser l'environnement bac à sable Enedis

    Returns:
        Liste de 8760 floats normalisés si succès, [] sinon (le module appelant
        doit alors basculer sur un profil type synthétique).
    """
    from datetime import date, timedelta

    if date_end is None:
        date_end = date.today().isoformat()
    if date_start is None:
        date_start = (date.today() - timedelta(days=365)).isoformat()

    try:
        intervals = fetch_enedis_load_curve_30min(pdl, access_token, date_start, date_end, sandbox)
        if not intervals:
            return []
        return build_8760h_profile_from_enedis(intervals)
    except ValueError as e:
        print(f"[ENEDIS_DC] get_enedis_dataconnect_profile erreur PDL={pdl}: {e}")
        return []
