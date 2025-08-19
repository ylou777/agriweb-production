# 🚨 GUIDE COMPLET: STABILITÉ GEOSERVER SUR RAILWAY

## 📋 CAUSES PRINCIPALES D'INSTABILITÉ

### 1. 💾 LIMITATIONS MÉMOIRE (CRITIQUE)
- **Problème**: Railway gratuit limite à ~512MB-1GB RAM
- **GeoServer + Tomcat**: Consomme facilement 800MB+
- **Symptômes**: OutOfMemoryError, crashes fréquents
- **Solutions**:
  ```bash
  # Optimiser JVM dans Railway
  JAVA_OPTS="-Xmx512m -Xms256m -XX:+UseG1GC"
  ```

### 2. ⏱️ COLD START RAILWAY (FRÉQUENT)
- **Problème**: Railway suspend après 10-15min d'inactivité
- **Démarrage**: 5-10 minutes pour GeoServer complet
- **Solutions**:
  - Ping automatique toutes les 10-15 minutes
  - Utiliser `geoserver_auto_manager.py` en mode monitoring

### 3. 🔄 TIMEOUTS DE DÉPLOIEMENT
- **Problème**: Railway timeout si démarrage > 10 minutes
- **Cause**: GeoServer + Tomcat = démarrage lent
- **Solutions**:
  - Utiliser images GeoServer plus légères
  - Optimiser configuration Tomcat

### 4. 📦 RESSOURCES CPU/IO LIMITÉES
- **Problème**: Plan gratuit Railway = ressources partagées
- **Impact**: Performance dégradée, timeouts
- **Solutions**:
  - Éviter opérations lourdes simultanées
  - Limiter nombre de couches chargées

## 🛠️ SOLUTIONS IMMÉDIATES

### Option 1: Redéploiement Standard
```bash
# Dans Railway Dashboard:
1. Aller dans votre projet GeoServer
2. Cliquer "Deploy" > "Redeploy"
3. ATTENDRE 15 MINUTES COMPLÈTEMENT
4. Tester uniquement /geoserver/ d'abord
5. Puis tester /geoserver/web/ après 5min
```

### Option 2: Diagnostic Automatique
```bash
# Utiliser nos outils
python geoserver_auto_manager.py
# Choisir option 1: Diagnostic rapide
```

### Option 3: Monitoring Continu
```bash
# Surveillance automatique
python geoserver_auto_manager.py
# Choisir option 2: Monitoring continu
# Laisse tourner en arrière-plan
```

## 📊 PATTERN TYPIQUE DE CRASH

```
1. 🟢 GeoServer démarré OK
2. 🟡 Inactivité 10-15 minutes
3. 😴 Railway suspend le service
4. 🔄 Réveil sur requête suivante
5. ⏱️ 5-10 minutes redémarrage
6. 🔴 Possible timeout/crash si trop lent
```

## 🚀 PRÉVENTION DES CRASHES

### 1. Keepalive Automatique
```python
# Script keepalive (inclus dans auto_manager)
import requests
import time

def keepalive():
    while True:
        try:
            requests.get("https://geoserver-agriweb-production.up.railway.app/")
            print("💓 Ping envoyé")
        except:
            print("❌ Ping échoué")
        time.sleep(900)  # 15 minutes
```

### 2. Configuration JVM Optimisée
```bash
# Variables d'environnement Railway
JAVA_OPTS=-Xmx512m -Xms256m -XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

### 3. Configuration Tomcat Légère
```xml
<!-- server.xml optimisé -->
<Connector port="8080" 
           maxThreads="50" 
           minSpareThreads="10"
           connectionTimeout="20000"/>
```

## 📈 MONITORING ET ALERTES

### Script de Monitoring Personnalisé
```bash
# Surveillance toutes les 5 minutes
python geoserver_auto_manager.py

# Ou intégration dans votre app
from geoserver_auto_manager import GeoServerAutoManager
manager = GeoServerAutoManager()
status = manager.check_health()
```

### Logs d'Analyse
```bash
# Historique des crashes
python geoserver_stability_analyzer.py
```

## 🆘 PROCÉDURE D'URGENCE

### Si GeoServer est complètement DOWN:

1. **Vérification Rapide**:
   ```bash
   python geoserver_auto_manager.py
   # Option 1: Diagnostic rapide
   ```

2. **Si ROUGE (DOWN)**:
   - 🔄 Redéployer dans Railway Dashboard
   - ⏱️ Attendre 15 minutes COMPLÈTEMENT
   - 🚫 Ne pas tester avant 10 minutes

3. **Si JAUNE (PARTIAL)**:
   - ⏳ Attendre 5-10 minutes
   - 🔄 Relancer diagnostic
   - 🚫 Ne PAS redéployer

4. **Si VERT (HEALTHY)**:
   - ✅ Procéder aux opérations normales
   - 📊 Créer workspace et importer données

## 💰 SOLUTIONS LONG TERME

### Plan Railway Payant ($5-20/mois)
- ✅ Plus de RAM (jusqu'à 8GB)
- ✅ CPU dédié
- ✅ Pas de suspension automatique
- ✅ Meilleure stabilité

### Alternative: GeoServer Local
```bash
# Pour développement stable
docker run -p 8080:8080 kartoza/geoserver:2.24.0
```

### Optimisation Images Docker
```dockerfile
# Dockerfile optimisé pour Railway
FROM kartoza/geoserver:2.24.0-slim
ENV JAVA_OPTS="-Xmx512m -Xms256m"
```

## 🎯 RECOMMANDATIONS ACTUELLES

**Pour votre situation actuelle**:

1. **Immédiat**: Redéployer GeoServer Railway
2. **Court terme**: Utiliser `geoserver_auto_manager.py` pour monitoring
3. **Moyen terme**: Considérer plan Railway payant ($5/mois)
4. **Long terme**: Architecture hybride (Railway + backup local)

## 📞 SUPPORT

Si les crashes persistent après ces solutions:
- 📊 Collecter logs avec `geoserver_stability_analyzer.py`
- 🐛 Vérifier statut Railway platform
- 💬 Contacter support Railway avec données de monitoring

---

**⚡ ACTIONS IMMÉDIATES POUR MAINTENANT**:
1. Redéployer GeoServer dans Railway Dashboard
2. Attendre 15 minutes
3. Lancer `python geoserver_auto_manager.py` option 1
4. Si VERT → Continuer avec workspace création
5. Si ROUGE → Relancer redéploiement
