-- Tables supplémentaires pour les fonctionnalités Helia CRM avancées
-- À exécuter sur Railway PostgreSQL

-- Table pour les notes sur les prospects
CREATE TABLE IF NOT EXISTS prospect_notes (
    id SERIAL PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES agriweb_prospects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    note_text TEXT NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_prospect_notes_prospect_id ON prospect_notes(prospect_id);
CREATE INDEX IF NOT EXISTS idx_prospect_notes_date ON prospect_notes(date_creation DESC);

-- Commentaires
COMMENT ON TABLE prospect_notes IS 'Notes et commentaires ajoutés aux prospects CRM';
COMMENT ON COLUMN prospect_notes.prospect_id IS 'Référence au prospect concerné';
COMMENT ON COLUMN prospect_notes.note_text IS 'Contenu de la note';
