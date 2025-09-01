/* 
 * Fonction simplifiée pour l'affichage de carte dans l'iframe
 * Remplace la logique complexe dans search_panel.html
 */

function displayMapInIframe(carteUrl) {
    console.log('🚀 [SIMPLE_DISPLAY] Affichage simple de la carte');
    console.log('🔍 carte_url reçue:', carteUrl);
    
    // Construire l'URL complète de la carte
    const baseUrl = window.location.origin;
    const absoluteUrl = carteUrl.startsWith('http') ? carteUrl : baseUrl + carteUrl;
    const newUrl = absoluteUrl + (absoluteUrl.includes('?') ? '&' : '?') + 't=' + Date.now();
    console.log('🎯 URL carte finale:', newUrl);
    
    // Trouver l'iframe directement
    const mapFrame = document.getElementById('mapFrame');
    
    if (mapFrame) {
        console.log('✅ Iframe mapFrame trouvé, mise à jour...');
        appendLog('✅ Carte générée ! Chargement dans l\'interface...');
        
        // Changer la source de l'iframe
        mapFrame.src = newUrl;
        
        // Gérer les événements de chargement
        mapFrame.onload = function() {
            console.log('✅ Carte chargée avec succès dans l\'iframe');
            appendLog('✅ Carte affichée avec succès !');
        };
        
        mapFrame.onerror = function() {
            console.error('❌ Erreur de chargement de la carte dans l\'iframe');
            appendLog('❌ Erreur de chargement - <a href="' + newUrl + '" target="_blank" style="color: #007bff;">Cliquez ici pour voir la carte</a>');
        };
        
        return true; // Succès
        
    } else {
        console.warn('⚠️ Iframe mapFrame non trouvé');
        appendLog('⚠️ Interface non disponible - <a href="' + newUrl + '" target="_blank" style="color: #007bff;">Cliquez ici pour voir la carte</a>');
        return false; // Échec
    }
}

// Fonction pour tester l'iframe
function testIframe() {
    const mapFrame = document.getElementById('mapFrame');
    console.log('=== TEST IFRAME ===');
    console.log('mapFrame element:', mapFrame);
    if (mapFrame) {
        console.log('Current src:', mapFrame.src);
        console.log('Dimensions:', mapFrame.offsetWidth, 'x', mapFrame.offsetHeight);
        console.log('Visible:', mapFrame.offsetParent !== null);
        console.log('Parent:', mapFrame.parentElement);
    } else {
        console.log('❌ Iframe mapFrame non trouvé !');
    }
    console.log('==================');
}

// Fonction pour appendLog si elle n'existe pas
if (typeof appendLog === 'undefined') {
    function appendLog(message) {
        console.log('[LOG]', message);
    }
}
