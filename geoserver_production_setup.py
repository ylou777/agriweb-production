#!/usr/bin/env python3
"""
🌐 CONFIGURATION GEOSERVER PRODUCTION
Adaptateur pour déployer votre GeoServer en production avec gestion des licences
"""

import os
import yaml
import json
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

class GeoServerProductionConfig:
    """Configuration GeoServer pour la production"""
    
    def __init__(self, geoserver_url="http://localhost:8080/geoserver", 
                 admin_user="admin", admin_password="geoserver"):
        self.geoserver_url = geoserver_url.rstrip('/')
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.auth = (admin_user, admin_password)
        
    def create_production_workspace(self, workspace_name="agriweb_prod"):
        """Crée un workspace de production pour AgriWeb"""
        
        workspace_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <workspace>
            <name>{workspace_name}</name>
        </workspace>'''
        
        url = f"{self.geoserver_url}/rest/workspaces"
        headers = {'Content-Type': 'application/xml'}
        
        response = requests.post(url, data=workspace_xml, headers=headers, auth=self.auth)
        
        if response.status_code in [200, 201]:
            print(f"✅ Workspace '{workspace_name}' créé avec succès")
            return True
        elif response.status_code == 409:
            print(f"ℹ️  Workspace '{workspace_name}' existe déjà")
            return True
        else:
            print(f"❌ Erreur création workspace: {response.status_code} - {response.text}")
            return False
    
    def create_datastore(self, workspace_name="agriweb_prod", store_name="agriweb_data", 
                        db_host="localhost", db_port="5432", db_name="agriweb", 
                        db_user="agriweb", db_password="agriweb_password"):
        """Crée un datastore PostGIS pour les données AgriWeb"""
        
        datastore_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <dataStore>
            <name>{store_name}</name>
            <connectionParameters>
                <host>{db_host}</host>
                <port>{db_port}</port>
                <database>{db_name}</database>
                <user>{db_user}</user>
                <passwd>{db_password}</passwd>
                <dbtype>postgis</dbtype>
            </connectionParameters>
        </dataStore>'''
        
        url = f"{self.geoserver_url}/rest/workspaces/{workspace_name}/datastores"
        headers = {'Content-Type': 'application/xml'}
        
        response = requests.post(url, data=datastore_xml, headers=headers, auth=self.auth)
        
        if response.status_code in [200, 201]:
            print(f"✅ Datastore '{store_name}' créé avec succès")
            return True
        else:
            print(f"❌ Erreur création datastore: {response.status_code} - {response.text}")
            return False
    
    def publish_layer(self, workspace_name, store_name, table_name, layer_title=None):
        """Publie une couche depuis la base de données"""
        
        layer_title = layer_title or table_name.replace('_', ' ').title()
        
        feature_type_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <featureType>
            <name>{table_name}</name>
            <title>{layer_title}</title>
            <nativeName>{table_name}</nativeName>
            <srs>EPSG:4326</srs>
            <enabled>true</enabled>
        </featureType>'''
        
        url = f"{self.geoserver_url}/rest/workspaces/{workspace_name}/datastores/{store_name}/featuretypes"
        headers = {'Content-Type': 'application/xml'}
        
        response = requests.post(url, data=feature_type_xml, headers=headers, auth=self.auth)
        
        if response.status_code in [200, 201]:
            print(f"✅ Couche '{table_name}' publiée avec succès")
            return True
        else:
            print(f"❌ Erreur publication couche: {response.status_code} - {response.text}")
            return False
    
    def create_layer_security_rules(self, license_type_rules):
        """Configure la sécurité des couches selon les types de licence"""
        
        # Mapping des règles de sécurité par type de licence
        security_rules = {
            "trial": [
                "*.*.r=ROLE_TRIAL",  # Lecture seule pour essai
                "*.parcelles.r=ROLE_TRIAL",
                "*.postes.r=ROLE_TRIAL"
            ],
            "basic": [
                "*.*.r=ROLE_BASIC",
                "*.parcelles.*=ROLE_BASIC",
                "*.postes.*=ROLE_BASIC",
                "*.communes.*=ROLE_BASIC"
            ],
            "professional": [
                "*.*.r=ROLE_PROFESSIONAL",
                "*.*.w=ROLE_PROFESSIONAL"
            ],
            "enterprise": [
                "*.*.*=ROLE_ENTERPRISE"  # Accès complet
            ]
        }
        
        # Écrire les règles dans security.properties
        rules_content = "\n".join(security_rules.get(license_type_rules, security_rules["trial"]))
        
        print(f"📋 Règles de sécurité pour {license_type_rules}:")
        print(rules_content)
        
        return rules_content

class GeoServerDeploymentHelper:
    """Assistant pour le déploiement GeoServer en production"""
    
    def __init__(self):
        self.config = GeoServerProductionConfig()
    
    def setup_production_environment(self):
        """Configure l'environnement de production complet"""
        
        print("🚀 Configuration de l'environnement GeoServer de production...")
        
        # 1. Créer le workspace de production
        self.config.create_production_workspace("agriweb_prod")
        
        # 2. Configuration des couches essentielles
        essential_layers = [
            {
                "table": "parcelles_rpg", 
                "title": "Parcelles RPG",
                "description": "Registre Parcellaire Graphique"
            },
            {
                "table": "postes_electriques_bt", 
                "title": "Postes Électriques BT",
                "description": "Postes d'injection basse tension"
            },
            {
                "table": "postes_electriques_hta", 
                "title": "Postes Électriques HTA",
                "description": "Postes d'injection haute tension"
            },
            {
                "table": "communes_france", 
                "title": "Communes de France",
                "description": "Limites administratives communales"
            },
            {
                "table": "eleveurs_geocodes", 
                "title": "Éleveurs Géocodés",
                "description": "Établissements d'élevage avec coordonnées"
            }
        ]
        
        # 3. Créer le fichier de configuration pour votre application
        self.generate_production_config(essential_layers)
        
        # 4. Générer les scripts de migration de données
        self.generate_data_migration_scripts()
        
        print("✅ Environnement de production configuré !")
    
    def generate_production_config(self, layers):
        """Génère le fichier de configuration pour la production"""
        
        config = {
            "production": {
                "geoserver": {
                    "url": "http://your-production-server.com:8080/geoserver",
                    "workspace": "agriweb_prod",
                    "datastore": "agriweb_data"
                },
                "database": {
                    "host": "your-db-server.com",
                    "port": 5432,
                    "name": "agriweb_prod",
                    "user": "agriweb_user",
                    "password": "CHANGE_THIS_PASSWORD"
                },
                "layers": {
                    layer["table"]: {
                        "title": layer["title"],
                        "description": layer["description"],
                        "access_level": "professional"  # Niveau d'accès requis
                    }
                    for layer in layers
                },
                "license_tiers": {
                    "trial": {
                        "allowed_layers": ["parcelles_rpg", "postes_electriques_bt"],
                        "max_requests_per_minute": 30,
                        "max_features_per_request": 1000
                    },
                    "basic": {
                        "allowed_layers": ["parcelles_rpg", "postes_electriques_bt", "communes_france"],
                        "max_requests_per_minute": 100,
                        "max_features_per_request": 5000
                    },
                    "professional": {
                        "allowed_layers": "all",
                        "max_requests_per_minute": 500,
                        "max_features_per_request": 10000
                    },
                    "enterprise": {
                        "allowed_layers": "all",
                        "max_requests_per_minute": -1,
                        "max_features_per_request": -1
                    }
                }
            }
        }
        
        with open("production_geoserver_config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print("✅ Configuration production sauvegardée dans production_geoserver_config.yaml")
        
        return config
    
    def generate_data_migration_scripts(self):
        """Génère les scripts de migration des données vers la production"""
        
        # Script SQL pour créer les tables de production
        sql_script = '''
