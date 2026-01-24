/**
 * HELIA - Assistante Solaire Interactive ☀️
 * Votre experte photovoltaïque personnelle
 * Chaleureuse, pédagogue et passionnée d'énergie solaire
 * Version enrichie avec culture photovoltaïque approfondie
 */

class SunsticeAssistant {
    constructor() {
        this.isOpen = false;
        this.currentPage = this.detectPage();
        this.conversationHistory = [];
        this.knowledgeBase = null;
        this.sessionId = this.generateSessionId();
        this.aiEnabled = false;
        this.loadKnowledgeBase();
        this.checkAIStatus();
        this.init();
    }

    generateSessionId() {
        return 'helia_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async checkAIStatus() {
        try {
            const response = await fetch('/api/helia/status');
            const data = await response.json();
            this.aiEnabled = data.ai_enabled;
            console.log(`🤖 Helia AI: ${this.aiEnabled ? 'Activée (' + data.model + ')' : 'Mode fallback'}`);
        } catch (error) {
            console.warn('⚠️ Helia AI status check failed, using fallback mode');
            this.aiEnabled = false;
        }
    }

    async loadKnowledgeBase() {
        try {
            // Charger la base de connaissances
            const response = await fetch('/static/js/assistant-knowledge-base.js');
            const script = await response.text();
            eval(script);
            if (typeof SunsticeKnowledgeBase !== 'undefined') {
                this.knowledgeBase = SunsticeKnowledgeBase;
                console.log('✅ Base de connaissances chargée');
            }
        } catch (error) {
            console.warn('⚠️ Base de connaissances non disponible, mode simplifié');
        }
    }

    detectPage() {
        const path = window.location.pathname;
        if (path === '/' || path.includes('homepage')) return 'homepage';
        if (path.includes('login')) return 'login';
        if (path.includes('register')) return 'register';
        if (path.includes('crm')) return 'crm';
        if (path.includes('app') || path.includes('index')) return 'recherche';
        if (path.includes('rapport')) return 'rapport';
        if (path.includes('demo')) return 'demo';
        return 'general';
    }

    init() {
        this.createAssistant();
        this.attachEventListeners();
        
        // Afficher message de bienvenue après 3 secondes
        setTimeout(() => this.showWelcomeMessage(), 3000);
    }

