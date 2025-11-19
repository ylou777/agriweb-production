// ====== MOBILE GESTURES & INTERACTIONS 2025 ======

class MobileGestures {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.sidebar = document.getElementById('sidebar');
        this.isExpanded = false;
        this.startY = 0;
        this.currentY = 0;
        this.isDragging = false;
        
        if (this.isMobile && this.sidebar) {
            this.init();
        }
    }

    init() {
        this.setupMobileLayout();
        this.bindSwipeEvents();
        this.addSwipeIndicator();
        this.handleResize();
    }

    setupMobileLayout() {
        // Wrapper pour le contenu de la sidebar
        const sidebarContent = this.sidebar.innerHTML;
        this.sidebar.innerHTML = `<div class="sidebar-content">${sidebarContent}</div>`;
        
        // Ajouter classes mobiles
        this.sidebar.classList.add('mobile-sidebar');
        document.body.classList.add('mobile-layout');
    }

    bindSwipeEvents() {
        // Touch events pour le swipe
        this.sidebar.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        this.sidebar.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.sidebar.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
        
        // Mouse events pour le desktop testing
        this.sidebar.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Tap sur la carte pour fermer la sidebar
        const mapFrame = document.getElementById('mapFrame');
        if (mapFrame) {
            mapFrame.addEventListener('click', () => {
                if (this.isExpanded) {
                    this.collapseSidebar();
                }
            });
        }
    }

    handleTouchStart(e) {
        this.startY = e.touches[0].clientY;
        this.isDragging = true;
        this.sidebar.classList.add('sidebar-sliding');
    }

    handleTouchMove(e) {
        if (!this.isDragging) return;
        
        e.preventDefault(); // Empêcher le scroll par défaut
        this.currentY = e.touches[0].clientY;
        const deltaY = this.currentY - this.startY;
        
        // Calculer la position de la sidebar
        let newTransform;
        if (this.isExpanded) {
            // Si déjà étendue, permettre de la réduire
            newTransform = Math.max(0, deltaY);
        } else {
            // Si réduite, permettre de l'étendre
            newTransform = Math.min(0, 60 + (deltaY / window.innerHeight) * 100);
        }
        
        this.sidebar.style.transform = `translateY(${newTransform}%)`;
    }

    handleTouchEnd() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        this.sidebar.classList.remove('sidebar-sliding');
        
        const deltaY = this.currentY - this.startY;
        const threshold = 50; // Seuil de déclenchement en pixels
        
        if (this.isExpanded) {
            // Si étendue et swipe vers le bas suffisant
            if (deltaY > threshold) {
                this.collapseSidebar();
            } else {
                this.expandSidebar();
            }
        } else {
            // Si réduite et swipe vers le haut suffisant
            if (deltaY < -threshold) {
                this.expandSidebar();
            } else {
                this.collapseSidebar();
            }
        }
    }

    // Mouse events pour le desktop testing
    handleMouseDown(e) {
        this.startY = e.clientY;
        this.isDragging = true;
        this.sidebar.classList.add('sidebar-sliding');
    }

    handleMouseMove(e) {
        if (!this.isDragging) return;
        
        this.currentY = e.clientY;
        const deltaY = this.currentY - this.startY;
        
        let newTransform;
        if (this.isExpanded) {
            newTransform = Math.max(0, deltaY / window.innerHeight * 100);
        } else {
            newTransform = Math.min(0, 60 + (deltaY / window.innerHeight) * 100);
        }
        
        this.sidebar.style.transform = `translateY(${newTransform}%)`;
    }

    handleMouseUp() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        this.sidebar.classList.remove('sidebar-sliding');
        
        const deltaY = this.currentY - this.startY;
        const threshold = 50;
        
        if (this.isExpanded) {
            if (deltaY > threshold) {
                this.collapseSidebar();
            } else {
                this.expandSidebar();
            }
        } else {
            if (deltaY < -threshold) {
                this.expandSidebar();
            } else {
                this.collapseSidebar();
            }
        }
    }

    expandSidebar() {
        this.isExpanded = true;
        this.sidebar.classList.add('expanded');
        this.sidebar.style.transform = 'translateY(0)';
        
        // Masquer l'indicateur de swipe
        const indicator = document.querySelector('.swipe-indicator');
        if (indicator) {
            indicator.style.opacity = '0';
        }
        
        // Ajouter un overlay léger sur la carte
        this.addMapOverlay();
    }

    collapseSidebar() {
        this.isExpanded = false;
        this.sidebar.classList.remove('expanded');
        this.sidebar.style.transform = 'translateY(60%)';
        
        // Réafficher l'indicateur de swipe
        const indicator = document.querySelector('.swipe-indicator');
        if (indicator) {
            indicator.style.opacity = '0.7';
        }
        
        // Supprimer l'overlay de la carte
        this.removeMapOverlay();
    }

    addMapOverlay() {
        let overlay = document.querySelector('.map-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'map-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100vh;
                background: rgba(0, 0, 0, 0.3);
                z-index: 999;
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: auto;
            `;
            
            overlay.addEventListener('click', () => this.collapseSidebar());
            document.body.appendChild(overlay);
        }
        
        setTimeout(() => {
            overlay.style.opacity = '1';
        }, 10);
    }

    removeMapOverlay() {
        const overlay = document.querySelector('.map-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => {
                overlay.remove();
            }, 300);
        }
    }

    addSwipeIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'swipe-indicator';
        indicator.innerHTML = '👆 Glissez vers le haut pour plus d\'options';
        document.body.appendChild(indicator);
        
        // Masquer après quelques secondes
        setTimeout(() => {
            indicator.style.animation = 'none';
            indicator.style.opacity = '0.5';
        }, 5000);
    }

    handleResize() {
        window.addEventListener('resize', () => {
            const newIsMobile = window.innerWidth <= 768;
            if (newIsMobile !== this.isMobile) {
                location.reload(); // Rechargement pour switcher le layout
            }
        });
    }
}

// ====== OPTIMISATIONS MOBILE ======

class MobileOptimizations {
    constructor() {
        if (window.innerWidth <= 768) {
            this.init();
        }
    }

    init() {
        this.optimizeInputs();
        this.addTouchFeedback();
        this.optimizeScrolling();
        this.preventZoom();
    }

    optimizeInputs() {
        // Agrandir les zones de touch pour les inputs
        const inputs = document.querySelectorAll('input, select, button');
        inputs.forEach(input => {
            input.style.minHeight = '44px'; // Recommandation iOS/Android
            input.classList.add('touch-optimized');
        });
    }

    addTouchFeedback() {
        // Ajouter feedback visuel pour les touches
        const touchElements = document.querySelectorAll('.modern-btn, .modern-toggle-switch, .accordion-button');
        
        touchElements.forEach(element => {
            element.classList.add('touch-feedback');
            
            element.addEventListener('touchstart', function() {
                this.classList.add('touching');
            }, { passive: true });
            
            element.addEventListener('touchend', function() {
                this.classList.remove('touching');
            }, { passive: true });
        });
    }

    optimizeScrolling() {
        // Smooth scrolling amélioré pour mobile
        document.documentElement.style.scrollBehavior = 'smooth';
        
        // Momentum scrolling pour iOS
        const scrollAreas = document.querySelectorAll('#sidebar, .sidebar-content, .accordion-body');
        scrollAreas.forEach(area => {
            area.style.webkitOverflowScrolling = 'touch';
            area.style.overflowScrolling = 'touch';
        });
    }

    preventZoom() {
        // Empêcher le zoom accidentel sur les inputs
        const inputs = document.querySelectorAll('input[type="text"], input[type="number"], select');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                const viewport = document.querySelector('meta[name="viewport"]');
                if (viewport) {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no');
                }
            });
            
            input.addEventListener('blur', function() {
                const viewport = document.querySelector('meta[name="viewport"]');
                if (viewport) {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1');
                }
            });
        });
    }
}

// ====== ADAPTIVE LOADING ======

class AdaptiveLoading {
    constructor() {
        this.connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        this.init();
    }

    init() {
        // Adapter le chargement selon la connexion
        if (this.connection) {
            if (this.connection.effectiveType === '2g' || this.connection.effectiveType === 'slow-2g') {
                this.enableLowDataMode();
            }
        }
        
        // Lazy loading pour les images
        this.setupLazyLoading();
    }

    enableLowDataMode() {
        // Réduire les animations pour économiser la bande passante
        const style = document.createElement('style');
        style.textContent = `
            *, *::before, *::after {
                animation-duration: 0.1s !important;
                transition-duration: 0.1s !important;
            }
            
            .modern-card:hover {
                transform: none !important;
            }
        `;
        document.head.appendChild(style);
        
        console.log('🐌 Mode données limitées activé');
    }

    setupLazyLoading() {
        // Observer pour le lazy loading
        if ('IntersectionObserver' in window) {
            const lazyImages = document.querySelectorAll('img[data-src]');
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
}

// ====== VIBRATION FEEDBACK ======

class HapticFeedback {
    constructor() {
        this.isSupported = 'vibrate' in navigator;
        if (this.isSupported) {
            this.init();
        }
    }

    init() {
        // Ajouter vibration pour les interactions importantes
        const importantButtons = document.querySelectorAll('.modern-btn, button[type="submit"]');
        importantButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.lightTap();
            });
        });
        
        const toggles = document.querySelectorAll('.modern-toggle-switch');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                this.selectionFeedback();
            });
        });
    }

    lightTap() {
        if (this.isSupported) {
            navigator.vibrate(10); // Vibration légère
        }
    }

    selectionFeedback() {
        if (this.isSupported) {
            navigator.vibrate([5, 5, 5]); // Pattern pour la sélection
        }
    }

    errorFeedback() {
        if (this.isSupported) {
            navigator.vibrate([50, 50, 50]); // Pattern pour les erreurs
        }
    }
}

// ====== INITIALIZATION ======

document.addEventListener('DOMContentLoaded', () => {
    // Délai pour s'assurer que tout est chargé
    setTimeout(() => {
        new MobileGestures();
        new MobileOptimizations();
        new AdaptiveLoading();
        new HapticFeedback();
    }, 200);
});

// Export pour usage externe
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        MobileGestures, 
        MobileOptimizations, 
        AdaptiveLoading, 
        HapticFeedback 
    };
}
