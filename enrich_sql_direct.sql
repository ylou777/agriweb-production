-- Script SQL direct pour enrichir les prospects
-- Enrichir 100 prospects en une requête

UPDATE agriweb_prospects ap
SET 
    proprietaire_siren = pp.siren,
    proprietaire_denomination = pp.denomination,
    proprietaire_forme_juridique = pp.forme_juridique,
    proprietaire_enrichi_date = NOW()
FROM (
    SELECT DISTINCT ON (ap2.id)
        ap2.id as prospect_id,
        pp2.siren,
        pp2.denomination,
        pp2.forme_juridique
    FROM agriweb_prospects ap2
    CROSS JOIN LATERAL (
        SELECT 
            (ap2.parcelles_cadastrales::jsonb->0->>'section') as section,
            LPAD(ap2.parcelles_cadastrales::jsonb->0->>'numero', 4, '0') as numero
    ) parcelle_info
    JOIN proprietaires_parcelles pp2 ON (
        (pp2.code_commune = get_code_insee_from_commune(ap2.commune) 
         OR pp2.code_insee = get_code_insee_from_commune(ap2.commune))
        AND pp2.section = parcelle_info.section
        AND pp2.numero = parcelle_info.numero
        AND pp2.siren IS NOT NULL
    )
    WHERE ap2.parcelles_cadastrales IS NOT NULL
      AND ap2.parcelles_cadastrales NOT IN ('', '[]')
      AND ap2.proprietaire_siren IS NULL
    LIMIT 100
) pp
WHERE ap.id = pp.prospect_id;

-- Afficher les stats
SELECT 
    COUNT(*) as total_parcelles,
    COUNT(proprietaire_siren) as avec_siren,
    ROUND(COUNT(proprietaire_siren)::numeric / COUNT(*)::numeric * 100, 1) as pourcentage
FROM agriweb_prospects
WHERE parcelles_cadastrales IS NOT NULL 
  AND parcelles_cadastrales NOT IN ('', '[]');
