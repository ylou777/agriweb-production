/**
 * Module de visualisation 3D WebGL pour le calpinage PV
 * Version corrigée avec support ombrières
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
        this.sunLight.shadow.camera.near = 10;
        this.sunLight.shadow.camera.far = 200;
        this.sunLight.shadow.camera.left = -50;
        this.sunLight.shadow.camera.right = 50;
        this.sunLight.shadow.camera.top = 50;
        this.sunLight.shadow.camera.bottom = -50;
        
        this.scene.add(this.sunLight);
        
        // Helper pour visualiser les ombres (debug)
        // const shadowHelper = new THREE.CameraHelper(this.sunLight.shadow.camera);
        // this.scene.add(shadowHelper);
    }
    
    /**
     * Ajouter un sol avec grille
     */
    addGround() {
        // Sol
        const groundGeometry = new THREE.PlaneGeometry(200, 200);
        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0x4a7c59,
            roughness: 0.8,
            metalness: 0
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = 0;
        ground.receiveShadow = true;
        this.scene.add(ground);
        
        // Grille
        const gridHelper = new THREE.GridHelper(200, 40, 0x666666, 0x444444);
        gridHelper.position.y = 0.01; // Légèrement au-dessus du sol
        this.scene.add(gridHelper);
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
        
        // Déterminer le type d'installation
        const typeInstallation = document.getElementById('typeInstallation')?.value || 'toiture';
        
        // Créer la structure selon le type
        if (typeInstallation === 'ombriere') {
            // Créer les structures d'ombrière pour chaque zone
            zones.forEach((zone, index) => {
                const structure = this.createOmbriereStructure(zone, centerX, centerZ);
                if (structure) {
                    this.building3D.add(structure);
                }
            });
        } else {
            // Créer une toiture standard pour chaque zone
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
                
                // Hauteur du bâtiment
                let height = this.buildingHeight;
                if (typeInstallation === 'sol') {
                    height = 0.5; // Installation au sol
                }
                
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
        }
        
        this.scene.add(this.building3D);
        
        // Centrer la caméra sur le bâtiment
        this.camera.lookAt(0, this.buildingHeight / 2, 0);
    }
    
    /**
     * Créer une structure d'ombrière de parking
     */
    createOmbriereStructure(zone, centerX, centerZ) {
        const group = new THREE.Group();
        
        // Récupérer les paramètres de l'ombrière
        const hauteur = parseFloat(document.getElementById('ombriereHauteur')?.value || 4.5);
        const hauteurFerme = parseFloat(document.getElementById('ombriereHauteurFerme')?.value || 0.8);
        const diametrePilier = parseFloat(document.getElementById('ombriereDiametrePilier')?.value || 15) / 100; // cm -> m
        const sectionPanne = parseFloat(document.getElementById('ombriereSectionPanne')?.value || 10) / 100;
        const sectionFerme = parseFloat(document.getElementById('ombriereSectionFerme')?.value || 8) / 100;
        
        // Récupérer les dimensions de la zone
        const bounds = zone.layer.getBounds();
        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();
        const swMeters = this.latLngToMeters(sw.lat, sw.lng);
        const neMeters = this.latLngToMeters(ne.lat, ne.lng);
        
        const width = Math.abs(neMeters.x - swMeters.x);
        const depth = Math.abs(neMeters.z - swMeters.z);
        const centerMeters = this.latLngToMeters(
            (sw.lat + ne.lat) / 2,
            (sw.lng + ne.lng) / 2
        );
        
        const offsetX = centerMeters.x - centerX;
        const offsetZ = centerMeters.z - centerZ;
        
        // Matériau métallique
        const metalMaterial = new THREE.MeshStandardMaterial({
            color: 0x808080,
            roughness: 0.5,
            metalness: 0.8
        });
        
        // Créer les piliers aux 4 coins
        const pilierGeometry = new THREE.CylinderGeometry(diametrePilier / 2, diametrePilier / 2, hauteur, 12);
        const pilierPositions = [
            { x: -width/2 + 0.5, z: -depth/2 + 0.5 },
            { x: width/2 - 0.5, z: -depth/2 + 0.5 },
            { x: -width/2 + 0.5, z: depth/2 - 0.5 },
            { x: width/2 - 0.5, z: depth/2 - 0.5 }
        ];
        
        pilierPositions.forEach(pos => {
            const pilier = new THREE.Mesh(pilierGeometry, metalMaterial);
            pilier.position.set(offsetX + pos.x, hauteur / 2, offsetZ + pos.z);
            pilier.castShadow = true;
            pilier.receiveShadow = true;
            group.add(pilier);
        });
        
        // Créer les pannes (poutres horizontales longitudinales)
        const panneGeometry = new THREE.BoxGeometry(sectionPanne, sectionPanne, depth);
        const pannePositions = [
            { x: -width/2 + 0.5 },
            { x: width/2 - 0.5 }
        ];
        
        pannePositions.forEach(pos => {
            const panne = new THREE.Mesh(panneGeometry, metalMaterial);
            panne.position.set(offsetX + pos.x, hauteur, offsetZ);
            panne.castShadow = true;
            panne.receiveShadow = true;
            group.add(panne);
        });
        
        // Créer les fermes (poutres transversales avec inclinaison)
        const inclinaison = zone.inclinaison || 10;
        const inclinaisonRad = inclinaison * Math.PI / 180;
        const hauteurFermeReelle = Math.tan(inclinaisonRad) * (width / 2) + sectionFerme/2;
        
        // Nombre de fermes selon la profondeur
        const nbFermes = Math.max(2, Math.floor(depth / 3));
        const espacementFermes = depth / (nbFermes + 1);
        
        for (let i = 1; i <= nbFermes; i++) {
            const zPos = -depth/2 + i * espacementFermes;
            
            // Ferme gauche (montante)
            const fermeGeometry1 = new THREE.BoxGeometry(sectionFerme, sectionFerme, width/2 + 0.2);
            const ferme1 = new THREE.Mesh(fermeGeometry1, metalMaterial);
            ferme1.position.set(offsetX - width/4, hauteur + hauteurFermeReelle/2, offsetZ + zPos);
            ferme1.rotation.x = Math.PI / 2;
            ferme1.rotation.z = inclinaisonRad;
            ferme1.castShadow = true;
            group.add(ferme1);
            
            // Ferme droite (descendante)
            const ferme2 = new THREE.Mesh(fermeGeometry1, metalMaterial);
            ferme2.position.set(offsetX + width/4, hauteur + hauteurFermeReelle/2, offsetZ + zPos);
            ferme2.rotation.x = Math.PI / 2;
            ferme2.rotation.z = -inclinaisonRad;
            ferme2.castShadow = true;
            group.add(ferme2);
            
            // Poutre faîtière (au sommet)
            const faitiereGeometry = new THREE.BoxGeometry(sectionFerme, sectionFerme, sectionFerme * 3);
            const faitiere = new THREE.Mesh(faitiereGeometry, metalMaterial);
            faitiere.position.set(offsetX, hauteur + hauteurFerme, offsetZ + zPos);
            faitiere.castShadow = true;
            group.add(faitiere);
        }
        
        // Appliquer la rotation de la structure selon l'orientation de la zone
        const orientation = zone.orientation || 180;
        const rotationAngle = zone.rotationAngle || 0;
        group.rotation.y = -rotationAngle * Math.PI / 180;
        
        return group;
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
     * Ajouter les modules PV en 3D (VERSION CORRIGÉE - un seul affichage)
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
        
        // Récupérer le type d'installation
        const typeInstallation = document.getElementById('typeInstallation')?.value || 'toiture';
        
        // Créer les modules pour chaque zone
        zones.forEach(zone => {
            if (!zone.modulesPositions || zone.modulesPositions.length === 0) return;
            
            const moduleLongueurMM = parseFloat(document.getElementById('moduleLongueur')?.value || 2278);
            const moduleLargeurMM = parseFloat(document.getElementById('moduleLargeur')?.value || 1134);
            const moduleOrientation = zone.moduleOrientation || 'paysage';
            
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
            
            // Calculer la hauteur de base selon le type d'installation
            let baseHeight = this.buildingHeight;
            if (typeInstallation === 'sol') {
                baseHeight = 0.5;
            } else if (typeInstallation === 'ombriere') {
                const hauteur = parseFloat(document.getElementById('ombriereHauteur')?.value || 4.5);
                const hauteurFerme = parseFloat(document.getElementById('ombriereHauteurFerme')?.value || 0.8);
                baseHeight = hauteur + hauteurFerme;
            }
            
            // Créer un groupe pour tous les modules de cette zone
            const zoneModulesGroup = new THREE.Group();
            
            // Calculer le centre de la zone pour la rotation
            const bounds = zone.layer.getBounds();
            const center = bounds.getCenter();
            const centerMeters = this.latLngToMeters(center.lat, center.lng);
            
            // Créer chaque module
            zone.modulesPositions.forEach(modulePos => {
                const meters = this.latLngToMeters(modulePos.lat, modulePos.lng);
                
                const module = new THREE.Mesh(moduleGeometry, moduleMaterial);
                
                // Position relative au centre de la zone
                module.position.set(
                    meters.x - centerMeters.x,
                    baseHeight + this.moduleThickness/2,
                    meters.z - centerMeters.z
                );
                
                // Inclinaison du module (plan incliné global, pas individuel)
                const inclinaison = zone.inclinaison || 0;
                module.rotation.x = -inclinaison * Math.PI / 180;
                
                module.castShadow = true;
                module.receiveShadow = true;
                
                zoneModulesGroup.add(module);
            });
            
            // Positionner le groupe au centre de la zone
            zoneModulesGroup.position.set(
                centerMeters.x - centerX,
                0,
                centerMeters.z - centerZ
            );
            
            // Rotation du groupe entier selon l'orientation de la zone
            const rotationAngle = zone.rotationAngle || 0;
            zoneModulesGroup.rotation.y = -rotationAngle * Math.PI / 180;
            
            this.scene.add(zoneModulesGroup);
            this.modules3D.push(zoneModulesGroup);
        });
        
        console.log(`✅ ${this.modules3D.length} modules PV ajoutés en 3D`);
    }
    
    /**
     * Convertir latitude/longitude en coordonnées métriques (simplifiée)
     */
    latLngToMeters(lat, lng) {
        // Utiliser une projection simple pour la visualisation locale
        const latRef = prospectLat || 46.5;
        const metersPerDegreeLat = 111320;
        const metersPerDegreeLng = 111320 * Math.cos(latRef * Math.PI / 180);
        
        const x = (lng - (prospectLon || 0)) * metersPerDegreeLng;
        const z = -(lat - (prospectLat || 0)) * metersPerDegreeLat;
        
        return { x, z };
    }
    
    /**
     * Mettre à jour la position du soleil (heure/saison)
     */
    updateSunPosition(hour = 12, month = 6) {
        if (!this.sunLight) return;
        
        // Simulation simplifiée de la position du soleil
        const hourAngle = ((hour - 12) / 12) * 180;
        const elevation = 30 + (month - 6) * 5;
        
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
        
        if (this.controls) {
            this.controls.update();
        }
        
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
