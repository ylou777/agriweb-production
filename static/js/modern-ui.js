// ====== MODERN SLIDERS & INTERACTIONS 2025 ======

class ModernSliders {
    constructor() {
        this.init();
        this.bindEvents();
    }

    init() {
        // Convertir tous les sliders en version moderne
        this.upgradeSliders();
        this.createToggleSwitches();
        this.createModernRadioButtons();
        this.upgradeSearchButtons();
        this.addAnimations();
    }

    upgradeSliders() {
        const sliders = document.querySelectorAll('input[type="range"]');
        
        sliders.forEach(slider => {
            // Ajouter les classes modernes
            slider.classList.remove('form-range');
            slider.classList.add('modern-range-slider');
            
            // Créer le container moderne
            const container = document.createElement('div');
            container.className = 'modern-slider-container animate-fade-in';
            
            // Trouver le label existant
            const label = slider.previousElementSibling;
            const valueDisplay = slider.parentNode.querySelector('.slider-value') || 
                                slider.parentNode.querySelector('[id$="_val"]') ||
                                slider.parentNode.querySelector('.slider-value, #sirene_radius_val, #btMaxValAddr, #htMaxValAddr');
            
            if (label && label.tagName === 'LABEL') {
                // Créer le nouveau label moderne
                const modernLabel = document.createElement('div');
                modernLabel.className = 'modern-slider-label';
                
                const labelText = document.createElement('span');
                labelText.textContent = label.textContent.replace(/\s*\d*\.?\d*\s*$/, ''); // Enlever la valeur du label
                
                const valueSpan = document.createElement('span');
                valueSpan.className = 'slider-value-display';
                valueSpan.id = valueDisplay ? valueDisplay.id : `${slider.id}_modern_val`;
                
                modernLabel.appendChild(labelText);
                modernLabel.appendChild(valueSpan);
                
                // Insérer le container avant l'ancien label
                label.parentNode.insertBefore(container, label);
                container.appendChild(modernLabel);
                container.appendChild(slider);
                
                // Supprimer l'ancien label
                label.remove();
                if (valueDisplay && valueDisplay !== valueSpan) {
                    valueDisplay.remove();
                }
            }
            
            // Initialiser la valeur
            this.updateSliderValue(slider);
        });
    }

    updateSliderValue(slider) {
        const valueDisplay = slider.parentNode.querySelector('.slider-value-display');
        if (!valueDisplay) return;

        let value = parseFloat(slider.value);
        let displayValue;
        
        // Formatage intelligent selon le type de slider
        if (slider.id.includes('radius') || slider.id.includes('sirene')) {
            displayValue = value < 1 ? `${(value * 1000).toFixed(0)}m` : `${value.toFixed(1)}km`;
        } else if (slider.id.includes('distance') || slider.id.includes('max')) {
            displayValue = value >= 1000 ? `${(value/1000).toFixed(1)}km` : `${value.toFixed(0)}m`;
        } else if (slider.id.includes('area') || slider.id.includes('surface')) {
            displayValue = value >= 10000 ? `${(value/10000).toFixed(1)}ha` : `${value.toFixed(0)}m²`;
        } else {
            displayValue = value.toFixed(1);
        }
        
        valueDisplay.textContent = displayValue;
        
        // Animation de mise à jour
        valueDisplay.style.transform = 'scale(1.1)';
        setTimeout(() => {
            valueDisplay.style.transform = 'scale(1)';
        }, 150);
    }

