# Documentation API Sirene - Résumé Technique

## 🔗 Sources officielles

### Portails principaux
- **INSEE API Catalogue**: https://api.insee.fr/catalogue/
- **Portail API INSEE**: https://portail-api.insee.fr/
- **API Entreprise (data.gouv.fr)**: https://entreprise.data.gouv.fr/

### Deux APIs disponibles

#### 1. API INSEE Sirene V3 (Officielle)
- **Base URL**: `https://api.insee.fr/entreprises/sirene/V3/`
- **Authentification**: **REQUISE** - Bearer Token OAuth2
- **Quotas**: 30 requêtes/minute (authentifié)
- **Documentation**: https://api.insee.fr/catalogue/site/themes/wso2/subthemes/insee/pages/item-info.jag?name=Sirene&version=V3&provider=insee

#### 2. API Entreprise (data.gouv.fr) - Proxy
- **Base URL**: `https://entreprise.data.gouv.fr/api/sirene/v3/`
- **Authentification**: **NON REQUISE** (accès public)
- **Quotas**: Plus restrictifs, non documentés publiquement
- **Note**: Proxy vers l'API INSEE, peut être instable

## 📊 Endpoints disponibles

### Recherche par établissement (SIRET - 14 chiffres)
```
GET /etablissements/{siret}
```
**Exemple**:
```
https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/31252693800047
```

### Recherche par unité légale (SIREN - 9 chiffres)
```
GET /unites_legales/{siren}
```
**Exemple**:
```
https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales/312526938
```

### Recherche multi-critères
```
GET /siret?q={critères}
```
**Exemple**:
```
https://entreprise.data.gouv.fr/api/sirene/v3/siret?q=denominationUniteLegale:AGRICULTURE
```

## 🔒 Authentification (API INSEE uniquement)

### Obtenir un token
```bash
curl -X POST https://api.insee.fr/token \
  -H "Authorization: Basic {client_credentials_base64}" \
  -d "grant_type=client_credentials"
```

### Utiliser le token
```bash
curl https://api.insee.fr/entreprises/sirene/V3/siret/{siret} \
  -H "Authorization: Bearer {access_token}"
```

## ⚠️ Limitations et Quotas

### API INSEE (authentifiée)
- ✅ **30 requêtes/minute**
- ✅ Service stable et fiable
- ❌ Nécessite inscription et gestion token
- ❌ Token expire après 7 jours

### API Entreprise (publique)
- ⚠️ **Quota non documenté** (estimé ~10-20 req/min)
- ⚠️ Service peut être instable
- ⚠️ Rate limiting agressif
- ✅ Pas d'authentification requise
- ✅ Accès immédiat

## 🐛 Problèmes connus

### Erreurs réseau courantes

#### 1. ConnectionResetError (10054)
```
'Une connexion existante a dû être fermée par l'hôte distant'
```
**Causes**:
- API en maintenance
- Rate limiting déclenché
- Trop de connexions simultanées

#### 2. ConnectionRefusedError (10061)
```
'Aucune connexion n'a pu être établie'
```
**Causes**:
- Service temporairement indisponible
- Blocage pare-feu
- IP bannie temporairement (rate limit)

#### 3. Timeout
**Causes**:
- API surchargée
- Réseau lent
- SIRET/SIREN invalide (réponse lente)

### Solutions recommandées

#### ✅ Pattern de retry avec backoff
```python
for attempt in range(max_retries):
    try:
        response = requests.get(url, timeout=3)
        return response.json()
    except (Timeout, ConnectionError):
        if attempt < max_retries - 1:
            time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s, 2s
```

#### ✅ Cache en mémoire
```python
_cache = {}
if siret in _cache:
    return _cache[siret]
```

#### ✅ Limitation du nombre d'appels
```python
# Maximum 10 enrichissements par batch
for eleveur in eleveurs[:10]:
    enrich_siret(eleveur)
```

#### ✅ Circuit breaker (éviter les retry inutiles)
```python
_failures = set()
if siret in _failures:
    return None  # Ne pas réessayer
```

## 📈 Structure des réponses

### Établissement (SIRET)
```json
{
  "etablissement": {
    "siret": "31252693800047",
    "siren": "312526938",
    "nic": "00047",
    "dateCreationEtablissement": "1975-01-01",
    "uniteLegale": {
      "denominationUniteLegale": "EXPLOITATION AGRICOLE",
      "activitePrincipaleUniteLegale": "01.11Z"
    },
    "adresseEtablissement": {
      "numeroVoieEtablissement": "123",
      "typeVoieEtablissement": "RUE",
      "libelleVoieEtablissement": "DE LA FERME"
    }
  }
}
```

### Unité légale (SIREN)
```json
{
  "uniteLegale": {
    "siren": "312526938",
    "denomination": "EXPLOITATION AGRICOLE",
    "activitePrincipale": "01.11Z",
    "categorieJuridiqueUniteLegale": "1000"
  }
}
```

## 🔧 Implémentation actuelle dans AgriWeb

### Fichier: `agriweb_hebergement_gratuit.py`

#### Fonction: `fetch_sirene_info(siret, max_retries=2, timeout=3)`

**Améliorations apportées**:
1. ✅ Cache en mémoire (`_sirene_cache`)
2. ✅ Tracking des échecs (`_sirene_failures`)
3. ✅ Retry avec backoff exponentiel (0.5s, 1s)
4. ✅ Timeout court (2-3s)
5. ✅ Gestion spécifique des erreurs réseau
6. ✅ Limitation à 10 enrichissements max par rapport département

**Endpoint utilisé**:
```python
url = f"https://entreprise.data.gouv.fr/api/sirene/v3/etablissements/{siret}"
```

## 💡 Recommandations

### Court terme (immédiat)
1. ✅ **Utiliser le cache** - Déjà implémenté
2. ✅ **Limiter les appels** - Max 10 par rapport
3. ✅ **Retry intelligent** - Avec backoff

### Moyen terme
1. ⚠️ **Surveiller la stabilité** de l'API publique
2. 💡 **Envisager l'API INSEE authentifiée** si problèmes récurrents
3. 💡 **Implémenter un cache persistant** (Redis/fichier) pour éviter les re-requêtes

### Long terme
1. 🔄 **Basculer vers API INSEE officielle** avec authentification
2. 💾 **Cache base de données** pour les SIRET fréquents
3. 📊 **Monitoring des erreurs** et alertes

## 🎯 État actuel (10 octobre 2025)

### Diagnostic
- ❌ API `entreprise.data.gouv.fr` **inaccessible** depuis votre réseau
- ⚠️ Erreurs 10054 et 10061 lors des tests
- 🔄 Cause probable: **Maintenance** ou **Rate limiting sévère**

### Impact
- ✅ Application continue de fonctionner
- ⚠️ Enrichissement SIRET limité/impossible
- ✅ Données de base (éleveurs) toujours disponibles
- ✅ Cache protège contre les appels répétés

### Prochaines étapes
1. ⏱️ Réessayer dans 1-2 heures
2. 🔍 Vérifier statut API sur https://status.entreprise.api.gouv.fr/ (si disponible)
3. 💡 Envisager migration vers API INSEE officielle avec token
