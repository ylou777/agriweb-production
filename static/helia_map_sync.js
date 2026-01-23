/**
 * Helia Map Sync - Synchronisation bidirectionnelle entre Helia AI et la carte Leaflet
 * Permet à Helia de contrôler la carte (zoom, calques) et de recevoir l'état de la carte
 */

class HeliaMapSync {
    constructor(mapInstance) {
        this.map = mapInstance;
        this.layers = {};
        this.pollInterval = 2000; // Polling toutes les 2 secondes
        this.isPolling = false;
        
        console.log('🗺️ Helia Map Sync initialized');
        
        // Démarrer la synchronisation
        this.startSync();
    }
    
    /**
     * Enregistre une couche avec son nom pour le contrôle par Helia
     */
    registerLayer(layerName, layerObject) {
        this.layers[layerName] = layerObject;
        console.log(`✅ Calque enregistré: ${layerName}`);
    }
    
    /**
     * Démarre la synchronisation automatique
     */
    startSync() {
        // Envoyer l'état initial
        this.sendMapState();
        
        // Écouter les changements de carte
        this.map.on('moveend', () => this.sendMapState());
        this.map.on('zoomend', () => this.sendMapState());
        
        // Polling des commandes Helia
        this.startPolling();
    }
    
    /**
     * Envoie l'état actuel de la carte au serveur
     */
    async sendMapState() {
        try {
            const center = this.map.getCenter();
            const zoom = this.map.getZoom();
            const bounds = this.map.getBounds();
            
            // Déterminer quelles couches sont actives
            const activeLayers = [];
            for (const [name, layer] of Object.entries(this.layers)) {
                if (this.map.hasLayer(layer)) {
                    activeLayers.push(name);
                }
            }
            
            const state = {
                center: {
                    lat: center.lat,
                    lon: center.lng
                },
                zoom: zoom,
                bounds: {
                    north: bounds.getNorth(),
                    south: bounds.getSouth(),
                    east: bounds.getEast(),
                    west: bounds.getWest()
                },
                active_layers: activeLayers
            };
            
            const response = await fetch('/api/helia/map/state', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(state)
            });
            
            if (!response.ok) {
                console.warn('⚠️ Erreur sync état carte:', await response.text());
            }
        } catch (error) {
            console.error('❌ Erreur sendMapState:', error);
        }
    }
    
    /**
     * Démarre le polling des commandes Helia
     */
    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        this.pollCommands();
    }
    
    /**
     * Arrête le polling
     */
    stopPolling() {
        this.isPolling = false;
    }
    
    /**
     * Récupère et exécute les commandes de carte depuis Helia
     */
    async pollCommands() {
        if (!this.isPolling) return;
        
        try {
            const response = await fetch('/api/helia/map/commands');
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.commands && data.commands.length > 0) {
                    console.log(`📥 ${data.commands.length} commande(s) Helia reçue(s)`);
                    
                    for (const command of data.commands) {
                        await this.executeCommand(command);
                    }
                }
            }
        } catch (error) {
            console.error('❌ Erreur polling commandes:', error);
        }
        
        // Continuer le polling
        if (this.isPolling) {
            setTimeout(() => this.pollCommands(), this.pollInterval);
        }
    }
    
    /**
     * Exécute une commande de carte
     */
    async executeCommand(command) {
        console.log('🎬 Exécution commande:', command);
        
        try {
            switch (command.action) {
                case 'toggle_layer':
                    this.toggleLayer(command.layer_name, command.visible);
                    break;
                    
                case 'zoom_to':
                    this.zoomToLocation(command.lat, command.lon, command.zoom);
                    break;
                    
                default:
                    console.warn('⚠️ Commande inconnue:', command.action);
            }
        } catch (error) {
            console.error('❌ Erreur exécution commande:', error);
        }
    }
    
    /**
     * Active/désactive un calque
     */
    toggleLayer(layerName, visible) {
        const layer = this.layers[layerName];
        
        if (!layer) {
            console.warn(`⚠️ Calque inconnu: ${layerName}`);
            console.log('Calques disponibles:', Object.keys(this.layers));
            return;
        }
        
        if (visible) {
            if (!this.map.hasLayer(layer)) {
                this.map.addLayer(layer);
                console.log(`✅ Calque ${layerName} activé`);
                this.showNotification(`Calque ${layerName} activé`, 'success');
            }
        } else {
            if (this.map.hasLayer(layer)) {
                this.map.removeLayer(layer);
                console.log(`✅ Calque ${layerName} désactivé`);
                this.showNotification(`Calque ${layerName} désactivé`, 'info');
            }
        }
        
        // Mettre à jour l'état après changement
        setTimeout(() => this.sendMapState(), 100);
    }
    
    /**
     * Centre la carte sur une position
     */
    zoomToLocation(lat, lon, zoom = 15) {
        console.log(`🎯 Zoom vers [${lat}, ${lon}] niveau ${zoom}`);
        
        // Animation de zoom
        this.map.flyTo([lat, lon], zoom, {
            duration: 1.5,
            easeLinearity: 0.5
        });
        
        // Ajouter un marqueur temporaire
        const marker = L.marker([lat, lon], {
            icon: L.divIcon({
                className: 'helia-marker',
                html: '<div style="background: #FFD700; border: 3px solid #FF6B00; border-radius: 50%; width: 30px; height: 30px; box-shadow: 0 0 20px rgba(255,107,0,0.8);"></div>',
                iconSize: [30, 30]
            })
        }).addTo(this.map);
        
        // Retirer le marqueur après 3 secondes
        setTimeout(() => {
            this.map.removeLayer(marker);
        }, 3000);
        
        this.showNotification('🎯 Carte centrée par Helia', 'success');
    }
    
    /**
     * Affiche une notification visuelle
     */
    showNotification(message, type = 'info') {
        // Créer l'élément de notification
        const notification = document.createElement('div');
        notification.className = `helia-notification helia-notification-${type}`;
        notification.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
                color: white;
                padding: 15px 25px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                animation: slideInRight 0.3s ease-out;
            ">
                <i class="fas fa-robot"></i> ${message}
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Retirer après 3 secondes
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    /**
     * Enregistre automatiquement les calques standard
     */
    autoRegisterStandardLayers(layerConfig) {
        // Mapping des noms de calques
        const layerMapping = {
            'postes_bt': 'Postes BT',
            'postes_hta': 'Postes HTA',
            'lignes_hta': 'Lignes HTA',
            'capacites_accueil': 'Capacités d\'accueil',
            'rpg': 'RPG',
            'cadastre': 'Cadastre',
            'plu': 'PLU',
            'risques': 'Risques',
            'satellite': 'Satellite',
            'osm': 'OpenStreetMap'
        };
        
        // Enregistrer chaque calque
        for (const [key, layer] of Object.entries(layerConfig)) {
            if (layerMapping[key]) {
                this.registerLayer(key, layer);
            }
        }
    }
}

// Ajouter les animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .helia-marker {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.3);
            opacity: 0.7;
        }
    }
`;
document.head.appendChild(style);

// Export global
window.HeliaMapSync = HeliaMapSync;
