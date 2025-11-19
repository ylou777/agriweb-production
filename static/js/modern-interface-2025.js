/* =============================================================================
   AGRIWEB MODERN INTERFACE 2025 - JAVASCRIPT CONTROLLER
   Mobile Navigation | Touch Gestures | Modern Interactions
   ============================================================================= */

class ModernInterface {
  constructor() {
    this.isMobile = window.innerWidth <= 768;
    this.sidebarOpen = false;
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.minSwipeDistance = 50;
    
    this.init();
  }
  
  init() {
    this.createMobileElements();
    this.bindEvents();
    this.setupAccordions();
    this.setupRangeSliders();
    this.handleResize();
    
    console.log('🚀 Modern Interface 2025 initialized');
  }
  
  /* ===== MOBILE NAVIGATION ===== */
  createMobileElements() {
    // Create mobile menu button if not exists
    if (!document.querySelector('.mobile-menu-btn')) {
      const menuBtn = document.createElement('button');
      menuBtn.className = 'mobile-menu-btn';
      menuBtn.innerHTML = `
        <div class="hamburger">
          <span></span>
          <span></span>
          <span></span>
        </div>
      `;
      document.body.appendChild(menuBtn);
    }
    
    // Create overlay for mobile
    if (!document.querySelector('.mobile-overlay')) {
      const overlay = document.createElement('div');
      overlay.className = 'mobile-overlay';
      document.body.appendChild(overlay);
    }
  }
  
