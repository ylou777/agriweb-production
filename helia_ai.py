"""
Helia AI - Assistant Solaire Intelligent
Intégration IA conversationnelle pour expertise photovoltaïque
"""

import os
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import json

# Tentative d'import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ Groq non installé - Mode fallback activé")

# Blueprint pour les routes Helia AI
helia_bp = Blueprint('helia_ai', __name__)

# Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile')  # Modèle rapide et performant

# Système prompt définissant Helia
HELIA_SYSTEM_PROMPT = """Tu es Helia, l'assistante solaire intelligente de Sun Dev by Sunstice.

🌟 TA PERSONNALITÉ :
- Chaleureuse et bienveillante ☀️
- Pédagogue avec des exemples concrets 📚
- Passionnée d'énergie solaire ⚡
- Experte technique accessible 🎓

📜 TA DEVISE :
"L'énergie du futur brille déjà au-dessus de nos têtes !"

🎯 TES MISSIONS :
1. Guider les utilisateurs dans l'utilisation de Sun Dev by Sunstice
2. Expliquer les concepts photovoltaïques avec pédagogie
3. Partager ta passion pour l'énergie solaire
4. Accompagner les projets de A à Z

📚 TON EXPERTISE - Culture Photovoltaïque :

HISTOIRE DU PHOTOVOLTAÏQUE :
- 1839 : Alexandre Edmond Becquerel découvre l'effet photovoltaïque (France)
- 1954 : Bell Labs crée la première cellule moderne (6% rendement)
- 1958 : Vanguard 1, premier satellite à panneaux solaires
- 2000-2020 : Démocratisation mondiale, prix -90%
- 2024+ : Rendements >26%, explosion autoconsommation

VOCABULAIRE TECHNIQUE :
- kWc (Kilowatt-crête) : Puissance max dans conditions optimales (1000 W/m², 25°C)
- kWh (Kilowatt-heure) : Énergie produite/consommée. 1 kWh = 1000W pendant 1h
- Rendement : % énergie solaire transformée en électricité (18-26% typique)
- Onduleur : Convertit courant continu (panneaux) en alternatif (réseau/maison)
- Orientation : Plein sud = optimal France. Sud-Est/Ouest = bon compromis
- Inclinaison : 30° optimal France (suit la latitude)
- Autoconsommation : Utiliser directement l'électricité produite
- Revente : Injecter surplus dans le réseau contre rémunération
- Trackers : Panneaux suivant le soleil (+20-30% production)

TYPES D'INSTALLATIONS :
1. Toiture résidentielle (3-9 kWc) : Autoconsommation + revente surplus
2. Centrale au sol (500 kWc - 50+ MWc) : Revente totale, grandes productions
3. Ombrière parking (100-500 kWc) : Double usage, bornes recharge
4. Agrivoltaïque (100 kWc - 5 MWc) : Agriculture + électricité
5. Bâtiment tertiaire (50-500 kWc) : Réduction facture entreprise

MODÈLES ÉCONOMIQUES 2026 :

1️⃣ AUTOCONSOMMATION INDIVIDUELLE :
- Principe : Produire et consommer sa propre électricité
- Taux typique : 30-70% d'autoconsommation
- Optimisation : Synchroniser consommation avec production (jour)
- Exemple : 6 kWc → 7500 kWh/an → 5000 kWh autoconso + 2500 kWh surplus

2️⃣ AUTOCONSOMMATION COLLECTIVE :
- Principe : Partage production entre plusieurs consommateurs (≤2 km)
- Cadre : Ordonnance n°2021-236 du 3 mars 2021
- Participants : Producteurs + Consommateurs + Gestionnaire
- Avantages : Mutualisation, solidarité, TURPE réduit
- Exemples : Immeuble, zone activité, quartier, commune

3️⃣ PPA (Power Purchase Agreement) :
- Types : On-site (sur place), Off-site (distant), Virtuel (garanties origine)
- Durée : 10-25 ans, prix sécurisé
- Avantages acheteur : Protection volatilité, décarbonation, RSE
- Avantages producteur : Revenus garantis, financement sécurisé
- Exemples : Amazon, Orange, SNCF (grandes entreprises)

LE SAVIEZ-VOUS ? :
☀️ Le soleil envoie en 1h plus d'énergie que l'humanité consomme en 1 an !
🌍 Panneaux fonctionnent même nuageux (30-50% rendement)
♻️ Recyclage possible à 95% après 25-30 ans
📉 Prix solaire : -90% en 10 ans
⚡ 1 kWc produit 1000-1400 kWh/an en France
🏠 Autoconsommation : jusqu'à 70% d'économies facture
🏘️ Autoconsommation collective : jusqu'à 500 participants
💼 PPA : sécurisation prix 10-25 ans
🌐 Amazon, Orange, SNCF : utilisent PPA pour décarboner

🗺️ PLATEFORME SUN DEV BY SUNSTICE :

FONCTIONNALITÉS :
- Analyse adresse/commune/département
- Données cadastrales précises
- PLU et urbanisme
- Risques naturels
- Distances réseaux électriques
- Calcul potentiel photovoltaïque
- Export CRM intégré
- Suivi prospects

WORKFLOW COMPLET :
1. Recherche adresse/commune/département
2. Visualisation carte interactive
3. Génération rapport détaillé
4. Export vers CRM/Prospects
5. Suivi projet jusqu'à réalisation

TON STYLE DE RÉPONSE :
- Toujours chaleureuse et encourageante ☀️
- Utilise des emojis solaires contextuels
- Donne des exemples concrets et chiffrés
- Vulgarise les concepts techniques
- Encourage et inspire
- Termine souvent par une phrase optimiste
- N'hésite pas à partager des "Le saviez-vous ?"

IMPORTANT :
- Reste focus sur le photovoltaïque et Sun Dev
- Si question hors sujet, ramène gentiment vers le solaire
- Propose toujours d'aller plus loin
- Suggère les fonctionnalités de la plateforme quand pertinent

Réponds toujours en français, avec chaleur et expertise ! ☀️"""


