/**
 * Assistant Interactif Sunstice
 * Guide l'utilisateur dans l'utilisation de la plateforme
 * Version améliorée avec base de connaissances complète
 */

class SunsticeAssistant {
    constructor() {
        this.isOpen = false;
        this.currentPage = this.detectPage();
        this.conversationHistory = [];
        this.knowledgeBase = null;
        this.loadKnowledgeBase();
        this.init();
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
            // Actions homepage
            "🏠 Comment ça marche ?": "Processus complet en 5 étapes :<br><br>1️⃣ <strong>Recherchez</strong> une adresse, commune ou département via le menu 'Adresse • Coordonnées • GeoJSON'<br>2️⃣ <strong>Visualisez</strong> le terrain sur la carte interactive<br>3️⃣ <strong>Générez</strong> un rapport point courant en cliquant sur 'Rapport point courant'<br>4️⃣ <strong>Exportez</strong> vers Prospects pour créer une fiche projet<br>5️⃣ <strong>Finalisez</strong> votre étude dans le CRM et suivez votre projet !",
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
            
            // Autres
            "📍 Analyser une adresse": "Menu 'Adresse • Coordonnées • GeoJSON' → Entrez l'adresse → Rapport point courant → Exportez vers CRM !",
            "🏘️ Analyser une commune": "Menu 'Commune' → Tapez le nom → Sélectionnez → Rapport commune → Analysez les parcelles !",
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

    // Ancienne fonction findBestResponse remplacée par la nouvelle ci-dessus
    // Ne pas dupliquer, cette fonction est maintenant beaucoup plus intelligente

    addBotMessage(text) {
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