    createToggleSwitches() {
        // Convertir les checkboxes en toggle switches modernes
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            if (checkbox.closest('.modern-toggle-container')) return; // Déjà converti
            
            const label = checkbox.closest('label') || 
                         document.querySelector(`label[for="${checkbox.id}"]`) ||
                         checkbox.nextElementSibling;
            
            if (!label) return;
            
            // Créer le container moderne
            const container = document.createElement('div');
            container.className = 'modern-toggle-container animate-slide-in';
            
            // Créer le label moderne
            const modernLabel = document.createElement('div');
            modernLabel.className = 'toggle-label';
            
            // Ajouter une icône selon le type
            const icon = this.getIconForToggle(checkbox.id || checkbox.name);
            if (icon) {
                const iconSpan = document.createElement('i');
                iconSpan.className = `toggle-icon ${icon}`;
                modernLabel.appendChild(iconSpan);
            }
            
            const labelText = document.createElement('span');
            labelText.textContent = label.textContent || 'Option';
            modernLabel.appendChild(labelText);
            
            // Créer le switch moderne
            const switchElement = document.createElement('div');
            switchElement.className = `modern-toggle-switch ${checkbox.checked ? 'active' : ''}`;
            
            const handle = document.createElement('div');
            handle.className = 'toggle-handle';
            switchElement.appendChild(handle);
            
            // Assembler
            container.appendChild(modernLabel);
            container.appendChild(switchElement);
            
            // Remplacer l'ancien checkbox
            checkbox.style.display = 'none'; // Garder pour la fonctionnalité
            if (label.tagName === 'LABEL') {
                label.parentNode.insertBefore(container, label);
                label.style.display = 'none';
            } else {
                checkbox.parentNode.insertBefore(container, checkbox);
            }
            
            // Bind events
            switchElement.addEventListener('click', () => {
                checkbox.checked = !checkbox.checked;
                switchElement.classList.toggle('active', checkbox.checked);
                
                // Trigger change event
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            });
        });
    }

    getIconForToggle(id) {
        const iconMap = {
            'filter_rpg': 'bi bi-tree',
            'filter_parkings': 'bi bi-car-front',
            'filter_friches': 'bi bi-house',
            'filter_zones': 'bi bi-map',
            'filter_toitures': 'bi bi-house-door',
            'filter_by_distance': 'bi bi-geo-alt',
            'debug': 'bi bi-bug',
            'admin': 'bi bi-gear'
        };
        
        for (const [key, icon] of Object.entries(iconMap)) {
            if (id && id.includes(key)) return icon;
        }
        return 'bi bi-toggle-on';
    }

    addAnimations() {
        // Ajouter des animations d'apparition progressives
        const elements = document.querySelectorAll('.accordion-item');
        elements.forEach((element, index) => {
            element.style.animationDelay = `${index * 100}ms`;
            element.classList.add('animate-fade-in');
        });
    }

    bindEvents() {
        // Bind events pour les sliders
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('modern-range-slider')) {
                this.updateSliderValue(e.target);
            }
        });

        // Smooth scroll pour les sections
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('accordion-button')) {
                setTimeout(() => {
                    e.target.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'nearest' 
                    });
                }, 300);
            }
        });
    }
}

// ====== MODERN CARDS UPGRADE ======

class ModernCards {
    constructor() {
        this.upgradeCards();
    }

    createModernRadioButtons() {
        // Gérer les boutons radio modernes
        const radioGroups = document.querySelectorAll('.modern-radio-group');
        
        radioGroups.forEach(group => {
            const radios = group.querySelectorAll('input[type="radio"]');
            const labels = group.querySelectorAll('.modern-radio-btn');
            
            // Initialiser l'état actif
            radios.forEach((radio, index) => {
                if (radio.checked) {
                    labels[index].classList.add('active');
                }
                
                radio.addEventListener('change', () => {
                    // Retirer active de tous les labels du groupe
                    labels.forEach(label => label.classList.remove('active'));
                    
                    // Ajouter active au label sélectionné
                    if (radio.checked) {
                        labels[index].classList.add('active');
                        
                        // Animation de feedback
                        labels[index].style.transform = 'scale(0.95)';
                        setTimeout(() => {
                            labels[index].style.transform = '';
                        }, 150);
                    }
                });
            });
            
            // Gérer le clic sur les labels
            labels.forEach((label, index) => {
                label.addEventListener('click', () => {
                    radios[index].checked = true;
                    radios[index].dispatchEvent(new Event('change', { bubbles: true }));
                });
            });
        });
    }

