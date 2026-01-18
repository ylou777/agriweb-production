"""
GUIDE D'IMPLÉMENTATION - ISOLATION DES DONNÉES PAR UTILISATEUR
================================================================

Ce guide explique comment mettre en place l'isolation des données pour que 
chaque utilisateur ne voie que ses propres prospects et projets.

ÉTAPE 1: MIGRATION DE LA BASE DE DONNÉES
-----------------------------------------
Exécuter le script de migration pour ajouter la colonne user_id:

    python migrate_add_user_isolation.py

Ce script va:
- Ajouter la colonne user_id à agriweb_prospects
- Assigner les prospects existants à un utilisateur par défaut
- Créer une contrainte foreign key vers la table users

ÉTAPE 2: MODIFICATIONS DU CODE
-------------------------------

### 2.1. Routes GET - Filtrage par utilisateur

✅ DÉJÀ FAIT:
- /api/crm/prospects : Filtre par user_id
- /api/crm/prospects/<id> : Vérifie la propriété

À FAIRE:
- /api/crm/dashboard/stats : Filtrer les stats par user_id
- /api/crm/stats : Filtrer les stats par user_id

### 2.2. Routes INSERT - Ajout automatique du user_id

POUR CHAQUE ROUTE QUI CRÉE UN PROSPECT, MODIFIER:

Avant (ligne ~514 dans crm_routes.py):
```python
result = execute_query('''
    INSERT INTO agriweb_prospects (
        type, commune, departement, ...
    ) VALUES (%s, %s, %s, ...)
```

Après:
```python
user_id = get_current_user_id()  # Fonction helper déjà créée
if not user_id:
    return jsonify({'success': False, 'error': 'Authentification requise'}), 401

result = execute_query('''
    INSERT INTO agriweb_prospects (
        user_id, type, commune, departement, ...
    ) VALUES (%s, %s, %s, %s, ...)
''', (user_id, 'parking', parking.get('commune'), ...))
```

ROUTES À MODIFIER:
1. /api/crm/export-to-prospects (ligne ~460)
   - 4 INSERT statements: parkings, toitures, friches, RPG
   
2. /api/crm/prospects/<id> PUT (ligne ~755)
   - Vérifier que prospect appartient à l'utilisateur avant update
   
3. /api/crm/prospects/<id> DELETE (ligne ~1105)
   - Vérifier que prospect appartient à l'utilisateur avant delete

### 2.3. Routes UPDATE et DELETE - Vérification propriété

Pour chaque UPDATE ou DELETE, ajouter:

```python
user_id = get_current_user_id()
if not user_id:
    return jsonify({'success': False, 'error': 'Authentification requise'}), 401

# Vérifier que le prospect appartient bien à cet utilisateur
check = execute_query(
    'SELECT id FROM agriweb_prospects WHERE id = %s AND user_id = %s',
    (prospect_id, user_id),
    fetch_one=True
)
if not check:
    return jsonify({'success': False, 'error': 'Accès refusé'}), 403
```

ÉTAPE 3: TESTS
--------------

1. Créer deux comptes utilisateurs:
   - user1@test.com
   - user2@test.com

2. Se connecter avec user1:
   - Créer quelques prospects
   - Vérifier qu'on les voit dans /crm

3. Se connecter avec user2:
   - Vérifier qu'on NE voit PAS les prospects de user1
   - Créer ses propres prospects
   - Vérifier qu'ils sont bien isolés

4. Tester les accès directs:
   - Se connecter avec user2
   - Essayer d'accéder à /api/crm/prospects/<id_de_user1>
   - Devrait retourner 404 ou 403

ÉTAPE 4: STATISTIQUES
---------------------

Mettre à jour les routes de statistiques pour filtrer par user:

### /api/crm/stats
```python
stats = execute_query('''
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN statut = 'nouveau' THEN 1 END) as nouveau,
        ...
    FROM agriweb_prospects
    WHERE user_id = %s
''', (user_id,), fetch_one=True)
```

### /api/crm/dashboard/stats
```python
# KPIs filtré par utilisateur
total_prospects = execute_query('''
    SELECT COUNT(*) as count 
    FROM agriweb_prospects 
    WHERE user_id = %s
''', (user_id,), fetch_one=True)
```

ÉTAPE 5: SÉCURITÉ RENFORCÉE
----------------------------

1. Middleware de vérification:
   - S'assurer que request.current_user est toujours défini
   - Rejeter les requêtes sans authentification

2. Logs d'audit:
   - Logger les tentatives d'accès non autorisé
   - Alerter en cas d'accès suspect

3. Frontend:
   - Cacher les prospects dans les filtres de recherche
   - Ne montrer que les données autorisées

ÉTAPE 6: RÔLE ADMINISTRATEUR
----------------------------

✅ DÉJÀ IMPLÉMENTÉ:

Les administrateurs (role='admin' ou is_admin=true) peuvent voir TOUS les prospects :

### Routes avec accès admin global:

1. **GET /api/crm/prospects**
   - Admin : Voit TOUS les prospects de TOUS les utilisateurs + email/nom du propriétaire
   - User : Voit uniquement ses propres prospects

2. **GET /api/crm/stats**
   - Admin : Statistiques globales (tous prospects)
   - User : Statistiques personnelles uniquement

3. **GET /api/crm/dashboard/stats**
   - Admin : KPIs globaux
   - User : KPIs personnels

### Code de vérification admin:

```python
def is_current_user_admin():
    """Vérifie si l'utilisateur connecté est un administrateur"""
    from flask import request
    current_user = getattr(request, 'current_user', None)
    if current_user:
        return (
            current_user.get('is_admin') == True or 
            current_user.get('is_admin') == 1 or
            current_user.get('role') == 'admin'
        )
    return False