    createAssistant() {
        const assistantHTML = `
            <!-- Bouton flottant de l'assistant -->
            <div id="sunstice-assistant-btn" class="sunstice-assistant-btn" title="Helia, votre experte solaire ☀️">
                <div class="assistant-avatar">
                    <i class="bi bi-sun-fill"></i>
                </div>
                <div class="assistant-pulse"></div>
            </div>

            <!-- Fenêtre de chat -->
            <div id="sunstice-assistant-window" class="sunstice-assistant-window">
                <div class="assistant-header">
                    <div class="d-flex align-items-center">
                        <div class="assistant-avatar-small me-2">
                            <i class="bi bi-sun-fill"></i>
                        </div>
                        <div class="flex-grow-1">
                            <h6 class="mb-0">☀️ Helia</h6>
                            <small class="text-muted">Votre experte en énergie solaire</small>
                        </div>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <!-- Sélecteur de mode Helia -->
                        <div class="helia-mode-selector">
                            <button class="helia-mode-btn active" data-mode="assiste" title="Mode Assisté (proactif)">
                                <i class="bi bi-stars"></i>
                            </button>
                            <button class="helia-mode-btn" data-mode="manuel" title="Mode Manuel (réactif)">
                                <i class="bi bi-hand-index"></i>
                            </button>
                        </div>
                        <button class="btn-close-assistant" id="close-assistant">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>

                <div class="assistant-messages" id="assistant-messages">
                    <!-- Messages apparaîtront ici -->
                </div>

                <div class="assistant-quick-actions" id="quick-actions">
                    <!-- Actions rapides basées sur la page -->
                </div>

                <div class="assistant-input">
                    <input 
                        type="text" 
                        id="assistant-input-field" 
                        placeholder="Posez votre question..."
                        autocomplete="off"
                    />
                    <button id="send-message-btn">
                        <i class="bi bi-send-fill"></i>
                    </button>
                </div>
            </div>
        `;

        const styles = `
            <style>
                .sunstice-assistant-btn {
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, #FFD700, #FFA500, #FF8C00);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 20px rgba(255, 215, 0, 0.5);
                    z-index: 9998;
                    transition: all 0.3s ease;
                    border: 3px solid #FFED4E;
                }

                .sunstice-assistant-btn:hover {
                    transform: scale(1.1) rotate(15deg);
                    box-shadow: 0 6px 30px rgba(255, 215, 0, 0.8);
                }

                .assistant-avatar {
                    font-size: 32px;
                    color: #FF6B00;
                    animation: rotate 4s linear infinite, pulse-glow 2s ease-in-out infinite;
                    text-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
                }

                @keyframes rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }

                @keyframes pulse-glow {
                    0%, 100% { 
                        filter: drop-shadow(0 0 5px #FFD700);
                    }
                    50% { 
                        filter: drop-shadow(0 0 20px #FFA500);
                    }
                }

                .assistant-pulse {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    background: rgba(255, 215, 0, 0.5);
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% {
                        transform: scale(1);
                        opacity: 1;
                    }
                    50% {
                        transform: scale(1.4);
                        opacity: 0;
                    }
                }

                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-5px); }
                }

                .sunstice-assistant-window {
                    position: fixed;
                    bottom: 100px;
                    right: 30px;
                    width: 380px;
                    height: 600px;
                    background: white;
                    border-radius: 16px;
                    box-shadow: 0 10px 50px rgba(255, 140, 0, 0.3);
                    z-index: 9999;
                    display: none;
                    flex-direction: column;
                    border: 3px solid #FFD700;
                    overflow: hidden;
                    animation: slideUp 0.3s ease;
                }

                .sunstice-assistant-window.open {
                    display: flex;
                }

                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .assistant-header {
                    background: linear-gradient(135deg, #FFD700, #FFA500);
                    padding: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 3px solid #FF8C00;
                    box-shadow: 0 2px 10px rgba(255, 140, 0, 0.3);
                }

                .assistant-avatar-small {
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #FF6B00, #FF8C00);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #FFF;
                    font-size: 20px;
                    box-shadow: 0 2px 8px rgba(255, 107, 0, 0.4);
                    animation: gentle-pulse 3s ease-in-out infinite;
                }

                @keyframes gentle-pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                }

                .btn-close-assistant {
                    background: rgba(255, 107, 0, 0.2);
                    border: 2px solid #FF8C00;
                    color: #FF6B00;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }

                .btn-close-assistant:hover {
                    background: #FF6B00;
                    color: white;
                    transform: rotate(90deg);
                }

                .assistant-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    background: #f8f9fa;
                }

                .message {
                    margin-bottom: 15px;
                    animation: fadeIn 0.3s ease;
                }

                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                /* Indicateur de frappe (typing) */
                .typing-indicator {
                    display: flex;
                    gap: 5px;
                    padding: 10px;
                }

                .typing-indicator span {
                    width: 8px;
                    height: 8px;
                    background: #FFD700;
                    border-radius: 50%;
                    animation: typing-bounce 1.4s infinite;
                }

                .typing-indicator span:nth-child(2) {
                    animation-delay: 0.2s;
                }

                .typing-indicator span:nth-child(3) {
                    animation-delay: 0.4s;
                }

                @keyframes typing-bounce {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-10px); }
                }

                .message.bot {
                    display: flex;
                    gap: 10px;
                }

                .message.bot .avatar {
                    width: 32px;
                    height: 32px;
                    background: linear-gradient(135deg, #FFD700, #FFA500);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #FFF;
                    font-size: 16px;
                    flex-shrink: 0;
                    box-shadow: 0 2px 6px rgba(255, 140, 0, 0.3);
                }

                .message.bot .content {
                    background: linear-gradient(to right, #FFF9E6, white);
                    padding: 12px 16px;
                    border-radius: 12px;
                    max-width: 80%;
                    box-shadow: 0 2px 8px rgba(255, 140, 0, 0.1);
                    border-left: 3px solid #FFD700;
                }

                .message.user .content {
                    background: #1a1a1a;
                    color: white;
                    padding: 12px 16px;
                    border-radius: 12px;
                    margin-left: auto;
                    max-width: 80%;
                    text-align: right;
                }

                .assistant-quick-actions {
                    padding: 15px;
                    background: white;
                    border-top: 1px solid #e0e0e0;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }

                .quick-action-btn {
                    background: linear-gradient(135deg, #FFF9E6, #FFEDD5);
                    border: 2px solid #FFD700;
                    padding: 8px 14px;
                    border-radius: 20px;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.3s;
                    white-space: nowrap;
                    color: #FF6B00;
                    font-weight: 500;
                }

                .quick-action-btn:hover {
                    background: linear-gradient(135deg, #FFD700, #FFA500);
                    color: white;
                    font-weight: 600;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(255, 140, 0, 0.3);
                }

                .assistant-input {
                    padding: 15px;
                    background: linear-gradient(to bottom, white, #FFF9E6);
                    display: flex;
                    gap: 10px;
                    border-top: 3px solid #FFD700;
                }

                .assistant-input input {
                    flex: 1;
                    border: 1px solid #e0e0e0;
                    border-radius: 24px;
                    padding: 10px 16px;
                    font-size: 14px;
                    outline: none;
                }

                .assistant-input input:focus {
                    border-color: #FFD700;
                    box-shadow: 0 0 0 3px rgba(255, 215, 0, 0.2);
                }

                .assistant-input button {
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #FFD700, #FFA500);
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    transition: all 0.3s;
                    box-shadow: 0 2px 8px rgba(255, 140, 0, 0.3);
                }

                .assistant-input button:hover {
                    background: linear-gradient(135deg, #FFA500, #FF8C00);
                    transform: scale(1.15) rotate(15deg);
                    box-shadow: 0 4px 12px rgba(255, 140, 0, 0.5);
                }

                /* Mode Selector Styles */
                .helia-mode-selector {
                    display: flex;
                    gap: 5px;
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 20px;
                    padding: 4px;
                }

                .helia-mode-btn {
                    background: transparent;
                    border: none;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    cursor: pointer;
                    color: rgba(255, 107, 0, 0.6);
                    font-size: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                }

                .helia-mode-btn:hover {
                    background: rgba(255, 255, 255, 0.5);
                    color: #FF6B00;
                }

                .helia-mode-btn.active {
                    background: white;
                    color: #FF6B00;
                    box-shadow: 0 2px 6px rgba(255, 107, 0, 0.3);
                    font-weight: bold;
                }

                @media (max-width: 768px) {
                    .sunstice-assistant-window {
                        width: calc(100vw - 20px);
                        right: 10px;
                        bottom: 90px;
                    }
                }
            </style>
        `;

        document.body.insertAdjacentHTML('beforeend', styles + assistantHTML);
    }

