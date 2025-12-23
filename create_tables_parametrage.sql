-- =====================================================
-- TABLES DE PARAMÉTRAGE ENTREPRISE ET PRIX
-- =====================================================

-- Table 1: Paramétrage de l'entreprise (logo, coordonnées, certifications)
CREATE TABLE IF NOT EXISTS parametrage_entreprise (
    id SERIAL PRIMARY KEY,
    nom_entreprise VARCHAR(255) NOT NULL DEFAULT 'Votre Société Photovoltaïque',
    adresse TEXT,
    code_postal VARCHAR(10),
    ville VARCHAR(100),
    telephone VARCHAR(20),
    email VARCHAR(100),
    site_web VARCHAR(255),
    
    -- Identifiants légaux
    siret VARCHAR(14),
    tva_intracommunautaire VARCHAR(20),
    
    -- Certifications
    rge_numero VARCHAR(50),
    rge_date_validite DATE,
    qualibat_numero VARCHAR(50),
    qualibat_date_validite DATE,
    qualifelec_numero VARCHAR(50),
    autres_certifications TEXT,
    
    -- Logo et charte graphique
    logo_base64 TEXT,  -- Logo en base64 pour PDF
    couleur_primaire VARCHAR(7) DEFAULT '#003d7a',  -- Bleu foncé
    couleur_secondaire VARCHAR(7) DEFAULT '#0066cc',  -- Bleu clair
    couleur_accent VARCHAR(7) DEFAULT '#28a745',  -- Vert
    
    -- Informations complémentaires
    capital_social DECIMAL(12,2),
    numero_rc VARCHAR(50),
    assurance_rc VARCHAR(255),
    numero_police_assurance VARCHAR(50),
    
    -- Mentions légales
    mentions_legales TEXT,
    conditions_generales TEXT,
    
    -- Métadonnées
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actif BOOLEAN DEFAULT TRUE
);

-- Table 2: Paramétrage des prix des organes
CREATE TABLE IF NOT EXISTS parametrage_prix_organes (
    id SERIAL PRIMARY KEY,
    nom_organe VARCHAR(100) NOT NULL,
    categorie VARCHAR(50) NOT NULL,  -- 'module', 'onduleur', 'structure', 'cable', 'protection', 'main_oeuvre', 'admin'
    
    -- Prix unitaires
    prix_unitaire_ht DECIMAL(10,2),
    unite VARCHAR(20),  -- '€/Wc', '€/kW', '€/m²', '€/ml', '€/u', '€/h'
    
    -- Caractéristiques techniques (pour modules et onduleurs)
    puissance_wc INTEGER,  -- Pour modules: 550, 600, etc.
    puissance_kw DECIMAL(6,2),  -- Pour onduleurs: 25, 50, 100 kW
    marque VARCHAR(100),
    modele VARCHAR(100),
    
    -- Marges commerciales
    marge_commerciale_pct DECIMAL(5,2) DEFAULT 15.00,  -- % de marge
    remise_max_autorisee_pct DECIMAL(5,2) DEFAULT 10.00,
    
    -- Prix par tranches (optionnel pour tarification progressive)
    prix_tranche_1_ht DECIMAL(10,2),  -- < 100 kWc
    prix_tranche_2_ht DECIMAL(10,2),  -- 100-250 kWc
    prix_tranche_3_ht DECIMAL(10,2),  -- > 250 kWc
    
    -- Métadonnées
    fournisseur VARCHAR(100),
    reference_fournisseur VARCHAR(100),
    delai_livraison_jours INTEGER,
    stock_disponible BOOLEAN DEFAULT TRUE,
    date_dernier_prix DATE DEFAULT CURRENT_DATE,
    
    -- Validité
    actif BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(nom_organe, categorie, marque, modele)
);

