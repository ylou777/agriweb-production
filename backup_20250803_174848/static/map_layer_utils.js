// Utility functions for map layer interaction and dynamic report features

function showLayerOnMap(layerName) {
    // Function to highlight and center on a specific layer
    console.log('Showing layer on map:', layerName);
    
    if (typeof window.map !== 'undefined' && window.map) {
        try {
            // Example for Leaflet integration:
            // window.map.eachLayer(function(layer) {
            //     if (layer.options && layer.options.layerName === layerName) {
            //         window.map.fitBounds(layer.getBounds());
            //         layer.openPopup();
            //     }
            // });
            
            // For now, show enhanced notification with layer information
            showLayerNotification(layerName);
            
        } catch (error) {
            console.error('Error showing layer on map:', error);
            alert('Erreur lors de l\'affichage de la couche: ' + layerName);
        }
    } else {
        console.warn('Map object not found, opening in new window');
        // Try to open the map in a new window if available
        const mapUrl = document.querySelector('iframe[title="Carte interactive"]')?.src;
        if (mapUrl) {
            window.open(mapUrl, '_blank', 'width=1200,height=800');
        } else {
            alert('Carte non disponible. Veuillez générer le rapport avec la carte activée.');
        }
    }
}

function showLayerNotification(layerName) {
    // Create and show a notification for layer interaction
    const notification = document.createElement('div');
    notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-map me-2"></i>
            <div>
                <strong>Couche sélectionnée:</strong><br>
                <small>${layerName}</small><br>
                <small class="text-muted">Consultez la carte interactive pour plus de détails</small>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function highlightFeature(featureId) {
    console.log('Highlighting feature:', featureId);
    // Enhanced feature highlighting with visual feedback
    const element = document.getElementById(featureId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.style.transition = 'all 0.3s ease';
        element.style.backgroundColor = 'rgba(255, 193, 7, 0.3)';
        element.style.border = '2px solid #ffc107';
        
        setTimeout(() => {
            element.style.backgroundColor = '';
            element.style.border = '';
        }, 2000);
    }
}

function zoomToLayer(layerName) {
    console.log('Zooming to layer:', layerName);
    // Implementation for zooming to layer extent
    showLayerOnMap(layerName);
}

// Enhanced interaction functions for rapport features
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const isHidden = section.style.display === 'none';
        section.style.display = isHidden ? 'block' : 'none';
        
        // Update button text if there's a toggle button
        const toggleBtn = document.querySelector(`[data-target="#${sectionId}"]`);
        if (toggleBtn) {
            toggleBtn.textContent = isHidden ? 'Masquer' : 'Afficher';
        }
    }
}

function filterTableRows(tableId, searchTerm) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

// Initialize enhanced features when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add search functionality to tables
    const tables = document.querySelectorAll('table');
    tables.forEach((table, index) => {
        if (table.rows.length > 5) { // Only add search for tables with many rows
            addTableSearch(table, `table-search-${index}`);
        }
    });
    
    // Enhance metric cards with click interactions
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach(card => {
        card.style.cursor = 'pointer';
        card.addEventListener('click', function() {
            this.style.transform = 'scale(1.02)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
        });
    });
});

function addTableSearch(table, searchId) {
    const searchContainer = document.createElement('div');
    searchContainer.className = 'mb-2';
    searchContainer.innerHTML = `
        <input type="text" class="form-control form-control-sm" 
               id="${searchId}" 
               placeholder="Rechercher dans le tableau..." 
               onkeyup="filterTableRows('${table.id}', this.value)">
    `;
    
    // Insert search before table
    table.parentNode.insertBefore(searchContainer, table);
    
    // Assign ID to table if it doesn't have one
    if (!table.id) {
        table.id = searchId.replace('search', 'table');
    }
}