```

### Exemple d'utilisation:

```python
if is_current_user_admin():
    # Admin voit TOUT
    prospects = execute_query('''
        SELECT p.*, u.email as user_email, u.name as user_name
        FROM agriweb_prospects p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.date_creation DESC
    ''', fetch_all=True)
else:
    # User normal voit uniquement ses données
    prospects = execute_query('''
        SELECT * FROM agriweb_prospects 
        WHERE user_id = %s
        ORDER BY date_creation DESC
    ''', (user_id,), fetch_all=True)
```

### Avantages:
✅ Sunstice (admin) supervise tous les projets
✅ Support client facilité
✅ Audit et conformité
✅ Statistiques globales disponibles

ÉTAPE 7: COMPATIBILITÉ SUNSTICE
--------------------------------

Pour Sunstice qui veut voir TOUS les prospects de TOUS les clients:

Option A - Rôle "super_admin":
```python
user_id = get_current_user_id()
current_user = getattr(request, 'current_user', None)
is_sunstice = current_user.get('email') in ['admin@sunstice.fr', ...]

if is_sunstice:
    # Sunstice voit TOUT
    prospects = execute_query('''
        SELECT * FROM agriweb_prospects 
        ORDER BY date_creation DESC
    ''', fetch_all=True)
else:
    # Utilisateurs normaux voient uniquement leurs données
    prospects = execute_query('''
        SELECT * FROM agriweb_prospects 
        WHERE user_id = %s
        ORDER BY date_creation DESC
    ''', (user_id,), fetch_all=True)
```

Option B - Colonne "shared_with_sunstice":
```python
# Ajouter colonne booléenne
ALTER TABLE agriweb_prospects ADD COLUMN shared_with_sunstice BOOLEAN DEFAULT TRUE;

# Sunstice voit seulement les prospects partagés
prospects = execute_query('''
    SELECT * FROM agriweb_prospects 
    WHERE shared_with_sunstice = TRUE
    ORDER BY date_creation DESC
''', fetch_all=True)
```

RÉSUMÉ DES FICHIERS MODIFIÉS
-----------------------------

✅ CRÉÉS:
- migrate_add_user_isolation.py : Script de migration
- GUIDE_ISOLATION_UTILISATEURS.py : Ce guide

✅ MODIFIÉS:
- crm_routes.py:
  * get_current_user_id() : Fonction helper (ligne ~20)
  * get_prospects() : Filtrage par user_id (ligne ~688)
  * get_prospect() : Vérification propriété (ligne ~727)

⚠️ À MODIFIER:
- crm_routes.py:
  * export_to_prospects() : 4 INSERT à modifier (ligne ~460)
  * update_prospect() : Vérifier propriété (ligne ~755)
  * delete_prospect() : Vérifier propriété (ligne ~1105)
  * crm_stats() : Filtrer stats (ligne ~165)
  * get_dashboard_stats() : Filtrer stats (ligne ~201)

COMMANDES RAPIDES
-----------------

1. Exécuter la migration:
   python migrate_add_user_isolation.py

2. Redémarrer Flask:
   python run_app.py

3. Tester:
   # Se connecter et créer des prospects
   curl -X POST http://localhost:5000/login -d "email=test@test.com&password=test123"
   curl http://localhost:5000/api/crm/prospects

NOTES IMPORTANTES
-----------------

⚠️  SÉCURITÉ: Ne JAMAIS supprimer les filtres user_id une fois en place
⚠️  RGPD: Cette isolation garantit la conformité RGPD
✅  PERFORMANCE: Ajouter un index sur agriweb_prospects.user_id pour les requêtes rapides

INDEX RECOMMANDÉ:
CREATE INDEX idx_prospects_user_id ON agriweb_prospects(user_id);
CREATE INDEX idx_prospects_user_created ON agriweb_prospects(user_id, date_creation DESC);

SUPPORT
-------
En cas de problème, vérifier:
1. La colonne user_id existe dans agriweb_prospects
2. La table users existe et contient des utilisateurs
3. request.current_user est bien défini après authentification
4. Les logs montrent le user_id dans les requêtes
"""

if __name__ == "__main__":
    print(__doc__)
