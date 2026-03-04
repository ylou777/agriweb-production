"""
Module Autoconsommation - HeliaPV AgriWeb
=========================================
Calcul et analyse de l'autoconsommation solaire à partir des données PVGIS 8760h
et des profils de consommation types Enedis (RES1, RES2, PRO1, PRO2, AGR, ENT).

Références :
  - PVGIS EU Science Hub (données 8760h)
  - Enedis Open Data : courbes de charge fictives résidentielles/professionnelles
  - https://openservices.enedis.fr/service/simulateur-courbes-de-charge/
"""

from datetime import datetime, timedelta
import math

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
    tarif_achat_kwh: float = 0.2516,    # Prix électricité achetée (€/kWh, tarif réglementé HC/HP moyen 2024)
    prix_revente_kwh: float = 0.1276,   # Tarif OA EDF achat surplus ≤36 kVA (€/kWh, 2024)
    degradation_annuelle_pct: float = 0.5,
    duree_contrat_ans: int = 20,
) -> dict:
    """Calcul économique de l'autoconsommation sur la durée du contrat."""
    auto   = kpis['autoconso_kwh']
    surp   = kpis['surplus_kwh']

    economies   = []
    revenus_surp = []
    total_ec    = 0.0
    total_rev   = 0.0

    for y in range(duree_contrat_ans):
        facto = (1 - degradation_annuelle_pct / 100) ** y
        eco   = auto * facto * tarif_achat_kwh
        rev   = surp * facto * prix_revente_kwh
        economies.append(round(eco, 0))
        revenus_surp.append(round(rev, 0))
        total_ec  += eco
        total_rev += rev

    return {
        'tarif_achat'         : tarif_achat_kwh,
        'tarif_revente'       : prix_revente_kwh,
        'degradation_pct'     : degradation_annuelle_pct,
        'duree_ans'           : duree_contrat_ans,
        'economie_an1'        : round(auto * tarif_achat_kwh, 0),
        'revenu_surplus_an1'  : round(surp * prix_revente_kwh, 0),
        'gain_total_an1'      : round(auto * tarif_achat_kwh + surp * prix_revente_kwh, 0),
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
