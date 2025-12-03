-- Migration pour ajouter la colonne proprietaires à la table agriweb_prospects
-- À exécuter dans la console Railway PostgreSQL

-- Ajouter la colonne proprietaires (JSONB pour stocker la liste des propriétaires)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agriweb_prospects' AND column_name = 'proprietaires_json'
    ) THEN
        ALTER TABLE agriweb_prospects ADD COLUMN proprietaires_json JSONB;
        RAISE NOTICE 'Colonne proprietaires_json créée';
    ELSE
        RAISE NOTICE 'Colonne proprietaires_json existe déjà';
    END IF;
END $$;

-- Vérifier que la colonne a été créée
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'agriweb_prospects' 
AND column_name = 'proprietaires_json';

-- Note: Cette colonne stockera un tableau JSON de propriétaires avec la structure:
-- [
--   {
--     "nom": "SCI EXEMPLE",
--     "adresse": "123 Rue de Paris 75001 PARIS",
--     "commune": "Nice",
--     "code_commune": "06088",
--     "reference_parcelle": "AB0123",
--     "section": "AB",
--     "numero_parcelle": "0123"
--   }
-- ]