-- Table 3: Paramétrage main d'œuvre et prestations
CREATE TABLE IF NOT EXISTS parametrage_main_oeuvre (
    id SERIAL PRIMARY KEY,
    type_prestation VARCHAR(100) NOT NULL,  -- 'pose_modules', 'cablage', 'raccordement', etc.
    
    -- Tarifs
    tarif_horaire_ht DECIMAL(8,2),
    nb_heures_unitaire DECIMAL(6,2),  -- Temps estimé par unité (ex: 0.5h par module)
    forfait_ht DECIMAL(10,2),  -- Ou forfait global
    
    -- Détails
    description TEXT,
    competence_requise VARCHAR(100),  -- 'electricien', 'couvreur', 'charpentier'
    
    -- Validité
    actif BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INSERTION DES DONNÉES PAR DÉFAUT
-- =====================================================

-- Entreprise par défaut
INSERT INTO parametrage_entreprise (
    nom_entreprise, adresse, code_postal, ville, telephone, email,
    siret, rge_numero, qualibat_numero,
    couleur_primaire, couleur_secondaire, couleur_accent
) VALUES (
    'AgriWeb Photovoltaïque', 
    '123 Avenue du Soleil', 
    '75001', 
    'Paris', 
    '01 23 45 67 89', 
    'contact@agriweb-pv.fr',
    '12345678900012',
    'RGE-2024-001',
    'QB-2024-001',
    '#003d7a',
    '#0066cc',
    '#28a745'
) ON CONFLICT DO NOTHING;

-- Prix modules photovoltaïques (gamme complète)
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, puissance_wc, marque, modele, marge_commerciale_pct, fournisseur) VALUES
-- JA Solar (marque premium)
('Module PV 500Wc', 'module', 0.35, '€/Wc', 500, 'JA Solar', 'JAM72S30-500/MR', 15.00, 'Krannich Solar'),
('Module PV 550Wc', 'module', 0.32, '€/Wc', 550, 'JA Solar', 'JAM72S30-550/MR', 15.00, 'Krannich Solar'),
('Module PV 600Wc', 'module', 0.30, '€/Wc', 600, 'JA Solar', 'JAM72S30-600/MR', 15.00, 'Krannich Solar'),
-- Longi (haute performance)
('Module PV 665Wc', 'module', 0.28, '€/Wc', 665, 'Longi', 'LR5-72HIH-665M', 15.00, 'Alma Solar'),
('Module PV 700Wc', 'module', 0.26, '€/Wc', 700, 'Longi', 'LR5-72HIH-700M', 15.00, 'Alma Solar'),
-- Trina Solar (économique)
('Module PV 450Wc', 'module', 0.38, '€/Wc', 450, 'Trina Solar', 'Vertex S TSM-450DE19', 15.00, 'Solarwatt'),
('Module PV 540Wc', 'module', 0.33, '€/Wc', 540, 'Trina Solar', 'Vertex S TSM-540DE19', 15.00, 'Solarwatt')
ON CONFLICT (nom_organe, categorie, marque, modele) DO UPDATE SET
    prix_unitaire_ht = EXCLUDED.prix_unitaire_ht,
    puissance_wc = EXCLUDED.puissance_wc,
    marge_commerciale_pct = EXCLUDED.marge_commerciale_pct,
    fournisseur = EXCLUDED.fournisseur,
    date_modification = CURRENT_TIMESTAMP;