-- ==================================================
-- AGRIWEB 2.0 - SCRIPT DE MIGRATION PRODUCTION
-- ==================================================

-- Création de la base de données de production
CREATE DATABASE agriweb_prod;
\\c agriweb_prod;

-- Extension PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Table des parcelles RPG
CREATE TABLE parcelles_rpg (
    id SERIAL PRIMARY KEY,
    id_parcel VARCHAR(50),
    surface_ha NUMERIC(10,2),
    code_culture VARCHAR(10),
    nom_culture VARCHAR(100),
    code_commune VARCHAR(5),
    nom_commune VARCHAR(100),
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index spatial
CREATE INDEX idx_parcelles_rpg_geom ON parcelles_rpg USING GIST (geom);
CREATE INDEX idx_parcelles_rpg_commune ON parcelles_rpg (code_commune);

-- Table des postes électriques BT
CREATE TABLE postes_electriques_bt (
    id SERIAL PRIMARY KEY,
    nom_poste VARCHAR(100),
    type_poste VARCHAR(50),
    puissance_mva NUMERIC(8,2),
    gestionnaire VARCHAR(50),
    code_commune VARCHAR(5),
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_postes_bt_geom ON postes_electriques_bt USING GIST (geom);

-- Table des postes électriques HTA
CREATE TABLE postes_electriques_hta (
    id SERIAL PRIMARY KEY,
    nom_poste VARCHAR(100),
    type_poste VARCHAR(50),
    puissance_mva NUMERIC(8,2),
    gestionnaire VARCHAR(50),
    code_commune VARCHAR(5),
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_postes_hta_geom ON postes_electriques_hta USING GIST (geom);

-- Table des communes
CREATE TABLE communes_france (
    id SERIAL PRIMARY KEY,
    code_insee VARCHAR(5) UNIQUE,
    nom_commune VARCHAR(100),
    code_departement VARCHAR(3),
    nom_departement VARCHAR(100),
    population INTEGER,
    surface_ha NUMERIC(12,2),
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_communes_geom ON communes_france USING GIST (geom);
CREATE INDEX idx_communes_insee ON communes_france (code_insee);

-- Table des éleveurs géocodés
CREATE TABLE eleveurs_geocodes (
    id SERIAL PRIMARY KEY,
    siret VARCHAR(14),
    nom_etablissement VARCHAR(200),
    adresse TEXT,
    code_postal VARCHAR(5),
    commune VARCHAR(100),
    activite VARCHAR(100),
    effectif VARCHAR(50),
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_eleveurs_geom ON eleveurs_geocodes USING GIST (geom);
CREATE INDEX idx_eleveurs_siret ON eleveurs_geocodes (siret);

-- Vues pour les requêtes fréquentes
CREATE VIEW v_parcelles_avec_distances AS
SELECT 
    p.*,
    (SELECT bt.nom_poste FROM postes_electriques_bt bt 
     ORDER BY p.geom <-> bt.geom LIMIT 1) as poste_bt_proche,
    (SELECT ST_Distance(p.geom::geography, bt.geom::geography) 
     FROM postes_electriques_bt bt 
     ORDER BY p.geom <-> bt.geom LIMIT 1) as distance_bt_m
FROM parcelles_rpg p;

-- Permissions pour l'utilisateur de production
CREATE USER agriweb_user WITH PASSWORD 'CHANGE_THIS_PASSWORD';
GRANT CONNECT ON DATABASE agriweb_prod TO agriweb_user;
GRANT USAGE ON SCHEMA public TO agriweb_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO agriweb_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agriweb_user;
'''
        
        with open("migration_production.sql", "w", encoding="utf-8") as f:
            f.write(sql_script)
        
        # Script Python de migration des données
        python_migration = '''#!/usr/bin/env python3
"""
Script de migration des données vers la production
"""

import psycopg2
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import os

def migrate_data_to_production():
    """Migre les données vers la base de production"""
    
    # Configuration (à adapter)
    DEV_DB = "postgresql://user:password@localhost/agriweb_dev"
    PROD_DB = "postgresql://agriweb_user:PASSWORD@production-server/agriweb_prod"
    
    dev_engine = create_engine(DEV_DB)
    prod_engine = create_engine(PROD_DB)
    
    # Migration des tables principales
    tables_to_migrate = [
        "parcelles_rpg",
        "postes_electriques_bt", 
        "postes_electriques_hta",
        "communes_france",
        "eleveurs_geocodes"
    ]
    
    for table in tables_to_migrate:
        print(f"Migration de {table}...")
        
        # Lire depuis le développement
        df = pd.read_sql(f"SELECT * FROM {table}", dev_engine)
        
        # Écrire vers la production
        df.to_sql(table, prod_engine, if_exists='append', index=False)
        
        print(f"✅ {len(df)} enregistrements migrés pour {table}")
    
    print("🎉 Migration terminée !")

if __name__ == "__main__":
    migrate_data_to_production()
'''
        
        with open("migrate_data.py", "w", encoding="utf-8") as f:
            f.write(python_migration)
        
        print("✅ Scripts de migration générés :")
        print("   - migration_production.sql (structure de base)")
        print("   - migrate_data.py (migration des données)")
    
    def generate_deployment_guide(self):
        """Génère un guide de déploiement complet"""
        
        guide = '''
# 🚀 GUIDE DE DÉPLOIEMENT AGRIWEB 2.0 EN PRODUCTION

## 1. Prérequis Infrastructure

### Serveur Base de Données (PostgreSQL + PostGIS)
```bash
# Installation PostgreSQL 14+ avec PostGIS
sudo apt update
sudo apt install postgresql-14 postgresql-14-postgis-3
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### Serveur GeoServer
```bash
# Installation Java 11
sudo apt install openjdk-11-jdk

# Téléchargement GeoServer
wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.22.0/geoserver-2.22.0-bin.zip
unzip geoserver-2.22.0-bin.zip
sudo mv geoserver-2.22.0 /opt/geoserver
```

### Serveur Application (Python + Flask)
```bash
# Installation Python 3.9+
sudo apt install python3.9 python3.9-venv python3.9-dev

# Création environnement virtuel
python3.9 -m venv /opt/agriweb
source /opt/agriweb/bin/activate
pip install -r requirements.txt
```

## 2. Configuration Base de Données

### Création de la base de production
```bash
sudo -u postgres psql
```

```sql
-- Exécuter le contenu de migration_production.sql
\\i migration_production.sql
```

### Migration des données
```bash
# Adapter les paramètres dans migrate_data.py
python migrate_data.py
```

## 3. Configuration GeoServer

### Démarrage GeoServer
```bash
cd /opt/geoserver/bin
./startup.sh
```

### Configuration via interface web
1. Accédez à http://votre-serveur:8080/geoserver
2. Connectez-vous (admin/geoserver par défaut)
3. Créez le workspace "agriweb_prod"
4. Configurez le datastore PostGIS
5. Publiez les couches essentielles

## 4. Déploiement Application

### Configuration Nginx (proxy inverse)
```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /geoserver {
        proxy_pass http://127.0.0.1:8080/geoserver;
        proxy_set_header Host $host;
    }
}
```

### Service systemd pour l'application
```ini
[Unit]
Description=AgriWeb 2.0 Production
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/agriweb
Environment=PATH=/opt/agriweb/bin
ExecStart=/opt/agriweb/bin/gunicorn -w 4 -b 127.0.0.1:5000 production_integration:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## 5. Configuration SSL avec Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

## 6. Monitoring et Maintenance

### Logs de l'application
```bash
journalctl -u agriweb -f
```

### Sauvegarde base de données
```bash
# Script de sauvegarde automatique
pg_dump agriweb_prod | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Monitoring GeoServer
- Vérifiez les logs dans /opt/geoserver/logs/
- Surveillez l'utilisation mémoire Java
- Configurez les alertes de performance

## 7. Tests de Production

### Test de l'essai gratuit
1. Allez sur http://votre-domaine.com/landing
2. Inscrivez-vous avec un email de test
3. Vérifiez l'activation de l'essai
4. Testez les fonctionnalités principales

### Test des performances
```bash
# Test de charge avec Apache Bench
ab -n 1000 -c 10 http://votre-domaine.com/api/trial/start
```

## 8. Sécurité

### Firewall
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### Sauvegardes
- Base de données : quotidienne
- Code application : via Git
- Configuration GeoServer : hebdomadaire

## 9. Intégration Paiement (optionnel)

Pour ajouter Stripe :
```python
import stripe
stripe.api_key = "sk_live_..."

# À intégrer dans production_system.py
```

## 10. Support et Maintenance

### Mise à jour de l'application
```bash
cd /opt/agriweb
git pull origin main
sudo systemctl restart agriweb
```

### Surveillance des logs
```bash
tail -f /var/log/nginx/access.log
tail -f /opt/geoserver/logs/geoserver.log
```
'''
        
        with open("DEPLOYMENT_GUIDE.md", "w", encoding="utf-8") as f:
            f.write(guide)
        
        print("✅ Guide de déploiement créé : DEPLOYMENT_GUIDE.md")

def setup_production_geoserver():
    """Script principal pour configurer GeoServer en production"""
    
    print("🌐 CONFIGURATION GEOSERVER PRODUCTION - AGRIWEB 2.0")
    print("=" * 60)
    
    helper = GeoServerDeploymentHelper()
    
    # 1. Configuration de l'environnement
    helper.setup_production_environment()
    
    # 2. Génération du guide de déploiement
    helper.generate_deployment_guide()
    
    print("""
🎉 Configuration terminée !

Fichiers générés :
📄 production_geoserver_config.yaml - Configuration production
📄 migration_production.sql - Script de création base de données
📄 migrate_data.py - Script de migration des données
📄 DEPLOYMENT_GUIDE.md - Guide de déploiement complet

Prochaines étapes :
1. Configurez votre serveur de production (voir DEPLOYMENT_GUIDE.md)
2. Exécutez migration_production.sql sur votre base de production
3. Adaptez les paramètres dans production_geoserver_config.yaml
4. Déployez votre application avec production_integration.py
5. Testez l'essai gratuit !

🚀 Votre système AgriWeb 2.0 sera prêt pour la commercialisation !
""")

if __name__ == "__main__":
    setup_production_geoserver()
