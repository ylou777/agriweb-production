-- Migration pour ajouter les colonnes OSM à la table agriweb_prospects
-- À exécuter dans la console Railway PostgreSQL

-- Vérifier si la table existe
DO $$ 
BEGIN
    -- Ajouter osm_amenity
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' AND column_name = 'osm_amenity'
    ) THEN
        ALTER TABLE agriweb_prospects ADD COLUMN osm_amenity TEXT;
        RAISE NOTICE 'Colonne osm_amenity créée';
    ELSE
        RAISE NOTICE 'Colonne osm_amenity existe déjà';
    END IF;

    -- Ajouter osm_shop
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' AND column_name = 'osm_shop'
    ) THEN
        ALTER TABLE agriweb_prospects ADD COLUMN osm_shop TEXT;
        RAISE NOTICE 'Colonne osm_shop créée';
    ELSE
        RAISE NOTICE 'Colonne osm_shop existe déjà';
    END IF;

    -- Ajouter osm_building
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' AND column_name = 'osm_building'
    ) THEN
        ALTER TABLE agriweb_prospects ADD COLUMN osm_building TEXT;
        RAISE NOTICE 'Colonne osm_building créée';
    ELSE
        RAISE NOTICE 'Colonne osm_building existe déjà';
    END IF;

    -- Ajouter osm_landuse
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' AND column_name = 'osm_landuse'
    ) THEN
        ALTER TABLE agriweb_prospects ADD COLUMN osm_landuse TEXT;
        RAISE NOTICE 'Colonne osm_landuse créée';
    ELSE
        RAISE NOTICE 'Colonne osm_landuse existe déjà';
    END IF;

    -- Ajouter osm_office
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' AND column_name = 'osm_office'
    ) THEN
        ALTER TABLE agriweb_prospects ADD COLUMN osm_office TEXT;
        RAISE NOTICE 'Colonne osm_office créée';
    ELSE
        RAISE NOTICE 'Colonne osm_office existe déjà';
    END IF;

    -- Ajouter osm_industrial
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' AND column_name = 'osm_industrial'
    ) THEN
        ALTER TABLE agriweb_prospects ADD COLUMN osm_industrial TEXT;
        RAISE NOTICE 'Colonne osm_industrial créée';
    ELSE
        RAISE NOTICE 'Colonne osm_industrial existe déjà';
    END IF;

END $$;

-- Vérifier que les colonnes ont été créées
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'agriweb_prospects' 
AND column_name LIKE 'osm_%'
ORDER BY column_name;