    upgradeSearchButtons() {
        // Améliorer les boutons de recherche
        const searchButtons = document.querySelectorAll('.modern-search-btn, .modern-secondary-btn');
        
        searchButtons.forEach(button => {
            // Ajouter effet de chargement
            button.addEventListener('click', function(e) {
                if (!this.classList.contains('loading')) {
                    this.classList.add('loading');
                    
                    // Simuler le chargement
                    setTimeout(() => {
                        this.classList.remove('loading');
                    }, 2000);
                }
            });
            
            // Ajouter feedback visuel
            this.addButtonFeedback(button);
        });
    }

    addButtonFeedback(button) {
        button.addEventListener('mousedown', function(e) {
            const rect = this.getBoundingClientRect();
            const ripple = document.createElement('span');
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple-effect 0.6s ease-out;
                pointer-events: none;
                z-index: 10;
            `;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    }
        // Convertir les accordion-body en modern-cards
        const accordionBodies = document.querySelectorAll('.accordion-body');
        
        accordionBodies.forEach(body => {
            body.classList.add('modern-card');
            
            // Ajouter un header moderne si il y a un titre
            const header = body.closest('.accordion-item').querySelector('.accordion-button');
            if (header) {
                const cardHeader = document.createElement('div');
                cardHeader.className = 'modern-card-header';
                
                // Extraire l'icône et le texte
                const icon = header.querySelector('i');
                const text = header.textContent.replace(/[^\w\s•]/g, '').trim();
                
                if (icon) {
                    const cardIcon = document.createElement('div');
                    cardIcon.className = 'modern-card-icon';
                    cardIcon.innerHTML = `<i class="${icon.className}"></i>`;
                    cardHeader.appendChild(cardIcon);
                }
                
                const cardTitle = document.createElement('span');
                cardTitle.textContent = text;
                cardHeader.appendChild(cardTitle);
                
                // Insérer au début du body
                body.insertBefore(cardHeader, body.firstChild);
            }
        });
    }
}

// ====== MODERN BUTTONS ======

class ModernButtons {
    constructor() {
        this.upgradeButtons();
    }

    upgradeButtons() {
        const buttons = document.querySelectorAll('.btn:not(.accordion-button)');
        
        buttons.forEach(btn => {
            if (!btn.classList.contains('modern-btn')) {
                btn.classList.remove('btn-primary', 'btn-secondary', 'btn-success');
                btn.classList.add('modern-btn');
                
                // Ajouter l'effet ripple
                this.addRippleEffect(btn);
            }
        });
    }

    addRippleEffect(button) {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    }
}

// ====== THEME MANAGER ======

class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        this.applyTheme();
        this.createThemeToggle();
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        if (this.currentTheme === 'dark') {
            document.body.style.background = 'linear-gradient(135deg, #0c4a6e 0%, #1e40af 100%)';
        } else {
            document.body.style.background = 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)';
        }
    }

    createThemeToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'theme-toggle';
        toggle.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
        toggle.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        `;
        
        toggle.addEventListener('click', () => this.toggleTheme());
        document.body.appendChild(toggle);
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.currentTheme);
        this.applyTheme();
        
        const toggle = document.querySelector('.theme-toggle');
        toggle.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
    }
}

// ====== INITIALIZATION ======

document.addEventListener('DOMContentLoaded', () => {
    // Délai pour laisser le temps au DOM de se charger complètement
    setTimeout(() => {
        new ModernSliders();
        new ModernCards();
        new ModernButtons();
        new ThemeManager();
        
        // Ajouter des micro-animations
        addMicroAnimations();
    }, 100);
});

function addMicroAnimations() {
    // Animation au hover pour tous les éléments interactifs
    const style = document.createElement('style');
    style.textContent = `
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s linear;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .theme-toggle:hover {
            transform: scale(1.1);
            background: rgba(255,255,255,0.3);
        }
    `;
    document.head.appendChild(style);
}

// Export pour usage externe
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ModernSliders, ModernCards, ModernButtons, ThemeManager };
}
