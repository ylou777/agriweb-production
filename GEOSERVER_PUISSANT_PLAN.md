# 🚀 GeoServer Puissant - Architecture Commerciale AgriWeb 2.0

## 🎯 Vision : GeoServer Centralisé Haute Performance

### Objectif
Déployer **UN** GeoServer ultra-performant qui servira **TOUS** vos clients AgriWeb 2.0 simultanément.

## 🏗️ Architecture Technique

### Schéma de Déploiement
```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTS AGRIWEB 2.0                     │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   Client A  │   Client B  │   Client C  │   Client N...   │
│   (Trial)   │   (Pro)     │ (Enterprise)│   (Starter)     │
└─────────────┴─────────────┴─────────────┴─────────────────┘
             │             │             │             │
             └─────────────┼─────────────┼─────────────┘
                           │             │
                    ┌──────▼─────────────▼──────┐
                    │     LOAD BALANCER         │
                    │   (HAProxy/Nginx)         │
                    └──────┬─────────────┬──────┘
                           │             │
              ┌────────────▼──┐    ┌─────▼────────────┐
              │  GEOSERVER 1  │    │   GEOSERVER 2    │
              │  (Master)     │    │   (Replica)      │
              └────────────┬──┘    └─────┬────────────┘
                           │             │
                    ┌──────▼─────────────▼──────┐
                    │    BASE DE DONNÉES        │
                    │   PostGIS + Données       │
                    │   (Haute Performance)     │
                    └───────────────────────────┘
```

## 💪 Spécifications Serveur Recommandées

### Serveur Principal (GeoServer Master)
```yaml
CPU: 16+ cores (Intel Xeon ou AMD EPYC)
RAM: 64 GB minimum (128 GB recommandé)
Stockage: 
  - SSD NVMe 2TB (données chaudes)
  - HDD 10TB (archives/backup)
Réseau: 10 Gbps
OS: Ubuntu Server 22.04 LTS
```

### Base de Données PostGIS
```yaml
CPU: 12+ cores optimisés pour DB
RAM: 32 GB (avec 24 GB pour cache PostgreSQL)
Stockage: SSD NVMe 1TB en RAID 10
Réseau: 10 Gbps (connexion dédiée GeoServer)
```

### Load Balancer / Proxy
```yaml
CPU: 8 cores
RAM: 16 GB
Réseau: 10 Gbps + CDN (Cloudflare/AWS)
SSL: Certificat wildcard *.agriweb.com
```

## ⚙️ Configuration GeoServer Optimisée

### 1. Paramètres JVM Haute Performance
```bash
# /opt/geoserver/bin/startup.sh
export JAVA_OPTS="
  -Xms16g -Xmx48g
  -XX:+UseG1GC
  -XX:MaxGCPauseMillis=200
  -XX:G1HeapRegionSize=32m
  -XX:+UseStringDeduplication
  -Dorg.geotools.coverage.jaiext.enabled=true
  -Dorg.geotools.referencing.forceXY=true
  -Djava.awt.headless=true
  -DGEOSERVER_DATA_DIR=/opt/geoserver_data
  -DGEOWEBCACHE_CACHE_DIR=/opt/gwc_cache
"
```

### 2. Configuration Multi-Threading
```xml
<!-- web.xml - Optimisation servlets -->
<web-app>
  <context-param>
    <param-name>GEOSERVER_CSRF_DISABLED</param-name>
    <param-value>true</param-value>
  </context-param>
  
  <context-param>
    <param-name>PROXY_BASE_URL</param-name>
    <param-value>https://geoserver.agriweb.com/geoserver</param-value>
  </context-param>
</web-app>
```

### 3. Configuration WFS Optimisée
```xml
<!-- global.xml - Paramètres globaux -->
<global>
  <settings>
    <contact/>
    <charset>UTF-8</charset>
    <numDecimals>6</numDecimals>
    <onlineResource>https://geoserver.agriweb.com/geoserver</onlineResource>
    <proxyBaseUrl>https://geoserver.agriweb.com/geoserver</proxyBaseUrl>
    <useHeadersProxyURL>true</useHeadersProxyURL>
  </settings>
  
  <jai>
    <allowInterpolation>true</allowInterpolation>
    <recycling>true</recycling>
    <tilePriority>5</tilePriority>
    <tileThreads>12</tileThreads>
    <memoryCapacity>0.75</memoryCapacity>
    <memoryThreshold>0.75</memoryThreshold>
  </jai>
  
  <coverageAccess>
    <maxPoolSize>25</maxPoolSize>
    <corePoolSize>5</corePoolSize>
    <keepAliveTime>30000</keepAliveTime>
    <queueType>UNBOUNDED</queueType>
  </coverageAccess>
</global>
```