-- Prix onduleurs (gamme complète par puissance)
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, puissance_kw, marque, modele, marge_commerciale_pct, fournisseur) VALUES
-- Huawei (marque leader)
('Onduleur 8kW', 'onduleur', 140.00, '€/kW', 8, 'Huawei', 'SUN2000-8KTL-M1', 18.00, 'Huawei France'),
('Onduleur 10kW', 'onduleur', 130.00, '€/kW', 10, 'Huawei', 'SUN2000-10KTL-M1', 18.00, 'Huawei France'),
('Onduleur 12kW', 'onduleur', 120.00, '€/kW', 12, 'Huawei', 'SUN2000-12KTL-M2', 18.00, 'Huawei France'),
('Onduleur 15kW', 'onduleur', 110.00, '€/kW', 15, 'Huawei', 'SUN2000-15KTL-M2', 18.00, 'Huawei France'),
('Onduleur 20kW', 'onduleur', 105.00, '€/kW', 20, 'Huawei', 'SUN2000-20KTL-M2', 18.00, 'Huawei France'),
('Onduleur 25kW', 'onduleur', 100.00, '€/kW', 25, 'Huawei', 'SUN2000-25KTL-M3', 18.00, 'Huawei France'),
('Onduleur 30kW', 'onduleur', 95.00, '€/kW', 30, 'Huawei', 'SUN2000-30KTL-M3', 18.00, 'Huawei France'),
('Onduleur 40kW', 'onduleur', 92.00, '€/kW', 40, 'Huawei', 'SUN2000-40KTL-M3', 18.00, 'Huawei France'),
('Onduleur 50kW', 'onduleur', 90.00, '€/kW', 50, 'Huawei', 'SUN2000-50KTL-M3', 18.00, 'Huawei France'),
('Onduleur 60kW', 'onduleur', 87.00, '€/kW', 60, 'Huawei', 'SUN2000-60KTL-M3', 18.00, 'Huawei France'),
('Onduleur 100kW', 'onduleur', 80.00, '€/kW', 100, 'Huawei', 'SUN2000-100KTL-M3', 18.00, 'Huawei France'),
('Onduleur 110kW', 'onduleur', 78.00, '€/kW', 110, 'Huawei', 'SUN2000-110KTL-M3', 18.00, 'Huawei France'),
('Onduleur 125kW', 'onduleur', 75.00, '€/kW', 125, 'Huawei', 'SUN2000-125KTL-M3', 18.00, 'Huawei France'),
-- SMA (premium allemand)
('Onduleur 10kW', 'onduleur', 145.00, '€/kW', 10, 'SMA', 'Sunny Tripower 10.0', 18.00, 'SMA Solar'),
('Onduleur 15kW', 'onduleur', 135.00, '€/kW', 15, 'SMA', 'Sunny Tripower 15.0', 18.00, 'SMA Solar'),
('Onduleur 20kW', 'onduleur', 125.00, '€/kW', 20, 'SMA', 'Sunny Tripower 20.0', 18.00, 'SMA Solar'),
('Onduleur 25kW', 'onduleur', 115.00, '€/kW', 25, 'SMA', 'Sunny Tripower CORE1', 18.00, 'SMA Solar'),
('Onduleur 50kW', 'onduleur', 105.00, '€/kW', 50, 'SMA', 'Sunny Tripower CORE2', 18.00, 'SMA Solar'),
('Onduleur 110kW', 'onduleur', 95.00, '€/kW', 110, 'SMA', 'Sunny Central 110', 18.00, 'SMA Solar'),
-- Fronius (qualité autrichienne)
('Onduleur 10kW', 'onduleur', 140.00, '€/kW', 10, 'Fronius', 'Symo 10.0-3-M', 18.00, 'Fronius France'),
('Onduleur 15kW', 'onduleur', 130.00, '€/kW', 15, 'Fronius', 'Symo 15.0-3-M', 18.00, 'Fronius France'),
('Onduleur 20kW', 'onduleur', 120.00, '€/kW', 20, 'Fronius', 'Symo 20.0-3-M', 18.00, 'Fronius France'),
-- === GRANDES PUISSANCES (150-500kW) ===
-- Huawei SUN2000 H3 Series (150-215kW)
('Onduleur 150kW', 'onduleur', 76.00, '€/kW', 150, 'Huawei', 'SUN2000-150KTL-H3', 17.00, 'Huawei France'),
('Onduleur 175kW', 'onduleur', 74.00, '€/kW', 175, 'Huawei', 'SUN2000-175KTL-H3', 17.00, 'Huawei France'),
('Onduleur 185kW', 'onduleur', 73.00, '€/kW', 185, 'Huawei', 'SUN2000-185KTL-H3', 17.00, 'Huawei France'),
('Onduleur 200kW', 'onduleur', 72.00, '€/kW', 200, 'Huawei', 'SUN2000-200KTL-H3', 17.00, 'Huawei France'),
('Onduleur 215kW', 'onduleur', 71.00, '€/kW', 215, 'Huawei', 'SUN2000-215KTL-H3', 17.00, 'Huawei France'),
-- SMA Sunny Central (125-330kW)
('Onduleur 125kW', 'onduleur', 85.00, '€/kW', 125, 'SMA', 'Sunny Central 125 UP', 17.00, 'SMA Solar'),
('Onduleur 150kW', 'onduleur', 82.00, '€/kW', 150, 'SMA', 'Sunny Central 150 UP', 17.00, 'SMA Solar'),
('Onduleur 200kW', 'onduleur', 79.00, '€/kW', 200, 'SMA', 'Sunny Central 200 UP', 17.00, 'SMA Solar'),
('Onduleur 250kW', 'onduleur', 76.00, '€/kW', 250, 'SMA', 'Sunny Central 250 UP', 16.00, 'SMA Solar'),
('Onduleur 300kW', 'onduleur', 74.00, '€/kW', 300, 'SMA', 'Sunny Central 300 UP', 16.00, 'SMA Solar'),
('Onduleur 330kW', 'onduleur', 73.00, '€/kW', 330, 'SMA', 'Sunny Central 330 UP', 16.00, 'SMA Solar'),
-- Sungrow (250-500kW)
('Onduleur 250kW', 'onduleur', 75.00, '€/kW', 250, 'Sungrow', 'SG250HX', 16.00, 'Sungrow France'),
('Onduleur 320kW', 'onduleur', 73.00, '€/kW', 320, 'Sungrow', 'SG320HX', 16.00, 'Sungrow France'),
('Onduleur 500kW', 'onduleur', 70.00, '€/kW', 500, 'Sungrow', 'SG500HX', 15.00, 'Sungrow France')
ON CONFLICT (nom_organe, categorie, marque, modele) DO UPDATE SET
    prix_unitaire_ht = EXCLUDED.prix_unitaire_ht,
    puissance_kw = EXCLUDED.puissance_kw,
    marge_commerciale_pct = EXCLUDED.marge_commerciale_pct,
    fournisseur = EXCLUDED.fournisseur,
    date_modification = CURRENT_TIMESTAMP;

