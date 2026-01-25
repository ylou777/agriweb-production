-- Table pour stocker les données de consommation électrique Enedis
-- Source: https://opendata.enedis.fr/datasets/consommation-annuelle-entreprise-par-adresse

CREATE TABLE IF NOT EXISTS consommation_enedis (
    id SERIAL PRIMARY KEY,
    annee INTEGER,
    code_iris VARCHAR(50),
    nom_iris VARCHAR(255),
    numero_de_voie VARCHAR(50),
    indice_de_repetition VARCHAR(10),
    type_de_voie VARCHAR(50),
    libelle_de_voie VARCHAR(255),
    adresse VARCHAR(500),
    nombre_de_sites INTEGER,
    consommation_annuelle_totale_mwh NUMERIC(10, 3),
    code_grand_secteur VARCHAR(50),
    code_categorie_consommation VARCHAR(10),
    code_secteur_naf2 VARCHAR(10),
    code_commune VARCHAR(10),
    nom_commune VARCHAR(255),
    code_epci VARCHAR(20),
    code_departement VARCHAR(5),
    code_region VARCHAR(5),
    tri_des_adresses INTEGER,
    
    -- Coordonnées GPS (sera rempli par géocodage) - Alternative à PostGIS
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    geocoded BOOLEAN DEFAULT FALSE,
    
    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les recherches fréquentes
CREATE INDEX IF NOT EXISTS idx_enedis_commune ON consommation_enedis(code_commune);
CREATE INDEX IF NOT EXISTS idx_enedis_annee ON consommation_enedis(annee);
CREATE INDEX IF NOT EXISTS idx_enedis_consommation ON consommation_enedis(consommation_annuelle_totale_mwh DESC);
CREATE INDEX IF NOT EXISTS idx_enedis_secteur ON consommation_enedis(code_grand_secteur);
CREATE INDEX IF NOT EXISTS idx_enedis_coords ON consommation_enedis(latitude, longitude) WHERE latitude IS NOT NULL;

-- Index composite pour recherche par commune et année
CREATE INDEX IF NOT EXISTS idx_enedis_commune_annee ON consommation_enedis(code_commune, annee DESC);

-- Commentaires
COMMENT ON TABLE consommation_enedis IS 'Consommation électrique annuelle des entreprises par adresse (source: Enedis Open Data)';
COMMENT ON COLUMN consommation_enedis.consommation_annuelle_totale_mwh IS 'Consommation en MWh - clé pour dimensionner installations PV';
COMMENT ON COLUMN consommation_enedis.code_grand_secteur IS 'AGRICULTURE, INDUSTRIE, TERTIAIRE, etc.';
COMMENT ON COLUMN consommation_enedis.latitude IS 'Latitude GPS obtenue par géocodage (WGS84)';
COMMENT ON COLUMN consommation_enedis.longitude IS 'Longitude GPS obtenue par géocodage (WGS84)';