## 🗄️ Base de Données PostGIS Optimisée

### Configuration PostgreSQL
```sql
-- postgresql.conf optimisations
shared_buffers = 24GB                    # 75% de la RAM disponible
effective_cache_size = 28GB              # Estimation cache OS
work_mem = 256MB                         # Pour tri/hash
maintenance_work_mem = 2GB               # Maintenance
max_connections = 200                    # Connexions simultanées
random_page_cost = 1.1                   # SSD optimisé
effective_io_concurrency = 200           # SSD parallélisme

# Checkpoint et WAL
checkpoint_completion_target = 0.9
wal_buffers = 64MB
max_wal_size = 4GB
min_wal_size = 1GB

# Monitoring
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

### Indexes Spatiaux Optimisés
```sql
-- Création d'indexes pour performance
CREATE INDEX CONCURRENTLY idx_parcelles_geom_gist 
ON parcelles_2024 USING GIST (geom);

CREATE INDEX CONCURRENTLY idx_parcelles_geom_spgist 
ON parcelles_2024 USING SPGIST (geom);

-- Index composites pour requêtes fréquentes
CREATE INDEX CONCURRENTLY idx_parcelles_dept_geom 
ON parcelles_2024 (code_dept, geom);

-- Statistiques étendues
CREATE STATISTICS parcelles_stats 
ON code_dept, commune, geom FROM parcelles_2024;

ANALYZE parcelles_2024;
```

## 🚀 GeoWebCache pour Performance

### Configuration Cache Intelligent
```xml
<!-- geowebcache.xml -->
<gwcConfiguration>
  <version>1.0.0</version>
  <backendTimeout>120</backendTimeout>
  <cacheBypassAllowed>false</cacheBypassAllowed>
  
  <!-- Cache sur disque rapide -->
  <cacheConfigurations>
    <FileBlobStoreConfiguration>
      <id>defaultCache</id>
      <enabled>true</enabled>
      <baseDirectory>/opt/gwc_cache</baseDirectory>
      <fileSystemBlockSize>16384</fileSystemBlockSize>
    </FileBlobStoreConfiguration>
  </cacheConfigurations>
  
  <!-- Pré-génération des tuiles populaires -->
  <gridSets>
    <gridSet>
      <name>EPSG:3857_AGRIWEB</name>
      <srs><number>3857</number></srs>
      <extent>
        <coords>
          <double>-20037508.34</double>
          <double>-20037508.34</double>
          <double>20037508.34</double>
          <double>20037508.34</double>
        </coords>
      </extent>
      <scaleDenominators>
        <double>559082264.0287178</double>
        <double>279541132.0143589</double>
        <double>139770566.0071794</double>
        <!-- ... jusqu'au niveau 15 pour détail France -->
      </scaleDenominators>
      <tileHeight>256</tileHeight>
      <tileWidth>256</tileWidth>
    </gridSet>
  </gridSets>
</gwcConfiguration>
```

## 🔧 Intégration avec AgriWeb 2.0

### Configuration Dynamique dans votre API
```python
# config_production.py
import os
from urllib.parse import urljoin

class GeoServerConfig:
    def __init__(self):
        # URL du GeoServer centralisé
        self.base_url = os.getenv('GEOSERVER_URL', 'https://geoserver.agriweb.com/geoserver')
        self.workspace = 'agriweb_public'
        
        # Paramètres de performance
        self.timeout = 30  # Plus long pour gros datasets
        self.max_features = 10000  # Limite par requête
        self.cache_ttl = 3600  # Cache 1h côté client
        
        # URLs optimisées
        self.wfs_url = f"{self.base_url}/{self.workspace}/ows"
        self.wms_url = f"{self.base_url}/{self.workspace}/wms"
        self.gwc_url = f"{self.base_url}/gwc/service"
    
    def get_wfs_params(self, layer_name, bbox, max_features=None):
        """Paramètres WFS optimisés"""
        return {
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typeName': f"{self.workspace}:{layer_name}",
            'outputFormat': 'application/json',
            'bbox': bbox,
            'srsname': 'EPSG:4326',
            'maxFeatures': max_features or self.max_features,
            # Optimisations
            'startIndex': 0,
            'resultType': 'results'
        }

# Intégration dans agriweb_source.py
geoserver_config = GeoServerConfig()