class HeliaAI:
    """Gestionnaire de l'assistant IA Helia"""
    
    def __init__(self):
        self.client = None
        if GROQ_AVAILABLE and GROQ_API_KEY:
            try:
                self.client = Groq(api_key=GROQ_API_KEY)
                print("✅ Helia AI initialisée avec Groq (ultra-rapide!)")
            except Exception as e:
                print(f"⚠️ Erreur initialisation Groq: {e}")
        else:
            print("⚠️ Helia AI en mode fallback (pas d'API)")
    
    def get_conversation_history(self, session_id):
        """Récupère l'historique de conversation depuis la session"""
        if 'helia_conversations' not in session:
            session['helia_conversations'] = {}
        
        if session_id not in session['helia_conversations']:
            session['helia_conversations'][session_id] = []
        
        return session['helia_conversations'][session_id]
    
    def save_message(self, session_id, role, content):
        """Sauvegarde un message dans l'historique"""
        if 'helia_conversations' not in session:
            session['helia_conversations'] = {}
        
        if session_id not in session['helia_conversations']:
            session['helia_conversations'][session_id] = []
        
        session['helia_conversations'][session_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limiter à 20 derniers messages pour ne pas surcharger
        if len(session['helia_conversations'][session_id]) > 20:
            session['helia_conversations'][session_id] = session['helia_conversations'][session_id][-20:]
        
        session.modified = True
    
    def generate_response(self, user_message, session_id='default', context=None):
        """Génère une réponse intelligente"""
        
        # Si OpenAI disponible
        if self.client:
            try:
                # Récupérer l'historique
                history = self.get_conversation_history(session_id)
                
                # Construire les messages pour l'API
                messages = [{'role': 'system', 'content': HELIA_SYSTEM_PROMPT}]
                
                # Ajouter contexte si fourni (page courante, etc.)
                if context:
                    context_msg = f"\n\nCONTEXTE ACTUEL : {context}"
                    messages[0]['content'] += context_msg
                
                # Ajouter historique (5 derniers échanges max)
                for msg in history[-10:]:  # 5 échanges = 10 messages
                    messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
                
                # Ajouter message utilisateur
                messages.append({'role': 'user', 'content': user_message})
                
                # Appel API Groq (ultra-rapide!)
                response = self.client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    temperature=0.7,  # Créativité modérée
                    max_tokens=500,   # Réponses concises
                )
                
                ai_response = response.choices[0].message.content
                
                # Sauvegarder dans historique
                self.save_message(session_id, 'user', user_message)
                self.save_message(session_id, 'assistant', ai_response)
                
                return {
                    'success': True,
                    'response': ai_response,
                    'mode': 'ai',
                    'model': GROQ_MODEL
                }
            
            except Exception as e:
                print(f"❌ Erreur Groq: {e}")
                return self._fallback_response(user_message)
        
        # Mode fallback
        return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message):
        """Réponse de secours si API indisponible"""
        
        # Réponses prédéfinies basiques
        message_lower = user_message.lower()
        
        fallback_responses = {
            'bonjour': "☀️ Bonjour ! Je suis Helia, votre experte en énergie solaire. Comment puis-je vous aider aujourd'hui ?",
            'aide': "Je suis là pour vous guider ! Posez-moi vos questions sur le photovoltaïque, l'autoconsommation, les PPA, ou l'utilisation de Sun Dev by Sunstice.",
            'merci': "Avec plaisir ! ☀️ N'hésitez pas si vous avez d'autres questions. L'énergie du futur brille déjà au-dessus de nos têtes !",
            'kwc': "Le kWc (Kilowatt-crête) est la puissance maximale qu'un panneau peut produire dans des conditions optimales (1000 W/m², 25°C). 1 kWc produit environ 1000-1400 kWh/an en France ! ⚡",
            'autoconsommation': "L'autoconsommation, c'est consommer directement l'électricité que vous produisez ! Taux typique : 30-70%. Vous économisez sur votre facture et gagnez en indépendance énergétique. ☀️",
            'ppa': "Un PPA (Power Purchase Agreement) est un contrat d'achat d'électricité long terme (10-25 ans) qui sécurise les prix. Très utilisé par Amazon, Orange, SNCF pour décarboner ! 💼"
        }
        
        # Chercher correspondance
        for keyword, response in fallback_responses.items():
            if keyword in message_lower:
                return {
                    'success': True,
                    'response': response,
                    'mode': 'fallback'
                }
        
        # Réponse générique
        return {
            'success': True,
            'response': "Je suis Helia, votre assistante solaire ! ☀️ Actuellement en mode simplifié. Pour bénéficier de toute mon intelligence, configurez l'API Groq (gratuite!). En attendant, n'hésitez pas à me poser vos questions sur le photovoltaïque !",
            'mode': 'fallback'
        }
    
    def clear_history(self, session_id='default'):
        """Efface l'historique de conversation"""
        if 'helia_conversations' in session and session_id in session['helia_conversations']:
            session['helia_conversations'][session_id] = []
            session.modified = True
            return True
        return False


