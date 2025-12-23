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

-- Prix modules photovoltaïques
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, puissance_wc, marque, modele, marge_commerciale_pct) VALUES
('Module PV 550Wc', 'module', 0.32, '€/Wc', 550, 'JA Solar', 'JAM72S30-550/MR', 15.00),
('Module PV 600Wc', 'module', 0.30, '€/Wc', 600, 'JA Solar', 'JAM72S30-600/MR', 15.00),
('Module PV 665Wc', 'module', 0.28, '€/Wc', 665, 'Longi', 'LR5-72HIH-665M', 15.00)
ON CONFLICT (nom_organe, categorie, marque, modele) DO NOTHING;

-- Prix onduleurs
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, puissance_kw, marque, modele, marge_commerciale_pct) VALUES
('Onduleur 25kW', 'onduleur', 100.00, '€/kW', 25, 'Huawei', 'SUN2000-25KTL-M3', 18.00),
('Onduleur 50kW', 'onduleur', 90.00, '€/kW', 50, 'Huawei', 'SUN2000-50KTL-M3', 18.00),
('Onduleur 100kW', 'onduleur', 80.00, '€/kW', 100, 'Huawei', 'SUN2000-100KTL-M3', 18.00),
('Onduleur 25kW', 'onduleur', 105.00, '€/kW', 25, 'SMA', 'Sunny Tripower CORE1', 18.00)
ON CONFLICT (nom_organe, categorie, marque, modele) DO NOTHING;

-- Prix structure et fixations
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, marge_commerciale_pct) VALUES
('Rails aluminium', 'structure', 45.00, '€/m²', 15.00),
('Crochets toiture', 'structure', 8.50, '€/u', 15.00),
('Étanchéité EPDM', 'structure', 12.00, '€/u', 15.00)
ON CONFLICT (nom_organe, categorie, marque, modele) DO NOTHING;

-- Prix câbles
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, marge_commerciale_pct) VALUES
('Câble solaire 6mm²', 'cable', 3.50, '€/ml', 20.00),
('Câble U1000R2V 3G16mm²', 'cable', 8.00, '€/ml', 20.00),
('Câble U1000R2V 3G25mm²', 'cable', 12.00, '€/ml', 20.00)
ON CONFLICT (nom_organe, categorie, marque, modele) DO NOTHING;

-- Prix protections électriques
INSERT INTO parametrage_prix_organes (nom_organe, categorie, prix_unitaire_ht, unite, marge_commerciale_pct) VALUES
('Coffret AC/DC', 'protection', 850.00, '€/u', 20.00),
('Parafoudre DC Type II', 'protection', 250.00, '€/u', 25.00),
('Parafoudre AC Type II', 'protection', 180.00, '€/u', 25.00),
('Sectionneur DC', 'protection', 320.00, '€/u', 20.00),
('Disjoncteur 63A', 'protection', 145.00, '€/u', 20.00)
ON CONFLICT (nom_organe, categorie, marque, modele) DO NOTHING;

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