def fetch_wfs_data_optimized(layer_name, bbox, max_features=None):
    """Version optimisée pour GeoServer puissant"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'AgriWeb-2.0-Client',
        'Accept': 'application/json',
        'Cache-Control': 'max-age=3600'
    })
    
    params = geoserver_config.get_wfs_params(layer_name, bbox, max_features)
    
    try:
        response = session.get(
            geoserver_config.wfs_url, 
            params=params, 
            timeout=geoserver_config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get('features', [])
        
    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] GeoServer timeout pour {layer_name}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erreur GeoServer {layer_name}: {e}")
        return []
```

## 📊 Monitoring et Alertes

### Dashboard Performance
```python
# monitoring_geoserver.py
import psutil
import requests
from datetime import datetime

def check_geoserver_health():
    """Monitoring santé GeoServer"""
    health_check = {
        'timestamp': datetime.now().isoformat(),
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/opt/geoserver_data').percent,
        'geoserver_responsive': False,
        'response_time_ms': None
    }
    
    # Test connectivité GeoServer
    try:
        start = datetime.now()
        response = requests.get(
            'https://geoserver.agriweb.com/geoserver/rest/about/version.json',
            timeout=5
        )
        end = datetime.now()
        
        if response.status_code == 200:
            health_check['geoserver_responsive'] = True
            health_check['response_time_ms'] = (end - start).total_seconds() * 1000
            
    except Exception as e:
        health_check['error'] = str(e)
    
    return health_check

# Alertes automatiques
def send_alert_if_needed(health):
    """Alertes si problème performance"""
    alerts = []
    
    if health['cpu_usage'] > 80:
        alerts.append(f"🚨 CPU usage élevé: {health['cpu_usage']}%")
    
    if health['memory_usage'] > 85:
        alerts.append(f"🚨 Mémoire usage élevé: {health['memory_usage']}%")
    
    if not health['geoserver_responsive']:
        alerts.append("🚨 GeoServer non accessible")
    
    if health.get('response_time_ms', 0) > 2000:
        alerts.append(f"🚨 Temps de réponse lent: {health['response_time_ms']}ms")
    
    if alerts:
        # Envoyer notification (email, Slack, etc.)
        print("ALERTES GEOSERVER:", alerts)
```

## 🎯 Plan de Déploiement

### Phase 1 : Infrastructure (Semaine 1-2)
- [ ] **Provisioning serveurs** (OVH, AWS, ou bare metal)
- [ ] **Installation PostgreSQL/PostGIS** optimisé
- [ ] **Installation GeoServer** avec configuration haute performance
- [ ] **Configuration Load Balancer** avec SSL

### Phase 2 : Migration Données (Semaine 3)
- [ ] **Import toutes vos couches** dans PostGIS
- [ ] **Configuration espaces de travail** GeoServer
- [ ] **Tests performance** avec charge simulée
- [ ] **Pré-génération cache** zones populaires

### Phase 3 : Intégration API (Semaine 4)
- [ ] **Modification agriweb_source.py** pour nouveau GeoServer
- [ ] **Tests fonctionnels** toutes les couches
- [ ] **Optimisation requêtes** selon usage réel
- [ ] **Documentation API** pour clients

### Phase 4 : Production (Semaine 5)
- [ ] **Monitoring en continu**
- [ ] **Tests charge** avec clients réels
- [ ] **Backup automatisé**
- [ ] **Support 24/7**

## 💰 Estimation Coûts Mensuels

### Option Cloud (AWS/Azure)
```
Serveur GeoServer:    €800/mois (c5.4xlarge)
Base PostGIS:        €400/mois (db.r5.xlarge)
Load Balancer:       €100/mois
Stockage (5TB):      €200/mois
Trafic réseau:       €300/mois
TOTAL:              €1800/mois
```

### Option Serveur Dédié (OVH/Hetzner)
```
Serveur principal:   €400/mois (64GB RAM, 16 cores)
Serveur BDD:        €200/mois (32GB RAM, SSD)
Bande passante:     €100/mois
TOTAL:             €700/mois
```

## 🚀 Bénéfices Business

### Performance
- ⚡ **Temps de réponse < 200ms** pour 95% des requêtes
- 🔄 **Support 1000+ clients** simultanés
- 📈 **Scalabilité horizontale** selon croissance

### Économique
- 💰 **Coût mutualisé** entre tous les clients
- 📊 **ROI rapide** avec 50+ clients payants
- 🔧 **Maintenance centralisée** = coûts réduits

Voulez-vous que je commence par créer le script de migration de votre configuration actuelle vers cette architecture GeoServer centralisée ?
