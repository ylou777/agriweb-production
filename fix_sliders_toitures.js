// === CORRECTION POUR LES SLIDERS TOITURES ===
// Code à ajouter/remplacer dans search_panel.html

document.addEventListener('DOMContentLoaded', function() {
  console.log('🔧 [SLIDERS] Initialisation des sliders toitures...');
  
  // Fonction robuste pour configurer les sliders
  function setupSliderWithRetry(sliderId, displayId, suffix = '', maxRetries = 5) {
    let attempts = 0;
    
    const trySetup = () => {
      attempts++;
      const slider = document.getElementById(sliderId);
      const display = document.getElementById(displayId);
      
      console.log(`🔧 [SLIDERS] Tentative ${attempts} pour ${sliderId}: slider=${!!slider}, display=${!!display}`);
      
      if (slider && display) {
        const updateDisplay = () => {
          const value = slider.value + suffix;
          display.textContent = value;
          console.log(`🔧 [SLIDERS] Mis à jour ${displayId}: ${value}`);
        };
        
        // Plusieurs événements pour assurer la compatibilité
        slider.addEventListener('input', updateDisplay);
        slider.addEventListener('change', updateDisplay);
        slider.addEventListener('mousemove', updateDisplay);
        
        // Valeur initiale
        updateDisplay();
        
        console.log(`✅ [SLIDERS] ${sliderId} configuré avec succès`);
        return true;
      } else if (attempts < maxRetries) {
        console.log(`⏳ [SLIDERS] Nouvel essai dans 200ms pour ${sliderId}...`);
        setTimeout(trySetup, 200);
        return false;
      } else {
        console.error(`❌ [SLIDERS] Échec configuration ${sliderId} après ${maxRetries} tentatives`);
        return false;
      }
    };
    
    trySetup();
  }
  
  // Configuration avec délai pour s'assurer que tout est chargé
  setTimeout(() => {
    console.log('🔧 [SLIDERS] Configuration des sliders avec délai...');
    
    setupSliderWithRetry('min_surface_toiture', 'minSurfaceToitureVal', ' m²');
    setupSliderWithRetry('max_distance_bt_toitures', 'maxDistanceBtToituresVal', ' m');
    setupSliderWithRetry('max_distance_hta_toitures', 'maxDistanceHtaToituresVal', ' m');
    
    // Test de vérification après configuration
    setTimeout(() => {
      console.log('🔧 [SLIDERS] Vérification finale...');
      
      const testIds = [
        'min_surface_toiture',
        'max_distance_bt_toitures', 
        'max_distance_hta_toitures'
      ];
      
      testIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
          console.log(`✅ [SLIDERS] ${id} valeur: ${element.value}`);
        } else {
          console.error(`❌ [SLIDERS] ${id} non trouvé`);
        }
      });
    }, 1000);
    
  }, 100);
  
  // Fonction alternative directe (au cas où)
  window.updateToituresSliders = function() {
    console.log('🔧 [SLIDERS] Mise à jour manuelle des sliders...');
    
    const sliders = [
      { id: 'min_surface_toiture', display: 'minSurfaceToitureVal', suffix: ' m²' },
      { id: 'max_distance_bt_toitures', display: 'maxDistanceBtToituresVal', suffix: ' m' },
      { id: 'max_distance_hta_toitures', display: 'maxDistanceHtaToituresVal', suffix: ' m' }
    ];
    
    sliders.forEach(config => {
      const slider = document.getElementById(config.id);
      const display = document.getElementById(config.display);
      
      if (slider && display) {
        display.textContent = slider.value + config.suffix;
        console.log(`✅ [SLIDERS] Mis à jour manuellement ${config.id}: ${slider.value}`);
      }
    });
  };
});
