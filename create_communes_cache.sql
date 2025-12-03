-- Script pour créer une table de cache commune → code_insee
-- et peupler avec les données de l'API Geo.gouv.fr

-- 1. Créer la table de cache
CREATE TABLE IF NOT EXISTS communes_insee_cache (
    id SERIAL PRIMARY KEY,
    nom_commune VARCHAR(255) NOT NULL,
    nom_commune_lower VARCHAR(255) NOT NULL,  -- Pour recherche insensible à la casse
    code_insee VARCHAR(5) NOT NULL,
    code_departement VARCHAR(3),
    nom_complet TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nom_commune_lower, code_insee)
);

-- Index pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_communes_nom_lower ON communes_insee_cache(nom_commune_lower);
CREATE INDEX IF NOT EXISTS idx_communes_insee ON communes_insee_cache(code_insee);

-- 2. Fonction pour géocoder une commune (appellera l'API Geo.gouv.fr via extension plpython3u si disponible)
-- Sinon, on peuplera la table via Python

-- 3. Fonction pour obtenir le code INSEE d'une commune depuis le cache
CREATE OR REPLACE FUNCTION get_code_insee_from_commune(p_commune VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_code_insee VARCHAR(5);
BEGIN
    IF p_commune IS NULL OR p_commune = '' THEN
        RETURN NULL;
    END IF;
    
    -- Rechercher dans le cache (insensible à la casse)
    SELECT code_insee INTO v_code_insee
    FROM communes_insee_cache
    WHERE nom_commune_lower = LOWER(TRIM(p_commune))
    LIMIT 1;
    
    RETURN v_code_insee;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE communes_insee_cache IS 'Cache des correspondances nom_commune → code_insee pour éviter les appels API répétés';
COMMENT ON FUNCTION get_code_insee_from_commune IS 'Retourne le code INSEE d''une commune depuis le cache';
