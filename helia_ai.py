"""
Helia AI v2 - Assistant Solaire Intelligent avec Function Calling
Intégration IA conversationnelle avec actions réelles sur la plateforme
"""

import os
import json
from flask import Blueprint, request, jsonify, session
from datetime import datetime

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
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')  # Modèle mis à jour (Jan 2026)

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

1️⃣ create_prospect(adresse, commune, lat, lon, puissance_kwc, type_projet)
   → Créer un nouveau prospect dans le CRM

2️⃣ list_prospects(statut, limit)
   → Lister les prospects avec filtres

3️⃣ get_prospect_details(prospect_id)
   → Afficher tous les détails d'un prospect

4️⃣ update_prospect_status(prospect_id, nouveau_statut)
   → Changer le statut d'un prospect

5️⃣ search_commune(nom_commune)
   → Rechercher et analyser une commune

QUAND UTILISER CES FONCTIONS :
- Si l'utilisateur dit "crée un prospect pour...", appelle create_prospect
- Si il demande "liste mes prospects en attente", appelle list_prospects
- Si il dit "montre-moi le prospect #123", appelle get_prospect_details
- Si il demande "passe le prospect 45 en gagné", appelle update_prospect_status
- Si il veut "analyser la commune de Lyon", appelle search_commune

TON STYLE DE RÉPONSE :
- Toujours chaleureuse et encourageante ☀️
- Utilise des emojis solaires contextuels
- Donne des exemples concrets et chiffrés
- Vulgarise les concepts techniques
- **Propose proactivement des actions !**
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
        
        query = """
            INSERT INTO prospects (
                user_id, nom, adresse, commune, lat, lon, 
                puissance_kwc, type_projet, statut, date_creation
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'nouveau', NOW())
            RETURNING id
        """
        
        params = (
            user_id,
            args.get('nom', 'Prospect'),
            args['adresse'],
            args['commune'],
            args.get('lat'),
            args.get('lon'),
            args.get('puissance_kwc', 0),
            args.get('type_projet', 'toiture')
        )
        
        print(f"🔍 [HELIA] Params SQL: {params}")
        
        result = execute_query(query, params)
        
        print(f"🔍 [HELIA] Résultat query: {result}")
        
        if result and len(result) > 0:
            prospect_id = result[0]['id']
            return {
                "success": True,
                "prospect_id": prospect_id,
                "message": f"✅ Prospect #{prospect_id} créé avec succès !",
                "lien": f"/crm/prospects/{prospect_id}"
            }
        else:
            return {"success": False, "message": "Erreur lors de la création"}
            
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
                SELECT id, nom, adresse, commune, puissance_kwc, statut, date_creation
                FROM prospects
                WHERE user_id = %s AND statut = %s
                ORDER BY date_creation DESC
                LIMIT %s
            """
            params = (user_id, statut, limit)
        else:
            query = """
                SELECT id, nom, adresse, commune, puissance_kwc, statut, date_creation
                FROM prospects
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
            FROM prospects
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
            UPDATE prospects
            SET statut = %s, date_modification = NOW()
            WHERE id = %s
            RETURNING id, nom, statut
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


# Mapping des fonctions
AVAILABLE_FUNCTIONS = {
    "create_prospect": function_create_prospect,
    "list_prospects": function_list_prospects,
    "get_prospect_details": function_get_prospect_details,
    "update_prospect_status": function_update_prospect_status,
    "search_commune": function_search_commune,
    "analyze_commune_report": function_analyze_commune_report
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
        
        # Limiter à 20 derniers messages
        if len(session['helia_conversations'][session_id]) > 20:
            session['helia_conversations'][session_id] = session['helia_conversations'][session_id][-20:]
        
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
            
            # Ajouter historique (10 derniers messages)
            for msg in history[-10:]:
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
