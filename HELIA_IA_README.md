# 🤖 Helia - Assistant IA Photovoltaïque

## 📋 Vue d'ensemble

Helia est un assistant IA conversationnel expert en photovoltaïque, intégré dans AgriWeb. Elle utilise OpenAI GPT-4o-mini pour fournir des réponses intelligentes et contextuelles sur le photovoltaïque, l'autoconsommation, et les outils AgriWeb.

## ✨ Caractéristiques principales

### 🎭 Personnalité Helia
- **Nom**: Helia (déesse solaire)
- **Ton**: Chaleureux, lumineux, pédagogue
- **Expertise**: Photovoltaïque, autoconsommation, AgriWeb
- **Style**: Émojis solaires (☀️🌞⚡), métaphores lumineuses

### 🧠 Connaissances
- **Histoire PV**: 1839 à 2024 (Becquerel → installations modernes)
- **Vocabulaire technique**: kWc, kWh, rendement, onduleur, etc.
- **Types d'installations**: Sol, toiture, ombrière, trackers, flottant
- **Modèles économiques**: Autoconsommation, autoconsommation collective, PPA
- **Outils AgriWeb**: Recherche commune, plan de masse, rapports PDF, CRM

## 🏗️ Architecture technique

### Backend (Flask Blueprint)
```
helia_ai.py
├── HeliaAI (classe)
│   ├── OpenAI client (GPT-4o-mini)
│   ├── Gestion historique conversations
│   └── Génération réponses
└── Routes API
    ├── POST /api/helia/chat
    ├── GET /api/helia/history
    ├── POST /api/helia/clear
    └── GET /api/helia/status
```

### Frontend (JavaScript)
```
sunstice-assistant.js
├── SunsticeAssistant (classe)
│   ├── Détection IA disponible
│   ├── Envoi messages API
│   ├── Indicateur de frappe
│   └── Fallback réponses prédéfinies
└── UI
    ├── Chat interface
    ├── Boutons actions rapides
    └── Animations solaires
```

## 🔌 Intégration

### 1. Configuration Flask
```python
# agriweb_hebergement_gratuit.py
from helia_ai import helia_bp
app.register_blueprint(helia_bp)
```

### 2. Variable d'environnement
```bash
# Fichier .env ou Railway
OPENAI_API_KEY=sk-...votre_clé...
```

### 3. Dépendances Python
```bash
pip install openai
```

## 📡 API Endpoints

### POST /api/helia/chat
Envoie un message à Helia et reçoit une réponse IA.

**Request:**
```json
{
  "message": "Comment fonctionne l'autoconsommation collective ?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "☀️ L'autoconsommation collective permet à plusieurs...",
  "session_id": "abc123..."
}
```

### GET /api/helia/status
Vérifie si l'IA est disponible.

**Response:**
```json
{
  "ai_enabled": true,
  "message": "Assistant IA Helia actif ☀️"
}
```

### GET /api/helia/history
Récupère l'historique de conversation.

**Response:**
```json
{
  "success": true,
  "history": [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "☀️ Bonjour ! Je suis Helia..."}
  ]
}
```

### POST /api/helia/clear
Efface l'historique de conversation.

**Response:**
```json
{
  "success": true,
  "message": "Historique effacé"
}
```

## 🎨 Design & UX

### Thème solaire
```css
/* Couleurs */
--helia-gold: #FFD700
--helia-orange: #FF8C42
--helia-yellow: #FFC857

/* Animations */
.typing-indicator {
  /* 3 points qui rebondissent */
  animation: bounce 1.4s infinite
}

/* Dégradés */
background: linear-gradient(135deg, #FFD700, #FF8C42)
```

### Messages
- **User**: Bulles blanches à droite
- **Helia**: Bulles dorées à gauche avec icône ☀️
- **Typing**: Animation 3 points dorés

## 🔄 Mode Fallback

Si OpenAI n'est pas disponible (pas de clé API, quota dépassé, etc.):

1. Frontend détecte via `/api/helia/status`
2. Bascule sur réponses prédéfinies (assistant-knowledge-base.js)
3. Conserve toutes les fonctionnalités de base
4. Message d'info: "Mode réponses rapides actif"

## 💾 Gestion de session

