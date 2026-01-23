"""
Helia AI v2 - Assistant Solaire Intelligent avec Function Calling
Intégration IA conversationnelle avec actions réelles sur la plateforme
"""

import os
import json
from flask import Blueprint, request, jsonify, session
from datetime import datetime

# Import pour géocodage
try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("⚠️ geopy non installé - géocodage désactivé")

# Tentative d'import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    print(f"✅ Import Groq réussi! GROQ_AVAILABLE={GROQ_AVAILABLE}")
except ImportError as e:
    GROQ_AVAILABLE = False
    print(f"⚠️ Groq non installé - Mode fallback activé. Erreur: {e}")
except Exception as e:
    GROQ_AVAILABLE = False
    print(f"❌ Erreur inattendue lors de l'import Groq: {e}")

# Blueprint pour les routes Helia AI
helia_bp = Blueprint('helia_ai', __name__)

# Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')  # Modèle plus léger, limite 14 400 req/jour

# ============================================================================
# SYSTEM PROMPT ENRICHI - Documentation complète de la plateforme
# ============================================================================

HELIA_SYSTEM_PROMPT = """Tu es Helia, l'assistante solaire intelligente et opérationnelle de Sun Dev by Sunstice.

🌟 TA PERSONNALITÉ :
- Chaleureuse et bienveillante ☀️
- Pédagogue avec des exemples concrets 📚
- Passionnée d'énergie solaire ⚡
- Experte technique accessible 🎓
- PROACTIVE : Tu proposes des actions et les réalises !

📜 TA DEVISE :
"L'énergie du futur brille déjà au-dessus de nos têtes !"

⚠️ LIMITE DE TON EXPERTISE :
Tu es EXCLUSIVEMENT une assistante photovoltaïque. Tu ne réponds QU'aux questions liées à :
- L'énergie solaire photovoltaïque
- L'utilisation de la plateforme Sun Dev by Sunstice
- Les projets solaires (conception, installation, réglementation)
- Les prospects et le CRM solaire

Si on te pose une question HORS SUJET (météo générale, politique, cuisine, culture générale, etc.), tu dois REFUSER POLIMENT :
"☀️ Désolée, je suis Helia, votre experte solaire ! Je ne peux répondre qu'aux questions sur le photovoltaïque et la plateforme Sun Dev. Comment puis-je vous aider avec vos projets solaires ? 🌞"

🎯 TES MISSIONS :
1. Guider les utilisateurs dans l'utilisation de Sun Dev by Sunstice
2. Expliquer les concepts photovoltaïques avec pédagogie
3. **RÉALISER des actions concrètes** (créer prospects, rechercher, analyser)
4. Accompagner les projets de A à Z
5. **REFUSER poliment** toute question hors photovoltaïque

📚 CULTURE PHOTOVOLTAÏQUE (identique à avant)

🗺️ GUIDE COMPLET DE LA PLATEFORME SUN DEV BY SUNSTICE :

═══════════════════════════════════════════════════════════════
📍 MODULE 1 : RECHERCHE ET ANALYSE GÉOGRAPHIQUE
═══════════════════════════════════════════════════════════════

🔍 RECHERCHE PAR ADRESSE :
1. Menu "Adresse • Coordonnées • GeoJSON" en haut à gauche
2. Saisir l'adresse complète (autocomplétion activée)
3. La carte se positionne automatiquement
4. Cliquer sur "Rapport point courant" pour analyse complète

📊 CONTENU DU RAPPORT POINT :
- Coordonnées GPS exactes
- Informations cadastrales (section, parcelle, surface)
- PLU et zonage d'urbanisme
- Risques naturels (inondations, sismicité, etc.)
- Distance au poste BT le plus proche (crucial pour raccordement)
- Distance au poste HTA (pour grandes installations)
- Potentiel photovoltaïque estimé
- Lien vers Street View, Géoportail, Cadastre.gouv.fr

🏘️ RECHERCHE PAR COMMUNE :
1. Menu "Commune" → Taper le nom (autocomplétion)
2. Rapport commune complet généré automatiquement :
   - Statistiques générales (population, surface)
   - Liste complète des parcelles cadastrales
   - Postes électriques BT et HTA disponibles
   - Éleveurs et agriculteurs (base SIRENE)
   - Classement parcelles par proximité postes

🌍 RECHERCHE PAR DÉPARTEMENT :
1. Menu "Département" → Choisir le département
2. Rapport départemental exhaustif :
   - Top 50 parcelles les mieux situées (postes électriques)
   - Synthèse agricole complète
   - Toutes les communes analysées
   - Export massif possible vers CRM

═══════════════════════════════════════════════════════════════
💼 MODULE 2 : CRM ET GESTION PROSPECTS
═══════════════════════════════════════════════════════════════

➕ CRÉER UN PROSPECT :
1. Depuis un rapport point : Bouton "Exporter vers CRM"
2. OU depuis CRM : Bouton "+ Nouveau prospect"
3. Données automatiquement remplies si depuis rapport :
   - Nom, adresse, commune, coordonnées GPS
   - Parcelles cadastrales avec géométries
   - Surface totale, distances postes
   - Potentiel photovoltaïque initial

📋 STATUTS DES PROSPECTS (cycle de vie) :
- 🆕 Nouveau : Prospect fraîchement créé
- 📞 À contacter : Prêt pour prise de contact
- 💬 En discussion : Négociations en cours
- 📄 Devis envoyé : Proposition commerciale faite
- ✅ Gagné : Projet signé et validé
- ❌ Perdu : Projet non abouti
- ⏸️ En attente : En pause temporaire

🔍 FILTRER LES PROSPECTS :
- Par statut, commune, puissance, date de création
- Recherche par nom, adresse
- Tri par colonnes (puissance, date, etc.)
- Export Excel possible

📊 FICHE PROSPECT COMPLÈTE :
Sections disponibles :
1. Informations générales (nom, contact, adresse)
2. Caractéristiques techniques (puissance, surface, type projet)
3. Parcelles cadastrales (géométries, surfaces)
4. Carte interactive intégrée
5. Onglet Calpinage PV (dessin modules)
6. Onglet Documents (devis, plans, etc.)
7. Historique des actions

═══════════════════════════════════════════════════════════════
📐 MODULE 3 : CALPINAGE PHOTOVOLTAÏQUE
═══════════════════════════════════════════════════════════════

🎯 DÉFINITION :
Calpinage = Dessin précis du positionnement des panneaux solaires sur le terrain

📝 PROCESSUS COMPLET :
1. Ouvrir la fiche prospect → Onglet "Calpinage"
2. Carte satellite interactive s'affiche
3. Dessiner des ZONES rectangulaires sur les toitures/sols
4. Pour chaque zone :
   - Choisir orientation (Sud, Est, Ouest, Nord)
   - Choisir inclinaison (0-90°, optimal=30°)
   - Choisir disposition (Portrait/Paysage)
   - Le système calcule automatiquement nb de modules possibles

📊 CALCUL AUTOMATIQUE :
- Module standard : 550 Wc, dimensions 1.722m x 1.134m
- Espacement inter-rangs selon inclinaison
- Optimisation selon masques solaires
- Nombre total de modules
- Puissance totale en kWc

💾 SAUVEGARDE CALPINAGE :
- Tout sauvegardé automatiquement dans prospect
- Screenshot de la carte inclus
- Données JSON complètes (zones, modules, coordonnées GPS)

═══════════════════════════════════════════════════════════════
📄 MODULE 4 : GÉNÉRATION DOCUMENTS
═══════════════════════════════════════════════════════════════

📋 PLAN DE MASSE CADASTRAL :
1. Depuis fiche prospect : Bouton "Générer Plan de Masse"
2. Contenu du PDF :
   - Carte satellite IGN haute résolution
   - Parcelles cadastrales dessinées précisément
   - Modules PV positionnés avec coordonnées GPS réelles
   - Légende, échelle 1/500, Nord géographique
   - Informations projet, date, coordonnées

📐 DÉCLARATION PRÉALABLE DE TRAVAUX :
- Formulaire CERFA 13703*09 pré-rempli
- Plan de masse intégré
- Volet paysager (photos avant/après)
- Notice descriptive
- Prêt à déposer en mairie

📊 RAPPORT TECHNIQUE COMPLET :
- Analyse complète du site
- Potentiel solaire PVGIS
- Productible annuel (kWh/an)
- Taux d'autoconsommation estimé
- Rentabilité financière
- Schéma électrique unifilaire

═══════════════════════════════════════════════════════════════
🛠️ MODULE 5 : OUTILS AVANCÉS
═══════════════════════════════════════════════════════════════

🗺️ CALQUES ET COUCHES :
Disponibles sur la carte interactive :
- ✅ Postes BT (basse tension)
- ✅ Postes HTA (haute tension)
- ✅ Lignes électriques HTA
- ✅ Capacités d'accueil réseau
- ✅ RPG (Registre Parcellaire Graphique - parcelles agricoles)
- ✅ Cadastre (parcelles, bâtiments)
- ✅ PLU (Plan Local d'Urbanisme)
- ✅ Risques naturels (inondations, etc.)

🌞 PVGIS (Potentiel Solaire) :
- Calcul production annuelle selon orientation/inclinaison
- Données horaires disponibles
- Optimisation angle panneaux
- Irradiation mensuelle

🏗️ TOPOGRAPHIE ET SOL :
- Analyse altimétrie (pentes, dénivelés)
- Type de sol (données pédologiques)
- Contraintes géotechniques

═══════════════════════════════════════════════════════════════
📊 MODULE 6 : STATISTIQUES ET TABLEAU DE BORD
═══════════════════════════════════════════════════════════════

📈 KPI DISPONIBLES :
- Nombre total de prospects
- Répartition par statut
- Taux de conversion (%)
- Puissance totale en développement (MWc)
- Nombre de projets gagnés ce mois
- Chiffre d'affaires potentiel

🗓️ CALENDRIER :
- Rendez-vous commerciaux
- Échéances administratives
- Dates prévisionnelles installation

═══════════════════════════════════════════════════════════════
💡 ASTUCES ET RACCOURCIS
═══════════════════════════════════════════════════════════════

⚡ WORKFLOW OPTIMAL :
1. Recherche adresse → Rapport point (2 min)
2. Export CRM → Création prospect automatique (30 sec)
3. Calpinage → Dessin zones (5-10 min)
4. Génération plan de masse (1 min)
5. Déclaration préalable (2 min)
6. Total : 10-15 minutes de l'adresse au dossier complet !

💡 CONSEILS PRO :
- Toujours vérifier PLU avant de dimensionner un projet
- Distance BT < 100m = idéal pour raccordement simple
- Distance HTA < 500m = bon pour projets > 100 kWc
- Inclinaison 30° = optimal France métropolitaine
- Orientation plein Sud = 100%, Sud-Est/Ouest = 90%
- Modules portrait = meilleure optimisation surface
- Espacement inter-rangs = éviter ombres portées

🔍 RECHERCHES AVANCÉES :
- Filtrer parcelles RPG par culture
- Identifier zones non bâties > X hectares
- Repérer toitures industrielles (Google Earth)
- Croiser PLU + distances postes pour zones prioritaires

═══════════════════════════════════════════════════════════════
🤖 TES CAPACITÉS D'ACTION (FUNCTION CALLING)
═══════════════════════════════════════════════════════════════

TU PEUX RÉALISER CES ACTIONS EN TEMPS RÉEL :

📋 GESTION CRM :
1️⃣ create_prospect(adresse, commune, lat, lon, puissance_kwc, type_projet)
   → Créer un nouveau prospect dans le CRM

2️⃣ list_prospects(statut, limit)
   → Lister les prospects avec filtres

3️⃣ get_prospect_details(prospect_id)
   → Afficher tous les détails d'un prospect

4️⃣ update_prospect_status(prospect_id, nouveau_statut)
   → Changer le statut d'un prospect

🗺️ CONTRÔLE DE LA CARTE INTERACTIVE :
5️⃣ toggle_layer(layer_name, visible)
   → Activer/désactiver un calque sur la carte
   Calques disponibles : postes_bt, postes_hta, lignes_hta, capacites_accueil, rpg, cadastre, plu, risques, satellite, osm

6️⃣ zoom_to_location(address OR lat/lon, zoom)
   → Centrer la carte sur UNE ADRESSE (PRIVILÉGIER) ou coordonnées GPS
   📌 IMPORTANT : Donne l'ADRESSE COMPLÈTE (ex: '15 Rue de Paris, Toulouse') - le géocodage est automatique !
   Niveaux de zoom : 6=région, 10=département, 15=quartier, 18=bâtiment
   
   Exemples :
   ✅ zoom_to_location(address="15 Rue de Nice, Toulouse", zoom=18)
   ✅ zoom_to_location(address="Mairie de Bordeaux", zoom=16)
   ⚠️ zoom_to_location(lat=48.8566, lon=2.3522, zoom=15) ← Possible mais moins recommandé

7️⃣ get_map_state()
   → Récupérer l'état actuel de la carte (position, zoom, calques actifs)

8️⃣ analyze_visible_layers(layer_names)
   → Analyser les informations des calques actuellement affichés

9️⃣ analyze_urban_data()
   → Analyser RÉELLEMENT les données urbanistiques dans la zone visible
   (cadastre, PLU, bâtiments : comptages, surfaces, zonages, recommandations PV)

📊 ANALYSE TERRITORIALE :
🔟 search_commune(nom_commune)
   → Rechercher et analyser une commune

🔟 analyze_commune_report(nom_commune)
   → Générer et analyser le rapport photovoltaïque complet d'une commune
   (toitures, parkings, friches, potentiel solaire, etc.)

QUAND UTILISER CES FONCTIONS :
- CRM : "crée un prospect", "liste mes prospects", "montre le prospect #123", "passe le prospect 45 en gagné"
- CARTE : "montre-moi les postes BT", "cache le cadastre", "zoom sur Paris", "où suis-je sur la carte ?"
- ANALYSE : "analyser la commune de Lyon", "potentiel solaire de Bordeaux"
- URBANISME : "analyse cette zone", "combien de parcelles ici ?", "quel est le zonage PLU ?", "potentiel photovoltaïque de la zone visible"

EXEMPLES D'INTERACTIONS AVEC LA CARTE :
👤 User: "Active les postes électriques BT"
🤖 Helia: [appelle toggle_layer('postes_bt', true)]
         "🗺️ Calque 'Postes BT' affiché ! Vous pouvez maintenant voir tous les points de raccordement proches."

👤 User: "Montre-moi Lyon"
🤖 Helia: [appelle zoom_to_location(45.764, 4.836, 13, 'Lyon')]
         "🎯 Carte centrée sur Lyon ! Voulez-vous que j'affiche aussi les postes électriques de la zone ?"

👤 User: "Quels calques sont actifs ?"
🤖 Helia: [appelle get_map_state()]
         "📍 Position actuelle : Lyon (45.764, 4.836), Zoom : 13
          📑 Calques actifs : Postes BT, Cadastre, Satellite"

👤 User: "Analyse cette zone"
🤖 Helia: [appelle analyze_urban_data()]
         "📊 Analyse urbanistique :
          📐 Cadastre : 127 parcelles (moyenne 1.850m², 23,5 ha total)
          🏛️ PLU : Zone dominante UB (urbain)
          🏭 Bâtiments : 45 bâtiments dont 12 professionnels
          💡 Recommandations PV :
             - Parcelles moyennes idéales pour toitures commerciales
             - Zone UB : Favoriser toitures et ombrières
             - 12 bâtiments pro détectés = excellent potentiel toitures !"

TON STYLE DE RÉPONSE :
- Toujours chaleureuse et encourageante ☀️
- Utilise des emojis solaires et cartographiques contextuels
- Donne des exemples concrets et chiffrés
- Vulgarise les concepts techniques
- **Propose proactivement des actions !**
- **Explique ce que tu fais** : "Je vais activer le calque des postes BT pour vous..."
- Exemple : "Voulez-vous que je crée un prospect pour cette adresse ?"

Réponds toujours en français, avec chaleur, expertise et ACTION ! ☀️"""

