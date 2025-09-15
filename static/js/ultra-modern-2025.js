// Ultra-Modern Interactive JavaScript 2025 - AgriWeb Revolution
class UltraModernUI {
    constructor() {
        this.particles = [];
        this.isInitialized = false;
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        this.createNeuralBackground();
        this.initParticleSystem();
        this.initQuantumButtons();
        this.initMorphingSearch();
        this.init3DToggles();
        this.initFloatingActionButtons();
        this.initHolographicEffects();
        this.initCyberpunkPanels();
        this.initGestureControls();
        this.initVoiceCommands();
        this.initAIAssistant();
        this.initMicroInteractions();
        
        this.isInitialized = true;
        console.log('🚀 Ultra-Modern UI 2025 initialized!');
    }

    // === NEURAL NETWORK BACKGROUND === //
    createNeuralBackground() {
        const container = document.querySelector('.neural-background') || document.createElement('div');
        container.className = 'neural-background';
        
        const nodes = document.createElement('div');
        nodes.className = 'neural-nodes';
        container.appendChild(nodes);
        
        if (!document.querySelector('.neural-background')) {
            document.body.insertBefore(container, document.body.firstChild);
        }

        // Create dynamic neural connections
        this.createNeuralConnections(container);
    }

    createNeuralConnections(container) {
        const canvas = document.createElement('canvas');
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.pointerEvents = 'none';
        canvas.style.opacity = '0.3';
        
        container.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const nodes = [];
        
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        // Create neural nodes
        for (let i = 0; i < 50; i++) {
            nodes.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 3 + 1
            });
        }

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Update and draw nodes
            nodes.forEach((node, i) => {
                node.x += node.vx;
                node.y += node.vy;
                
                if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
                if (node.y < 0 || node.y > canvas.height) node.vy *= -1;
                
                // Draw node
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(0, 255, 255, 0.6)`;
                ctx.fill();
                
                // Draw connections
                nodes.forEach((otherNode, j) => {
                    if (i !== j) {
                        const distance = Math.sqrt(
                            (node.x - otherNode.x) ** 2 + (node.y - otherNode.y) ** 2
                        );
                        
                        if (distance < 150) {
                            ctx.beginPath();
                            ctx.moveTo(node.x, node.y);
                            ctx.lineTo(otherNode.x, otherNode.y);
                            ctx.strokeStyle = `rgba(0, 255, 255, ${0.3 - distance / 500})`;
                            ctx.lineWidth = 1;
                            ctx.stroke();
                        }
                    }
                });
            });
            
            requestAnimationFrame(animate);
        };
        
        animate();
    }

    // === PARTICLE SYSTEM === //
    initParticleSystem() {
        const container = document.createElement('div');
        container.className = 'particle-container';
        document.body.appendChild(container);

        setInterval(() => {
            this.createParticle(container);
        }, 200);
    }

    createParticle(container) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        particle.style.left = Math.random() * 100 + 'vw';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        particle.style.animationDelay = Math.random() * 2 + 's';
        
        container.appendChild(particle);
        
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        }, 8000);
    }

    // === QUANTUM BUTTONS === //
    initQuantumButtons() {
        const buttons = document.querySelectorAll('.quantum-btn');
        
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.createQuantumRipple(e, button);
                this.triggerQuantumEffect(button);
            });
            
            button.addEventListener('mouseenter', () => {
                this.addQuantumGlow(button);
            });
            
            button.addEventListener('mouseleave', () => {
                this.removeQuantumGlow(button);
            });
        });
    }

    createQuantumRipple(e, button) {
        const ripple = document.createElement('div');
        const rect = button.getBoundingClientRect();
        const size = 100;
        
        ripple.style.position = 'absolute';
        ripple.style.width = size + 'px';
        ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
        ripple.style.background = 'radial-gradient(circle, rgba(255,255,255,0.8) 0%, transparent 70%)';
        ripple.style.borderRadius = '50%';
        ripple.style.transform = 'scale(0)';
        ripple.style.animation = 'quantumRipple 0.6s ease-out';
        ripple.style.pointerEvents = 'none';
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }

    triggerQuantumEffect(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = '';
        }, 150);
    }

    addQuantumGlow(button) {
        button.style.boxShadow = '0 0 30px rgba(0, 255, 255, 0.8), 0 0 60px rgba(255, 0, 255, 0.4)';
    }

    removeQuantumGlow(button) {
        button.style.boxShadow = '';
    }

    // === MORPHING SEARCH === //
    initMorphingSearch() {
        const searchBars = document.querySelectorAll('.morph-search');
        
        searchBars.forEach(searchBar => {
            const input = searchBar.querySelector('input');
            
            input.addEventListener('focus', () => {
                this.expandSearch(searchBar);
            });
            
            input.addEventListener('blur', () => {
                this.contractSearch(searchBar);
            });
            
            input.addEventListener('input', (e) => {
                this.handleSearchInput(e, searchBar);
            });
        });
    }

    expandSearch(searchBar) {
        searchBar.style.transform = 'scale(1.05)';
        searchBar.style.boxShadow = '0 0 40px rgba(0, 255, 255, 0.6)';
        
        this.createSearchParticles(searchBar);
    }

    contractSearch(searchBar) {
        searchBar.style.transform = '';
        searchBar.style.boxShadow = '';
    }

    handleSearchInput(e, searchBar) {
        const value = e.target.value;
        const intensity = Math.min(value.length / 10, 1);
        
        searchBar.style.boxShadow = `0 0 ${20 + intensity * 40}px rgba(0, 255, 255, ${0.3 + intensity * 0.5})`;
    }

    createSearchParticles(searchBar) {
        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'absolute';
            particle.style.width = '4px';
            particle.style.height = '4px';
            particle.style.background = '#00ffff';
            particle.style.borderRadius = '50%';
            particle.style.pointerEvents = 'none';
            
            const rect = searchBar.getBoundingClientRect();
            particle.style.left = rect.left + Math.random() * rect.width + 'px';
            particle.style.top = rect.top + Math.random() * rect.height + 'px';
            
            document.body.appendChild(particle);
            
            particle.animate([
                { transform: 'translateY(0) scale(1)', opacity: 1 },
                { transform: 'translateY(-50px) scale(0)', opacity: 0 }
            ], {
                duration: 1000,
                easing: 'ease-out'
            }).onfinish = () => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            };
        }
    }

    // === 3D TOGGLES === //
    init3DToggles() {
        const toggles = document.querySelectorAll('.toggle-3d');
        
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                this.animate3DToggle(toggle);
            });
            
            toggle.addEventListener('mouseenter', () => {
                this.hover3DToggle(toggle);
            });
            
            toggle.addEventListener('mouseleave', () => {
                this.unhover3DToggle(toggle);
            });
        });
    }

    animate3DToggle(toggle) {
        toggle.classList.toggle('active');
        
        // Create toggle particles
        this.createToggleParticles(toggle);
        
        // Haptic feedback simulation
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }

    hover3DToggle(toggle) {
        toggle.style.transform = 'translateY(-2px) rotateX(10deg)';
    }

    unhover3DToggle(toggle) {
        toggle.style.transform = '';
    }

    createToggleParticles(toggle) {
        const rect = toggle.getBoundingClientRect();
        
        for (let i = 0; i < 8; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'fixed';
            particle.style.width = '3px';
            particle.style.height = '3px';
            particle.style.background = toggle.classList.contains('active') ? '#00ffaa' : '#00ffff';
            particle.style.borderRadius = '50%';
            particle.style.pointerEvents = 'none';
            particle.style.zIndex = '9999';
            
            particle.style.left = rect.left + rect.width / 2 + 'px';
            particle.style.top = rect.top + rect.height / 2 + 'px';
            
            document.body.appendChild(particle);
            
            const angle = (i / 8) * Math.PI * 2;
            const distance = 30;
            
            particle.animate([
                { 
                    transform: 'translate(0, 0) scale(1)', 
                    opacity: 1 
                },
                { 
                    transform: `translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance}px) scale(0)`, 
                    opacity: 0 
                }
            ], {
                duration: 600,
                easing: 'ease-out'
            }).onfinish = () => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            };
        }
    }

    // === FLOATING ACTION BUTTONS === //
    initFloatingActionButtons() {
        const fabContainers = document.querySelectorAll('.fab-container');
        
        fabContainers.forEach(container => {
            const fab = container.querySelector('.fab');
            const menu = container.querySelector('.fab-menu');
            
            fab.addEventListener('click', () => {
                container.classList.toggle('active');
                this.animateFABMenu(container);
            });
        });
    }

    animateFABMenu(container) {
        const items = container.querySelectorAll('.fab-item');
        const isActive = container.classList.contains('active');
        
        items.forEach((item, index) => {
            setTimeout(() => {
                if (isActive) {
                    item.style.animation = `bounceIn 0.4s ease-out ${index * 0.1}s both`;
                } else {
                    item.style.animation = `fadeOut 0.2s ease-in ${index * 0.05}s both`;
                }
            }, isActive ? index * 50 : 0);
        });
    }

    // === HOLOGRAPHIC EFFECTS === //
    initHolographicEffects() {
        const holoCards = document.querySelectorAll('.holo-card');
        
        holoCards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                this.updateHolographicEffect(e, card);
            });
            
            card.addEventListener('mouseleave', () => {
                this.resetHolographicEffect(card);
            });
        });
    }

    updateHolographicEffect(e, card) {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 10;
        const rotateY = (centerX - x) / 10;
        
        card.style.transform = `
            translateY(-10px) 
            rotateX(${rotateX}deg) 
            rotateY(${rotateY}deg)
        `;
        
        // Update gradient based on mouse position
        const gradientX = (x / rect.width) * 100;
        const gradientY = (y / rect.height) * 100;
        
        card.style.background = `
            radial-gradient(circle at ${gradientX}% ${gradientY}%, 
                rgba(255, 255, 255, 0.2) 0%,
                rgba(255, 255, 255, 0.1) 30%,
                rgba(255, 255, 255, 0.05) 70%,
                rgba(255, 255, 255, 0.02) 100%)
        `;
    }

    resetHolographicEffect(card) {
        card.style.transform = '';
        card.style.background = '';
    }

    // === CYBERPUNK PANELS === //
    initCyberpunkPanels() {
        const panels = document.querySelectorAll('.cyber-panel');
        
        panels.forEach(panel => {
            this.addCyberpunkGlitch(panel);
        });
    }

    addCyberpunkGlitch(panel) {
        setInterval(() => {
            if (Math.random() < 0.1) {
                panel.style.filter = 'hue-rotate(90deg) saturate(150%)';
                setTimeout(() => {
                    panel.style.filter = '';
                }, 100);
            }
        }, 2000);
    }

    // === GESTURE CONTROLS === //
    initGestureControls() {
        let startX, startY;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            this.handleGesture(deltaX, deltaY);
        });
    }

    handleGesture(deltaX, deltaY) {
        const threshold = 50;
        
        if (Math.abs(deltaX) > threshold) {
            if (deltaX > 0) {
                this.triggerGestureEffect('swipe-right');
            } else {
                this.triggerGestureEffect('swipe-left');
            }
        }
        
        if (Math.abs(deltaY) > threshold) {
            if (deltaY > 0) {
                this.triggerGestureEffect('swipe-down');
            } else {
                this.triggerGestureEffect('swipe-up');
            }
        }
    }

    triggerGestureEffect(gesture) {
        console.log(`🖐️ Gesture detected: ${gesture}`);
        // Add specific gesture actions here
    }

    // === VOICE COMMANDS === //
    initVoiceCommands() {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'fr-FR';
            
            recognition.onresult = (event) => {
                const command = event.results[0][0].transcript.toLowerCase();
                this.processVoiceCommand(command);
            };
            
            // Add voice activation button
            this.createVoiceButton(recognition);
        }
    }

    processVoiceCommand(command) {
        console.log(`🎤 Voice command: ${command}`);
        
        if (command.includes('recherche') || command.includes('chercher')) {
            this.focusSearchBar();
        } else if (command.includes('menu')) {
            this.toggleMenu();
        } else if (command.includes('aide')) {
            this.showHelp();
        }
    }

    createVoiceButton(recognition) {
        const voiceBtn = document.createElement('button');
        voiceBtn.className = 'fab-item';
        voiceBtn.innerHTML = '🎤';
        voiceBtn.title = 'Commande vocale';
        
        voiceBtn.addEventListener('click', () => {
            recognition.start();
            this.showVoiceIndicator();
        });
        
        const fabMenu = document.querySelector('.fab-menu');
        if (fabMenu) {
            fabMenu.appendChild(voiceBtn);
        }
    }

    showVoiceIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'voice-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 255, 255, 0.9);
            color: white;
            padding: 20px;
            border-radius: 50px;
            font-weight: bold;
            z-index: 10000;
            animation: pulse 1s ease-in-out infinite;
        `;
        indicator.textContent = '🎤 Parlez maintenant...';
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.parentNode.removeChild(indicator);
            }
        }, 3000);
    }

    // === AI ASSISTANT === //
    initAIAssistant() {
        this.createAIAssistant();
    }

    createAIAssistant() {
        const assistant = document.createElement('div');
        assistant.className = 'ai-assistant';
        assistant.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(45deg, #00ff80, #00ffff);
            border-radius: 50%;
            cursor: pointer;
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            transition: all 0.3s ease;
            box-shadow: 0 0 20px rgba(0, 255, 128, 0.5);
            animation: aiPulse 2s ease-in-out infinite;
        `;
        assistant.innerHTML = '🤖';
        
        assistant.addEventListener('click', () => {
            this.toggleAIChat();
        });
        
        document.body.appendChild(assistant);
    }

    toggleAIChat() {
        let chatBox = document.querySelector('.ai-chat-box');
        
        if (!chatBox) {
            chatBox = this.createAIChatBox();
        }
        
        chatBox.style.display = chatBox.style.display === 'none' ? 'block' : 'none';
    }

    createAIChatBox() {
        const chatBox = document.createElement('div');
        chatBox.className = 'ai-chat-box';
        chatBox.style.cssText = `
            position: fixed;
            bottom: 170px;
            right: 30px;
            width: 300px;
            height: 400px;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid #00ffff;
            border-radius: 15px;
            padding: 20px;
            z-index: 1000;
            display: none;
            backdrop-filter: blur(20px);
        `;
        
        chatBox.innerHTML = `
            <div style="color: #00ffff; font-weight: bold; margin-bottom: 15px;">
                🤖 Assistant IA AgriWeb
            </div>
            <div class="chat-messages" style="height: 300px; overflow-y: auto; margin-bottom: 15px; color: white;">
                <div style="margin-bottom: 10px;">Bonjour ! Je suis votre assistant IA. Comment puis-je vous aider ?</div>
            </div>
            <input type="text" placeholder="Tapez votre question..." style="width: 100%; padding: 10px; border: 1px solid #00ffff; background: transparent; color: white; border-radius: 5px;">
        `;
        
        const input = chatBox.querySelector('input');
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleAIMessage(e.target.value, chatBox);
                e.target.value = '';
            }
        });
        
        document.body.appendChild(chatBox);
        return chatBox;
    }

    handleAIMessage(message, chatBox) {
        const messagesContainer = chatBox.querySelector('.chat-messages');
        
        // Add user message
        const userMsg = document.createElement('div');
        userMsg.style.cssText = 'margin-bottom: 10px; text-align: right; color: #00ffff;';
        userMsg.textContent = `Vous: ${message}`;
        messagesContainer.appendChild(userMsg);
        
        // Simulate AI response
        setTimeout(() => {
            const aiMsg = document.createElement('div');
            aiMsg.style.cssText = 'margin-bottom: 10px; color: #00ff80;';
            aiMsg.textContent = `IA: ${this.generateAIResponse(message)}`;
            messagesContainer.appendChild(aiMsg);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 1000);
        
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    generateAIResponse(message) {
        const responses = [
            "Je comprends votre question. Laissez-moi analyser les données agricoles...",
            "Excellente question ! Voici ce que je peux vous dire...",
            "D'après les données géospatiales, je recommande...",
            "C'est une problématique intéressante en agriculture de précision...",
            "Permettez-moi de consulter la base de données AgriWeb..."
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }

    // === MICRO-INTERACTIONS === //
    initMicroInteractions() {
        this.observeElements();
        this.initScrollAnimations();
        this.initHoverEffects();
    }

    observeElements() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('bounce-in');
                }
            });
        });

        document.querySelectorAll('.holo-card, .cyber-panel').forEach(el => {
            observer.observe(el);
        });
    }

    initScrollAnimations() {
        let ticking = false;
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.updateScrollAnimations();
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    updateScrollAnimations() {
        const scrollPercent = window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight);
        
        // Update neural background based on scroll
        const neuralNodes = document.querySelector('.neural-nodes');
        if (neuralNodes) {
            neuralNodes.style.transform = `translateY(${scrollPercent * 50}px)`;
        }
    }

    initHoverEffects() {
        document.querySelectorAll('button, .clickable').forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.classList.add('glow-pulse');
            });
            
            element.addEventListener('mouseleave', () => {
                element.classList.remove('glow-pulse');
            });
        });
    }

    // === UTILITY METHODS === //
    focusSearchBar() {
        const searchInput = document.querySelector('.morph-search input');
        if (searchInput) {
            searchInput.focus();
        }
    }

    toggleMenu() {
        const menu = document.querySelector('.sidebar');
        if (menu) {
            menu.classList.toggle('active');
        }
    }

    showHelp() {
        alert('🚀 Interface Ultra-Moderne 2025 activée ! Utilisez les commandes vocales ou les gestes tactiles.');
    }
}

// === CSS ANIMATION KEYFRAMES (à ajouter dynamiquement) === //
const additionalStyles = `
@keyframes quantumRipple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

@keyframes aiPulse {
    0%, 100% {
        box-shadow: 0 0 20px rgba(0, 255, 128, 0.5);
        transform: scale(1);
    }
    50% {
        box-shadow: 0 0 40px rgba(0, 255, 128, 0.8);
        transform: scale(1.05);
    }
}

@keyframes fadeOut {
    to {
        opacity: 0;
        transform: scale(0);
    }
}

@keyframes pulse {
    0%, 100% { transform: translate(-50%, -50%) scale(1); }
    50% { transform: translate(-50%, -50%) scale(1.1); }
}
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.ultraModernUI = new UltraModernUI();
});

// Export for external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UltraModernUI;
}