-- Prix structure et fixations (complet)
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, marge_commerciale_pct, fournisseur, description) VALUES
('Rails aluminium 4.2m', 'structure', 45.00, '€/m²', 15.00, 'K2 Systems', 'Rails de montage alu anodisé'),
('Crochets toiture tuiles', 'structure', 8.50, '€/u', 15.00, 'Schletter', 'Crochets inox A4 tuiles mécaniques'),
('Crochets toiture ardoise', 'structure', 9.20, '€/u', 15.00, 'Schletter', 'Crochets inox A4 ardoise'),
('Crochets bac acier', 'structure', 12.50, '€/u', 15.00, 'K2 Systems', 'Système fixation bac acier'),
('Étanchéité EPDM', 'structure', 12.00, '€/u', 15.00, 'Würth', 'Manchon étanchéité toiture'),
('Écrous M8 inox', 'structure', 0.35, '€/u', 20.00, 'Würth', 'Écrous autofreinés inox A4'),
('Boulons M8x30 inox', 'structure', 0.45, '€/u', 20.00, 'Würth', 'Boulons tête hexagonale'),
('Collier serrage', 'structure', 1.80, '€/u', 20.00, 'K2 Systems', 'Collier fixation module'),
('Équerre renfort', 'structure', 4.50, '€/u', 15.00, 'Schletter', 'Équerre renfort structure')
ON CONFLICT (nom_organe, categorie, marque, modele) DO UPDATE SET
    prix_unitaire_ht = EXCLUDED.prix_unitaire_ht,
    marge_commerciale_pct = EXCLUDED.marge_commerciale_pct,
    fournisseur = EXCLUDED.fournisseur,
    date_modification = CURRENT_TIMESTAMP;

-- Prix câbles (toutes sections)
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, marge_commerciale_pct, fournisseur, description) VALUES
-- Câbles DC solaires
('Câble solaire 4mm²', 'cable', 2.80, '€/ml', 20.00, 'Lapp Kabel', 'Câble DC PV 1x4mm² -40°C/+90°C'),
('Câble solaire 6mm²', 'cable', 3.50, '€/ml', 20.00, 'Lapp Kabel', 'Câble DC PV 1x6mm² -40°C/+90°C'),
('Câble solaire 10mm²', 'cable', 5.20, '€/ml', 20.00, 'Lapp Kabel', 'Câble DC PV 1x10mm² -40°C/+90°C'),
('Câble solaire 16mm²', 'cable', 7.80, '€/ml', 20.00, 'Lapp Kabel', 'Câble DC PV 1x16mm² -40°C/+90°C'),
('Câble solaire 25mm²', 'cable', 11.50, '€/ml', 20.00, 'Lapp Kabel', 'Câble DC PV 1x25mm² -40°C/+90°C'),
-- Câbles AC
('Câble U1000R2V 3G6mm²', 'cable', 4.50, '€/ml', 20.00, 'Nexans', 'Câble AC 3x6mm² + terre'),
('Câble U1000R2V 3G10mm²', 'cable', 6.20, '€/ml', 20.00, 'Nexans', 'Câble AC 3x10mm² + terre'),
('Câble U1000R2V 3G16mm²', 'cable', 8.00, '€/ml', 20.00, 'Nexans', 'Câble AC 3x16mm² + terre'),
('Câble U1000R2V 3G25mm²', 'cable', 12.00, '€/ml', 20.00, 'Nexans', 'Câble AC 3x25mm² + terre'),
('Câble U1000R2V 3G35mm²', 'cable', 16.50, '€/ml', 20.00, 'Nexans', 'Câble AC 3x35mm² + terre'),
('Câble U1000R2V 3G50mm²', 'cable', 22.00, '€/ml', 20.00, 'Nexans', 'Câble AC 3x50mm² + terre'),
('Câble U1000R2V 3G70mm²', 'cable', 30.00, '€/ml', 20.00, 'Nexans', 'Câble AC 3x70mm² + terre'),
('Câble U1000R2V 3G95mm²', 'cable', 38.00, '€/ml', 20.00, 'Nexans', 'Câble AC 3x95mm² + terre'),
-- === CÂBLES AC GRANDES PUISSANCES ===
('Câble U1000R2V 3G120mm²', 'cable', 48.00, '€/ml', 18.00, 'Nexans', 'Câble AC 3x120mm² + terre'),
('Câble U1000R2V 3G150mm²', 'cable', 58.00, '€/ml', 18.00, 'Nexans', 'Câble AC 3x150mm² + terre'),
('Câble U1000R2V 3G185mm²', 'cable', 70.00, '€/ml', 18.00, 'Nexans', 'Câble AC 3x185mm² + terre'),
('Câble U1000R2V 3G240mm²', 'cable', 88.00, '€/ml', 18.00, 'Nexans', 'Câble AC 3x240mm² + terre'),
-- Câbles de terre
('Câble terre 6mm²', 'cable', 2.20, '€/ml', 20.00, 'Nexans', 'Câble cuivre nu 6mm²'),
('Câble terre 10mm²', 'cable', 3.50, '€/ml', 20.00, 'Nexans', 'Câble cuivre nu 10mm²'),
('Câble terre 16mm²', 'cable', 5.00, '€/ml', 20.00, 'Nexans', 'Câble cuivre nu 16mm²'),
('Câble terre 25mm²', 'cable', 7.50, '€/ml', 20.00, 'Nexans', 'Câble cuivre nu 25mm²'),
-- === CÂBLES TERRE GRANDES PUISSANCES ===
('Câble terre 35mm²', 'cable', 10.50, '€/ml', 18.00, 'Nexans', 'Câble cuivre nu 35mm²'),
('Câble terre 50mm²', 'cable', 14.50, '€/ml', 18.00, 'Nexans', 'Câble cuivre nu 50mm²'),
('Câble terre 70mm²', 'cable', 19.50, '€/ml', 18.00, 'Nexans', 'Câble cuivre nu 70mm²')
ON CONFLICT (nom_organe, categorie, marque, modele) DO UPDATE SET
    prix_unitaire_ht = EXCLUDED.prix_unitaire_ht,
    marge_commerciale_pct = EXCLUDED.marge_commerciale_pct,
    fournisseur = EXCLUDED.fournisseur,
    date_modification = CURRENT_TIMESTAMP;