    attachEventListeners() {
        const btn = document.getElementById('sunstice-assistant-btn');
        const closeBtn = document.getElementById('close-assistant');
        const window = document.getElementById('sunstice-assistant-window');
        const sendBtn = document.getElementById('send-message-btn');
        const input = document.getElementById('assistant-input-field');
        
        // Initialiser le conteneur de messages
        this.messagesContainer = document.getElementById('assistant-messages');
        this.quickActionsContainer = document.getElementById('quick-actions');

        // Mode buttons
        const modeBtns = document.querySelectorAll('.helia-mode-btn');
        modeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.switchMode(e.target.closest('.helia-mode-btn').dataset.mode));
        });

        // Charger le mode actuel au démarrage
        this.loadCurrentMode();

        btn.addEventListener('click', () => this.toggleWindow());
        closeBtn.addEventListener('click', () => this.toggleWindow());
        sendBtn.addEventListener('click', () => this.sendMessage());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    }

    toggleWindow() {
        const window = document.getElementById('sunstice-assistant-window');
        this.isOpen = !this.isOpen;
        window.classList.toggle('open');
        
        if (this.isOpen && this.conversationHistory.length === 0) {
            this.showInitialMessage();
        }
    }

    async loadCurrentMode() {
        try {
            const response = await fetch('/api/helia/mode');
            const data = await response.json();
            this.updateModeUI(data.mode);
        } catch (error) {
            console.warn('⚠️ Impossible de charger le mode Helia, défaut: assisté');
            this.updateModeUI('assiste');
        }
    }

    async switchMode(mode) {
        try {
            const response = await fetch('/api/helia/mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mode: mode })
            });

            if (response.ok) {
                const data = await response.json();
                this.updateModeUI(mode);
                
                // Afficher une notification de changement de mode
                const modeLabel = mode === 'assiste' ? 'Assisté (proactif)' : 'Manuel (réactif)';
                this.addMessage('bot', `🔄 Mode changé : **${modeLabel}**\n\n${mode === 'assiste' ? 
                    'Je suis maintenant **proactive** et vais vous suggérer des actions automatiquement !' :
                    'Je vais maintenant attendre vos demandes explicites avant d\'agir.'}`);
            }
        } catch (error) {
            console.error('❌ Erreur changement de mode:', error);
            this.addMessage('bot', '❌ Impossible de changer de mode. Veuillez réessayer.');
        }
    }

    updateModeUI(mode) {
        const modeBtns = document.querySelectorAll('.helia-mode-btn');
        modeBtns.forEach(btn => {
            if (btn.dataset.mode === mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }

    showWelcomeMessage() {
        const btn = document.getElementById('sunstice-assistant-btn');
        const tooltip = document.createElement('div');
        tooltip.style.cssText = `
            position: fixed;
            bottom: 100px;
            right: 100px;
            background: #1a1a1a;
            color: white;
            padding: 12px 18px;
            border-radius: 12px;
            font-size: 14px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            z-index: 9997;
            animation: fadeIn 0.3s ease;
        `;
        tooltip.textContent = "👋 Besoin d'aide ? Je suis là !";
        document.body.appendChild(tooltip);
        
        setTimeout(() => tooltip.remove(), 4000);
    }

    showInitialMessage() {
        const messages = this.getPageMessages();
        this.addBotMessage(messages.welcome);
        this.showQuickActions();
    }

    getPageMessages() {
        const messages = {
            homepage: {
                welcome: "👋 Bienvenue sur Sun Dev by Sunstice ! Je suis là pour vous guider dans votre pré-étude photovoltaïque. Par où souhaitez-vous commencer ?",
                actions: [
                    "🏠 Comment ça marche ?",
                    "📍 Lancer une analyse",
                    "💡 Voir les avantages",
                    "📞 Contacter l'équipe"
                ]
            },
            recherche: {
                welcome: "🗺️ Vous êtes sur l'interface de recherche. Choisissez votre type d'analyse : adresse, commune ou département. Je peux vous guider !",
                actions: [
                    "📍 Comment analyser une adresse ?",
                    "🏘️ Comment analyser une commune ?",
                    "🗺️ Comment analyser un département ?",
                    "📄 Comment générer un rapport ?",
                    "💼 Comment exporter vers CRM ?"
                ]
            },
            rapport: {
                welcome: "📊 Votre rapport est généré ! Vous pouvez maintenant l'analyser et l'exporter vers le CRM pour créer un prospect.",
                actions: [
                    "📖 Comment lire ce rapport ?",
                    "💼 Exporter vers CRM",
                    "📥 Télécharger en PDF",
                    "🔄 Faire une nouvelle recherche"
                ]
            },
            login: {
                welcome: "Bienvenue ! Connectez-vous pour accéder à votre espace personnel et gérer vos projets.",
                actions: [
                    "🔐 Mot de passe oublié ?",
                    "✨ Créer un compte",
                    "❓ Problème de connexion"
                ]
            },
            crm: {
                welcome: "💼 Bienvenue dans votre espace CRM ! Gérez vos prospects et suivez vos projets facilement.",
                actions: [
                    "➕ Comment ajouter un prospect ?",
                    "🔍 Comment rechercher un projet ?",
                    "📊 Voir mes statistiques",
                    "📅 Gérer le calendrier",
                    "📈 Changer un statut prospect"
                ]
            },
            demo: {
                welcome: "Découvrez nos exemples concrets ! Testez différents types de terrains et parcelles.",
                actions: [
                    "🏘️ Analyser une commune",
                    "📍 Analyser une adresse",
                    "🗺️ Analyser un département"
                ]
            },
            general: {
                welcome: "☀️ Bonjour ! Je suis Helia, votre experte en énergie solaire. Comment puis-je illuminer votre journée ? 😊",
                actions: [
                    "ℹ️ En savoir plus",
                    "📚 Guide d'utilisation",
                    "💡 Le saviez-vous ?",
                    "⚡ C'est quoi l'autoconsommation ?",
                    "💬 Contacter le support"
                ]
            }
        };

        return messages[this.currentPage] || messages.general;
    }

    showQuickActions() {
        const container = document.getElementById('quick-actions');
        const messages = this.getPageMessages();
        
        container.innerHTML = messages.actions.map(action => 
            `<button class="quick-action-btn" onclick="assistant.handleQuickAction('${action}')">${action}</button>`
        ).join('');
    }

    handleQuickAction(action) {
        this.addUserMessage(action);
        
        setTimeout(() => {
            const response = this.getResponse(action);
            this.addBotMessage(response);
        }, 500);
    }

    getResponse(question) {
        const responses = {
            // Actions homepage
            "🏠 Comment ça marche ?": "☀️ Laissez-moi vous guider dans votre aventure solaire ! Voici le processus en <strong>5 étapes simples</strong> :<br><br>1️⃣ <strong>Recherchez</strong> ➡️ Menu 'Adresse • Coordonnées • GeoJSON' - Tapez n'importe quelle adresse<br><br>2️⃣ <strong>Visualisez</strong> ➡️ La carte interactive vous montre le terrain - Zoomez, explorez !<br><br>3️⃣ <strong>Générez</strong> ➡️ Cliquez sur 'Rapport point courant' - J'analyse tout pour vous<br><br>4️⃣ <strong>Exportez</strong> ➡️ Créez une fiche prospect dans le CRM<br><br>5️⃣ <strong>Finalisez</strong> ➡️ Suivez votre projet jusqu'à la réalisation !<br><br>🌟 <em>C'est aussi simple que ça !</em>",
            "📍 Lancer une analyse": "Parfait ! Voici comment faire :<br><br>• Cliquez sur 'Adresse • Coordonnées • GeoJSON' dans le menu<br>• Saisissez une adresse complète ou des coordonnées GPS<br>• La carte se positionnera automatiquement<br>• Générez ensuite votre rapport point<br>• Exportez vers Prospects pour suivre le projet !",
            "💡 Voir les avantages": "Sun Dev by Sunstice vous offre : ✅ Analyses gratuites et illimitées, ✅ Données cadastrales précises, ✅ Calcul automatique du potentiel photovoltaïque, ✅ Export CRM intégré, ✅ Suivi de projets, ✅ Support expert.",
            "📞 Contacter l'équipe": "Notre équipe est à votre écoute ! Utilisez le formulaire de contact sur la page d'accueil ou envoyez un email à contact@sunstice.com",
            
            // Actions page recherche
            "📍 Comment analyser une adresse ?": "Pour analyser une adresse :<br><br>1️⃣ Cliquez sur <strong>'Adresse • Coordonnées • GeoJSON'</strong> dans le menu latéral gauche<br>2️⃣ Entrez l'adresse complète (ex: 15 rue de la République, 75001 Paris)<br>3️⃣ La carte se centre automatiquement sur le point<br>4️⃣ Menu <strong>'Rapports'</strong> → <strong>'Rapport point courant'</strong><br>5️⃣ Consultez l'analyse complète<br>6️⃣ Bouton <strong>'Exporter vers CRM'</strong> en bas du rapport<br>7️⃣ Créez votre fiche prospect !",
            "🏘️ Comment analyser une commune ?": "Pour analyser une commune :<br><br>1️⃣ Cliquez sur <strong>'Commune'</strong> dans le menu latéral gauche<br>2️⃣ Tapez le nom de la commune (l'autocomplétion vous aide)<br>3️⃣ Sélectionnez dans la liste proposée<br>4️⃣ La carte affiche toute la commune<br>5️⃣ Menu <strong>'Rapports'</strong> → <strong>'Rapport commune'</strong><br>6️⃣ Identifiez les parcelles à fort potentiel<br>7️⃣ Cliquez sur une parcelle pour un rapport point détaillé",
            "🗺️ Comment analyser un département ?": "Pour analyser un département :<br><br>1️⃣ Cliquez sur <strong>'Département (SSE)'</strong> dans le menu latéral gauche<br>2️⃣ Entrez le code (ex: 75) ou le nom du département<br>3️⃣ Sélectionnez dans la liste<br>4️⃣ La carte affiche tout le département<br>5️⃣ Menu <strong>'Rapports'</strong> → <strong>'Rapport département'</strong><br>6️⃣ Consultez les statistiques globales et communes prioritaires<br>7️⃣ Zoomez sur une commune pour approfondir l'analyse",
            "📄 Comment générer un rapport ?": "Pour générer un rapport :<br><br><strong>Rapport Point :</strong><br>1. Localisez un point (adresse/coordonnées)<br>2. Menu Rapports → Rapport point courant<br><br><strong>Rapport Commune :</strong><br>1. Sélectionnez une commune<br>2. Menu Rapports → Rapport commune<br><br><strong>Rapport Département :</strong><br>1. Sélectionnez un département<br>2. Menu Rapports → Rapport département<br><br>💡 Tous les rapports peuvent être exportés en PDF et vers le CRM !",
            "💼 Comment exporter vers CRM ?": "Pour exporter vers le CRM :<br><br>1️⃣ Générez d'abord un <strong>rapport point</strong><br>2️⃣ Descendez en bas du rapport<br>3️⃣ Bouton <strong>'Exporter vers CRM/Prospects'</strong><br>4️⃣ Remplissez les informations du prospect :<br>   • Nom du prospect (obligatoire)<br>   • Contact, téléphone, email<br>   • Notes et remarques<br>5️⃣ Cliquez sur <strong>'Créer le prospect'</strong><br>6️⃣ Retrouvez-le dans le menu <strong>CRM</strong> !<br><br>💡 Le rapport est automatiquement attaché à la fiche prospect.",
            
            // Actions page rapport
            "📖 Comment lire ce rapport ?": "Sections du rapport :<br><br>📍 <strong>Localisation</strong> - Carte et coordonnées<br>📐 <strong>Cadastre</strong> - Parcelles et surfaces<br>🏗️ <strong>PLU</strong> - Zonage et règlement<br>⚠️ <strong>Risques</strong> - Inondations, sismique, etc.<br>⚡ <strong>Réseaux</strong> - Distances postes sources<br>☀️ <strong>Potentiel PV</strong> - Puissance et production estimée<br>🌳 <strong>Environnement</strong> - Zones protégées<br><br>Descendez pour voir tous les détails !",
            "💼 Exporter vers CRM": "En bas du rapport, cliquez sur 'Exporter vers CRM/Prospects'. Remplissez le formulaire et validez !",
            "📥 Télécharger en PDF": "En haut du rapport, bouton '📥 Télécharger PDF'. Le fichier est généré automatiquement !",
            "🔄 Faire une nouvelle recherche": "Utilisez le menu latéral gauche pour lancer une nouvelle recherche (adresse, commune, département).",
            
            // Actions page CRM
            "➕ Comment ajouter un prospect ?": "Deux méthodes :<br><br><strong>Méthode 1 (recommandée) :</strong><br>1. Faites une analyse (adresse/commune)<br>2. Générez un rapport point<br>3. Exportez vers CRM<br><br><strong>Méthode 2 :</strong><br>1. Dans le CRM, bouton '+ Nouveau Prospect'<br>2. Remplissez manuellement les informations<br>3. Sauvegardez",
            "🔍 Comment rechercher un projet ?": "Dans le CRM :<br><br>1. Utilisez la barre de recherche en haut<br>2. Ou utilisez les filtres :<br>   • Par statut (Nouveau, Qualifié, Gagné...)<br>   • Par date<br>   • Par commune<br>   • Par type de projet<br>   • Par utilisateur<br><br>Combinez plusieurs filtres pour affiner !",
            "📊 Voir mes statistiques": "Le dashboard CRM affiche :<br><br>📈 Nombre total de prospects<br>✅ Projets qualifiés<br>🎉 Projets gagnés<br>📊 Taux de conversion<br>📅 Activité récente<br>💰 Valeur du pipeline<br><br>Graphiques et indicateurs en temps réel !",
            "📅 Gérer le calendrier": "Dans une fiche prospect :<br><br>1. Section 'Calendrier'<br>2. Bouton 'Ajouter rendez-vous'<br>3. Date, heure, type (visite, appel, réunion)<br>4. Sauvegardez<br><br>Les RDV apparaissent dans votre dashboard !",
            "📈 Changer un statut prospect": "Statuts disponibles :<br><br>🆕 Nouveau → 📞 Contact → ✅ Qualifié → 📄 Proposition → 🎉 Gagné<br><br>Dans la fiche prospect, menu déroulant 'Statut'. Changez selon l'avancement du projet !",
            
            // Actions login
            "🔐 Mot de passe oublié ?": "Page de connexion → 'Mot de passe oublié' → Entrez votre email → Suivez le lien reçu par email pour réinitialiser.",
            "✨ Créer un compte": "Cliquez sur 'Créer un compte'. Remplissez le formulaire : email, mot de passe, nom, entreprise. C'est gratuit !",
            "❓ Problème de connexion": "Vérifiez :<br><br>✓ Email correct<br>✓ Mot de passe correct (majuscules/minuscules)<br>✓ Compte activé (email de confirmation)<br><br>Sinon, utilisez 'Mot de passe oublié' ou contactez support@sunstice.com",
                        // Modèles économiques modernes
            "⚡ C'est quoi l'autoconsommation ?": "Excellente question ! 💡<br><br><strong>L'autoconsommation</strong> = consommer directement l'électricité que vous produisez avec vos panneaux solaires.<br><br>🏠 <strong>Principe</strong> :<br>Panneaux → Onduleur → Consommation directe → Surplus revendu ou stocké<br><br>✅ <strong>Avantages</strong> :<br>• Économies immédiates sur votre facture<br>• Indépendance énergétique partielle<br>• Taux d'autoconso typique : 30-70%<br>• Rentabilité immédiate<br><br>📊 <strong>Exemple</strong> :<br>Installation 6 kWc produit 7500 kWh/an<br>→ 5000 kWh autoconsommés = économies directes<br>→ 2500 kWh surplus revendus<br><br>💡 <em>Optimisez en utilisant vos appareils pendant la journée !</em>",
            "🏘️ Autoconsommation collective ?": "Concept innovant de partage d'énergie ! 🌟<br><br><strong>Autoconsommation collective</strong> = Partager la production solaire entre plusieurs consommateurs via le réseau public.<br><br>🎯 <strong>Principe</strong> :<br>Un ou plusieurs producteurs alimentent plusieurs consommateurs dans un périmètre ≤ 2 km<br><br>👥 <strong>Qui peut participer ?</strong><br>• Copropriétaires d'un immeuble<br>• Entreprises d'une zone d'activité<br>• Habitants + commerces d'un quartier<br>• Bâtiments publics + citoyens<br><br>✅ <strong>Avantages</strong> :<br>• Mutualisation des coûts<br>• Accès au solaire sans toiture<br>• Solidarité énergétique locale<br>• Réduction pertes (proximité)<br>• Tarif réseau réduit (TURPE)<br><br>📐 <strong>Cadre</strong> : Ordonnance 3 mars 2021<br><br>💡 <em>Une révolution pour démocratiser le solaire !</em>",
            "💼 C'est quoi un PPA ?": "Le PPA, outil stratégique des grandes entreprises ! 🎯<br><br><strong>PPA (Power Purchase Agreement)</strong> = Contrat d'achat d'électricité long terme entre producteur et consommateur.<br><br>📋 <strong>Types de PPA</strong> :<br><br>1️⃣ <strong>On-site</strong> : Installation sur votre site<br>   → Panneaux sur toiture usine<br>   → Autoconsommation maximale<br><br>2️⃣ <strong>Off-site</strong> : Centrale distante<br>   → Production livrée via réseau<br>   → Grandes quantités possibles<br><br>3️⃣ <strong>Virtuel (VPPA)</strong> : Échange garanties d'origine<br>   → Compensation carbone<br>   → Flexibilité géographique<br><br>✅ <strong>Avantages acheteur</strong> :<br>• Prix électricité sécurisé 10-25 ans<br>• Protection volatilité marché<br>• Décarbonation consommation<br>• Objectifs RSE atteints<br><br>🏢 <strong>Exemples</strong> : Amazon, Orange, SNCF utilisent des PPA<br><br>💡 <em>L'avenir de l'approvisionnement électrique corporate !</em>",            // Autres
            "💡 Le saviez-vous ?": "Voici quelques faits fascinants sur l'énergie solaire : <br><br>☀️ Le soleil envoie en <strong>1 heure</strong> plus d'énergie que l'humanité n'en consomme en <strong>1 an</strong> !<br><br>🌍 Les panneaux solaires fonctionnent même par temps <strong>nuageux</strong> (30-50% de rendement) !<br><br>♻️ Un panneau solaire peut être <strong>recyclé à 95%</strong> en fin de vie (25-30 ans) !<br><br>📊 Le prix du solaire a <strong>baissé de 90%</strong> en 10 ans !<br><br>⚡ 1 kWc produit environ <strong>1000-1400 kWh/an</strong> en France selon les régions !",
            // Autres
            "📍 Analyser une adresse": "Menu 'Adresse • Coordonnées • GeoJSON' → Entrez l'adresse → Rapport point courant → Exportez vers CRM !",
            "🏘️ Analyser une commune": "Menu 'Commune' → Tapez le nom → Sélectionnez → Rapport commune → Analysez les parcelles !",
            "ℹ️ En savoir plus": "☀️ Je suis ravie de vous présenter <strong>Sun Dev by Sunstice</strong> !<br><br>Nous sommes la plateforme de pré-études photovoltaïques la plus complète. J'analyse pour vous :<br><br>📍 <strong>Cadastre</strong> - Parcelles et surfaces disponibles<br>🏛️ <strong>PLU</strong> - Réglementation d'urbanisme<br>⚠️ <strong>Risques</strong> - Pour sécuriser vos projets<br>⚡ <strong>Réseaux électriques</strong> - Distance aux postes sources<br>☀️ <strong>Potentiel solaire</strong> - Production estimée en kWh<br>📊 <strong>Export CRM</strong> - Suivi de vos prospects<br><br>Mon objectif ? Rendre l'énergie solaire accessible à tous ! 🌟",
            "📚 Guide d'utilisation": "☀️ Parfait ! Voici votre feuille de route solaire :<br><br>📍 <strong>1. Recherche</strong><br>Menu Adresse/Commune/Département ➡️ Trouvez votre site<br><br>🗺️ <strong>2. Visualisation</strong><br>Carte interactive ➡️ Explorez le terrain<br><br>📄 <strong>3. Rapport</strong><br>Générez une analyse complète ➡️ Cadastre, PLU, potentiel PV<br><br>💼 <strong>4. Export CRM</strong><br>Créez une fiche prospect ➡️ Centralisez vos projets<br><br>📊 <strong>5. Suivi</strong><br>Dashboard CRM ➡️ Pilotez du premier contact à la réalisation<br><br>💡 <em>Astuce : Commencez par une adresse simple pour vous familiariser !</em>",
            "💬 Contacter le support": "👋 Besoin d'aide supplémentaire ? Notre équipe passionnée est là pour vous !<br><br>📧 <strong>Email</strong> : support@sunstice.com<br>📞 <strong>Téléphone</strong> : +33 1 23 45 67 89<br>🕒 <strong>Horaires</strong> : Lundi-Vendredi, 9h-18h<br><br>🌟 Nous répondons généralement en moins de 2h !<br><br><em>En attendant, je reste à votre disposition pour toute question !</em> ☀️"
        };

        return responses[question] || "Je n'ai pas de réponse spécifique à cette question. N'hésitez pas à contacter notre support pour plus d'informations !";
    }

    sendMessage() {
        const input = document.getElementById('assistant-input-field');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addUserMessage(message);
        input.value = '';
        
        // Essayer d'abord l'IA si activée
        if (this.aiEnabled) {
            this.sendToAI(message);
        } else {
            // Fallback sur réponses prédéfinies
            setTimeout(() => {
                const response = this.findBestResponse(message);
                this.addBotMessage(response);
            }, 500);
        }
    }

    async sendToAI(message) {
        try {
            // Ajouter un indicateur de chargement
            this.addBotMessage('<div class="typing-indicator"><span></span><span></span><span></span></div>', true);
            
            const response = await fetch('/api/helia/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    context: `Page: ${this.currentPage}`
                })
            });

            const data = await response.json();
            
            // Retirer l'indicateur de chargement
            const messagesContainer = document.getElementById('assistant-messages');
            const lastMessage = messagesContainer.lastElementChild;
            if (lastMessage && lastMessage.querySelector('.typing-indicator')) {
                lastMessage.remove();
            }

            if (data.success) {
                this.addBotMessage(data.response);
                console.log(`✨ Réponse ${data.mode === 'ai' ? 'IA' : 'fallback'}`);
                
                // Ouvrir automatiquement la carte si une URL est présente dans la réponse
                if (data.data && data.data.carte_url) {
                    console.log('🗺️ Ouverture automatique de la carte:', data.data.carte_url);
                    this.openMap(data.data.carte_url);
                }
            } else {
                // Si erreur, utiliser fallback
                const fallbackResponse = this.findBestResponse(message);
                this.addBotMessage(fallbackResponse);
            }
        } catch (error) {
            console.error('❌ Erreur API Helia:', error);
            
            // Retirer l'indicateur de chargement
            const messagesContainer = document.getElementById('assistant-messages');
            const lastMessage = messagesContainer.lastElementChild;
            if (lastMessage && lastMessage.querySelector('.typing-indicator')) {
                lastMessage.remove();
            }
            
            // Utiliser fallback
            const fallbackResponse = this.findBestResponse(message);
            this.addBotMessage(fallbackResponse);
        }
    }

    openMap(carte_url) {
        /**
         * Ouvre automatiquement la carte avec les résultats de la recherche
         */
        try {
            const mapFrame = document.getElementById('mapFrame');
            
            if (mapFrame) {
                // Charger l'URL dans l'iframe de la carte
                mapFrame.src = `/static/map.html?redirect=${encodeURIComponent(carte_url)}`;
                console.log('✅ Carte ouverte:', carte_url);
                
                // Feedback visuel dans le chat
                setTimeout(() => {
                    this.addBotMessage('🗺️ <em>Carte mise à jour avec les résultats !</em>', false);
                }, 500);
            } else {
                console.warn('⚠️ Iframe mapFrame non trouvée');
                // Ouvrir dans un nouvel onglet si l'iframe n'existe pas
                window.open(carte_url, '_blank');
            }
        } catch (error) {
            console.error('❌ Erreur ouverture carte:', error);
        }
    }

    findBestResponse(message) {
        const lowerMessage = message.toLowerCase();
        
        // Recherche dans la FAQ de la base de connaissances
        if (this.knowledgeBase && this.knowledgeBase.faq) {
            const faqMatch = this.searchInFAQ(lowerMessage);
            if (faqMatch) return faqMatch;
        }
        
        // Recherche dans le troubleshooting
        if (this.knowledgeBase && this.knowledgeBase.troubleshooting) {
            const troubleMatch = this.searchInTroubleshooting(lowerMessage);
            if (troubleMatch) return troubleMatch;
        }
        
        // Détection de workflows spécifiques
        if (lowerMessage.includes('workflow') || lowerMessage.includes('processus complet')) {
            return this.getWorkflowSummary();
        }
        
        // Questions contextuelles détaillées
        if (lowerMessage.includes('comment') || lowerMessage.includes('fonctionne') || lowerMessage.includes('étude') || lowerMessage.includes('etude')) {
            return this.getResponse("🏠 Comment ça marche ?");
        }
        
        if (lowerMessage.includes('rapport') && lowerMessage.includes('point')) {
            return this.getDetailedWorkflow('analyse_adresse', 4);
        }
        
        if (lowerMessage.includes('export') || (lowerMessage.includes('prospect') && !lowerMessage.includes('voir'))) {
            return this.getDetailedWorkflow('gestion_prospect', 1);
        }
        
        if (lowerMessage.includes('commune')) {
            if (lowerMessage.includes('comment') || lowerMessage.includes('analyser')) {
                return this.getDetailedWorkflow('analyse_commune');
            }
            return this.getResponse("🏘️ Analyser une commune");
        }
        
        if (lowerMessage.includes('département') || lowerMessage.includes('departement')) {
            return this.getDetailedWorkflow('analyse_departement');
        }
        
        if (lowerMessage.includes('adresse')) {
            if (lowerMessage.includes('comment') || lowerMessage.includes('analyser')) {
                return this.getDetailedWorkflow('analyse_adresse');
            }
            return this.getResponse("📍 Analyser une adresse");
        }
        
        if (lowerMessage.includes('statut')) {
            return "Les statuts de prospects :<br><br>🆕 <strong>Nouveau</strong> - Prospect jamais contacté<br>📞 <strong>Contact établi</strong> - Premier échange réalisé<br>✅ <strong>Qualifié</strong> - Projet confirmé et sérieux<br>📄 <strong>Proposition envoyée</strong> - Devis transmis<br>🎉 <strong>Gagné</strong> - Projet signé !<br>❌ <strong>Perdu</strong> - Abandon<br>⏳ <strong>En attente</strong> - Projet en pause<br><br>Changez le statut dans la fiche prospect.";
        }
        
        if (lowerMessage.includes('calendrier') || lowerMessage.includes('rendez-vous') || lowerMessage.includes('rdv')) {
            return "Gestion du calendrier :<br><br>1. Ouvrez une fiche prospect dans le CRM<br>2. Section 'Calendrier'<br>3. Bouton 'Ajouter un rendez-vous'<br>4. Renseignez date, heure, type (visite, réunion, appel)<br>5. Sauvegardez<br><br>💡 Les RDV apparaissent dans le dashboard CRM pour ne rien oublier !";
        }
        
        if (lowerMessage.includes('filtre') || lowerMessage.includes('recherche')) {
            return "Filtres disponibles dans le CRM :<br><br>📊 <strong>Par statut</strong> - Nouveau, Qualifié, Gagné...<br>📅 <strong>Par date</strong> - Création, modification<br>🏘️ <strong>Par commune</strong> - Localisation géographique<br>⚡ <strong>Par type</strong> - Sol, toiture, ombrière...<br>👤 <strong>Par utilisateur</strong> - Vos prospects ou équipe (admin)<br><br>Combinez les filtres pour affiner vos recherches !";
        }
        
        if (lowerMessage.includes('pdf') || lowerMessage.includes('télécharger') || lowerMessage.includes('telecharger')) {
            return "Pour télécharger un rapport en PDF :<br><br>1. Générez le rapport (point, commune, département)<br>2. En haut du rapport, bouton '📥 Télécharger PDF'<br>3. Le fichier est généré et téléchargé automatiquement<br>4. Il est aussi sauvegardé dans la fiche prospect si exporté vers CRM<br><br>💡 Tous vos rapports sont archivés dans les fiches prospects !";
        }
        
        if (lowerMessage.includes('contact') || lowerMessage.includes('aide') || lowerMessage.includes('support')) {
            return this.getResponse("💬 Contacter le support");
        }
        
        if (lowerMessage.includes('mot de passe') || lowerMessage.includes('connexion')) {
            return this.getResponse("🔐 Mot de passe oublié ?");
        }
        
        if (lowerMessage.includes('compte') || lowerMessage.includes('inscrire')) {
            return this.getResponse("✨ Créer un compte");
        }
        
        // Si aucune correspondance, proposer astuces
        if (this.knowledgeBase && this.knowledgeBase.astuces) {
            const randomTip = this.knowledgeBase.astuces[Math.floor(Math.random() * this.knowledgeBase.astuces.length)];
            return `Je n'ai pas de réponse spécifique. Voici une astuce :<br><br>${randomTip}<br><br>Utilisez les actions rapides ou contactez le support : support@sunstice.com 😊`;
        }
        
        return "Merci pour votre question ! Pour une réponse précise, je vous invite à utiliser les actions rapides ci-dessous ou à contacter notre support : support@sunstice.com 😊";
    }
    
    searchInFAQ(query) {
        if (!this.knowledgeBase || !this.knowledgeBase.faq) return null;
        
        for (const [question, answer] of Object.entries(this.knowledgeBase.faq)) {
            if (query.includes(question.toLowerCase()) || 
                question.toLowerCase().includes(query.split(' ').slice(0, 3).join(' '))) {
                return `<strong>${question}</strong><br><br>${answer}`;
            }
        }
        return null;
    }
    
    searchInTroubleshooting(query) {
        if (!this.knowledgeBase || !this.knowledgeBase.troubleshooting) return null;
        
        for (const [problem, solution] of Object.entries(this.knowledgeBase.troubleshooting)) {
            if (query.includes(problem.toLowerCase().slice(0, 15))) {
                return `🔧 <strong>${problem}</strong><br><br>${solution}`;
            }
        }
        return null;
    }
    
    getWorkflowSummary() {
        if (!this.knowledgeBase || !this.knowledgeBase.workflows) {
            return "Workflow de base : Recherche → Rapport → Export CRM → Suivi";
        }
        
        let summary = "<strong>📋 Workflows disponibles :</strong><br><br>";
        for (const [key, workflow] of Object.entries(this.knowledgeBase.workflows)) {
            summary += `<strong>${workflow.titre}</strong> (${workflow.etapes.length} étapes)<br>`;
        }
        summary += "<br>Demandez-moi un workflow spécifique pour plus de détails !";
        return summary;
    }
    
    getDetailedWorkflow(workflowName, startStep = 1) {
        if (!this.knowledgeBase || !this.knowledgeBase.workflows || !this.knowledgeBase.workflows[workflowName]) {
            return this.getResponse("🏠 Comment ça marche ?");
        }
        
        const workflow = this.knowledgeBase.workflows[workflowName];
        let response = `<strong>📋 ${workflow.titre}</strong><br><br>`;
        
        workflow.etapes.slice(startStep - 1).forEach(etape => {
            response += `<strong>${etape.numero}.</strong> ${etape.action}<br>`;
            response += `<small style="color: #666;">${etape.detail}</small><br><br>`;
        });
        
        return response;
    }

    addBotMessage(text, showButtons = true, isTyping = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'assistant-message bot-message';
        
        const iconDiv = document.createElement('div');
        iconDiv.className = 'message-icon';
        iconDiv.innerHTML = '☀️';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isTyping) {
            contentDiv.classList.add('typing-indicator');
            contentDiv.innerHTML = '<span></span><span></span><span></span>';
        } else {
            contentDiv.innerHTML = text;
        }
        
        messageDiv.appendChild(iconDiv);
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        
        if (showButtons && !isTyping) {
            this.showButtons();
        }
        
        this.scrollToBottom();
        
        return messageDiv;
    }

    addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'assistant-message user-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = text;
        
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    showButtons() {
        if (!this.quickActionsContainer) return;
        
        const buttons = this.getQuickActionsForPage();
        if (buttons.length === 0) return;
        
        this.quickActionsContainer.innerHTML = '';
        buttons.forEach(action => {
            const btn = document.createElement('button');
            btn.className = 'quick-action-btn';
            btn.innerHTML = action.label;
            btn.onclick = () => this.handleQuickAction(action.action);
            this.quickActionsContainer.appendChild(btn);
        });
    }

    getQuickActionsForPage() {
        const actions = {
            homepage: [
                { label: '🏠 Comment ça marche ?', action: 'how_it_works' },
                { label: '📍 Rechercher une commune', action: 'search_commune' },
                { label: '💬 Contacter le support', action: 'contact' }
            ],
            recherche: [
                { label: '🏘️ Analyser une commune', action: 'analyze_commune' },
                { label: '📊 Filtrer les résultats', action: 'filter_help' },
                { label: '📥 Exporter vers CRM', action: 'export_crm' }
            ],
            crm: [
                { label: '➕ Créer un prospect', action: 'create_prospect' },
                { label: '📊 Voir les KPI', action: 'show_kpi' },
                { label: '🔍 Filtrer prospects', action: 'filter_prospects' }
            ],
            rapport: [
                { label: '📥 Télécharger PDF', action: 'download_pdf' },
                { label: '📋 Copier dans presse-papier', action: 'copy_report' },
                { label: '💾 Exporter vers CRM', action: 'export_to_crm' }
            ],
            general: [
                { label: '🏠 Comment ça marche ?', action: 'how_it_works' },
                { label: '❓ Questions fréquentes', action: 'faq' },
                { label: '💬 Contacter le support', action: 'contact' }
            ]
        };
        
        return actions[this.currentPage] || actions.general;
    }

    handleQuickAction(action) {
        const responses = {
            'how_it_works': '🏠 Comment ça marche ?',
            'search_commune': '📍 Rechercher une commune',
            'contact': '💬 Contacter le support',
            'analyze_commune': '🏘️ Analyser une commune',
            'filter_help': '🔍 Utiliser les filtres',
            'export_crm': '📤 Exporter vers CRM',
            'create_prospect': '➕ Créer un prospect',
            'show_kpi': '📊 Statistiques CRM',
            'filter_prospects': '🔍 Filtrer les prospects',
            'download_pdf': '📥 Télécharger le rapport',
            'copy_report': '📋 Copier dans presse-papier',
            'export_to_crm': '💾 Sauvegarder dans CRM',
            'faq': '❓ Questions fréquentes'
        };
        
        const response = this.getResponse(responses[action] || action);
        this.addBotMessage(response);
    }

    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    showButtons() {
        if (!this.quickActionsContainer) return;
        
        const actions = this.getQuickActionsForPage();
        let buttonsHTML = '';
        
        actions.forEach(action => {
            buttonsHTML += `
                <button class="quick-action-btn" data-action="${action.id}">
                    ${action.icon} ${action.label}
                </button>
            `;
        });
        
        this.quickActionsContainer.innerHTML = buttonsHTML;
        
        // Attacher les événements
        this.quickActionsContainer.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const actionId = e.target.closest('button').dataset.action;
                this.handleQuickAction(actionId);
            });
        });
    }

    handleQuickAction(actionId) {
        const response = this.getResponse(actionId);
        if (response) {
            this.addBotMessage(response, false);
        }
    }
}

// Initialiser l'assistant quand la page est chargée
let assistant;
document.addEventListener('DOMContentLoaded', () => {
    assistant = new SunsticeAssistant();
});