  toggleMobileSidebar() {
    const sidebar = document.querySelector('.modern-sidebar') || document.querySelector('#sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    const hamburger = document.querySelector('.hamburger');
    
    if (!sidebar) return;
    
    this.sidebarOpen = !this.sidebarOpen;
    
    if (this.sidebarOpen) {
      sidebar.classList.add('mobile-open');
      overlay.classList.add('active');
      hamburger.classList.add('active');
      document.body.style.overflow = 'hidden';
    } else {
      sidebar.classList.remove('mobile-open');
      overlay.classList.remove('active');
      hamburger.classList.remove('active');
      document.body.style.overflow = '';
    }
  }
  
  closeMobileSidebar() {
    if (this.sidebarOpen) {
      this.toggleMobileSidebar();
    }
  }
  
  /* ===== TOUCH GESTURES ===== */
  setupTouchGestures() {
    const sidebar = document.querySelector('.modern-sidebar') || document.querySelector('#sidebar');
    
    if (!sidebar) return;
    
    // Swipe to open from left edge
    document.addEventListener('touchstart', (e) => {
      this.touchStartX = e.touches[0].clientX;
      this.touchStartY = e.touches[0].clientY;
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
      if (!e.changedTouches[0]) return;
      
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      const diffX = touchEndX - this.touchStartX;
      const diffY = Math.abs(touchEndY - this.touchStartY);
      
      // Swipe right from left edge to open
      if (this.touchStartX < 20 && diffX > this.minSwipeDistance && diffY < 100 && !this.sidebarOpen) {
        this.toggleMobileSidebar();
      }
      
      // Swipe left to close when sidebar is open
      if (diffX < -this.minSwipeDistance && diffY < 100 && this.sidebarOpen) {
        this.closeMobileSidebar();
      }
    }, { passive: true });
  }
  
  /* ===== MODERN ACCORDIONS ===== */
  setupAccordions() {
    // Convert Bootstrap accordions to modern style
    const accordions = document.querySelectorAll('.accordion');
    
    accordions.forEach(accordion => {
      accordion.classList.add('modern-accordion');
      
      const items = accordion.querySelectorAll('.accordion-item');
      items.forEach(item => {
        item.classList.add('modern-accordion-item');
        
        const header = item.querySelector('.accordion-header');
        const button = header?.querySelector('.accordion-button');
        const content = item.querySelector('.accordion-collapse');
        const body = item.querySelector('.accordion-body');
        
        if (header && button && content && body) {
          // Update classes
          header.classList.add('modern-accordion-header');
          content.classList.add('modern-accordion-content');
          body.classList.add('modern-accordion-body');
          
          // Add chevron if not exists
          if (!button.querySelector('.modern-accordion-chevron')) {
            const chevron = document.createElement('i');
            chevron.className = 'bi bi-chevron-down modern-accordion-chevron';
            button.appendChild(chevron);
          }
          
          // Handle click
          button.addEventListener('click', (e) => {
            e.preventDefault();
            
            const isActive = item.classList.contains('active');
            
            // Close all other items
            items.forEach(otherItem => {
              if (otherItem !== item) {
                otherItem.classList.remove('active');
                const otherContent = otherItem.querySelector('.modern-accordion-content');
                if (otherContent) {
                  otherContent.classList.remove('active');
                }
              }
            });
            
            // Toggle current item
            if (isActive) {
              item.classList.remove('active');
              content.classList.remove('active');
            } else {
              item.classList.add('active');
              content.classList.add('active');
            }
          });
        }
      });
    });
  }
  
  /* ===== MODERN RANGE SLIDERS ===== */
  setupRangeSliders() {
    const ranges = document.querySelectorAll('input[type="range"]');
    
    ranges.forEach(range => {
      if (!range.classList.contains('modern-range')) {
        range.classList.add('modern-range');
      }
      
      // Find or create value display
      const valueId = range.id + '_val';
      let valueDisplay = document.getElementById(valueId);
      
      if (!valueDisplay) {
        // Look for existing span with class slider-value
        const label = range.previousElementSibling;
        if (label && label.tagName === 'LABEL') {
          valueDisplay = label.querySelector('.slider-value') || label.querySelector(`#${valueId}`);
        }
      }
      
      if (!valueDisplay) {
        // Create new value display
        const label = range.previousElementSibling;
        if (label && label.tagName === 'LABEL') {
          valueDisplay = document.createElement('span');
          valueDisplay.className = 'modern-range-value slider-value';
          valueDisplay.id = valueId;
          label.appendChild(valueDisplay);
        }
      }
      
      // Update value display
      const updateValue = () => {
        if (valueDisplay) {
          let value = range.value;
          const unit = range.dataset.unit || '';
          
          // Format value based on type
          if (range.step && parseFloat(range.step) < 1) {
            value = parseFloat(value).toFixed(1);
          } else {
            value = parseInt(value);
          }
          
          valueDisplay.textContent = value + unit;
        }
      };
      
      // Initial update
      updateValue();
      
      // Update on change
      range.addEventListener('input', updateValue);
      range.addEventListener('change', updateValue);
    });
  }
  
  /* ===== MODERN BUTTONS ===== */
  upgradeButtons() {
    const buttons = document.querySelectorAll('button, .btn');
    
    buttons.forEach(btn => {
      if (!btn.classList.contains('modern-enhanced')) {
        // Ajouter seulement une classe d'amélioration SANS remplacer
        btn.classList.add('modern-enhanced');
        
        // Ajouter des effets visuels sans toucher aux event handlers
        btn.addEventListener('mouseenter', () => {
          btn.style.transform = 'translateY(-1px)';
          btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
          btn.style.transition = 'all 0.2s ease';
        });
        
        btn.addEventListener('mouseleave', () => {
          btn.style.transform = '';
          btn.style.boxShadow = '';
        });
        
        // NE PAS retirer les classes Bootstrap existantes
        // NE PAS ajouter de nouveaux click handlers
      }
    });
  }
  
  /* ===== MODERN FORMS ===== */
  upgradeForms() {
    // Upgrade form controls
    const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="number"], textarea');
    const selects = document.querySelectorAll('select');
    const labels = document.querySelectorAll('label');
    
    inputs.forEach(input => {
      if (!input.classList.contains('modern-input')) {
        input.classList.add('modern-input');
        input.classList.remove('form-control');
      }
    });
    
    selects.forEach(select => {
      if (!select.classList.contains('modern-select')) {
        select.classList.add('modern-select', 'modern-input');
        select.classList.remove('form-select');
      }
    });
    
    labels.forEach(label => {
      if (!label.classList.contains('modern-label')) {
        label.classList.add('modern-label');
        label.classList.remove('form-label');
      }
    });
    
    // Upgrade checkboxes and radios
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const radios = document.querySelectorAll('input[type="radio"]');
    
    checkboxes.forEach(checkbox => {
      if (!checkbox.closest('.modern-checkbox')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'modern-checkbox';
        checkbox.parentNode.insertBefore(wrapper, checkbox);
        wrapper.appendChild(checkbox);
        
        const label = document.querySelector(`label[for="${checkbox.id}"]`);
        if (label) {
          wrapper.appendChild(label);
        }
      }
    });
    
    radios.forEach(radio => {
      if (!radio.closest('.modern-radio')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'modern-radio';
        radio.parentNode.insertBefore(wrapper, radio);
        wrapper.appendChild(radio);
        
        const label = document.querySelector(`label[for="${radio.id}"]`);
        if (label) {
          wrapper.appendChild(label);
        }
      }
    });
  }
  
  /* ===== LOADING STATES ===== */
  setButtonLoading(button, isLoading = true, text = 'Chargement...') {
    if (typeof button === 'string') {
      button = document.getElementById(button) || document.querySelector(button);
    }
    
    if (!button) return;
    
    if (isLoading) {
      button.dataset.originalText = button.innerHTML;
      button.innerHTML = `<div class="modern-spinner"></div> ${text}`;
      button.classList.add('modern-btn-loading');
      button.disabled = true;
    } else {
      button.innerHTML = button.dataset.originalText || button.innerHTML;
      button.classList.remove('modern-btn-loading');
      button.disabled = false;
      delete button.dataset.originalText;
    }
  }
  
