/**
 * Module de visualisation 3D WebGL pour le calpinage PV
 * Utilise Three.js pour afficher les toitures et modules en 3D
 */

class Calpinage3DViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.modules3D = [];
        this.building3D = null;
        this.sunLight = null;
        this.isActive = false;
        
        // Configuration
        this.moduleThickness = 0.04; // 4cm d'épaisseur pour les modules
        this.buildingHeight = 8; // Hauteur par défaut du bâtiment (mètres)
    }
    
    /**
     * Initialiser la scène 3D
     */
    init() {
        if (this.isActive) return;
        
        console.log('🌐 Initialisation de la vue 3D WebGL...');
        
        // Créer la scène
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x87ceeb); // Bleu ciel
        this.scene.fog = new THREE.Fog(0x87ceeb, 100, 500);
        
        // Caméra perspective
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
        this.camera.position.set(50, 40, 50);
        this.camera.lookAt(0, 0, 0);
        
        // Renderer WebGL avec antialiasing
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.0;
        
        this.container.appendChild(this.renderer.domElement);
        
        // Contrôles orbitaux (rotation, zoom, pan)
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI / 2; // Empêcher de passer sous le sol
        this.controls.minDistance = 10;
        this.controls.maxDistance = 200;
        
        // Lumières
        this.setupLights();
        
        // Sol (grille)
        this.addGround();
        
        // Axes de référence (debug)
        const axesHelper = new THREE.AxesHelper(20);
        this.scene.add(axesHelper);
        
        // Gestion du redimensionnement
        window.addEventListener('resize', () => this.onWindowResize(), false);
        
        // Démarrer l'animation
        this.animate();
        
        this.isActive = true;
        console.log('✅ Vue 3D initialisée avec succès');
    }
    
    /**
     * Configuration des lumières
     */
    setupLights() {
        // Lumière ambiante (éclairage général)
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);
        
        // Soleil (lumière directionnelle avec ombres)
        this.sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
        this.sunLight.position.set(50, 80, 50);
        this.sunLight.castShadow = true;
        
        // Configuration des ombres
        this.sunLight.shadow.mapSize.width = 2048;
        this.sunLight.shadow.mapSize.height = 2048;
        this.sunLight.shadow.camera.near = 0.5;
        this.sunLight.shadow.camera.far = 500;
        this.sunLight.shadow.camera.left = -100;
        this.sunLight.shadow.camera.right = 100;
        this.sunLight.shadow.camera.top = 100;
        this.sunLight.shadow.camera.bottom = -100;
        
        this.scene.add(this.sunLight);
        
        // Helper pour visualiser la direction du soleil (debug)
        // const sunHelper = new THREE.DirectionalLightHelper(this.sunLight, 5);
        // this.scene.add(sunHelper);
        
        // Lumière hémisphérique (ciel/sol)
        const hemiLight = new THREE.HemisphereLight(0x87ceeb, 0x6b8e23, 0.3);
        this.scene.add(hemiLight);
    }
    
    /**
     * Ajouter un sol avec grille
     */
    addGround() {
        // Grille au sol
        const gridHelper = new THREE.GridHelper(200, 40, 0x888888, 0xcccccc);
        this.scene.add(gridHelper);
        
        // Plan au sol (pour recevoir les ombres)
        const groundGeometry = new THREE.PlaneGeometry(200, 200);
        const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.3 });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }
    
    /**
     * Créer un bâtiment 3D à partir des zones de calpinage
     */
    createBuildingFromZones(zones) {
        // Supprimer l'ancien bâtiment s'il existe
        if (this.building3D) {
            this.scene.remove(this.building3D);
        }
        
        if (!zones || zones.length === 0) return;
        
        // Groupe pour le bâtiment
        this.building3D = new THREE.Group();
        
        // Calculer le centre moyen des zones
        let centerX = 0, centerZ = 0;
        zones.forEach(zone => {
            const bounds = zone.layer.getBounds();
            const center = bounds.getCenter();
            centerX += this.latLngToMeters(center.lat, center.lng).x;
            centerZ += this.latLngToMeters(center.lat, center.lng).z;
        });
        centerX /= zones.length;
        centerZ /= zones.length;
        
        // Créer une toiture pour chaque zone
        zones.forEach((zone, index) => {
            const bounds = zone.layer.getBounds();
            const sw = bounds.getSouthWest();
            const ne = bounds.getNorthEast();
            
            // Convertir lat/lng en coordonnées métriques
            const swMeters = this.latLngToMeters(sw.lat, sw.lng);
            const neMeters = this.latLngToMeters(ne.lat, ne.lng);
            
            const width = Math.abs(neMeters.x - swMeters.x);
            const depth = Math.abs(neMeters.z - swMeters.z);
            const centerMeters = this.latLngToMeters(
                (sw.lat + ne.lat) / 2,
                (sw.lng + ne.lng) / 2
            );
            
            // Hauteur du bâtiment basée sur le type d'installation
            let height = this.buildingHeight;
            const typeInstallation = document.getElementById('typeInstallation')?.value || 'toiture';
            if (typeInstallation === 'sol') {
                height = 0.5; // Installation au sol (très basse)
            } else if (typeInstallation === 'ombriere') {
                height = 4; // Ombrière de parking
            }
            
            // Créer le toit (simple pour l'instant)
            const inclinaison = zone.inclinaison || 0;
            const orientation = zone.orientation || 180;
            
            // Bâtiment (murs)
            const buildingGeometry = new THREE.BoxGeometry(width, height, depth);
            const buildingMaterial = new THREE.MeshStandardMaterial({
                color: 0x8b7355,
                roughness: 0.8,
                metalness: 0.2
            });
            const buildingMesh = new THREE.Mesh(buildingGeometry, buildingMaterial);
            buildingMesh.position.set(
                centerMeters.x - centerX,
                height / 2,
                centerMeters.z - centerZ
            );
            buildingMesh.castShadow = true;
            buildingMesh.receiveShadow = true;
            this.building3D.add(buildingMesh);
            
            // Toit incliné
            if (inclinaison > 0) {
                const roofGroup = this.createInclinedRoof(width, depth, inclinaison, orientation);
                roofGroup.position.set(
                    centerMeters.x - centerX,
                    height,
                    centerMeters.z - centerZ
                );
                this.building3D.add(roofGroup);
            }
        });
        
        this.scene.add(this.building3D);
        
        // Centrer la caméra sur le bâtiment
        this.camera.lookAt(0, this.buildingHeight / 2, 0);
    }
    
    /**
     * Créer un toit incliné
     */
    createInclinedRoof(width, depth, inclinaisonDegres, orientationDegres) {
        const group = new THREE.Group();
        
        const inclinaisonRad = inclinaisonDegres * Math.PI / 180;
        const hauteurMax = Math.tan(inclinaisonRad) * (depth / 2);
        
        // Géométrie du toit (forme en pente)
        const roofShape = new THREE.Shape();
        roofShape.moveTo(-width/2, 0);
        roofShape.lineTo(width/2, 0);
        roofShape.lineTo(width/2, hauteurMax);
        roofShape.lineTo(-width/2, hauteurMax);
        roofShape.lineTo(-width/2, 0);
        
        const extrudeSettings = {
            steps: 1,
            depth: depth,
            bevelEnabled: false
        };
        
        const roofGeometry = new THREE.ExtrudeGeometry(roofShape, extrudeSettings);
        const roofMaterial = new THREE.MeshStandardMaterial({
            color: 0x8b4513,
            roughness: 0.7,
            metalness: 0.1
        });
        
        const roof = new THREE.Mesh(roofGeometry, roofMaterial);
        roof.rotation.x = -Math.PI / 2;
        roof.position.z = -depth / 2;
        roof.castShadow = true;
        roof.receiveShadow = true;
        
        group.add(roof);
        
        // Rotation selon l'orientation
        group.rotation.y = (orientationDegres - 180) * Math.PI / 180;
        
        return group;
    }
    
    /**
     * Ajouter les modules PV en 3D
     */
    addModules3D(zones) {
        // Supprimer les anciens modules
        this.modules3D.forEach(module => {
            this.scene.remove(module);
        });
        this.modules3D = [];
        
        if (!zones || zones.length === 0) return;
        
        // Calculer le centre de référence
        let centerX = 0, centerZ = 0;
        zones.forEach(zone => {
            const bounds = zone.layer.getBounds();
            const center = bounds.getCenter();
            const meters = this.latLngToMeters(center.lat, center.lng);
            centerX += meters.x;
            centerZ += meters.z;
        });
        centerX /= zones.length;
        centerZ /= zones.length;
        
        // Créer les modules pour chaque zone
        zones.forEach(zone => {
            if (!zone.modulesPositions || zone.modulesPositions.length === 0) return;
            
            const moduleLongueurMM = parseFloat(document.getElementById('moduleLongueur')?.value || 2278);
            const moduleLargeurMM = parseFloat(document.getElementById('moduleLargeur')?.value || 1134);
            const moduleOrientation = document.getElementById('moduleOrientation')?.value || 'paysage';
            
            // Dimensions en mètres
            const moduleLongueur = moduleLongueurMM / 1000;
            const moduleLargeur = moduleLargeurMM / 1000;
            
            // Dimensions selon l'orientation
            const moduleWidth = moduleOrientation === 'paysage' ? moduleLongueur : moduleLargeur;
            const moduleDepth = moduleOrientation === 'paysage' ? moduleLargeur : moduleLongueur;
            
            // Géométrie du module (une seule fois pour optimisation)
            const moduleGeometry = new THREE.BoxGeometry(moduleWidth, this.moduleThickness, moduleDepth);
            
            // Matériau des modules PV (bleu foncé brillant)
            const moduleMaterial = new THREE.MeshStandardMaterial({
                color: 0x1e3a8a,
                roughness: 0.3,
                metalness: 0.7,
                emissive: 0x0a1f5a,
                emissiveIntensity: 0.1
            });
            
            // Créer chaque module
            zone.modulesPositions.forEach(modulePos => {
                const meters = this.latLngToMeters(modulePos.lat, modulePos.lng);
                
                const module = new THREE.Mesh(moduleGeometry, moduleMaterial);
                
                // Position du module
                module.position.set(
                    meters.x - centerX,
                    this.buildingHeight + 0.1, // Légèrement au-dessus du toit
                    meters.z - centerZ
                );
                
                // Inclinaison du module
                const inclinaison = zone.inclinaison || 0;
                module.rotation.x = -inclinaison * Math.PI / 180;
                
                // Rotation selon l'orientation du panneau
                const rotationAngle = zone.rotationAngle || 0;
                module.rotation.y = -rotationAngle * Math.PI / 180;
                
                module.castShadow = true;
                module.receiveShadow = true;
                
                this.scene.add(module);
                this.modules3D.push(module);
            });
        });
        
        console.log(`✅ ${this.modules3D.length} modules PV ajoutés en 3D`);
    }
    
    /**
     * Convertir latitude/longitude en coordonnées métriques (simplifiée)
     */
    latLngToMeters(lat, lng) {
        // Utiliser une projection simple pour la visualisation locale
        // (pour de petites distances, on peut approximer)
        const latRef = prospectLat || 46.5; // Centre France par défaut
        const metersPerDegreeLat = 111320;
        const metersPerDegreeLng = 111320 * Math.cos(latRef * Math.PI / 180);
        
        const x = (lng - (prospectLon || 0)) * metersPerDegreeLng;
        const z = -(lat - (prospectLat || 0)) * metersPerDegreeLat; // Inverser Z
        
        return { x, z };
    }
    
    /**
     * Mettre à jour la position du soleil (heure/saison)
     */
    updateSunPosition(hour = 12, month = 6) {
        if (!this.sunLight) return;
        
        // Simulation simplifiée de la position du soleil
        // Angle horaire (-180° à 180°, midi = 0°)
        const hourAngle = ((hour - 12) / 12) * 180;
        
        // Élévation selon le mois (été = haute, hiver = basse)
        const elevation = 30 + (month - 6) * 5; // 30° à 60°
        
        const distance = 100;
        const elevationRad = elevation * Math.PI / 180;
        const hourAngleRad = hourAngle * Math.PI / 180;
        
        this.sunLight.position.set(
            distance * Math.cos(elevationRad) * Math.sin(hourAngleRad),
            distance * Math.sin(elevationRad),
            distance * Math.cos(elevationRad) * Math.cos(hourAngleRad)
        );
        
        console.log(`☀️ Soleil mis à jour: ${hour}h (mois ${month})`);
    }
    
    /**
     * Boucle d'animation
     */
    animate() {
        if (!this.isActive) return;
        
        requestAnimationFrame(() => this.animate());
        
        // Mettre à jour les contrôles
        if (this.controls) {
            this.controls.update();
        }
        
        // Rendu de la scène
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }
    
    /**
     * Gestion du redimensionnement de la fenêtre
     */
    onWindowResize() {
        if (!this.camera || !this.renderer || !this.container) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }
    
    /**
     * Activer/désactiver la vue 3D
     */
    toggle() {
        if (this.isActive) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    /**
     * Afficher la vue 3D
     */
    show() {
        this.container.style.display = 'block';
        if (!this.renderer) {
            this.init();
        }
        this.isActive = true;
        this.animate();
        this.onWindowResize();
    }
    
    /**
     * Masquer la vue 3D
     */
    hide() {
        this.container.style.display = 'none';
        this.isActive = false;
    }
    
    /**
     * Nettoyer les ressources
     */
    dispose() {
        if (this.renderer) {
            this.renderer.dispose();
            this.container.removeChild(this.renderer.domElement);
        }
        this.isActive = false;
    }
}