-- Prix protections électriques (complet schéma unifilaire)
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, marge_commerciale_pct, fournisseur, description) VALUES
-- Boîtes de jonction DC
('Boîte jonction DC 2 strings', 'protection', 320.00, '€/u', 20.00, 'Weidmüller', 'Boîte DC 2 entrées IP65'),
('Boîte jonction DC 4 strings', 'protection', 450.00, '€/u', 20.00, 'Weidmüller', 'Boîte DC 4 entrées IP65'),
('Boîte jonction DC 6 strings', 'protection', 580.00, '€/u', 20.00, 'Weidmüller', 'Boîte DC 6 entrées IP65'),
('Boîte jonction DC 8 strings', 'protection', 720.00, '€/u', 20.00, 'Weidmüller', 'Boîte DC 8 entrées IP65'),
('Boîte jonction DC 12 strings', 'protection', 950.00, '€/u', 20.00, 'Weidmüller', 'Boîte DC 12 entrées IP65'),
-- Parafoudres DC
('Parafoudre DC Type II 1000V', 'protection', 250.00, '€/u', 25.00, 'Phoenix Contact', 'SPD Type 2 DC 1000V 20kA'),
('Parafoudre DC Type I+II 1500V', 'protection', 380.00, '€/u', 25.00, 'Phoenix Contact', 'SPD Type 1+2 DC 1500V 40kA'),
-- Parafoudres AC
('Parafoudre AC Type II mono', 'protection', 180.00, '€/u', 25.00, 'Schneider', 'SPD Type 2 AC 230V 20kA'),
('Parafoudre AC Type II tri', 'protection', 285.00, '€/u', 25.00, 'Schneider', 'SPD Type 2 AC 400V 40kA'),
('Parafoudre AC Type I+II tri', 'protection', 420.00, '€/u', 25.00, 'Schneider', 'SPD Type 1+2 AC 400V 65kA'),
-- Sectionneurs DC
('Sectionneur DC 32A 1000V', 'protection', 185.00, '€/u', 20.00, 'ABB', 'Sectionneur cadenassable DC 32A'),
('Sectionneur DC 63A 1000V', 'protection', 240.00, '€/u', 20.00, 'ABB', 'Sectionneur cadenassable DC 63A'),
('Sectionneur DC 125A 1000V', 'protection', 380.00, '€/u', 20.00, 'ABB', 'Sectionneur cadenassable DC 125A'),
('Sectionneur DC 160A 1000V', 'protection', 485.00, '€/u', 20.00, 'ABB', 'Sectionneur cadenassable DC 160A'),
('Sectionneur DC 250A 1500V', 'protection', 720.00, '€/u', 20.00, 'ABB', 'Sectionneur cadenassable DC 250A'),
-- Disjoncteurs AC (AGCP)
('Disjoncteur 20A C courbe', 'protection', 45.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 20A courbe C 6kA'),
('Disjoncteur 32A C courbe', 'protection', 52.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 32A courbe C 6kA'),
('Disjoncteur 40A C courbe', 'protection', 68.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 40A courbe C 10kA'),
('Disjoncteur 63A C courbe', 'protection', 95.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 63A courbe C 10kA'),
('Disjoncteur 80A C courbe', 'protection', 125.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 80A courbe C 15kA'),
('Disjoncteur 100A C courbe', 'protection', 165.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 100A courbe C 15kA'),
('Disjoncteur 125A C courbe', 'protection', 210.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 125A courbe C 25kA'),
('Disjoncteur 160A C courbe', 'protection', 280.00, '€/u', 20.00, 'Schneider', 'Disjoncteur 3P 160A courbe C 25kA'),
-- Différentiels
('Différentiel 30mA Type A 40A', 'protection', 135.00, '€/u', 20.00, 'Schneider', 'Inter diff 3P 30mA Type A 40A'),
('Différentiel 30mA Type A 63A', 'protection', 165.00, '€/u', 20.00, 'Schneider', 'Inter diff 3P 30mA Type A 63A'),
('Différentiel 300mA Type A 63A', 'protection', 220.00, '€/u', 20.00, 'Schneider', 'Inter diff 3P 300mA Type A 63A'),
('Différentiel 300mA Type A 125A', 'protection', 385.00, '€/u', 20.00, 'Schneider', 'Inter diff 3P 300mA Type A 125A'),
-- Fusibles strings
('Fusible gPV 10A', 'protection', 12.50, '€/u', 25.00, 'Mersen', 'Fusible gPV 10A 1000V DC'),
('Fusible gPV 15A', 'protection', 12.50, '€/u', 25.00, 'Mersen', 'Fusible gPV 15A 1000V DC'),
('Fusible gPV 20A', 'protection', 13.20, '€/u', 25.00, 'Mersen', 'Fusible gPV 20A 1000V DC'),
('Fusible gPV 25A', 'protection', 14.00, '€/u', 25.00, 'Mersen', 'Fusible gPV 25A 1000V DC'),
-- === FUSIBLES GRANDES PUISSANCES ===
('Fusible gPV 32A', 'protection', 15.50, '€/u', 25.00, 'Mersen', 'Fusible gPV 32A 1500V DC'),
('Fusible gPV 40A', 'protection', 17.00, '€/u', 25.00, 'Mersen', 'Fusible gPV 40A 1500V DC'),
('Fusible gPV 50A', 'protection', 19.50, '€/u', 25.00, 'Mersen', 'Fusible gPV 50A 1500V DC'),
('Fusible gPV 63A', 'protection', 22.00, '€/u', 25.00, 'Mersen', 'Fusible gPV 63A 1500V DC'),
('Fusible gPV 80A', 'protection', 26.50, '€/u', 25.00, 'Bussmann', 'Fusible gPV 80A 1500V DC'),
('Fusible gPV 100A', 'protection', 32.00, '€/u', 25.00, 'Bussmann', 'Fusible gPV 100A 1500V DC'),
-- === SECTIONNEURS DC GRANDES PUISSANCES ===
('Sectionneur DC 315A 1500V', 'protection', 950.00, '€/u', 18.00, 'Socomec', 'Sectionneur cadenassable DC 315A 1500V'),
('Sectionneur DC 400A 1500V', 'protection', 1250.00, '€/u', 18.00, 'Socomec', 'Sectionneur cadenassable DC 400A 1500V'),
('Sectionneur DC 630A 1500V', 'protection', 1850.00, '€/u', 18.00, 'Socomec', 'Sectionneur cadenassable DC 630A 1500V'),
-- === DISJONCTEURS AC GRANDES PUISSANCES ===
('Disjoncteur 200A C courbe', 'protection', 380.00, '€/u', 18.00, 'Schneider', 'Disjoncteur 3P 200A courbe C 36kA'),
('Disjoncteur 250A C courbe', 'protection', 485.00, '€/u', 18.00, 'Schneider', 'Disjoncteur 3P 250A courbe C 36kA'),
('Disjoncteur 315A C courbe', 'protection', 620.00, '€/u', 18.00, 'Schneider', 'Disjoncteur 3P 315A courbe C 50kA'),
('Disjoncteur 400A C courbe', 'protection', 820.00, '€/u', 18.00, 'Schneider', 'Disjoncteur 3P 400A courbe C 50kA'),
-- === BOÎTES DE JONCTION GRANDES PUISSANCES ===
('Boîte DC 16 strings 1500V', 'protection', 1850.00, '€/u', 20.00, 'Phoenix Contact', 'Boîte jonction 16 entrées + parafoudre'),
('Boîte DC 20 strings 1500V', 'protection', 2350.00, '€/u', 20.00, 'Phoenix Contact', 'Boîte jonction 20 entrées + parafoudre'),
('Boîte DC 24 strings 1500V', 'protection', 2850.00, '€/u', 20.00, 'Phoenix Contact', 'Boîte jonction 24 entrées + parafoudre'),
-- Coffrets et tableaux
('Coffret AC/DC petit', 'protection', 650.00, '€/u', 20.00, 'Legrand', 'Coffret pré-équipé < 50kWc'),
('Coffret AC/DC moyen', 'protection', 1200.00, '€/u', 20.00, 'Legrand', 'Coffret pré-équipé 50-100kWc'),
('Coffret AC/DC grand', 'protection', 2400.00, '€/u', 20.00, 'Legrand', 'Coffret pré-équipé > 100kWc'),
('TGBT 18 modules', 'protection', 280.00, '€/u', 15.00, 'Schneider', 'Tableau Gamma 18 modules'),
('TGBT 36 modules', 'protection', 420.00, '€/u', 15.00, 'Schneider', 'Tableau Gamma 36 modules'),
-- Compteurs et monitoring
('Compteur énergie MID', 'protection', 185.00, '€/u', 20.00, 'Carlo Gavazzi', 'Compteur triphasé certifié MID'),
('Box monitoring', 'protection', 450.00, '€/u', 25.00, 'Huawei', 'SmartLogger 3000A avec 4G'),
-- === TRANSFORMATEURS HTA (pour installations >1MWc) ===
('Transformateur HTA/BT 250kVA', 'protection', 12500.00, '€/u', 15.00, 'Schneider', 'Transformateur 20kV/400V 250kVA huile'),
('Transformateur HTA/BT 400kVA', 'protection', 18500.00, '€/u', 15.00, 'Schneider', 'Transformateur 20kV/400V 400kVA huile'),
('Transformateur HTA/BT 630kVA', 'protection', 24500.00, '€/u', 15.00, 'Schneider', 'Transformateur 20kV/400V 630kVA huile'),
('Transformateur HTA/BT 800kVA', 'protection', 29500.00, '€/u', 15.00, 'Schneider', 'Transformateur 20kV/400V 800kVA huile'),
('Transformateur HTA/BT 1000kVA', 'protection', 35500.00, '€/u', 15.00, 'Schneider', 'Transformateur 20kV/400V 1000kVA huile'),
('Cellule HTA arrivée', 'protection', 8500.00, '€/u', 15.00, 'Schneider', 'Cellule HTA arrivée 20kV 630A'),
('Cellule HTA protection', 'protection', 11500.00, '€/u', 15.00, 'Schneider', 'Cellule HTA protection 20kV 630A + disjoncteur'),
('Cellule HTA départ', 'protection', 9500.00, '€/u', 15.00, 'Schneider', 'Cellule HTA départ 20kV 630A'),
('Poste préfabriqué béton 250kVA', 'protection', 45000.00, '€/u', 12.00, 'Cahors', 'Poste préfabriqué béton complet 250kVA'),
('Poste préfabriqué béton 630kVA', 'protection', 65000.00, '€/u', 12.00, 'Cahors', 'Poste préfabriqué béton complet 630kVA'),
('Poste préfabriqué béton 1000kVA', 'protection', 85000.00, '€/u', 12.00, 'Cahors', 'Poste préfabriqué béton complet 1000kVA')
ON CONFLICT (nom_organe, categorie, marque, modele) DO UPDATE SET
    prix_unitaire_ht = EXCLUDED.prix_unitaire_ht,
    marge_commerciale_pct = EXCLUDED.marge_commerciale_pct,
    fournisseur = EXCLUDED.fournisseur,
    date_modification = CURRENT_TIMESTAMP;

-- Composants de mise à la terre
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, marge_commerciale_pct, fournisseur, description) VALUES
('Piquet de terre acier 1.5m', 'terre', 18.00, '€/u', 20.00, 'Legrand', 'Piquet terre acier cuivré 1.5m'),
('Piquet de terre acier 2m', 'terre', 24.00, '€/u', 20.00, 'Legrand', 'Piquet terre acier cuivré 2m'),
('Barrette de mesure terre', 'terre', 32.00, '€/u', 20.00, 'Schneider', 'Barrette coupure + mesure terre'),
('Cosse de masse structure', 'terre', 4.50, '€/u', 25.00, 'K2 Systems', 'Cosse équipotentielle structure'),
('Conducteur cuivre nu 25mm²', 'terre', 7.50, '€/ml', 20.00, 'Nexans', 'Conducteur cuivre nu 25mm²'),
('Conducteur cuivre nu 35mm²', 'terre', 10.00, '€/ml', 20.00, 'Nexans', 'Conducteur cuivre nu 35mm²'),
('Borne connexion terre', 'terre', 12.50, '€/u', 20.00, 'Legrand', 'Borne de connexion terre modulaire')
ON CONFLICT (nom_organe, categorie, marque, modele) DO UPDATE SET prix_unitaire_ht = EXCLUDED.prix_unitaire_ht, marge_commerciale_pct = EXCLUDED.marge_commerciale_pct, date_modification = CURRENT_TIMESTAMP;

-- Batteries de stockage (optionnel)
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, puissance_kw, marge_commerciale_pct, fournisseur, description) VALUES
('Batterie Lithium 5kWh', 'batterie', 1100.00, '€/kWh', 5, 22.00, 'Huawei', 'LUNA2000-5-S0 Li-ion'),
('Batterie Lithium 10kWh', 'batterie', 950.00, '€/kWh', 10, 22.00, 'Huawei', 'LUNA2000-10-S0 Li-ion'),
('Batterie Lithium 15kWh', 'batterie', 900.00, '€/kWh', 15, 22.00, 'Huawei', 'LUNA2000-15-S0 Li-ion'),
('Batterie Lithium 20kWh', 'batterie', 875.00, '€/kWh', 20, 22.00, 'BYD', 'BYD Battery-Box Premium HVS'),
('Batterie Lithium 30kWh', 'batterie', 850.00, '€/kWh', 30, 22.00, 'BYD', 'BYD Battery-Box Premium HVM'),
('Onduleur hybride 10kW', 'onduleur', 185.00, '€/kW', 10, 20.00, 'Huawei', 'SUN2000-10KTL-M1 Hybrid'),
('Onduleur hybride 15kW', 'onduleur', 175.00, '€/kW', 15, 20.00, 'Huawei', 'SUN2000-15KTL-M2 Hybrid')
ON CONFLICT (nom_organe, categorie, marque, modele) DO UPDATE SET prix_unitaire_ht = EXCLUDED.prix_unitaire_ht, marge_commerciale_pct = EXCLUDED.marge_commerciale_pct, date_modification = CURRENT_TIMESTAMP;

-- Main d'œuvre
INSERT INTO parametrage_main_oeuvre (type_prestation, tarif_horaire_ht, nb_heures_unitaire, description, competence_requise) VALUES
('Pose modules', 65.00, 0.25, 'Installation et fixation module photovoltaïque', 'couvreur'),
('Câblage DC', 75.00, 0.15, 'Câblage côté continu (strings)', 'electricien'),
('Raccordement onduleur', 75.00, 2.50, 'Installation et raccordement onduleur', 'electricien'),
('Raccordement AC', 75.00, 4.00, 'Raccordement au tableau électrique', 'electricien'),
('Mise en service', 85.00, 3.00, 'Tests, réglages, mise en service', 'electricien')
ON CONFLICT DO NOTHING;

-- =====================================================
-- INDEX POUR PERFORMANCES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_prix_organes_categorie ON parametrage_prix_organes(categorie);
CREATE INDEX IF NOT EXISTS idx_prix_organes_actif ON parametrage_prix_organes(actif);
CREATE INDEX IF NOT EXISTS idx_main_oeuvre_actif ON parametrage_main_oeuvre(actif);

-- =====================================================
-- COMMENTAIRES
-- =====================================================

COMMENT ON TABLE parametrage_entreprise IS 'Configuration entreprise: logo, coordonnées, certifications pour génération PDF';
COMMENT ON TABLE parametrage_prix_organes IS 'Prix unitaires de tous les composants PV pour calculs dynamiques devis';
COMMENT ON TABLE parametrage_main_oeuvre IS 'Tarifs main d''œuvre par type de prestation';