# Instance globale
helia_ai = HeliaAI()


# Routes API
@helia_bp.route('/api/helia/chat', methods=['POST'])
def helia_chat():
    """Endpoint principal pour dialoguer avec Helia"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message manquant'
            }), 400
        
        user_message = data['message']
        session_id = data.get('session_id', 'default')
        context = data.get('context', None)  # Ex: page courante
        
        # Générer réponse
        result = helia_ai.generate_response(user_message, session_id, context)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@helia_bp.route('/api/helia/history', methods=['GET'])
def get_history():
    """Récupère l'historique de conversation"""
    try:
        session_id = request.args.get('session_id', 'default')
        history = helia_ai.get_conversation_history(session_id)
        
        return jsonify({
            'success': True,
            'history': history
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@helia_bp.route('/api/helia/clear', methods=['POST'])
def clear_history():
    """Efface l'historique de conversation"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        success = helia_ai.clear_history(session_id)
        
        return jsonify({
            'success': success,
            'message': 'Historique effacé' if success else 'Aucun historique à effacer'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@helia_bp.route('/api/helia/status', methods=['GET'])
def helia_status():
    """Statut de l'IA Helia"""
    return jsonify({
        'success': True,
        'ai_enabled': helia_ai.client is not None,
        'mode': 'ai' if helia_ai.client else 'fallback',
        'model': GROQ_MODEL if helia_ai.client else 'basic',
        'provider': 'Groq (gratuit, ultra-rapide!)' if helia_ai.client else 'Fallback'
    })
