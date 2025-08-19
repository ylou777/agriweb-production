# 🔧 Configuration GeoServer ↔ API AgriWeb - Commerce

## 🎯 Enjeu Central
**Comment configurer GeoServer pour que vos clients puissent utiliser votre API AgriWeb en production ?**

## 📊 Configuration Actuelle (Mode Test)

### Dans `agriweb_source.py`
```python
# Configuration locale actuelle
GEOSERVER_URL = "http://localhost:8080/geoserver"
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"

# Exemples de requêtes
def fetch_wfs_data(layer_name, bbox, srsname="EPSG:4326"):
    layer_q = quote(layer_name, safe=':')
    url = f"{GEOSERVER_WFS_URL}?service=WFS&version=2.0.0&request=GetFeature&typeName={layer_q}&outputFormat=application/json&bbox={bbox}&srsname={srsname}"
    resp = http_session.get(url, timeout=10)
    return resp.json().get('features', [])
```

## 🚀 Configurations pour Commercialisation

### Option 1 : GeoServer Centralisé (Recommandée)
```python
class GeoServerConfig:
    def __init__(self, environment="production"):
        if environment == "local":
            self.base_url = "http://localhost:8080/geoserver"
        elif environment == "production":
            self.base_url = "https://geoserver.votre-domaine.com/geoserver"
        elif environment == "client_hosted":
            # Configuration dynamique par client
            self.base_url = self.get_client_geoserver_url()
    
    def get_wfs_url(self, workspace="gpu"):
        return f"{self.base_url}/{workspace}/ows"
    
    def get_client_geoserver_url(self):
        # Logique pour récupérer l'URL GeoServer du client
        client_id = self.get_current_client()
        return client_configs.get(client_id, {}).get('geoserver_url')
```

### Option 2 : Configuration Multi-Clients
```python
# Configuration flexible pour différents types de déploiement
GEOSERVER_CONFIGS = {
    "saas_centralized": {
        "url": "https://geoserver.agriweb.com/geoserver",
        "workspace": "public",
        "auth": {"type": "none"}  # Données publiques
    },
    "client_dedicated": {
        "url": "https://geoserver-{client_id}.agriweb.com/geoserver",
        "workspace": "client_{client_id}",
        "auth": {"type": "basic", "user": "client", "pass": "generated"}
    },
    "client_onpremise": {
        "url": "http://{client_server}:8080/geoserver",
        "workspace": "agriweb",
        "auth": {"type": "configurable"}
    }
}
```

## 🔧 Adaptations Techniques Nécessaires

### 1. Configuration Dynamique dans l'API
```python
class GeoServerManager:
    def __init__(self, client_config):
        self.config = client_config
        self.base_url = client_config['geoserver']['url']
        self.workspace = client_config['geoserver']['workspace']
        self.auth = client_config['geoserver'].get('auth', {})
    
    def get_authenticated_session(self):
        session = requests.Session()
        if self.auth.get('type') == 'basic':
            session.auth = (self.auth['user'], self.auth['pass'])
        elif self.auth.get('type') == 'token':
            session.headers['Authorization'] = f"Bearer {self.auth['token']}"
        return session
    
    def fetch_layer_data(self, layer_name, bbox):
        session = self.get_authenticated_session()
        url = f"{self.base_url}/{self.workspace}/ows"
        params = {
            "service": "WFS",
            "version": "2.0.0", 
            "request": "GetFeature",
            "typeName": f"{self.workspace}:{layer_name}",
            "outputFormat": "application/json",
            "bbox": bbox
        }
        response = session.get(url, params=params, timeout=30)
        return response.json().get('features', [])
```

