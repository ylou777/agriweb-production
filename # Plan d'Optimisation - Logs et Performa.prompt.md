# Plan d'Optimisation - Logs et Performance de Recherche

## Diagnostic

**Problème identifié:** Milliers de logs dans la console qui ralentissent considérablement les recherches.

**Analyse du code:**
- Plus de 200+ instructions `print()` actives dans le fichier principal (16,210 lignes)
- Logs dans des boucles et fonctions appelées fréquemment
- Logs détaillés pour chaque étape de recherche (GeoRisques, OSM, parcelles, etc.)
- Formatage de strings coûteux même quand commenté (f-strings)

## Impact sur les performances

### 1. **Ralentissement par les logs**
   - Chaque `print()` = opération I/O bloquante
   - Formatage de strings (f-strings) même pour logs commentés
   - Accumulation dans la console = utilisation mémoire
   - Dans les boucles = impact exponentiel

### 2. **Logs identifiés comme critiques** (à désactiver en priorité)
   - `log_search_start()` - Lignes 61-69 (6 print actifs)
   - `log_data_collection()` - Ligne 76
   - GeoRisques API (lignes 234-380) - ~20 prints
   - Bâtiments OSM (lignes 4400-4659) - ~15 prints  
   - Friches (lignes 4269-4292) - ~10 prints
   - Capacités réseau (lignes 4177-4201) - ~7 prints
   - Parcelles RPG (lignes 4225-4232) - ~5 prints

### 3. **Logs déjà optimisés** (commentés mais toujours coûteux)
   - Beaucoup de logs commentés avec `# Optimisé pour production multi-user`
   - Mais les f-strings sont toujours évalués même commentés (NON - correction: ils ne sont pas évalués si commentés)

## Solutions proposées

### Phase 1: Désactivation immédiate des logs verbeux (RAPIDE)

**Actions:**
1. Commenter tous les `print()` actifs dans les fonctions de recherche
2. Remplacer par un système de logging niveau (DEBUG/INFO/ERROR)
3. Désactiver par défaut le niveau DEBUG/INFO en production

**Gains estimés:**
- Réduction 60-80% du temps de recherche
- Réduction 90% des logs console
- Meilleure lisibilité pour debugging

### Phase 2: Optimisation du système de logging

**Actions:**
1. Créer une configuration de logging centralisée
2. Utiliser `logging.getLogger(__name__)` au lieu de `print()`
3. Ajouter variable d'environnement `LOG_LEVEL` (default: ERROR)
4. Logger uniquement les erreurs critiques en production

**Structure proposée:**
```python
import logging
import os

# Configuration globale
LOG_LEVEL = os.getenv('LOG_LEVEL', 'ERROR')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

# Utilisation
logger.debug("Info détaillée pour debug")  # Invisible en production
logger.info("Info générale")  # Invisible en production  
logger.error("Erreur critique")  # Toujours visible
```

### Phase 3: Optimisations de performance supplémentaires

**Actions:**
1. **Requêtes en cache:**
   - Mettre en cache les résultats GeoRisques par code INSEE
   - Mettre en cache les géométries de communes
   - TTL: 24h pour données statiques

2. **Requêtes parallèles:**
   - Utiliser `asyncio` pour requêtes API simultanées
   - GeoRisques + OSM + parcelles en parallèle
   - Gains: 50-70% sur temps total

3. **Pagination des résultats:**
   - Limiter résultats par défaut (ex: 1000 éléments max)
   - Charger le reste à la demande (lazy loading)

4. **Index de base de données:**
   - Vérifier index sur colonnes fréquemment requêtées
   - Index spatial sur géométries

## Implémentation prioritaire

### Changements immédiats (30 min)

**Fichiers à modifier:**
- `agriweb_hebergement_gratuit.py`

**Sections à modifier:**
1. ✅ Désactiver `log_search_start()` (lignes 15-69)
2. ✅ Désactiver `log_data_collection()` (lignes 71-77)
3. ✅ Désactiver logs GeoRisques (lignes 234-380)
4. ✅ Désactiver logs Bâtiments OSM (lignes 4400-4659)
5. ✅ Désactiver logs Friches (lignes 4269-4292)
6. ✅ Désactiver logs RPG/Capacités (lignes 4177-4232)
7. ✅ Garder uniquement logs d'erreur (try/except blocks)

### Configuration logging (1h)

**Créer système de logging professionnel:**
```python
# En début de fichier
import logging
import os

# Configuration
LOG_LEVEL = os.getenv('AGRIWEB_LOG_LEVEL', 'ERROR')
ENABLE_SEARCH_LOGS = os.getenv('AGRIWEB_SEARCH_LOGS', 'false').lower() == 'true'

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(funcName)s: %(message)s',
    handlers=[
        logging.FileHandler('agriweb.log'),
        logging.StreamHandler()  # Console
    ]
)

logger = logging.getLogger('agriweb')

# Fonction utilitaire
def log_search(message):
    """Log de recherche - désactivable via variable d'env"""
    if ENABLE_SEARCH_LOGS:
        logger.info(message)
```

### Tests de performance (30 min)

**Métriques à mesurer:**
- Temps de recherche AVANT optimisation
- Temps de recherche APRÈS optimisation
- Nombre de logs générés
- Utilisation mémoire

**Commandes de test:**
```python
import time

start = time.time()
# Recherche commune
elapsed = time.time() - start
print(f"Temps de recherche: {elapsed:.2f}s")
```

## Résultats attendus

### Avant optimisation
- ⏱️ Temps recherche: 30-60 secondes
- 📊 Logs console: 1000-3000 lignes
- 💾 Mémoire: Croissance continue

### Après optimisation
- ⏱️ Temps recherche: 10-20 secondes (60-70% plus rapide)
- 📊 Logs console: 0-10 lignes (erreurs uniquement)
- 💾 Mémoire: Stable

## Recommandations long terme

1. **Monitoring:**
   - Implémenter métriques de performance (temps par endpoint)
   - Alertes sur erreurs critiques
   - Tableau de bord de santé de l'application

2. **Tests de charge:**
   - Tester avec 10+ utilisateurs simultanés
   - Identifier goulots d'étranglement
   - Optimiser requêtes SQL lentes

3. **Infrastructure:**
   - Considérer Redis pour cache
   - Worker queue pour tâches lourdes (Celery)
   - CDN pour assets statiques

## Notes importantes

- ⚠️ **Ne pas supprimer les logs d'erreur** (dans try/except)
- ✅ **Garder logs de démarrage** (initialisation, configuration)
- 🔍 **Logs de recherche = optionnels** (via variable d'env)
- 📈 **Mesurer l'impact** avant/après chaque changement