- **Session ID**: Généré automatiquement au chargement
- **Stockage**: Flask session (côté serveur)
- **Limite historique**: 20 derniers messages
- **Durée**: Session Flask standard (expiration navigateur)

## 🧪 Tests

### Test manuel
```javascript
// Console navigateur
await fetch('/api/helia/status').then(r => r.json())
// {ai_enabled: true, ...}

await fetch('/api/helia/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'Bonjour Helia'})
}).then(r => r.json())
// {success: true, response: "☀️ Bonjour ! Je suis Helia..."}
```

### Test Python
```python
from helia_ai import HeliaAI

helia = HeliaAI()
response = helia.get_response("Qu'est-ce que le kWc ?")
print(response)
# ☀️ Le kWc (kilowatt-crête) représente la puissance...
```

## 📊 Métriques & Monitoring

### Logs serveur
```
🤖 [HELIA] Blueprint assistant IA enregistré
🤖 [HELIA] Chat message reçu: "Bonjour"
🤖 [HELIA] Réponse générée (123 tokens)
⚠️ [HELIA] Erreur OpenAI: RateLimitError
```

### Métriques à surveiller
- Temps de réponse API (<2s souhaité)
- Taux d'erreur OpenAI
- Utilisation tokens (500 max par réponse)
- Sessions actives

## 🚀 Déploiement

### Railway
1. Ajouter variable d'environnement `OPENAI_API_KEY`
2. Déployer avec `helia_ai.py` inclus
3. Vérifier logs: "Blueprint assistant IA enregistré"

### Local
```bash
# Configurer variable
export OPENAI_API_KEY=sk-...

# Lancer serveur
python run_app.py

# Tester
curl http://localhost:5000/api/helia/status
```

## 🔧 Maintenance

### Mettre à jour les connaissances
Modifier `HELIA_SYSTEM_PROMPT` dans [helia_ai.py](helia_ai.py):
```python
HELIA_SYSTEM_PROMPT = """
Tu es Helia...
[Ajouter nouvelles connaissances ici]
"""
```

### Changer le modèle IA
```python
# Dans helia_ai.py, classe HeliaAI
self.client.chat.completions.create(
    model="gpt-4",  # Au lieu de gpt-4o-mini
    ...
)
```

### Ajuster la température
```python
temperature=0.8  # Plus créatif (0.0 = déterministe, 1.0 = créatif)
```

## ❓ FAQ Technique

### Q: Pourquoi GPT-4o-mini ?
**R**: Coût réduit (~50x moins cher que GPT-4), latence faible, qualité suffisante pour assistance PV.

### Q: Comment limiter les coûts ?
**R**: 
- `max_tokens=500` (limite réponse)
- Historique limité à 20 messages
- Fallback sur réponses prédéfinies si quota atteint

### Q: Helia peut-elle accéder aux données utilisateur ?
**R**: Non, Helia n'accède qu'aux messages de conversation. Pas de connexion DB/CRM dans v1.

### Q: Comment ajouter des actions ?
**R**: 
1. Entraîner Helia à reconnaître l'intention ("recherche commune")
2. Retourner JSON avec action: `{"action": "search_commune", "params": {...}}`
3. Frontend JavaScript exécute l'action

## 📚 Ressources

- [Documentation OpenAI](https://platform.openai.com/docs)
- [Flask Blueprints](https://flask.palletsprojects.com/en/2.3.x/blueprints/)
- [Guide assistant original](HELIA_ASSISTANT_README.md)
- [Base de connaissances](static/js/assistant-knowledge-base.js)

## 🎯 Roadmap

### v1.1 (Court terme)
- [ ] Connexion au CRM (créer prospect depuis chat)
- [ ] Commandes vocales (Web Speech API)
- [ ] Traduction multi-langues

### v1.2 (Moyen terme)
- [ ] Suggestions proactives (analyse page)
- [ ] Intégration base documentaire (RAG)
- [ ] Analytics conversations (Dashboard admin)

### v2.0 (Long terme)
- [ ] Agent autonome (recherches automatiques)
- [ ] Fine-tuning modèle personnalisé
- [ ] API publique pour partenaires

---

**Auteur**: AgriWeb Dev Team  
**Dernière mise à jour**: 2026-01-18  
**Version**: 1.0.0
