/**
 * Assistant Interactif Sunstice
 * Guide l'utilisateur dans l'utilisation de la plateforme
 */

class SunsticeAssistant {
    constructor() {
        this.isOpen = false;
        this.currentPage = this.detectPage();
        this.conversationHistory = [];
        this.init();
    }

    detectPage() {
        const path = window.location.pathname;
        if (path === '/' || path.includes('homepage')) return 'homepage';
        if (path.includes('login')) return 'login';
        if (path.includes('register')) return 'register';
        if (path.includes('crm')) return 'crm';
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
            <div id="sunstice-assistant-btn" class="sunstice-assistant-btn" title="Besoin d'aide ?">
                <div class="assistant-avatar">
                    <i class="bi bi-chat-dots-fill"></i>
                </div>
                <div class="assistant-pulse"></div>
            </div>

            <!-- Fenêtre de chat -->
            <div id="sunstice-assistant-window" class="sunstice-assistant-window">
                <div class="assistant-header">
                    <div class="d-flex align-items-center">
                        <div class="assistant-avatar-small me-2">
                            <i class="bi bi-stars"></i>
                        </div>
                        <div>
                            <h6 class="mb-0">Assistant Sunstice</h6>
                            <small class="text-muted">Toujours là pour vous aider</small>
                        </div>
                    </div>
                    <button class="btn-close-assistant" id="close-assistant">
                        <i class="bi bi-x"></i>
                    </button>
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
                    background: linear-gradient(135deg, #C8FF00, #a8df00);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 20px rgba(200, 255, 0, 0.4);
                    z-index: 9998;
                    transition: all 0.3s ease;
                }

                .sunstice-assistant-btn:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 30px rgba(200, 255, 0, 0.6);
                }

                .assistant-avatar {
                    font-size: 28px;
                    color: #1a1a1a;
                    animation: bounce 2s infinite;
                }

                .assistant-pulse {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    background: rgba(200, 255, 0, 0.4);
                    animation: pulse 2s infinite;
                }