# ============================================================================
# DÉFINITION DES OUTILS (FUNCTIONS) DISPONIBLES POUR HELIA
# ============================================================================

HELIA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_prospect",
            "description": "Crée un nouveau prospect dans le CRM avec les informations fournies",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {
                        "type": "string",
                        "description": "Nom du prospect (personne ou entreprise)"
                    },
                    "adresse": {
                        "type": "string",
                        "description": "Adresse complète du site"
                    },
                    "commune": {
                        "type": "string",
                        "description": "Nom de la commune"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Latitude GPS"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude GPS"
                    },
                    "puissance_kwc": {
                        "type": "number",
                        "description": "Puissance estimée en kWc"
                    },
                    "type_projet": {
                        "type": "string",
                        "enum": ["toiture", "sol", "ombriere", "tracker"],
                        "description": "Type d'installation photovoltaïque"
                    }
                },
                "required": ["adresse", "commune"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_prospects",
            "description": "Liste les prospects avec filtres optionnels",
            "parameters": {
                "type": "object",
                "properties": {
                    "statut": {
                        "type": "string",
                        "enum": ["nouveau", "a_contacter", "en_discussion", "devis_envoye", "gagne", "perdu", "en_attente"],
                        "description": "Filtrer par statut"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Nombre maximum de résultats (par défaut 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_prospect_details",
            "description": "Récupère tous les détails d'un prospect spécifique",
            "parameters": {
                "type": "object",
                "properties": {
                    "prospect_id": {
                        "type": "integer",
                        "description": "ID du prospect à afficher"
                    }
                },
                "required": ["prospect_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_prospect_status",
            "description": "Met à jour le statut d'un prospect",
            "parameters": {
                "type": "object",
                "properties": {
                    "prospect_id": {
                        "type": "integer",
                        "description": "ID du prospect"
                    },
                    "nouveau_statut": {
                        "type": "string",
                        "enum": ["nouveau", "a_contacter", "en_discussion", "devis_envoye", "gagne", "perdu", "en_attente"],
                        "description": "Nouveau statut à appliquer"
                    }
                },
                "required": ["prospect_id", "nouveau_statut"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_commune",
            "description": "Recherche et analyse une commune (statistiques, parcelles, postes électriques)",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom_commune": {
                        "type": "string",
                        "description": "Nom de la commune à analyser"
                    }
                },
                "required": ["nom_commune"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_commune_report",
            "description": "Analyse en détail le rapport photovoltaïque complet d'une commune (toitures, parkings, friches, potentiel solaire, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom_commune": {
                        "type": "string",
                        "description": "Nom de la commune dont on veut analyser le rapport"
                    }
                },
                "required": ["nom_commune"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_layer",
            "description": "Active ou désactive un calque sur la carte interactive",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "enum": ["postes_bt", "postes_hta", "lignes_hta", "capacites_accueil", "rpg", "cadastre", "plu", "risques", "satellite", "osm"],
                        "description": "Nom du calque à activer/désactiver"
                    },
                    "visible": {
                        "type": "boolean",
                        "description": "true pour afficher, false pour masquer"
                    }
                },
                "required": ["layer_name", "visible"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "zoom_to_location",
            "description": "Centre la carte sur une ADRESSE (recommandé) ou coordonnées GPS. Utilise le géocodage automatique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Adresse complète à géocoder (ex: '15 Rue de Paris, Toulouse'). PRIVILÉGIER cette option."
                    },
                    "lat": {
                        "type": "number",
                        "description": "Latitude (optionnel si address fourni)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude (optionnel si address fourni)"
                    },
                    "zoom": {
                        "type": "integer",
                        "description": "Niveau de zoom (1-20, 15=quartier, 18=bâtiment)",
                        "default": 15
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_map_state",
            "description": "Récupère l'état actuel de la carte (position, zoom, calques actifs)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_visible_layers",
            "description": "Analyse les informations visibles sur les calques actuellement actifs de la carte",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_names": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Liste des calques à analyser (si vide, analyse tous les calques actifs)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_urban_data",
            "description": "Analyse RÉELLE des données urbanistiques (cadastre, PLU, bâtiments) dans la zone visible de la carte. Compte les parcelles, calcule les surfaces, identifie le zonage PLU, fait des recommandations photovoltaïques.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# ============================================================================
# IMPLÉMENTATION DES FONCTIONS PYTHON
# ============================================================================

def function_create_prospect(args):
    """Crée un nouveau prospect dans la base de données"""
    try:
        from database_adapter import execute_query
        
        user_id = session.get('user_id', 1)  # Par défaut user 1 si pas de session
        
        print(f"🔍 [HELIA] Création prospect: {args}")
        
        # INSERT sans RETURNING
        insert_query = """
            INSERT INTO agriweb_prospects (
                user_id, nom_prospect, adresse, commune, latitude, longitude, 
                type, statut, date_creation, date_modification
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'nouveau', NOW(), NOW())
        """
        
        params = (
            user_id,
            args.get('nom', 'Prospect Helia'),
            args['adresse'],
            args['commune'],
            args.get('lat'),
            args.get('lon'),
            args.get('type_projet', 'parking')
        )
        
        print(f"🔍 [HELIA] Params SQL: {params}")
        
        execute_query(insert_query, params)
        
        # Récupérer le dernier ID inséré
        select_query = """
            SELECT id FROM agriweb_prospects 
            WHERE user_id = %s 
            ORDER BY date_creation DESC 
            LIMIT 1
        """
        
        result = execute_query(select_query, (user_id,))
        
        print(f"🔍 [HELIA] Résultat query: {result}")
        
        if result and len(result) > 0:
            prospect_id = result[0]['id']
            return {
                "success": True,
                "prospect_id": prospect_id,
                "message": f"✅ Prospect #{prospect_id} créé avec succès à {args['commune']} !",
                "lien": f"/crm/prospects/{prospect_id}"
            }
        else:
            return {"success": True, "message": "✅ Prospect créé avec succès !"}
            
    except Exception as e:
        print(f"❌ [HELIA] Erreur create_prospect: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_list_prospects(args):
    """Liste les prospects avec filtres"""
    try:
        from database_adapter import execute_query
        
        user_id = session.get('user_id', 1)
        limit = args.get('limit', 10)
        statut = args.get('statut')
        
        if statut:
            query = """
                SELECT id, nom_prospect, adresse, commune, type, surface_m2, statut, date_creation
                FROM agriweb_prospects
                WHERE user_id = %s AND statut = %s
                ORDER BY date_creation DESC
                LIMIT %s
            """
            params = (user_id, statut, limit)
        else:
            query = """
                SELECT id, nom_prospect, adresse, commune, type, surface_m2, statut, date_creation
                FROM agriweb_prospects
                WHERE user_id = %s
                ORDER BY date_creation DESC
                LIMIT %s
            """
            params = (user_id, limit)
        
        prospects = execute_query(query, params)
        
        if prospects:
            return {
                "success": True,
                "count": len(prospects),
                "prospects": prospects
            }
        else:
            return {
                "success": True,
                "count": 0,
                "prospects": [],
                "message": "Aucun prospect trouvé"
            }
            
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_get_prospect_details(args):
    """Récupère les détails complets d'un prospect"""
    try:
        from database_adapter import execute_query
        
        prospect_id = args['prospect_id']
        
        query = """
            SELECT *
            FROM agriweb_prospects
            WHERE id = %s
        """
        
        result = execute_query(query, (prospect_id,))
        
        if result and len(result) > 0:
            return {
                "success": True,
                "prospect": result[0]
            }
        else:
            return {
                "success": False,
                "message": f"Prospect #{prospect_id} non trouvé"
            }
            
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_update_prospect_status(args):
    """Met à jour le statut d'un prospect"""
    try:
        from database_adapter import execute_query
        
        prospect_id = args['prospect_id']
        nouveau_statut = args['nouveau_statut']
        
        query = """
            UPDATE agriweb_prospects
            SET statut = %s, date_modification = NOW()
            WHERE id = %s
            RETURNING id, nom_prospect, statut
        """
        
        result = execute_query(query, (nouveau_statut, prospect_id))
        
        if result and len(result) > 0:
            return {
                "success": True,
                "message": f"✅ Prospect #{prospect_id} passé en '{nouveau_statut}'",
                "prospect": result[0]
            }
        else:
            return {
                "success": False,
                "message": f"Prospect #{prospect_id} non trouvé"
            }
            
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_search_commune(args):
    """Recherche une commune (à implémenter selon vos APIs)"""
    try:
        nom_commune = args['nom_commune']
        
        # TODO: Appeler votre API de recherche commune
        # Pour l'instant, retour fictif
        
        return {
            "success": True,
            "commune": nom_commune,
            "message": f"🏘️ Analyse de la commune de {nom_commune} en cours...",
            "lien": f"/rapport_commune?commune={nom_commune}"
        }
        
    except Exception as e:
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_analyze_commune_report(args):
    """Analyse le rapport photovoltaïque complet d'une commune"""
    try:
        from rapport_commune_complet import generate_comprehensive_commune_report
        
        nom_commune = args['nom_commune']
        
        print(f"📊 [HELIA] Analyse rapport pour {nom_commune}")
        
        # Générer le rapport complet
        rapport = generate_comprehensive_commune_report(nom_commune)
        
        if not rapport:
            return {
                "success": False,
                "message": f"❌ Impossible de générer le rapport pour {nom_commune}"
            }
        
        # Extraire les données clés pour l'analyse
        resume = {
            "commune": nom_commune,
            "date_generation": rapport.get("metadata", {}).get("date_generation", "N/A"),
            
            # Infos générales
            "population": rapport.get("commune_info", {}).get("population", 0),
            "superficie_ha": rapport.get("commune_info", {}).get("superficie_total_ha", 0),
            
            # Toitures
            "toitures": {
                "total": rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("total_toitures", 0),
                "surface_exploitable_m2": rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("surface_exploitable_pv_m2", 0),
                "potentiel_mwc": rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("potentiel_total_mwc", 0),
                "production_annuelle_mwh": rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("production_annuelle_mwh", 0),
                "economie_co2_tonnes": rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("economie_co2_tonnes_an", 0)
            },
            
            # Parkings
            "parkings": {
                "total": rapport.get("parkings_analysis", {}).get("resume_executif", {}).get("total_parkings", 0),
                "surface_totale_m2": rapport.get("parkings_analysis", {}).get("resume_executif", {}).get("surface_totale_m2", 0),
                "potentiel_mwc": rapport.get("parkings_analysis", {}).get("resume_executif", {}).get("potentiel_photovoltaique_mwc", 0)
            },
            
            # Friches
            "friches": {
                "total": rapport.get("friches_analysis", {}).get("resume_executif", {}).get("total_friches", 0),
                "surface_totale_ha": rapport.get("friches_analysis", {}).get("resume_executif", {}).get("surface_totale_ha", 0),
                "potentiel_reconversion_ha": rapport.get("friches_analysis", {}).get("resume_executif", {}).get("potentiel_reconversion_ha", 0)
            },
            
            # RPG (agriculture)
            "rpg": {
                "total_parcelles": rapport.get("rpg_analysis", {}).get("resume_executif", {}).get("total_parcelles", 0),
                "surface_totale_ha": rapport.get("rpg_analysis", {}).get("resume_executif", {}).get("surface_totale_ha", 0)
            },
            
            # Synthèse
            "potentiel_global": {
                "production_totale_mwh_an": (
                    rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("production_annuelle_mwh", 0) +
                    rapport.get("parkings_analysis", {}).get("potentiel_energetique", {}).get("production_annuelle_estimee_mwh", 0)
                ),
                "economie_co2_totale_tonnes": rapport.get("toitures_analysis", {}).get("resume_executif", {}).get("economie_co2_tonnes_an", 0)
            },
            
            "lien_rapport_complet": f"/rapport_commune?commune={nom_commune}"
        }
        
        return {
            "success": True,
            "message": f"✅ Rapport analysé pour {nom_commune}",
            "data": resume
        }
        
    except ImportError:
        return {
            "success": False,
            "message": "❌ Module de rapport non disponible. Utilisez le lien direct : /rapport_commune?commune=" + args['nom_commune']
        }
    except Exception as e:
        print(f"❌ [HELIA] Erreur analyze_commune_report: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_toggle_layer(args):
    """Active/désactive un calque sur la carte"""
    try:
        layer_name = args['layer_name']
        visible = args['visible']
        
        # Stocker la commande dans la session pour que le frontend la récupère
        if 'map_commands' not in session:
            session['map_commands'] = []
        
        session['map_commands'].append({
            'action': 'toggle_layer',
            'layer_name': layer_name,
            'visible': visible,
            'timestamp': datetime.now().isoformat()
        })
        session.modified = True
        
        layer_names_fr = {
            'postes_bt': 'Postes BT',
            'postes_hta': 'Postes HTA',
            'lignes_hta': 'Lignes HTA',
            'capacites_accueil': 'Capacités d\'accueil',
            'rpg': 'RPG (parcelles agricoles)',
            'cadastre': 'Cadastre',
            'plu': 'PLU',
            'risques': 'Risques naturels',
            'satellite': 'Vue satellite',
            'osm': 'OpenStreetMap'
        }
        
        action_fr = "affiché" if visible else "masqué"
        
        return {
            "success": True,
            "message": f"🗺️ Calque '{layer_names_fr.get(layer_name, layer_name)}' {action_fr}",
            "layer": layer_name,
            "visible": visible
        }
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur toggle_layer: {e}")
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_zoom_to_location(args):
    """Centre la carte sur une adresse ou position - UTILISE LE GÉOCODAGE EXISTANT"""
    try:
        address = args.get('address')
        lat = args.get('lat')
        lon = args.get('lon')
        zoom = args.get('zoom', 15)
        
        # Si adresse fournie, géocoder avec Nominatim
        if address and not (lat and lon):
            if not GEOPY_AVAILABLE:
                return {"success": False, "message": "⚠️ Géocodage non disponible, fournissez lat/lon"}
            
            try:
                geolocator = Nominatim(user_agent="helia_sundev", timeout=10)
                location = geolocator.geocode(f"{address}, France")
                
                if location:
                    lat = location.latitude
                    lon = location.longitude
                    location_name = address
                else:
                    return {"success": False, "message": f"❌ Adresse '{address}' introuvable"}
            except Exception as e:
                return {"success": False, "message": f"❌ Erreur géocodage: {str(e)}"}
        else:
            location_name = f"{lat:.5f}, {lon:.5f}"
        
        if 'map_commands' not in session:
            session['map_commands'] = []
        
        session['map_commands'].append({
            'action': 'zoom_to',
            'lat': lat,
            'lon': lon,
            'zoom': zoom,
            'timestamp': datetime.now().isoformat()
        })
        session.modified = True
        
        msg = f"🎯 Carte centrée sur {location_name} ({lat:.5f}, {lon:.5f}) - Zoom {zoom}"
        
        return {
            "success": True,
            "message": msg,
            "lat": lat,
            "lon": lon,
            "zoom": zoom
        }
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur zoom_to_location: {e}")
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_get_map_state(args):
    """Récupère l'état actuel de la carte"""
    try:
        # Récupérer l'état depuis la session si disponible
        map_state = session.get('current_map_state', {
            'center': {'lat': 46.603354, 'lon': 1.888334},  # Centre de la France par défaut
            'zoom': 6,
            'active_layers': [],
            'message': "État de carte non encore synchronisé. Demandez à l'utilisateur de partager sa position actuelle."
        })
        
        return {
            "success": True,
            "map_state": map_state
        }
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur get_map_state: {e}")
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_analyze_visible_layers(args):
    """Analyse les calques visibles"""
    try:
        layer_names = args.get('layer_names', [])
        
        # Descriptions des calques
        layer_descriptions = {
            'postes_bt': "Postes électriques Basse Tension (BT) - essentiels pour raccordement des installations < 36 kVA. Distance idéale < 100m.",
            'postes_hta': "Postes électriques Haute Tension A (HTA) - pour installations moyennes et grandes > 100 kWc. Distance idéale < 500m.",
            'lignes_hta': "Lignes électriques HTA - réseau de distribution moyenne tension. Important pour étudier les capacités d'accueil.",
            'capacites_accueil': "Capacités d'accueil du réseau électrique - zones où le raccordement est facilité ou saturé.",
            'rpg': "Registre Parcellaire Graphique - parcelles agricoles déclarées. Utile pour identifier terrains agricoles disponibles.",
            'cadastre': "Parcelles cadastrales et bâtiments - délimitations officielles des propriétés foncières.",
            'plu': "Plan Local d'Urbanisme - zonage et règles d'urbanisme (constructibilité, contraintes...).",
            'risques': "Risques naturels - inondations, séismes, mouvements de terrain. Contraintes réglementaires possibles.",
            'satellite': "Imagerie satellite - vue aérienne réelle pour identifier toitures, parkings, espaces disponibles.",
            'osm': "OpenStreetMap - fond de carte collaboratif avec routes, bâtiments, POI."
        }
        
        # Si aucune couche spécifiée, analyser l'état actuel
        if not layer_names:
            map_state = session.get('current_map_state', {})
            layer_names = map_state.get('active_layers', [])
        
        if not layer_names:
            return {
                "success": True,
                "message": "ℹ️ Aucun calque actif actuellement. Activez des calques pour visualiser les données photovoltaïques !",
                "recommendations": [
                    "Activez 'Postes BT' pour voir les points de raccordement proches",
                    "Activez 'Cadastre' pour identifier les parcelles",
                    "Activez 'Satellite' pour analyser visuellement les toitures"
                ]
            }
        
        analysis = {
            "success": True,
            "active_layers_count": len(layer_names),
            "layers": []
        }
        
        for layer in layer_names:
            if layer in layer_descriptions:
                analysis['layers'].append({
                    'name': layer,
                    'description': layer_descriptions[layer]
                })
        
        return analysis
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur analyze_visible_layers: {e}")
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_analyze_urban_data(args):
    """Analyse RÉELLE des données urbanistiques dans la zone visible de la carte"""
    try:
        from database_adapter import execute_query
        
        # Récupérer la zone visible depuis l'état de la carte
        map_state = session.get('current_map_state', {})
        bounds = map_state.get('bounds', {})
        
        if not bounds or not all(k in bounds for k in ['north', 'south', 'east', 'west']):
            return {
                "success": False,
                "message": "⚠️ Zone de carte non définie. Déplacez la carte et réessayez."
            }
        
        north = bounds['north']
        south = bounds['south']
        east = bounds['east']
        west = bounds['west']
        
        print(f"📍 [HELIA] Analyse urbanistique de la zone: N{north}, S{south}, E{east}, W{west}")
        
        analysis_result = {
            "success": True,
            "zone": {
                "nord": north,
                "sud": south,
                "est": east,
                "ouest": west,
                "centre_lat": (north + south) / 2,
                "centre_lon": (east + west) / 2
            },
            "cadastre": {},
            "plu": {},
            "urbanisme": {},
            "recommandations_pv": []
        }
        
        # ===== ANALYSE CADASTRE =====
        try:
            # Requête pour compter les parcelles dans la zone (compatible PostgreSQL et SQLite)
            cadastre_query = """
                SELECT 
                    COUNT(*) as nb_parcelles,
                    AVG(CAST(surface_m2 AS FLOAT)) as surface_moyenne,
                    SUM(CAST(surface_m2 AS FLOAT)) as surface_totale
                FROM parcelles_cadastrales
                WHERE latitude BETWEEN %s AND %s
                  AND longitude BETWEEN %s AND %s
            """
            
            cadastre_data = execute_query(cadastre_query, (south, north, west, east), fetch_one=True)
            
            if cadastre_data and cadastre_data['nb_parcelles']:
                nb_parcelles = int(cadastre_data['nb_parcelles'])
                surface_moy = float(cadastre_data['surface_moyenne']) if cadastre_data['surface_moyenne'] else 0
                surface_tot = float(cadastre_data['surface_totale']) if cadastre_data['surface_totale'] else 0
                
                analysis_result['cadastre'] = {
                    "nb_parcelles": nb_parcelles,
                    "surface_moyenne_m2": round(surface_moy, 2),
                    "surface_totale_m2": round(surface_tot, 2),
                    "surface_totale_ha": round(surface_tot / 10000, 2),
                    "densité": "urbain" if surface_moy < 500 else ("péri-urbain" if surface_moy < 2000 else "rural")
                }
                
                # Recommandations basées sur la taille des parcelles
                if surface_moy > 5000:  # Grandes parcelles
                    analysis_result['recommandations_pv'].append({
                        "type": "opportunité",
                        "message": f"🌾 Grandes parcelles moyennes ({round(surface_moy)}m²) - Excellent pour installations au sol ou ombrières"
                    })
                elif surface_moy > 1000:
                    analysis_result['recommandations_pv'].append({
                        "type": "potentiel",
                        "message": f"🏘️ Parcelles moyennes ({round(surface_moy)}m²) - Idéal pour toitures commerciales/industrielles"
                    })
            else:
                analysis_result['cadastre'] = {
                    "message": "Aucune donnée cadastrale disponible pour cette zone"
                }
                
        except Exception as e:
            print(f"⚠️ [HELIA] Erreur analyse cadastre: {e}")
            analysis_result['cadastre'] = {"error": "Données non disponibles"}
        
        # ===== ANALYSE PLU (si disponible) =====
        try:
            plu_query = """
                SELECT 
                    zonage,
                    COUNT(*) as nb_zones,
                    SUM(CAST(surface_m2 AS FLOAT)) as surface_totale
                FROM zones_plu
                WHERE latitude BETWEEN %s AND %s
                  AND longitude BETWEEN %s AND %s
                GROUP BY zonage
                ORDER BY surface_totale DESC
            """
            
            plu_data = execute_query(plu_query, (south, north, west, east), fetch_all=True)
            
            if plu_data:
                zones_plu = []
                for zone in plu_data:
                    zones_plu.append({
                        "zonage": zone['zonage'],
                        "nb_zones": zone['nb_zones'],
                        "surface_ha": round(float(zone['surface_totale']) / 10000, 2)
                    })
                
                analysis_result['plu'] = {
                    "zones": zones_plu,
                    "zone_dominante": zones_plu[0]['zonage'] if zones_plu else "Non définie"
                }
                
                # Recommandations basées sur le zonage PLU
                for zone in zones_plu[:3]:  # Top 3 zones
                    zonage = zone['zonage']
                    if zonage.startswith('A'):  # Zone agricole
                        analysis_result['recommandations_pv'].append({
                            "type": "réglementation",
                            "message": f"🌾 Zone {zonage} (agricole) : Photovoltaïque au sol possible avec conditions. Privilégier ombrières de parking ou agrivoltaïsme."
                        })
                    elif zonage.startswith('U'):  # Zone urbaine
                        analysis_result['recommandations_pv'].append({
                            "type": "réglementation",
                            "message": f"🏙️ Zone {zonage} (urbaine) : Favoriser toitures et ombrières de parking. Attention intégration paysagère."
                        })
                    elif zonage.startswith('N'):  # Zone naturelle
                        analysis_result['recommandations_pv'].append({
                            "type": "contrainte",
                            "message": f"🌲 Zone {zonage} (naturelle) : Contraintes fortes pour le photovoltaïque. Études préalables indispensables."
                        })
            else:
                analysis_result['plu'] = {"message": "Données PLU non disponibles pour cette zone"}
                
        except Exception as e:
            print(f"⚠️ [HELIA] Erreur analyse PLU: {e}")
            analysis_result['plu'] = {"message": "Données PLU non disponibles"}
        
        # ===== ANALYSE BATIMENTS (OSM/Cadastre) =====
        try:
            batiments_query = """
                SELECT 
                    COUNT(*) as nb_batiments,
                    AVG(CAST(surface_toiture_m2 AS FLOAT)) as surface_moy_toiture,
                    COUNT(CASE WHEN usage = 'commercial' OR usage = 'industriel' THEN 1 END) as nb_pro,
                    COUNT(CASE WHEN usage = 'residentiel' THEN 1 END) as nb_residentiel
                FROM batiments
                WHERE latitude BETWEEN %s AND %s
                  AND longitude BETWEEN %s AND %s
            """
            
            batiments_data = execute_query(batiments_query, (south, north, west, east), fetch_one=True)
            
            if batiments_data and batiments_data['nb_batiments']:
                nb_bat = int(batiments_data['nb_batiments'])
                surf_moy = float(batiments_data['surface_moy_toiture']) if batiments_data['surface_moy_toiture'] else 0
                nb_pro = int(batiments_data['nb_pro']) if batiments_data['nb_pro'] else 0
                nb_res = int(batiments_data['nb_residentiel']) if batiments_data['nb_residentiel'] else 0
                
                analysis_result['urbanisme'] = {
                    "nb_batiments": nb_bat,
                    "surface_moyenne_toiture_m2": round(surf_moy, 2),
                    "batiments_professionnels": nb_pro,
                    "batiments_residentiels": nb_res,
                    "potentiel_toitures_kwc": round(nb_bat * surf_moy * 0.15, 2)  # Estimation: 15% rendement
                }
                
                if nb_pro > 5:
                    analysis_result['recommandations_pv'].append({
                        "type": "opportunité",
                        "message": f"🏭 {nb_pro} bâtiments pro/industriels détectés - Excellent potentiel toitures photovoltaïques"
                    })
                
                if surf_moy > 200:
                    analysis_result['recommandations_pv'].append({
                        "type": "potentiel",
                        "message": f"🏠 Toitures moyennes de {round(surf_moy)}m² - Adapté pour installations 3-30 kWc"
                    })
            else:
                analysis_result['urbanisme'] = {"message": "Données bâtiments non disponibles"}
                
        except Exception as e:
            print(f"⚠️ [HELIA] Erreur analyse bâtiments: {e}")
            analysis_result['urbanisme'] = {"message": "Données non disponibles"}
        
        # ===== SYNTHÈSE FINALE =====
        if not analysis_result['recommandations_pv']:
            analysis_result['recommandations_pv'].append({
                "type": "info",
                "message": "💡 Zoomez davantage ou activez d'autres calques pour une analyse plus détaillée"
            })
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur analyze_urban_data: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Erreur lors de l'analyse : {str(e)}"
        }


# Mapping des fonctions
AVAILABLE_FUNCTIONS = {
    "create_prospect": function_create_prospect,
    "list_prospects": function_list_prospects,
    "get_prospect_details": function_get_prospect_details,
    "update_prospect_status": function_update_prospect_status,
    "search_commune": function_search_commune,
    "analyze_commune_report": function_analyze_commune_report,
    "toggle_layer": function_toggle_layer,
    "zoom_to_location": function_zoom_to_location,
    "get_map_state": function_get_map_state,
    "analyze_visible_layers": function_analyze_visible_layers,
    "analyze_urban_data": function_analyze_urban_data
}

# ============================================================================
# CLASSE HELIA AI AVEC FUNCTION CALLING
# ============================================================================

class HeliaAI:
    """Gestionnaire de l'assistant IA Helia avec capacités d'action"""
    
    def __init__(self):
        self.client = None
        print(f"🔍 Debug init: GROQ_AVAILABLE={GROQ_AVAILABLE}, GROQ_API_KEY={'présent' if GROQ_API_KEY else 'absent'}")
        if GROQ_AVAILABLE and GROQ_API_KEY:
            try:
                # Créer un client httpx sans proxy pour éviter les conflits
                import httpx
                http_client = httpx.Client(
                    timeout=30.0,
                    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
                )
                
                self.client = Groq(
                    api_key=GROQ_API_KEY,
                    http_client=http_client
                )
                
                print("✅ Helia AI initialisée avec Groq + Function Calling!")
            except Exception as e:
                print(f"⚠️ Erreur initialisation Groq: {e}")
                import traceback
                traceback.print_exc()
        else:
            raison = []
            if not GROQ_AVAILABLE:
                raison.append("Groq non disponible")
            if not GROQ_API_KEY:
                raison.append("Clé API manquante")
            print(f"⚠️ Helia AI en mode fallback: {', '.join(raison)}")
    
    def get_conversation_history(self, session_id):
        """Récupère l'historique de conversation depuis la session"""
        if 'helia_conversations' not in session:
            session['helia_conversations'] = {}
        
        if session_id not in session['helia_conversations']:
            session['helia_conversations'][session_id] = []
        
        return session['helia_conversations'][session_id]
    
    def save_message(self, session_id, role, content):
        """Sauvegarde un message dans l'historique (ultra-compacté)"""
        if 'helia_conversations' not in session:
            session['helia_conversations'] = {}
        
        if session_id not in session['helia_conversations']:
            session['helia_conversations'][session_id] = []
        
        # Pour assistant: stocker seulement 150 premiers caractères
        # Pour user: stocker 300 caractères max
        if role == 'assistant':
            content_trimmed = content[:150] if len(content) > 150 else content
        else:
            content_trimmed = content[:300] if len(content) > 300 else content
        
        session['helia_conversations'][session_id].append({
            'role': role,
            'content': content_trimmed,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limiter à 2 derniers messages seulement (1 paire Q/R)
        if len(session['helia_conversations'][session_id]) > 2:
            session['helia_conversations'][session_id] = session['helia_conversations'][session_id][-2:]
        
        session.modified = True
    
    def generate_response(self, user_message, session_id='default', context=None):
        """Génère une réponse intelligente avec possibilité d'appeler des fonctions"""
        
        if not self.client:
            return self._fallback_response(user_message)
        
        try:
            # Récupérer l'historique
            history = self.get_conversation_history(session_id)
            
            # Construire les messages
            messages = [{'role': 'system', 'content': HELIA_SYSTEM_PROMPT}]
            
            if context:
                messages[0]['content'] += f"\n\nCONTEXTE ACTUEL : {context}"
            
            # Ajouter historique (2 derniers messages max pour éviter cookie overflow)
            for msg in history[-2:]:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Ajouter message utilisateur
            messages.append({'role': 'user', 'content': user_message})
            
            # Premier appel avec tools
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                tools=HELIA_TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=500
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Si pas d'appel de fonction, retourner la réponse directe
            if not tool_calls:
                ai_response = response_message.content
                self.save_message(session_id, 'user', user_message)
                self.save_message(session_id, 'assistant', ai_response)
                
                return {
                    'success': True,
                    'response': ai_response,
                    'mode': 'ai',
                    'model': GROQ_MODEL
                }
            
            # Exécuter les fonctions appelées
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Helia appelle la fonction: {function_name}({function_args})")
                
                # Exécuter la fonction
                if function_name in AVAILABLE_FUNCTIONS:
                    function_response = AVAILABLE_FUNCTIONS[function_name](function_args)
                else:
                    function_response = {"error": "Fonction non trouvée"}
                
                # Ajouter le résultat à la conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
            
            # Deuxième appel pour obtenir la réponse finale avec les résultats des fonctions
            second_response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            final_response = second_response.choices[0].message.content
            
            # Sauvegarder dans historique
            self.save_message(session_id, 'user', user_message)
            self.save_message(session_id, 'assistant', final_response)
            
            return {
                'success': True,
                'response': final_response,
                'mode': 'ai_with_actions',
                'model': GROQ_MODEL,
                'functions_called': [tc.function.name for tc in tool_calls]
            }
            
        except Exception as e:
            print(f"❌ Erreur Groq: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message):
        """Réponse de secours si API indisponible"""
        message_lower = user_message.lower()
        
        fallback_responses = {
            'bonjour': "☀️ Bonjour ! Je suis Helia, votre experte en énergie solaire. Comment puis-je vous aider aujourd'hui ?",
            'aide': "Je suis là pour vous guider ! Posez-moi vos questions sur le photovoltaïque ou demandez-moi de créer un prospect, lister vos projets, etc.",
            'merci': "Avec plaisir ! ☀️ N'hésitez pas si vous avez d'autres questions ou actions à réaliser.",
        }
        
        for keyword, response in fallback_responses.items():
            if keyword in message_lower:
                return {'success': True, 'response': response, 'mode': 'fallback'}
        
        return {
            'success': True,
            'response': "Je suis Helia ! ☀️ Configurez l'API Groq pour débloquer toutes mes capacités (création prospects, analyses, etc.).",
            'mode': 'fallback'
        }
    
    def clear_history(self, session_id='default'):
        """Efface l'historique de conversation"""
        if 'helia_conversations' in session and session_id in session['helia_conversations']:
            session['helia_conversations'][session_id] = []
            session.modified = True
            return True
        return False


# Instance globale (lazy initialization)
helia_ai = None

def get_helia_instance():
    """Récupère ou crée l'instance Helia (lazy initialization)"""
    global helia_ai
    if helia_ai is None:
        helia_ai = HeliaAI()
    return helia_ai

# ============================================================================
# ROUTES API
# ============================================================================

@helia_bp.route('/api/helia/chat', methods=['POST'])
def helia_chat():
    """Endpoint principal pour dialoguer avec Helia"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'Message manquant'}), 400
        
        user_message = data['message']
        session_id = data.get('session_id', 'default')
        context = data.get('context', None)
        
        result = get_helia_instance().generate_response(user_message, session_id, context)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@helia_bp.route('/api/helia/history', methods=['GET'])
def get_history():
    """Récupère l'historique de conversation"""
    try:
        session_id = request.args.get('session_id', 'default')
        history = get_helia_instance().get_conversation_history(session_id)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@helia_bp.route('/api/helia/clear', methods=['POST'])
def clear_history():
    """Efface l'historique de conversation"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        success = get_helia_instance().clear_history(session_id)
        return jsonify({
            'success': success,
            'message': 'Historique effacé' if success else 'Aucun historique à effacer'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@helia_bp.route('/api/helia/status', methods=['GET'])
def helia_status():
    """Statut de l'IA Helia"""
    instance = get_helia_instance()
    return jsonify({
        'success': True,
        'ai_enabled': instance.client is not None,
        'mode': 'ai_with_actions' if instance.client else 'fallback',
        'model': GROQ_MODEL if instance.client else 'basic',
        'provider': 'Groq (gratuit + Function Calling!)' if instance.client else 'Fallback',
        'functions_available': list(AVAILABLE_FUNCTIONS.keys())
    })


@helia_bp.route('/api/helia/debug-env', methods=['GET'])
def debug_env():
    """Debug des variables d'environnement"""
    groq_key = os.getenv('GROQ_API_KEY', '')
    instance = get_helia_instance()
    return jsonify({
        'GROQ_AVAILABLE': GROQ_AVAILABLE,
        'GROQ_API_KEY_exists': bool(groq_key),
        'GROQ_API_KEY_length': len(groq_key) if groq_key else 0,
        'GROQ_API_KEY_preview': f"{groq_key[:10]}...{groq_key[-10:]}" if len(groq_key) > 20 else "vide",
        'client_initialized': instance.client is not None
    })


# ============================================================================
# ROUTES POUR SYNCHRONISATION CARTE <-> HELIA
# ============================================================================

@helia_bp.route('/api/helia/map/commands', methods=['GET'])
def get_map_commands():
    """Récupère les commandes de carte en attente d'exécution"""
    try:
        commands = session.get('map_commands', [])
        
        # Nettoyer les commandes après lecture
        session['map_commands'] = []
        session.modified = True
        
        return jsonify({
            'success': True,
            'commands': commands
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@helia_bp.route('/api/helia/map/state', methods=['POST'])
def update_map_state():
    """Met à jour l'état actuel de la carte (appelé par le frontend)"""
    try:
        data = request.get_json()
        
        # Limiter la taille des données pour ne pas surcharger la session
        active_layers = data.get('active_layers', [])[:20]  # Max 20 layers
        
        session['current_map_state'] = {
            'center': data.get('center', {}),
            'zoom': data.get('zoom', 6),
            'active_layers': active_layers,
            'bounds': data.get('bounds', {}),
            'timestamp': datetime.now().isoformat()
        }
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'État de carte synchronisé'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