### 2. Configuration Client dans `production_commercial.py`
```python
@app.route('/api/configure/geoserver', methods=['POST'])
def configure_client_geoserver():
    """Configuration GeoServer pour un client spécifique"""
    if not session.get('authenticated'):
        return jsonify({"error": "Non autorisé"}), 401
    
    user_data = session.get('user_data', {})
    client_id = user_data.get('user_id')
    
    config_data = request.get_json()
    
    # Validation de la configuration
    required_fields = ['geoserver_url', 'workspace']
    if not all(field in config_data for field in required_fields):
        return jsonify({"error": "Configuration incomplète"}), 400
    
    # Test de connectivité
    test_result = test_geoserver_connection(config_data)
    if not test_result['success']:
        return jsonify({"error": f"Connexion échouée: {test_result['error']}"}), 400
    
    # Sauvegarde de la configuration
    save_client_geoserver_config(client_id, config_data)
    
    return jsonify({"success": True, "message": "Configuration GeoServer sauvegardée"})

def test_geoserver_connection(config):
    """Test de connectivité vers GeoServer client"""
    try:
        url = f"{config['geoserver_url']}/{config['workspace']}/ows"
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetCapabilities"
        }
        
        session = requests.Session()
        if 'auth' in config:
            if config['auth']['type'] == 'basic':
                session.auth = (config['auth']['user'], config['auth']['pass'])
        
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 3. Interface de Configuration pour les Clients
```html
<!-- Template pour configurer GeoServer client -->
<div class="geoserver-config-panel">
    <h3>🗺️ Configuration GeoServer</h3>
    
    <div class="config-options">
        <input type="radio" name="geoserver_type" value="saas" checked>
        <label>🌐 Utiliser notre GeoServer centralisé (Recommandé)</label>
        
        <input type="radio" name="geoserver_type" value="custom">
        <label>🏢 Utiliser votre GeoServer (Configuration avancée)</label>
    </div>
    
    <div id="custom-config" style="display:none;">
        <div class="form-group">
            <label>URL GeoServer:</label>
            <input type="url" id="geoserver_url" placeholder="http://votre-serveur:8080/geoserver">
        </div>
        
        <div class="form-group">
            <label>Workspace:</label>
            <input type="text" id="workspace" placeholder="agriweb" value="agriweb">
        </div>
        
        <div class="form-group">
            <label>Authentification:</label>
            <select id="auth_type">
                <option value="none">Aucune</option>
                <option value="basic">Basic Auth</option>
                <option value="token">Token</option>
            </select>
        </div>
        
        <div id="auth-fields" style="display:none;">
            <input type="text" id="auth_user" placeholder="Utilisateur">
            <input type="password" id="auth_pass" placeholder="Mot de passe">
        </div>
        
        <button onclick="testGeoServerConnection()">🔍 Tester la connexion</button>
    </div>
    
    <button onclick="saveGeoServerConfig()">💾 Sauvegarder</button>
</div>

<script>
async function testGeoServerConnection() {
    const config = {
        geoserver_url: document.getElementById('geoserver_url').value,
        workspace: document.getElementById('workspace').value,
        auth: {
            type: document.getElementById('auth_type').value,
            user: document.getElementById('auth_user').value,
            pass: document.getElementById('auth_pass').value
        }
    };
    
    const response = await fetch('/api/test/geoserver', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(config)
    });
    
    const result = await response.json();
    if (result.success) {
        alert('✅ Connexion GeoServer réussie !');
    } else {
        alert(`❌ Erreur: ${result.error}`);
    }
}
</script>
```

## 🚦 Gestion des Environnements

### Fichier de Configuration `config.json`
```json
{
    "environments": {
        "development": {
            "geoserver": {
                "url": "http://localhost:8080/geoserver",
                "workspace": "gpu",
                "timeout": 10
            }
        },
        "production_saas": {
            "geoserver": {
                "url": "https://geoserver.agriweb.com/geoserver", 
                "workspace": "public",
                "timeout": 30,
                "cache_ttl": 3600
            }
        },
        "client_custom": {
            "geoserver": {
                "url": "${CLIENT_GEOSERVER_URL}",
                "workspace": "${CLIENT_WORKSPACE}",
                "auth": "${CLIENT_AUTH_CONFIG}"
            }
        }
    }
}
```

## 📋 Checklist de Migration

### Pour le Mode SaaS Centralisé
- [ ] **Serveur GeoServer production** (domaine, SSL, haute dispo)
- [ ] **Import de toutes vos couches** en droit libre
- [ ] **Configuration CORS** pour les appels cross-domain
- [ ] **Monitoring et cache** (performances)
- [ ] **Documentation client** (URLs, exemples)

### Pour le Mode Client Custom
- [ ] **Interface de configuration** dans AgriWeb
- [ ] **Tests de connectivité** automatiques
- [ ] **Gestion des erreurs** de connexion
- [ ] **Documentation technique** pour l'installation client
- [ ] **Support configuration** GeoServer

## 🎯 Recommandations Immédiates

### 1. **Testez la Configuration Flexible**
Modifiez votre `agriweb_source.py` pour accepter des URLs GeoServer dynamiques :

```python
# Ajoutez cette classe en haut du fichier
class ConfigManager:
    def __init__(self):
        self.geoserver_url = os.getenv('GEOSERVER_URL', 'http://localhost:8080/geoserver')
        self.workspace = os.getenv('GEOSERVER_WORKSPACE', 'gpu')
    
    def get_wfs_url(self):
        return f"{self.geoserver_url}/{self.workspace}/ows"

# Remplacez les constantes par
config = ConfigManager()
GEOSERVER_WFS_URL = config.get_wfs_url()
```

### 2. **Préparez les Deux Modes**
- **Mode SaaS** : Plus simple pour vos clients
- **Mode Custom** : Plus de flexibilité pour les gros clients

### 3. **Documentation Technique**
Créez un guide d'installation GeoServer pour vos clients qui veulent leur propre instance.

Voulez-vous que je vous aide à implémenter une de ces configurations ? Ou préférez-vous d'abord clarifier quelle approche (SaaS centralisé vs. custom client) vous privilégiez ?