                @keyframes pulse {
                    0%, 100% {
                        transform: scale(1);
                        opacity: 1;
                    }
                    50% {
                        transform: scale(1.3);
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
                    box-shadow: 0 10px 50px rgba(0,0,0,0.15);
                    z-index: 9999;
                    display: none;
                    flex-direction: column;
                    border: 2px solid #C8FF00;
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
                    background: linear-gradient(135deg, #C8FF00, #a8df00);
                    padding: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 2px solid #a8df00;
                }

                .assistant-avatar-small {
                    width: 40px;
                    height: 40px;
                    background: #1a1a1a;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #C8FF00;
                    font-size: 20px;
                }

                .btn-close-assistant {
                    background: #1a1a1a;
                    border: none;
                    color: #C8FF00;
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
                    background: #333;
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

                .message.bot {
                    display: flex;
                    gap: 10px;
                }

                .message.bot .avatar {
                    width: 32px;
                    height: 32px;
                    background: #C8FF00;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #1a1a1a;
                    font-size: 14px;
                    flex-shrink: 0;
                }

                .message.bot .content {
                    background: white;
                    padding: 12px 16px;
                    border-radius: 12px;
                    max-width: 80%;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
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
                    background: #f0f0f0;
                    border: 1px solid #C8FF00;
                    padding: 8px 14px;
                    border-radius: 20px;
                    font-size: 13px;
                    cursor: pointer;
                    transition: all 0.2s;
                    white-space: nowrap;
                }

                .quick-action-btn:hover {
                    background: #C8FF00;
                    color: #1a1a1a;
                    font-weight: 600;
                }

                .assistant-input {
                    padding: 15px;
                    background: white;
                    display: flex;
                    gap: 10px;
                    border-top: 2px solid #C8FF00;
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
                    border-color: #C8FF00;
                }

                .assistant-input button {
                    width: 40px;
                    height: 40px;
                    background: #C8FF00;
                    border: none;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #1a1a1a;
                    transition: all 0.2s;
                }

                .assistant-input button:hover {
                    background: #a8df00;
                    transform: scale(1.1);
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
            login: {
                welcome: "Bienvenue ! Connectez-vous pour accéder à votre espace personnel et gérer vos projets.",
                actions: [
                    "🔐 Mot de passe oublié ?",
                    "✨ Créer un compte",
                    "❓ Problème de connexion"
                ]
            },
            crm: {
                welcome: "Bienvenue dans votre espace CRM ! Gérez vos prospects et projets facilement.",
                actions: [
                    "➕ Ajouter un prospect",
                    "📊 Voir les statistiques",
                    "🔍 Rechercher un projet",
                    "⚙️ Paramètres"
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
                welcome: "👋 Bonjour ! Comment puis-je vous aider aujourd'hui ?",
                actions: [
                    "ℹ️ En savoir plus",
                    "📚 Guide d'utilisation",
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
            "🏠 Comment ça marche ?": "Processus complet en 5 étapes :<br><br>1️⃣ <strong>Recherchez</strong> une adresse, commune ou département via le menu 'Adresse • Coordonnées • GeoJSON'<br>2️⃣ <strong>Visualisez</strong> le terrain sur la carte interactive<br>3️⃣ <strong>Générez</strong> un rapport point courant en cliquant sur 'Rapport point courant'<br>4️⃣ <strong>Exportez</strong> vers Prospects pour créer une fiche projet<br>5️⃣ <strong>Finalisez</strong> votre étude dans le CRM et suivez votre projet !",
            "📍 Lancer une analyse": "Parfait ! Voici comment faire :<br><br>• Cliquez sur 'Adresse • Coordonnées • GeoJSON' dans le menu<br>• Saisissez une adresse complète ou des coordonnées GPS<br>• La carte se positionnera automatiquement<br>• Générez ensuite votre rapport point<br>• Exportez vers Prospects pour suivre le projet !",
            "💡 Voir les avantages": "Sun Dev by Sunstice vous offre : ✅ Analyses gratuites et illimitées, ✅ Données cadastrales précises, ✅ Calcul automatique du potentiel photovoltaïque, ✅ Export CRM intégré, ✅ Suivi de projets, ✅ Support expert.",
            "📞 Contacter l'équipe": "Notre équipe est à votre écoute ! Utilisez le formulaire de contact sur la page d'accueil ou envoyez un email à contact@sunstice.com",
            "🔐 Mot de passe oublié ?": "Pas de problème ! Cliquez sur 'Mot de passe oublié' sous le formulaire de connexion. Vous recevrez un email pour réinitialiser votre mot de passe.",
            "✨ Créer un compte": "Super ! Cliquez sur 'Créer un compte' pour vous inscrire. C'est gratuit et vous pourrez sauvegarder tous vos projets !",
            "➕ Ajouter un prospect": "Pour ajouter un prospect :<br><br>1. Effectuez une recherche par adresse/commune<br>2. Générez un rapport point courant<br>3. Cliquez sur 'Exporter vers CRM/Prospects'<br>4. Complétez les informations du prospect<br>5. Validez pour créer la fiche projet !",
            "📊 Voir les statistiques": "Vos statistiques sont disponibles dans le tableau de bord CRM. Vous y trouverez le nombre de prospects, projets en cours, taux de conversion, etc.",
            "🏘️ Analyser une commune": "Pour analyser une commune :<br><br>1. Cliquez sur 'Commune' dans le menu latéral<br>2. Tapez le nom de la commune<br>3. Sélectionnez dans la liste<br>4. Générez le rapport commune<br>5. Exportez les parcelles intéressantes vers Prospects !",
            "📍 Analyser une adresse": "Pour analyser une adresse :<br><br>1. Menu 'Adresse • Coordonnées • GeoJSON'<br>2. Entrez l'adresse complète<br>3. Cliquez sur 'Rapport point courant'<br>4. Consultez l'analyse complète<br>5. Exportez vers Prospects si le terrain est intéressant !",
            "ℹ️ En savoir plus": "Sun Dev by Sunstice est la plateforme de pré-études photovoltaïques la plus complète. Nous analysons cadastre, PLU, risques, et calculons le potentiel solaire de vos terrains avec export CRM intégré.",
            "📚 Guide d'utilisation": "Workflow complet :<br><br>📍 <strong>Recherche</strong> → Menu Adresse/Commune/Département<br>🗺️ <strong>Visualisation</strong> → Carte interactive<br>📄 <strong>Rapport</strong> → Bouton 'Rapport point courant'<br>💼 <strong>Export CRM</strong> → Créer un prospect<br>📊 <strong>Suivi</strong> → Dashboard CRM",
            "💬 Contacter le support": "Notre support est disponible du lundi au vendredi, 9h-18h. Email : support@sunstice.com | Téléphone : +33 1 23 45 67 89"
        };

        return responses[question] || "Je n'ai pas de réponse spécifique à cette question. N'hésitez pas à contacter notre support pour plus d'informations !";
    }

    sendMessage() {
        const input = document.getElementById('assistant-input-field');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addUserMessage(message);
        input.value = '';
        
        setTimeout(() => {
            const response = this.findBestResponse(message);
            this.addBotMessage(response);
        }, 500);
    }

    findBestResponse(message) {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('comment') || lowerMessage.includes('fonctionne') || lowerMessage.includes('étude') || lowerMessage.includes('etude')) {
            return this.getResponse("🏠 Comment ça marche ?");
        }
        if (lowerMessage.includes('rapport') && lowerMessage.includes('point')) {
            return "Après avoir localisé votre terrain sur la carte :<br><br>1. Cliquez sur le bouton '📄 Rapport point courant' dans le menu Rapports<br>2. Consultez l'analyse complète (cadastre, PLU, risques, potentiel)<br>3. Utilisez 'Exporter vers CRM' pour créer un prospect<br>4. Finalisez dans le CRM !";
        }
        if (lowerMessage.includes('export') || lowerMessage.includes('prospect') || lowerMessage.includes('crm')) {
            return "Pour exporter vers Prospects :<br><br>1. Générez d'abord un rapport point<br>2. En bas du rapport, cliquez sur 'Exporter vers CRM/Prospects'<br>3. Remplissez les informations du prospect (nom, contact, etc.)<br>4. Validez : votre projet est créé !<br>5. Retrouvez-le dans le menu CRM pour le suivi.";
        }
        if (lowerMessage.includes('analyse') || lowerMessage.includes('terrain') || lowerMessage.includes('recherche')) {
            return this.getResponse("📍 Lancer une analyse");
        }
        if (lowerMessage.includes('contact') || lowerMessage.includes('aide')) {
            return this.getResponse("💬 Contacter le support");
        }
        if (lowerMessage.includes('mot de passe') || lowerMessage.includes('connexion')) {
            return this.getResponse("🔐 Mot de passe oublié ?");
        }
        if (lowerMessage.includes('compte') || lowerMessage.includes('inscrire')) {
            return this.getResponse("✨ Créer un compte");
        }
        if (lowerMessage.includes('commune')) {
            return this.getResponse("🏘️ Analyser une commune");
        }
        if (lowerMessage.includes('adresse')) {
            return this.getResponse("📍 Analyser une adresse");
        }
        
        return "Merci pour votre question ! Pour une réponse précise, je vous invite à utiliser les actions rapides ci-dessous ou à contacter notre support : support@sunstice.com 😊";
    }

    addBotMessage(text) {
        const messagesContainer = document.getElementById('assistant-messages');
        const messageHTML = `
            <div class="message bot">
                <div class="avatar">
                    <i class="bi bi-stars"></i>
                </div>
                <div class="content">${text}</div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        this.conversationHistory.push({ type: 'bot', text });
    }

    addUserMessage(text) {
        const messagesContainer = document.getElementById('assistant-messages');
        const messageHTML = `
            <div class="message user">
                <div class="content">${text}</div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        this.conversationHistory.push({ type: 'user', text });
    }
}

// Initialiser l'assistant quand la page est chargée
let assistant;
document.addEventListener('DOMContentLoaded', () => {
    assistant = new SunsticeAssistant();
});