  /* ===== ANIMATIONS ===== */
  animateElement(element, animation = 'fadeIn') {
    if (typeof element === 'string') {
      element = document.querySelector(element);
    }
    
    if (!element) return;
    
    element.classList.add(`animate-${animation}`);
    
    // Remove animation class after completion
    setTimeout(() => {
      element.classList.remove(`animate-${animation}`);
    }, 350);
  }
  
  /* ===== RESPONSIVE HANDLING ===== */
  handleResize() {
    const checkResize = () => {
      const wasMobile = this.isMobile;
      this.isMobile = window.innerWidth <= 768;
      
      // Close sidebar when switching to desktop
      if (wasMobile && !this.isMobile && this.sidebarOpen) {
        this.closeMobileSidebar();
      }
    };
    
    window.addEventListener('resize', checkResize);
    checkResize();
  }
  
  /* ===== EVENT BINDING ===== */
  bindEvents() {
    // Mobile menu button
    const menuBtn = document.querySelector('.mobile-menu-btn');
    if (menuBtn) {
      menuBtn.addEventListener('click', () => this.toggleMobileSidebar());
    }
    
    // Overlay click to close
    const overlay = document.querySelector('.mobile-overlay');
    if (overlay) {
      overlay.addEventListener('click', () => this.closeMobileSidebar());
    }
    
    // ESC key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.sidebarOpen) {
        this.closeMobileSidebar();
      }
    });
    
    // Setup touch gestures
    this.setupTouchGestures();
    
    // Auto-upgrade existing elements
    setTimeout(() => {
      this.upgradeButtons();
      this.upgradeForms();
    }, 100);
  }
  
  /* ===== PUBLIC API ===== */
  openSidebar() {
    if (!this.sidebarOpen) {
      this.toggleMobileSidebar();
    }
  }
  
  closeSidebar() {
    if (this.sidebarOpen) {
      this.toggleMobileSidebar();
    }
  }
  
  /* ===== UTILITY METHODS ===== */
  showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `modern-toast modern-toast-${type}`;
    toast.textContent = message;
    
    // Style the toast
    Object.assign(toast.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      background: type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : 'var(--primary)',
      color: 'white',
      padding: '12px 16px',
      borderRadius: 'var(--radius-md)',
      boxShadow: 'var(--shadow-lg)',
      zIndex: 'var(--z-toast)',
      opacity: '0',
      transform: 'translateY(-10px)',
      transition: 'all var(--transition-normal)'
    });
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    }, 10);
    
    // Remove after duration
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 250);
    }, duration);
  }
}

/* ===== GLOBAL UTILITIES ===== */
window.ModernInterface = ModernInterface;

// Global method for button loading states (compatibility)
window.setButtonLoadingState = function(buttonId, isLoading, text) {
  if (window.modernUI) {
    window.modernUI.setButtonLoading(buttonId, isLoading, text);
  }
};

// Global method for animations
window.animateElement = function(element, animation) {
  if (window.modernUI) {
    window.modernUI.animateElement(element, animation);
  }
};

// Global toast notifications
window.showToast = function(message, type, duration) {
  if (window.modernUI) {
    window.modernUI.showToast(message, type, duration);
  }
};

/* ===== INITIALIZATION ===== */
document.addEventListener('DOMContentLoaded', () => {
  // Initialize modern interface
  window.modernUI = new ModernInterface();
  
  // Expose to global scope for backward compatibility
  window.modernInterface = window.modernUI;
  
  console.log('✨ Modern Interface 2025 ready!');
});

/* ===== AUTO-UPGRADE LEGACY ELEMENTS ===== */
// Progressive enhancement for existing Bootstrap elements
function autoUpgrade() {
  if (!window.modernUI) return;
  
  // Upgrade buttons that might be added dynamically
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) { // Element node
          // Upgrade new buttons
          const buttons = node.querySelectorAll ? node.querySelectorAll('button, .btn') : [];
          buttons.forEach(btn => {
            if (!btn.classList.contains('modern-btn')) {
              window.modernUI.upgradeButtons();
            }
          });
          
          // Upgrade new form elements
          const inputs = node.querySelectorAll ? node.querySelectorAll('input, select, textarea') : [];
          if (inputs.length > 0) {
            window.modernUI.upgradeForms();
          }
          
          // Setup new range sliders
          const ranges = node.querySelectorAll ? node.querySelectorAll('input[type="range"]') : [];
          if (ranges.length > 0) {
            window.modernUI.setupRangeSliders();
          }
        }
      });
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Start auto-upgrade
document.addEventListener('DOMContentLoaded', autoUpgrade);
