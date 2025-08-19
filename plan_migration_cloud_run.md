# 🚀 MIGRATION VERS GOOGLE CLOUD RUN - PLAN D'ACTION

## ✅ AVANTAGES GOOGLE CLOUD RUN
- **Prix imbattable** : ~$8-15/mois pour 100 Go
- **Scaling automatique** : 0 à 1000 instances
- **HTTPS automatique** avec domaine personnalisé
- **Intégration native** avec Cloud Storage
- **99.95% uptime** garanti
- **Monitoring complet** inclus

## 📋 ÉTAPES DE MIGRATION

### 1. Préparation (30 min)
```bash
# Installation Google Cloud CLI
curl https://sdk.cloud.google.com | bash
gcloud auth login
gcloud config set project [YOUR-PROJECT-ID]
```

### 2. Configuration Storage (15 min)
```bash
# Créer bucket pour données GeoServer
gsutil mb gs://agriweb-geoserver-data
gsutil cp -r geoserver_data/* gs://agriweb-geoserver-data/
```

### 3. Dockerfile optimisé pour Cloud Run
```dockerfile
FROM kartoza/geoserver:2.24.0

# Variables d'environnement Cloud Run
ENV GEOSERVER_DATA_DIR=/geoserver_data
ENV JAVA_OPTS="-Xms512m -Xmx2048m -XX:+UseContainerSupport"

# Port fixe pour Cloud Run
ENV HTTP_PORT=8080
EXPOSE 8080

# Script de démarrage avec récupération des données
COPY start_cloud_run.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
```

### 4. Déploiement (10 min)
```bash
# Build et deploy en une commande
gcloud run deploy agriweb-geoserver \
  --source . \
  --region europe-west1 \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10 \
  --port 8080 \
  --allow-unauthenticated
```

## 💰 ESTIMATION COÛTS DÉTAILLÉE

### Storage (Cloud Storage)
- 100 GB données : $2.00/mois
- Opérations GET/PUT : ~$0.50/mois

### Compute (Cloud Run)
- 2 vCPU, 4 GB RAM
- 100 heures/mois usage : ~$5-8/mois
- Scaling automatique selon trafic

### Réseau
- Egress : ~$1-2/mois selon usage

**Total : $8.50-12.50/mois**

## 🎛️ CONFIGURATION RECOMMANDÉE
- **CPU** : 2 vCPU (suffisant pour GeoServer)
- **Mémoire** : 4 GB (peut monter à 8 GB si besoin)
- **Timeout** : 3600s (1 heure max par requête)
- **Concurrency** : 10 requêtes/instance
- **Min instances** : 0 (économie maximale)
- **Max instances** : 10 (protection contre surcharge)

## 🔧 MIGRATION AUTOMATISÉE
Script de migration complet disponible !
```bash
python migrate_to_cloud_run.py
```
