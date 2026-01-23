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

HELIA_SYSTEM_PROMPT = """Tu es Helia ☀️, assistante IA photovoltaïque AgriWeb.

**Fonctions disponibles:**
- search_location: recherche complète adresse (toutes APIs)
- Carte: toggle_layer, zoom_to_location, analyze_urban_data
- CRM: create_prospect, export_to_crm, add_prospect_note, update_project_step, get_project_status
- Rapports: generate_point_report, analyze_commune_report

**Comportement:**
1. UTILISE tes fonctions (agis, ne conseille pas)
2. Géocode adresses automatiquement
3. Explique brièvement ce que tu fais
4. Propose prochaine action
5. Réponds UNIQUEMENT sur photovoltaïque (refuse poliment autres sujets)

Français chaleureux !"""

# ============================================================================
# DÉFINITION DES OUTILS (FUNCTIONS) DISPONIBLES POUR HELIA
# ============================================================================

HELIA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_prospect",
            "description": "Crée prospect CRM",
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
            "description": "Liste prospects",
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
            "description": "Détails prospect",
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
            "description": "MAJ statut prospect",
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
            "name": "search_location",
            "description": "Recherche COMPLÈTE adresse (toutes APIs cadastre/PLU/postes) - PRIORITAIRE",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Adresse complète à analyser (ex: '15 Rue de Paris, Toulouse'). RECOMMANDÉ."
                    },
                    "lat": {
                        "type": "number",
                        "description": "Latitude (optionnel si address fourni)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude (optionnel si address fourni)"
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
            "description": "État carte (position, zoom, calques)",
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
            "description": "Analyse calques actifs",
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
            "description": "Analyse SQL cadastre/PLU zone visible (parcelles, surfaces, recommandations PV)",
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
            "name": "generate_point_report",
            "description": "Rapport point (parcelle, PLU, postes, solaire)",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Adresse complète à analyser (sera géocodée automatiquement)"
                    },
                    "lat": {
                        "type": "number",
                        "description": "Latitude (optionnel si address fourni)"
                    },
                    "lon": {
                        "type": "number",
                        "description": "Longitude (optionnel si address fourni)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_to_crm",
            "description": "Export rapport → CRM (nouveau prospect)",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_type": {
                        "type": "string",
                        "enum": ["point", "commune"],
                        "description": "Type de source du rapport (point ou commune)"
                    },
                    "adresse": {
                        "type": "string",
                        "description": "Adresse du site"
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
                    "surface_m2": {
                        "type": "number",
                        "description": "Surface disponible en m²"
                    },
                    "type_projet": {
                        "type": "string",
                        "enum": ["toiture", "sol", "ombriere", "tracker", "autoconso"],
                        "description": "Type d'installation photovoltaïque"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes additionnelles sur le prospect"
                    }
                },
                "required": ["commune"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_prospect_note",
            "description": "Ajoute note prospect",
            "parameters": {
                "type": "object",
                "properties": {
                    "prospect_id": {
                        "type": "integer",
                        "description": "ID du prospect"
                    },
                    "note": {
                        "type": "string",
                        "description": "Texte de la note à ajouter"
                    }
                },
                "required": ["prospect_id", "note"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_project_step",
            "description": "MAJ étape workflow projet (11 étapes: Rapport→Visite→Calepinage→Devis→DP→DDR→Installation→Consuel)",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "ID du projet"
                    },
                    "etape_id": {
                        "type": "integer",
                        "description": "ID de l'étape (optionnel si etape_nom fourni)"
                    },
                    "etape_nom": {
                        "type": "string",
                        "description": "Nom de l'étape (ex: 'Visite technique', 'Devis', 'DP', etc.)"
                    },
                    "statut": {
                        "type": "string",
                        "enum": ["a_faire", "en_cours", "termine", "bloque"],
                        "description": "Nouveau statut de l'étape"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes sur l'évolution de l'étape"
                    }
                },
                "required": ["project_id", "statut"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_status",
            "description": "Statut projet (progression % + étapes)",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "ID du projet à consulter"
                    }
                },
                "required": ["project_id"]
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
        
        # Extraction des variables
        adresse = args.get('adresse', '')
        commune = args.get('commune', '')
        puissance_kwc = args.get('puissance_kwc', 0)
        type_projet = args.get('type_projet', 'parking')
        nom = args.get('nom', 'Prospect Helia')
        lat = args.get('lat')
        lon = args.get('lon')
        
        # INSERT sans RETURNING
        insert_query = """
            INSERT INTO agriweb_prospects (
                user_id, nom_prospect, adresse, commune, latitude, longitude, 
                type, statut, date_creation, date_modification
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'nouveau', NOW(), NOW())
        """
        
        params = (user_id, nom, adresse, commune, lat, lon, type_projet)
        
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
            
            # Message enrichi
            summary = f"✅ **Prospect créé avec succès !**\n\n"
            summary += f"📋 **Détails:**\n"
            summary += f"- 📍 Adresse: {adresse}\n"
            summary += f"- 🏘️ Commune: {commune}\n"
            summary += f"- ⚡ Puissance: {puissance_kwc} kWc\n"
            summary += f"- 🏗️ Type: {type_projet}\n"
            summary += f"- 📊 Statut: En cours\n"
            summary += f"- 🆔 ID: #{prospect_id}\n\n"
            summary += f"🔗 Accès CRM: /crm/prospects/{prospect_id}"
            
            return {
                "success": True,
                "message": summary,
                "prospect_id": prospect_id,
                "lien": f"/crm/prospects/{prospect_id}",
                "data": {
                    "id": prospect_id,
                    "adresse": adresse,
                    "commune": commune,
                    "puissance_kwc": puissance_kwc,
                    "type_projet": type_projet
                }
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
    """RECHERCHE COMPLÈTE par commune - Appelle la fonctionnalité /search_by_commune"""
    try:
        nom_commune = args['nom_commune']
        
        print(f"🏘️ [HELIA COMMUNE] Recherche complète pour {nom_commune}")
        
        # Import des fonctions nécessaires
        try:
            from agriweb_hebergement_gratuit import (
                get_commune_bbox,
                get_all_parcelles,
                get_parkings_info,
                get_friches_info,
                get_rpg_info,
                get_plu_info
            )
        except ImportError as e:
            print(f"❌ [HELIA COMMUNE] Erreur import: {e}")
            return {"success": False, "message": "❌ Fonctions de recherche commune non disponibles"}
        
        # Récupérer les coordonnées et bbox de la commune
        try:
            # API Geo Gouv pour obtenir centre et contour commune
            import requests
            url = f"https://geo.api.gouv.fr/communes?nom={nom_commune}&fields=nom,code,centre,contour,surface,population&format=json&geometry=centre"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                communes = resp.json()
                if not communes:
                    return {"success": False, "message": f"❌ Commune '{nom_commune}' introuvable"}
                
                commune_data = communes[0]
                centre = commune_data.get('centre', {}).get('coordinates', [0, 0])
                lon, lat = centre[0], centre[1]
                population = commune_data.get('population', 0)
                surface_km2 = commune_data.get('surface', 0) / 100  # Conversion en km²
                
                print(f"✅ [HELIA COMMUNE] Commune trouvée: {commune_data.get('nom')} (pop: {population}, surface: {surface_km2:.2f} km²)")
            else:
                return {"success": False, "message": f"❌ Erreur API Geo Gouv: {resp.status_code}"}
        except Exception as e:
            print(f"❌ [HELIA COMMUNE] Erreur géocodage commune: {e}")
            return {"success": False, "message": f"❌ Erreur: {str(e)}"}
        
        # Recherche dans un rayon autour du centre (300m pour avoir un aperçu)
        search_radius = 0.03  # ~3.3 km
        
        # Collecter les données principales
        try:
            parcelles = get_all_parcelles(lat, lon, radius=search_radius)
            parkings = get_parkings_info(lat, lon, radius=search_radius)
            friches = get_friches_info(lat, lon, radius=search_radius)
            rpg_data = get_rpg_info(lat, lon, radius=search_radius)
            plu_info = get_plu_info(lat, lon, radius=search_radius)
            
            # Compter les résultats
            nb_parcelles = len(parcelles.get('features', [])) if isinstance(parcelles, dict) else len(parcelles) if isinstance(parcelles, list) else 0
            nb_parkings = len(parkings.get('features', [])) if isinstance(parkings, dict) else len(parkings) if isinstance(parkings, list) else 0
            nb_friches = len(friches.get('features', [])) if isinstance(friches, dict) else len(friches) if isinstance(friches, list) else 0
            nb_rpg = len(rpg_data.get('features', [])) if isinstance(rpg_data, dict) else len(rpg_data) if isinstance(rpg_data, list) else 0
            nb_zones_plu = len(plu_info.get('features', [])) if isinstance(plu_info, dict) else len(plu_info) if isinstance(plu_info, list) else 0
            
        except Exception as e:
            print(f"❌ [HELIA COMMUNE] Erreur collecte données: {e}")
            nb_parcelles = nb_parkings = nb_friches = nb_rpg = nb_zones_plu = 0
        
        # Centrer la carte sur la commune
        if 'map_commands' not in session:
            session['map_commands'] = []
        
        session['map_commands'].append({
            'action': 'zoom_to',
            'lat': lat,
            'lon': lon,
            'zoom': 13,  # Vue commune
            'timestamp': datetime.now().isoformat()
        })
        session.modified = True
        
        summary = f"🏘️ **Analyse de {commune_data.get('nom')}**\n\n"
        summary += f"📍 Population: {population:,} habitants\n"
        summary += f"📏 Surface: {surface_km2:.2f} km²\n\n"
        summary += f"📊 Données collectées (rayon {search_radius*111:.1f} km autour du centre):\n"
        summary += f"- 🗺️ {nb_parcelles} parcelle(s) cadastrale(s)\n"
        summary += f"- 🅿️ {nb_parkings} parking(s)\n"
        summary += f"- 🏚️ {nb_friches} friche(s)\n"
        summary += f"- 🏗️ {nb_zones_plu} zone(s) PLU\n"
        summary += f"- 🌾 {nb_rpg} parcelle(s) agricole(s) RPG\n\n"
        summary += f"✅ Carte centrée sur la commune !\n\n"
        summary += f"💡 Pour un rapport complet, utilise `analyze_commune_report('{nom_commune}')`"
        
        return {
            "success": True,
            "message": summary,
            "data": {
                "commune": commune_data.get('nom'),
                "code_insee": commune_data.get('code'),
                "lat": lat,
                "lon": lon,
                "population": population,
                "surface_km2": surface_km2,
                "parcelles_count": nb_parcelles,
                "parkings_count": nb_parkings,
                "friches_count": nb_friches,
                "plu_zones_count": nb_zones_plu,
                "rpg_parcelles_count": nb_rpg,
                "lien_rapport_complet": f"/rapport_commune_complet?commune={nom_commune}"
            }
        }
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur search_commune: {e}")
        import traceback
        traceback.print_exc()
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


def function_search_location(args):
    """Effectue une RECHERCHE COMPLÈTE (comme le bouton Rechercher) avec toutes les APIs"""
    try:
        from flask import current_app
        import requests
        
        address = args.get('address')
        lat = args.get('lat')
        lon = args.get('lon')
        
        # Si adresse fournie, géocoder d'abord
        if address and not (lat and lon):
            if not GEOPY_AVAILABLE:
                return {"success": False, "message": "⚠️ Géocodage non disponible"}
            
            try:
                geolocator = Nominatim(user_agent="helia_sundev", timeout=10)
                location = geolocator.geocode(f"{address}, France")
                
                if location:
                    lat = location.latitude
                    lon = location.longitude
                else:
                    return {"success": False, "message": f"❌ Adresse '{address}' introuvable"}
            except Exception as e:
                return {"success": False, "message": f"❌ Erreur géocodage: {str(e)}"}
        
        if not (lat and lon):
            return {"success": False, "message": "❌ Coordonnées requises"}
        
        # Appeler la route /search_by_address en interne
        try:
            # Import de la fonction search_by_address depuis agriweb_hebergement_gratuit
            from agriweb_hebergement_gratuit import geocode_address, get_all_parcelles, get_nearest_postes, get_nearest_ht_postes, get_plu_info, get_rpg_info
            
            print(f"🔍 [HELIA SEARCH] Recherche complète pour {address or f'{lat}, {lon}'}")
            
            # Simuler l'appel à la recherche complète
            # (On pourrait faire un vrai appel HTTP interne mais c'est plus simple d'appeler directement les fonctions)
            
            search_radius = 0.0027
            parcelles = get_all_parcelles(lat, lon, radius=search_radius)
            postes_bt = get_nearest_postes(lat, lon, count=3, radius_deg=0.01)
            postes_hta = get_nearest_ht_postes(lat, lon, count=3, radius_deg=0.01)
            plu_info = get_plu_info(lat, lon, radius=search_radius)
            rpg_data = get_rpg_info(lat, lon, radius=search_radius)
            
            # Compter les résultats
            nb_parcelles = len(parcelles.get('features', [])) if isinstance(parcelles, dict) else len(parcelles)
            nb_postes_bt = len(postes_bt) if isinstance(postes_bt, list) else 0
            nb_postes_hta = len(postes_hta) if isinstance(postes_hta, list) else 0
            nb_zones_plu = len(plu_info.get('features', [])) if isinstance(plu_info, dict) else len(plu_info) if isinstance(plu_info, list) else 0
            nb_rpg = len(rpg_data.get('features', [])) if isinstance(rpg_data, dict) else len(rpg_data) if isinstance(rpg_data, list) else 0
            
            # Déclencher aussi le zoom sur la carte
            if 'map_commands' not in session:
                session['map_commands'] = []
            
            session['map_commands'].append({
                'action': 'zoom_to',
                'lat': lat,
                'lon': lon,
                'zoom': 16,
                'timestamp': datetime.now().isoformat()
            })
            session.modified = True
            
            location_str = address or f"{lat:.5f}, {lon:.5f}"
            summary = f"🔍 Recherche complète effectuée pour **{location_str}**\\n\\n"
            summary += f"📊 Résultats :\\n"
            summary += f"- 🗺️ {nb_parcelles} parcelle(s) cadastrale(s)\\n"
            summary += f"- ⚡ {nb_postes_bt} poste(s) BT à proximité\\n"
            summary += f"- 🔌 {nb_postes_hta} poste(s) HTA à proximité\\n"
            summary += f"- 🏗️ {nb_zones_plu} zone(s) PLU\\n"
            summary += f"- 🌾 {nb_rpg} parcelle(s) agricole(s) RPG\\n"
            summary += f"\\n✅ Carte centrée et données affichées !"
            
            return {
                "success": True,
                "message": summary,
                "data": {
                    "lat": lat,
                    "lon": lon,
                    "address": address,
                    "parcelles_count": nb_parcelles,
                    "postes_bt_count": nb_postes_bt,
                    "postes_hta_count": nb_postes_hta,
                    "plu_zones_count": nb_zones_plu,
                    "rpg_parcelles_count": nb_rpg
                }
            }
            
        except ImportError as e:
            print(f"❌ [HELIA SEARCH] Erreur import: {e}")
            return {"success": False, "message": "❌ Fonctions de recherche non disponibles"}
        except Exception as e:
            print(f"❌ [HELIA SEARCH] Erreur recherche: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"❌ Erreur recherche: {str(e)}"}
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur search_location: {e}")
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


def function_generate_point_report(args):
    """Génère un rapport complet pour un point (adresse)"""
    try:
        address = args.get('address')
        lat = args.get('lat')
        lon = args.get('lon')
        
        # Géocoder si adresse fournie
        if address and not (lat and lon):
            if not GEOPY_AVAILABLE:
                return {"success": False, "message": "⚠️ Géocodage non disponible"}
            
            try:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="helia_sundev", timeout=10)
                location = geolocator.geocode(f"{address}, France")
                
                if location:
                    lat = location.latitude
                    lon = location.longitude
                else:
                    return {"success": False, "message": f"❌ Adresse '{address}' introuvable"}
            except Exception as e:
                return {"success": False, "message": f"❌ Erreur géocodage: {str(e)}"}
        
        if not (lat and lon):
            return {"success": False, "message": "❌ Coordonnées requises"}
        
        print(f"📄 [HELIA RAPPORT POINT] Génération rapport pour {address or f'{lat}, {lon}'}")
        
        # Importer et appeler la fonction de rapport
        try:
            from agriweb_hebergement_gratuit import build_report_data
            
            report_data = build_report_data(lat, lon, address=address)
            
            # Extraire résumé
            summary = f"📄 **Rapport point généré !**\n\n"
            summary += f"📍 Localisation: {address or f'{lat:.5f}, {lon:.5f}'}\n"
            summary += f"🗺️ Altitude: {report_data.get('altitude_m', 'N/A')} m\n"
            
            if report_data.get('parcelle'):
                parcelle = report_data['parcelle']
                summary += f"\n📐 **Parcelle cadastrale:**\n"
                summary += f"- Référence: {parcelle.get('feuille', 'N/A')}\n"
                summary += f"- Surface: {parcelle.get('contenance', 'N/A')} m²\n"
            
            nb_postes_bt = len(report_data.get('postes', []))
            nb_postes_hta = len(report_data.get('ht_postes', []))
            summary += f"\n⚡ **Réseau électrique:**\n"
            summary += f"- Postes BT: {nb_postes_bt}\n"
            summary += f"- Postes HTA: {nb_postes_hta}\n"
            
            if report_data.get('plu_info'):
                summary += f"\n🏗️ **Urbanisme:**\n"
                summary += f"- Zones PLU: {len(report_data['plu_info'].get('features', []))}\n"
            
            summary += f"\n☀️ **Potentiel solaire:**\n"
            summary += f"- Production estimée: {report_data.get('kwh_per_kwc', 'N/A')} kWh/kWc/an\n"
            
            summary += f"\n🔗 Lien rapport: /rapport_point?lat={lat}&lon={lon}"
            
            return {
                "success": True,
                "message": summary,
                "data": {
                    "lat": lat,
                    "lon": lon,
                    "address": address,
                    "altitude_m": report_data.get('altitude_m'),
                    "kwh_per_kwc": report_data.get('kwh_per_kwc'),
                    "nb_postes_bt": nb_postes_bt,
                    "nb_postes_hta": nb_postes_hta,
                    "lien_rapport": f"/rapport_point?lat={lat}&lon={lon}"
                }
            }
            
        except ImportError as e:
            print(f"❌ [HELIA RAPPORT POINT] Erreur import: {e}")
            return {"success": False, "message": "❌ Fonction de rapport non disponible"}
        except Exception as e:
            print(f"❌ [HELIA RAPPORT POINT] Erreur génération: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"❌ Erreur: {str(e)}"}
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur generate_point_report: {e}")
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_export_to_crm(args):
    """Exporte un rapport (point ou commune) vers le CRM en créant un prospect"""
    try:
        from database_adapter import execute_query
        
        source_type = args.get('source_type', 'point')  # 'point' ou 'commune'
        adresse = args.get('adresse', '')
        commune = args.get('commune', '')
        lat = args.get('lat')
        lon = args.get('lon')
        puissance_kwc = args.get('puissance_kwc', 0)
        surface_m2 = args.get('surface_m2', 0)
        type_projet = args.get('type_projet', 'autoconso')
        notes = args.get('notes', '')
        
        print(f"📤 [HELIA EXPORT CRM] Export {source_type} vers CRM")
        
        # Créer le prospect
        user_id = session.get('user_id', 1)
        
        nom_prospect = f"Prospect {commune or adresse}"
        description = f"Importé depuis rapport {source_type}"
        if notes:
            description += f" - {notes}"
        
        query = """
            INSERT INTO agriweb_prospects (
                user_id, nom_prospect, adresse, commune, latitude, longitude,
                puissance_kwc, surface_m2, type, statut, description, date_creation
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id, nom_prospect
        """
        
        result = execute_query(query, (
            user_id, nom_prospect, adresse, commune, lat, lon,
            puissance_kwc, surface_m2, type_projet, 'En cours', description
        ), fetch_one=True)
        
        if result:
            prospect_id = result['id']
            
            summary = f"✅ **Export CRM réussi !**\n\n"
            summary += f"📋 **Prospect créé:**\n"
            summary += f"- 🆔 ID: #{prospect_id}\n"
            summary += f"- 📍 Adresse: {adresse}\n"
            summary += f"- 🏘️ Commune: {commune}\n"
            summary += f"- ⚡ Puissance: {puissance_kwc} kWc\n"
            summary += f"- 📐 Surface: {surface_m2} m²\n"
            summary += f"- 🏗️ Type: {type_projet}\n"
            summary += f"- 📊 Statut: En cours\n\n"
            summary += f"🔗 Accès CRM: /crm/prospects/{prospect_id}"
            
            return {
                "success": True,
                "message": summary,
                "prospect_id": prospect_id,
                "lien": f"/crm/prospects/{prospect_id}"
            }
        else:
            return {"success": False, "message": "❌ Erreur lors de la création du prospect"}
            
    except Exception as e:
        print(f"❌ [HELIA] Erreur export_to_crm: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_add_prospect_note(args):
    """Ajoute une note à un prospect CRM"""
    try:
        from database_adapter import execute_query
        
        prospect_id = args['prospect_id']
        note_text = args['note']
        user_id = session.get('user_id', 1)
        
        print(f"📝 [HELIA NOTE] Ajout note pour prospect #{prospect_id}")
        
        # Ajouter la note
        query = """
            INSERT INTO prospect_notes (prospect_id, user_id, note_text, date_creation)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        """
        
        result = execute_query(query, (prospect_id, user_id, note_text), fetch_one=True)
        
        if result:
            return {
                "success": True,
                "message": f"✅ Note ajoutée au prospect #{prospect_id}",
                "note_id": result['id']
            }
        else:
            return {"success": False, "message": "❌ Erreur lors de l'ajout de la note"}
            
    except Exception as e:
        print(f"❌ [HELIA] Erreur add_prospect_note: {e}")
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_update_project_step(args):
    """Met à jour l'étape d'un projet (statut, dates, notes)"""
    try:
        from database_adapter import execute_query
        
        project_id = args['project_id']
        etape_id = args.get('etape_id')
        etape_nom = args.get('etape_nom')  # Alternative: nom de l'étape
        nouveau_statut = args.get('statut', 'en_cours')  # a_faire, en_cours, termine, bloque
        notes = args.get('notes')
        
        print(f"📋 [HELIA ETAPE] Mise à jour étape projet #{project_id}")
        
        # Trouver l'étape si nom fourni
        if etape_nom and not etape_id:
            query = "SELECT id FROM project_etapes WHERE project_id = %s AND nom_etape ILIKE %s LIMIT 1"
            result = execute_query(query, (project_id, f"%{etape_nom}%"), fetch_one=True)
            if result:
                etape_id = result['id']
        
        if not etape_id:
            return {"success": False, "message": "❌ Étape introuvable"}
        
        # Mettre à jour l'étape
        query = """
            UPDATE project_etapes
            SET statut = %s,
                notes = COALESCE(%s, notes),
                date_modification = CURRENT_TIMESTAMP
            WHERE id = %s AND project_id = %s
            RETURNING nom_etape, statut
        """
        
        result = execute_query(query, (nouveau_statut, notes, etape_id, project_id), fetch_one=True)
        
        if result:
            summary = f"✅ **Étape mise à jour !**\n\n"
            summary += f"📋 Projet #{project_id}\n"
            summary += f"📌 Étape: {result['nom_etape']}\n"
            summary += f"📊 Nouveau statut: {result['statut']}\n"
            if notes:
                summary += f"📝 Note: {notes}\n"
            
            return {
                "success": True,
                "message": summary,
                "etape": result
            }
        else:
            return {"success": False, "message": "❌ Erreur lors de la mise à jour"}
            
    except Exception as e:
        print(f"❌ [HELIA] Erreur update_project_step: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Erreur: {str(e)}"}


def function_get_project_status(args):
    """Récupère l'état d'avancement complet d'un projet (toutes les étapes)"""
    try:
        from database_adapter import execute_query
        
        project_id = args['project_id']
        
        print(f"📊 [HELIA PROJET] Récupération statut projet #{project_id}")
        
        # Récupérer infos projet
        project_query = """
            SELECT pf.*, ap.nom_prospect, ap.commune, ap.adresse
            FROM project_fiches pf
            LEFT JOIN agriweb_prospects ap ON pf.prospect_id = ap.id
            WHERE pf.id = %s
        """
        project = execute_query(project_query, (project_id,), fetch_one=True)
        
        if not project:
            return {"success": False, "message": f"❌ Projet #{project_id} introuvable"}
        
        # Récupérer toutes les étapes
        etapes_query = """
            SELECT id, nom_etape, ordre, statut, notes, date_debut_prevue, date_fin_prevue
            FROM project_etapes
            WHERE project_id = %s
            ORDER BY ordre
        """
        etapes = execute_query(etapes_query, (project_id,), fetch_all=True)
        
        # Calculer progression
        total_etapes = len(etapes)
        etapes_terminees = sum(1 for e in etapes if e['statut'] == 'termine')
        progression = round((etapes_terminees / total_etapes * 100)) if total_etapes > 0 else 0
        
        # Formater résumé
        summary = f"📊 **Statut du projet #{project_id}**\n\n"
        summary += f"📋 Nom: {project.get('nom_projet', 'N/A')}\n"
        summary += f"🏘️ Commune: {project.get('commune', 'N/A')}\n"
        summary += f"📍 Adresse: {project.get('adresse_projet', 'N/A')}\n"
        summary += f"📊 Statut général: {project.get('statut_projet', 'N/A')}\n"
        summary += f"📈 Progression: {progression}% ({etapes_terminees}/{total_etapes} étapes)\n\n"
        
        summary += f"📌 **Étapes:**\n"
        for etape in etapes:
            status_icon = {
                'a_faire': '⏳',
                'en_cours': '🔄',
                'termine': '✅',
                'bloque': '🚫'
            }.get(etape['statut'], '❓')
            
            summary += f"{status_icon} {etape['nom_etape']} ({etape['statut']})\n"
        
        summary += f"\n🔗 Lien projet: /crm/projets/{project_id}"
        
        return {
            "success": True,
            "message": summary,
            "data": {
                "project_id": project_id,
                "nom_projet": project.get('nom_projet'),
                "commune": project.get('commune'),
                "statut_projet": project.get('statut_projet'),
                "progression": progression,
                "total_etapes": total_etapes,
                "etapes_terminees": etapes_terminees,
                "etapes": etapes
            }
        }
        
    except Exception as e:
        print(f"❌ [HELIA] Erreur get_project_status: {e}")
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
    "analyze_commune_report": function_analyze_commune_report,
    "toggle_layer": function_toggle_layer,
    "zoom_to_location": function_zoom_to_location,
    "search_location": function_search_location,
    "get_map_state": function_get_map_state,
    "analyze_visible_layers": function_analyze_visible_layers,
    "analyze_urban_data": function_analyze_urban_data,
    "generate_point_report": function_generate_point_report,
    "export_to_crm": function_export_to_crm,
    "add_prospect_note": function_add_prospect_note,
    "update_project_step": function_update_project_step,
    "get_project_status": function_get_project_status
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
        
        # Limiter à 1 seul dernier message pour minimiser cookies (fix 4264 > 4093 bytes)
        if len(session['helia_conversations'][session_id]) > 1:
            session['helia_conversations'][session_id] = session['helia_conversations'][session_id][-1:]
        
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
            
            # Ajouter historique (1 seul message pour minimiser tokens)
            for msg in history[-1:]:
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
