# 📤 GUIDE : Upload des propriétaires MAJIC sur Railway

## ✅ Ce qui a été fait

1. **18,740,957 parcelles importées** dans SQLite local
   - Fichier: `C:\Users\Utilisateur\Desktop\AG32.1\proprietaires_parcelles.db`
   - Taille: ~1.5 GB
   - 97 départements couverts

2. **Scripts créés**:
   - `import_proprietaires_to_railway.py` - Import SQLite → PostgreSQL Railway
   - `proprietaires_utils_railway.py` - Fonctions de recherche (compatible Railway + local)

## 📋 Étapes pour déployer sur Railway

### Étape 1: Uploader le fichier SQLite sur Railway

**Option A - Via Railway CLI** (recommandé):
```powershell
# Installer Railway CLI si pas déjà fait
npm install -g @railway/cli

# Se connecter
railway login

# Uploader le fichier dans votre projet
railway up proprietaires_parcelles.db
```

**Option B - Via interface Railway**:
1. Aller sur railway.app → Votre projet
2. Settings → Volumes → Create Volume
3. Uploader `proprietaires_parcelles.db`

### Étape 2: Exécuter l'import depuis Railway Shell

```bash
# Se connecter au shell Railway
railway shell

# Installer dépendances si nécessaire
pip install psycopg2-binary tqdm

# Lancer l'import (prend ~30-60 minutes)
python import_proprietaires_to_railway.py

# L'import affichera la progression et créera la table avec index
```

### Étape 3: Vérifier l'import

Sur Railway Shell:
```bash
railway shell

# Vérifier la table
python -c "
import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM proprietaires_parcelles')
print(f'Total: {cur.fetchone()[0]:,} parcelles')
cur.execute('SELECT COUNT(DISTINCT departement) FROM proprietaires_parcelles')
print(f'Départements: {cur.fetchone()[0]}')
conn.close()
"
```

### Étape 4: Intégrer dans votre CRM

1. **Copier le fichier utils**:
   ```bash
   # Dans votre dossier AgriWeb-Railway-Deploy
   cp proprietaires_utils_railway.py proprietaires_utils.py
   ```

2. **Importer dans crm_routes.py**:
   ```python
   from proprietaires_utils import get_proprietaires_by_parcelle, check_proprietaires_table_exists
   ```

3. **Ajouter une route API**:
   ```python
   @app.route('/api/crm/prospect/<int:prospect_id>/proprietaires')
   def get_prospect_proprietaires(prospect_id):
       # Récupérer le prospect
       prospect = execute_query(
           "SELECT code_insee, parcelles_cadastrales FROM agriweb_prospects WHERE id = %s",
           (prospect_id,),
           fetch_one=True
       )
       
       if not prospect or not prospect['parcelles_cadastrales']:
           return jsonify({'proprietaires': []})
       
       # Parser les parcelles (format: "AB 123, CD 456")
       proprietaires = []
       for parcelle in prospect['parcelles_cadastrales'].split(','):
           parts = parcelle.strip().split()
           if len(parts) >= 2:
               section = parts[0]
               numero = parts[1]
               proprios = get_proprietaires_by_parcelle(
                   prospect['code_insee'], 
                   section, 
                   numero
               )
               proprietaires.extend(proprios)
       
       return jsonify({'proprietaires': proprietaires})
   ```

4. **Afficher dans le frontend** (templates/crm_web.html):
   ```javascript
   // Dans displayModalRapport(), après les infos GPS
   
   // Récupérer les propriétaires
   fetch(`/api/crm/prospect/${prospectId}/proprietaires`)
       .then(r => r.json())
       .then(data => {
           if (data.proprietaires && data.proprietaires.length > 0) {
               let html = '<h3>🏢 Propriétaires des parcelles</h3><ul>';
               data.proprietaires.forEach(p => {
                   html += `<li><strong>${p.denomination}</strong>`;
                   if (p.siren) html += ` (SIREN: ${p.siren})`;
                   html += ` - ${p.surface_ha} ha</li>`;
               });
               html += '</ul>';
               document.getElementById('proprietaires-section').innerHTML = html;
           }
       });
   ```

## 🎯 Résultat attendu

Dans vos rapports de prospects, vous verrez :

```
🏢 Propriétaires des parcelles

- COMMUNE DE L ABERGEMENT-CLEMENCIAT (SIREN: 210100012) - 21.49 ha
- SCP SOCIETE CIVILE AGRICOLE DU CHENE AUGER (SIREN: 387955222) - 12.52 ha
- GROUPEMENT FORESTIER DE L ORDRE - 8.53 ha
```

## ⚠️ Notes importantes

1. **Taille de la base**: 18.7M de lignes → Railway PostgreSQL gratuit limité à 1GB
   - Considérez Railway Pro si dépassement
   - Ou filtrez par région (départements PACA uniquement par exemple)

2. **Performance**: Les index sont créés automatiquement pour recherche rapide

3. **Maintenance**: La base MAJIC est mise à jour annuellement par l'État
   - Vous devrez re-importer les nouvelles données chaque année

## 🆘 Dépannage

**Problème**: Railway timeout durant l'import
- **Solution**: Augmentez le batch_size dans le script (default: 50000)

**Problème**: Table existe déjà
- **Solution**: Le script fait automatiquement `DROP TABLE IF EXISTS`

**Problème**: Manque de mémoire Railway
- **Solution**: Filtrez par départements avant import (modifiez la requête SQLite)

## 📞 Support

Si vous rencontrez des problèmes, vérifiez :
1. `DATABASE_URL` est bien définie sur Railway
2. Le fichier SQLite est bien uploadé et accessible
3. Les dépendances Python sont installées (psycopg2-binary, tqdm)
