/**
 * Système d'autocomplétion pour recherche d'adresses et communes
 * Avec tolérance aux fautes de frappe et debouncing
 */

class Autocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minChars: 3,
            debounceMs: 300,
            maxSuggestions: 8,
            apiEndpoint: options.apiEndpoint || '/api/autocomplete/address',
            onSelect: options.onSelect || (() => {}),
            placeholder: options.placeholder || 'Rechercher une adresse...',
            ...options
        };
        
        this.suggestionsContainer = null;
        this.debounceTimer = null;
        this.currentSuggestions = [];
        this.selectedIndex = -1;
        this.isOpen = false;
        
        this.init();
    }
    
    init() {
        // Créer le conteneur de suggestions
        this.createSuggestionsContainer();
        
        // Configurer les événements
        this.input.setAttribute('autocomplete', 'off');
        this.input.setAttribute('placeholder', this.options.placeholder);
        
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('focus', this.handleFocus.bind(this));
        
        // Fermer au clic ailleurs
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.suggestionsContainer.contains(e.target)) {
                this.close();
            }
        });
    }
    
    createSuggestionsContainer() {
        this.suggestionsContainer = document.createElement('div');
        this.suggestionsContainer.className = 'autocomplete-suggestions';
        this.suggestionsContainer.style.display = 'none';
        
        // Positionner sous l'input
        // Le parent doit avoir position: relative (déjà défini par la classe .autocomplete-wrapper)
        // Si le parent n'a pas position: relative, on l'ajoute en fallback
        const parent = this.input.parentElement;
        const parentPosition = window.getComputedStyle(parent).position;
        if (parentPosition === 'static') {
            parent.style.position = 'relative';
        }
        parent.appendChild(this.suggestionsContainer);
    }
    
    handleInput(e) {
        const query = e.target.value.trim();
        
        // Réinitialiser le timer de debounce
        clearTimeout(this.debounceTimer);
        
        if (query.length < this.options.minChars) {
            this.close();
            return;
        }
        
        // Attendre un peu avant de rechercher (debouncing)
        this.debounceTimer = setTimeout(() => {
            this.search(query);
        }, this.options.debounceMs);
    }
    
    handleKeydown(e) {
        if (!this.isOpen) return;
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                if (this.selectedIndex >= 0) {
                    e.preventDefault();
                    this.selectSuggestion(this.currentSuggestions[this.selectedIndex]);
                } else {
                    // Aucune suggestion sélectionnée : fermer le dropdown
                    // et laisser le Enter se propager au formulaire (pas de preventDefault)
                    this.close();
                }
                break;
            case 'Escape':
                this.close();
                break;
        }
    }
    
    handleFocus() {
        // Réouvrir les suggestions si il y en a
        if (this.currentSuggestions.length > 0) {
            this.open();
        }
    }
    
    async search(query) {
        try {
            const response = await fetch(`${this.options.apiEndpoint}?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.currentSuggestions = data.suggestions.slice(0, this.options.maxSuggestions);
                this.render();
                this.open();
            } else {
                this.close();
            }
        } catch (error) {
            console.error('Erreur autocomplétion:', error);
            this.close();
        }
    }
    
    render() {
        this.suggestionsContainer.innerHTML = '';
        this.selectedIndex = -1;
        
        this.currentSuggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            
            // Utiliser le champ 'display' si disponible, sinon 'label'
            const displayText = suggestion.display || suggestion.label;
            item.innerHTML = this.highlightMatch(displayText, this.input.value);
            
            // Ajouter des infos supplémentaires si disponibles
            if (suggestion.context) {
                const context = document.createElement('small');
                context.className = 'autocomplete-context';
                context.textContent = suggestion.context;
                item.appendChild(context);
            }
            
            item.addEventListener('click', () => this.selectSuggestion(suggestion));
            item.addEventListener('mouseenter', () => this.setSelectedIndex(index));
            
            this.suggestionsContainer.appendChild(item);
        });
    }
    
    highlightMatch(text, query) {
        // Surligner les correspondances (simple)
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }
    
    selectNext() {
        this.setSelectedIndex(Math.min(this.selectedIndex + 1, this.currentSuggestions.length - 1));
    }
    
    selectPrevious() {
        this.setSelectedIndex(Math.max(this.selectedIndex - 1, -1));
    }
    
    setSelectedIndex(index) {
        this.selectedIndex = index;
        
        // Mettre à jour le style visuel
        const items = this.suggestionsContainer.querySelectorAll('.autocomplete-item');
        items.forEach((item, i) => {
            if (i === index) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }
    
    selectSuggestion(suggestion) {
        this.input.value = suggestion.value || suggestion.label;
        this.close();
        
        // Callback personnalisé
        this.options.onSelect(suggestion);
        
        // Déclencher l'événement change (DÉSACTIVÉ pour éviter les boucles)
        // this.input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    open() {
        this.suggestionsContainer.style.display = 'block';
        this.isOpen = true;
    }
    
    close() {
        this.suggestionsContainer.style.display = 'none';
        this.isOpen = false;
        this.selectedIndex = -1;
    }
    
    destroy() {
        clearTimeout(this.debounceTimer);
        if (this.suggestionsContainer) {
            this.suggestionsContainer.remove();
        }
    }
}

// Export pour utilisation globale
window.Autocomplete = Autocomplete;

// Initialisation automatique au chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    
    // Autocomplétion pour la recherche par adresse
    const addressInput = document.getElementById('search_input');
    if (addressInput) {
        new Autocomplete(addressInput, {
            apiEndpoint: '/api/autocomplete/address',
            placeholder: 'Ex: 10 rue de la paix paris, verdun 55, montiers...',
            onSelect: function(suggestion) {
                console.log('Adresse sélectionnée:', suggestion);
                
                // Remplir les champs cachés si présents
                if (suggestion.lat && suggestion.lon) {
                    const latInput = document.getElementById('latitude');
                    const lonInput = document.getElementById('longitude');
                    const addressHidden = document.getElementById('address');
                    
                    if (latInput) latInput.value = suggestion.lat;
                    if (lonInput) lonInput.value = suggestion.lon;
                    if (addressHidden) addressHidden.value = suggestion.label;
                }
                
                // Optionnel: déclencher la recherche automatiquement
                // const form = document.getElementById('unifiedSearchForm');
                // if (form) form.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    // Autocomplétion pour la recherche par commune
    const communeInput = document.getElementById('commune');
    if (communeInput) {
        new Autocomplete(communeInput, {
            apiEndpoint: '/api/autocomplete/commune',
            placeholder: 'Ex: Lyon, Verdun, Moutiers-d\'Ahun, 75001...',
            minChars: 2,
            onSelect: function(suggestion) {
                console.log('Commune sélectionnée:', suggestion);
                
                // Optionnel: remplir des champs cachés avec les coordonnées
                if (suggestion.lat && suggestion.lon) {
                    // Vous pouvez stocker ces infos pour usage ultérieur
                    communeInput.dataset.lat = suggestion.lat;
                    communeInput.dataset.lon = suggestion.lon;
                    communeInput.dataset.codeInsee = suggestion.code_insee;
                    communeInput.dataset.codePostal = suggestion.code_postal;
                }
                
                // Utiliser juste le nom pour la valeur
                communeInput.value = suggestion.nom || suggestion.value;
                
                // Optionnel: déclencher la recherche automatiquement
                // const form = document.getElementById('communeSearchForm');
                // if (form) form.dispatchEvent(new Event('submit'));
            }
        });
    }
});
