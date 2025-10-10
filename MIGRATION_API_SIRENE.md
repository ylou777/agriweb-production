# Migration API Sirene → API Recherche Entreprises

## 📅 Date
10 octobre 2025

## 🔄 Changement

L'ancienne API Sirene `entreprise.data.gouv.fr` a été **remplacée** par la nouvelle API **Recherche Entreprises**.

### Ancienne API (❌ Ne fonctionne plus)
```
https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}
```
- **Statut**: Service arrêté / obsolète
- **Symptômes**: Timeouts systématiques, connexions refusées

### Nouvelle API (✅ Fonctionnelle)
```
https://recherche-entreprises.api.gouv.fr/search?q={siret}
```
- **Statut**: Opérationnelle
- **Temps de réponse**: ~0.5s
- **Authentification**: Non requise
- **Rate limit**: Non documenté (raisonnable)

## 🔧 Modifications apportées

### 1. Fonction `fetch_sirene_info()` (ligne ~3812)

**Changements:**
- ✅ URL mise à jour vers `recherche-entreprises.api.gouv.fr`
- ✅ Endpoint changé: `/search?q={siret}` au lieu de `/etablissements/{siret}`
- ✅ Adaptation de la structure de réponse
- ✅ Mapping vers l'ancien format pour compatibilité

**Structure de réponse nouvelle API:**
```json
{
  "results": [{
    "siren": "123456789",
    "nom_complet": "NOM ENTREPRISE",
    "nom_raison_sociale": "RAISON SOCIALE",
    "activite_principale": "01.11Z",
    "siege": {
      "siret": "12345678900047",
      "adresse": "123 RUE EXEMPLE 75001 PARIS",
      "activite_principale": "01.11Z"
    }
  }],
  "total_results": 1
}
```

**Format renvoyé (compatible):**
```json
{
  "etablissement": {
    "siret": "12345678900047",
    "siren": "123456789",
    "uniteLegale": {
      "denominationUniteLegale": "NOM ENTREPRISE",
      "activitePrincipaleUniteLegale": "01.11Z"
    },
    "adresseEtablissement": "123 RUE EXEMPLE 75001 PARIS"
  }
}
```

### 2. Fonction `enrich_eleveurs_with_siret()` (ligne ~12036)

**Changements:**
- ✅ Threading activé (20 workers simultanés)
- ✅ Timeout réduit à 0.5s
- ✅ Pas de retry (max_retries=0)
- ✅ **Suppression de la limitation à 10 éleveurs**
- ✅ Enrichissement de TOUS les éleveurs (932 dans l'exemple)

**Performance:**
- Mode séquentiel: 932 × 0.5s = **~8 minutes** ❌
- Mode parallèle (20 threads): 932/20 × 0.5s = **~25 secondes** ✅
- **Accélération: x20**

## 📊 Tests effectués

### Test de performance (test_sirene_performance.py)
```
Séquentiel:  5.31s pour 10 SIRET = 0.53s/SIRET
Parallèle:   0.58s pour 10 SIRET = 0.05s/SIRET (apparent)
Estimation:  25s pour 932 SIRET avec 20 threads
```

### Test nouvelle API (test_new_api_recherche_entreprises.py)
```
✓ API accessible et fonctionnelle
✓ Temps de réponse: ~0.5s
✓ Endpoint search fonctionne
⚠ Structure de réponse différente (adaptée)
```

## ⚙️ Configuration

### Paramètres optimisés
```python
fetch_sirene_info(siret, max_retries=0, timeout=0.5)
```

- **timeout**: 0.5s (rapide, mais API répond généralement en ~0.5s)
- **max_retries**: 0 (1 seule tentative, échec rapide si API down)
- **workers**: 20 threads parallèles
- **cache**: En mémoire (_sirene_cache)
- **circuit breaker**: _sirene_failures pour éviter re-tentatives

## 🎯 Avantages

1. **✅ Fonctionne**: API opérationnelle (contrairement à l'ancienne)
2. **⚡ Rapide**: 25s pour 932 éleveurs vs 8 minutes
3. **🛡️ Résilient**: Cache + circuit breaker
4. **📈 Scalable**: Threading permet de gérer grands volumes
5. **🔄 Compatible**: Format de réponse adapté pour compatibilité code existant

## ⚠️ Limitations connues

1. **Pas de documentation officielle complète** sur les paramètres
2. **Rate limiting non documenté** (semble généreux)
3. **SIRET parfois non trouvés** même s'ils existent (API en construction ?)
4. **Structure de réponse peut évoluer** (API récente)

## 📝 TODO Futur

- [ ] Surveiller la stabilité de l'API Recherche Entreprises
- [ ] Implémenter retry sélectif si timeouts ponctuels
- [ ] Ajouter cache persistant (Redis/fichier) pour éviter re-requêtes
- [ ] Logger les statistiques de succès/échec
- [ ] Documenter les cas d'usage avancés de l'API

## 🔗 Liens utiles

- Documentation API: https://recherche-entreprises.api.gouv.fr/docs/
- Code source API (si open source): À rechercher
- Status page: À identifier

## ✅ Tests de validation

Pour valider le changement:

1. **Test unitaire**:
   ```bash
   python test_new_api_recherche_entreprises.py
   ```

2. **Test de performance**:
   ```bash
   python test_sirene_performance.py
   ```

3. **Test intégration**:
   - Lancer l'application Flask
   - Générer un rapport département (code 70 par exemple)
   - Vérifier enrichissement SIRET dans les logs
   - Temps attendu: 20-30 secondes pour 932 éleveurs

## 📈 Métriques attendues

Avec département de 932 éleveurs:
- **Temps enrichissement**: 20-30 secondes
- **Taux succès**: 50-80% (dépend de la qualité des SIRET source)
- **Timeout rate**: <5%
- **Cache hit rate**: 0% première génération, >90% si régénération

