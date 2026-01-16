/**
 * Base de connaissances complète pour l'assistant Sunstice
 * Contient toutes les informations sur le fonctionnement de la plateforme
 */

const SunsticeKnowledgeBase = {
    // ===== ARCHITECTURE GLOBALE =====
    structure: {
        nom: "Sun Dev by Sunstice",
        description: "Plateforme de pré-études photovoltaïques avec analyse territoriale complète",
        modules: [
            "Analyse géospatiale (adresse, commune, département)",
            "CRM de gestion de prospects",
            "Génération de rapports détaillés",
            "Système d'authentification",
            "Export et suivi de projets"
        ]
    },

    // ===== WORKFLOWS COMPLETS =====
    workflows: {
        "analyse_adresse": {
            titre: "Analyse par adresse",
            etapes: [
                {
                    numero: 1,
                    action: "Ouvrir le menu 'Adresse • Coordonnées • GeoJSON'",
                    detail: "Dans le panneau latéral gauche, cliquer sur la première option"
                },
                {
                    numero: 2,
                    action: "Saisir une adresse complète",
                    detail: "Format: numéro, rue, code postal, ville. Ex: '15 rue de la République, 75001 Paris'"
                },
                {
                    numero: 3,
                    action: "Valider la recherche",
                    detail: "La carte se centre automatiquement sur le point"
                },
                {
                    numero: 4,
                    action: "Générer le rapport point",
                    detail: "Menu 'Rapports' → 'Rapport point courant'"
                },
                {
                    numero: 5,
                    action: "Analyser les résultats",
                    detail: "Consulter : surface, cadastre, PLU, risques, distances réseaux, potentiel PV"
                },
                {
                    numero: 6,
                    action: "Exporter vers CRM",
                    detail: "En bas du rapport → 'Exporter vers CRM/Prospects'"
                },
                {
                    numero: 7,
                    action: "Créer la fiche prospect",
                    detail: "Remplir nom, contact, notes, statut"
                },
                {
                    numero: 8,
                    action: "Finaliser dans le CRM",
                    detail: "Menu CRM → Suivi du prospect → Étapes du projet"
                }
            ]
        },
        
        "analyse_commune": {
            titre: "Analyse par commune",
            etapes: [
                {
                    numero: 1,
                    action: "Ouvrir le menu 'Commune'",
                    detail: "Dans le panneau latéral gauche"
                },
                {
                    numero: 2,
                    action: "Rechercher la commune",
                    detail: "Taper le nom, l'autocomplétion propose les résultats"
                },
                {
                    numero: 3,
                    action: "Sélectionner dans la liste",
                    detail: "Cliquer sur la commune souhaitée"
                },
                {
                    numero: 4,
                    action: "Générer le rapport commune",
                    detail: "Menu 'Rapports' → 'Rapport commune'"
                },
                {
                    numero: 5,
                    action: "Explorer les données",
                    detail: "Vue d'ensemble: population, superficie, PLU, zones propices"
                },
                {
                    numero: 6,
                    action: "Identifier les parcelles",
                    detail: "Repérer les terrains à fort potentiel"
                },
                {
                    numero: 7,
                    action: "Analyser parcelle par parcelle",
                    detail: "Cliquer sur une parcelle → Rapport point"
                }
            ]
        },

        "analyse_departement": {
            titre: "Analyse par département",
            etapes: [
                {
                    numero: 1,
                    action: "Ouvrir le menu 'Département (SSE)'",
                    detail: "Dans le panneau latéral gauche"
                },
                {
                    numero: 2,
                    action: "Sélectionner le département",
                    detail: "Soit par code (ex: 75) soit par nom"
                },
                {
                    numero: 3,
                    action: "Générer le rapport départemental",
                    detail: "Menu 'Rapports' → 'Rapport département'"
                },
                {
                    numero: 4,
                    action: "Consulter la vue macro",
                    detail: "Statistiques globales, communes prioritaires, potentiel total"
                },
                {
                    numero: 5,
                    action: "Zoomer sur une commune",
                    detail: "Cliquer pour approfondir l'analyse au niveau communal"
                }
            ]
        },

        "gestion_prospect": {
            titre: "Gestion d'un prospect",
            etapes: [
                {
                    numero: 1,
                    action: "Accéder au CRM",
                    detail: "Menu principal → CRM"
                },
                {
                    numero: 2,
                    action: "Voir tous les prospects",
                    detail: "Liste avec filtres (statut, date, commune, type)"
                },
                {
                    numero: 3,
                    action: "Ouvrir une fiche prospect",
                    detail: "Cliquer sur un prospect pour voir le détail"
                },
                {
                    numero: 4,
                    action: "Modifier les informations",
                    detail: "Nom, contact, téléphone, email, notes"
                },
                {
                    numero: 5,
                    action: "Changer le statut",
                    detail: "Nouveau → Contact → Qualifié → Proposition → Gagné/Perdu"
                },
                {
                    numero: 6,
                    action: "Ajouter des notes",
                    detail: "Historique des échanges, remarques importantes"
                },
                {
                    numero: 7,
                    action: "Planifier un RDV",
                    detail: "Section Calendrier → Ajouter rendez-vous"
                },
                {
                    numero: 8,
                    action: "Suivre les étapes du projet",
                    detail: "Pré-étude → Visite → Étude → Devis → Signature → Réalisation"
                }
            ]
        },

        "export_rapport": {
            titre: "Export et partage de rapports",
            etapes: [
                {
                    numero: 1,
                    action: "Générer un rapport",
                    detail: "Point, commune ou département"
                },
                {
                    numero: 2,
                    action: "Consulter le rapport",
                    detail: "Vérifier toutes les données"
                },
                {
                    numero: 3,
                    action: "Exporter en PDF",
                    detail: "Bouton 'Télécharger PDF' en haut du rapport"
                },
                {
                    numero: 4,
                    action: "Enregistrer dans le CRM",
                    detail: "'Exporter vers CRM' pour lier au prospect"
                },
                {
                    numero: 5,
                    action: "Partager avec le client",
                    detail: "Envoyer le PDF par email depuis le CRM"
                }
            ]
        }
    },

    // ===== FONCTIONNALITÉS DÉTAILLÉES =====
    fonctionnalites: {
        "recherche_geographique": {
            nom: "Recherche géographique",
            types: [
                {
                    type: "Adresse",
                    description: "Recherche par adresse postale complète",
                    exemple: "15 rue de la République, 75001 Paris"
                },
                {
                    type: "Coordonnées GPS",
                    description: "Latitude et longitude",
                    exemple: "48.8566, 2.3522 ou format DMS"
                },
                {
                    type: "GeoJSON",
                    description: "Import de polygones ou points GeoJSON",
                    exemple: "Fichier .geojson ou code JSON"
                },
                {
                    type: "Commune",
                    description: "Recherche par nom de commune avec autocomplétion",
                    exemple: "Paris, Lyon, Marseille..."
                },
                {
                    type: "Département",
                    description: "Recherche par code ou nom de département",
                    exemple: "75, Paris, Île-de-France"
                }
            ]
        },

        "analyses_disponibles": {
            nom: "Analyses disponibles",
            categories: [
                {
                    categorie: "Cadastre",
                    donnees: ["Parcelles", "Surfaces", "Propriétaires", "Références cadastrales"]
                },
                {
                    categorie: "Urbanisme",
                    donnees: ["PLU/PLUi", "Zones", "Règlements", "Servitudes"]
                },
                {
                    categorie: "Risques",
                    donnees: ["Inondations", "Sismique", "Radon", "Retrait-gonflement argiles", "Cavités"]
                },
                {
                    categorie: "Réseaux",
                    donnees: ["Distance poste source", "Distance lignes BT/HTA", "Raccordement ENEDIS"]
                },
                {
                    categorie: "Potentiel solaire",
                    donnees: ["Ensoleillement", "Surface exploitable", "Puissance estimée (kWc)", "Production annuelle (kWh)"]
                },
                {
                    categorie: "Environnement",
                    donnees: ["Natura 2000", "ZNIEFF", "Monuments historiques", "Sites classés"]
                }
            ]
        },

        "crm": {
            nom: "CRM - Gestion prospects",
            fonctions: [
                {
                    fonction: "Création prospect",
                    description: "Créer une fiche prospect depuis un rapport ou manuellement"
                },
                {
                    fonction: "Statuts",
                    valeurs: ["Nouveau", "Contact établi", "Qualifié", "Proposition envoyée", "Gagné", "Perdu", "En attente"]
                },
                {
                    fonction: "Filtres",
                    options: ["Par statut", "Par date", "Par commune", "Par type de projet", "Par utilisateur"]
                },
                {
                    fonction: "Étapes projet",
                    phases: ["Pré-étude", "Visite terrain", "Étude détaillée", "Devis", "Signature", "Réalisation", "Mise en service"]
                },
                {
                    fonction: "Documents",
                    types: ["Rapports PDF", "Photos", "Plans", "Devis", "Contrats"]
                },
                {
                    fonction: "Calendrier",
                    description: "Planification RDV, relances, deadlines"
                },
                {
                    fonction: "Notes et historique",
                    description: "Suivi complet des échanges et actions"
                }
            ]
        },

        "rapports": {
            nom: "Génération de rapports",
            types: [
                {
                    type: "Rapport point",
                    contenu: "Analyse complète d'une adresse/coordonnée spécifique",
                    sections: [
                        "Localisation et carte",
                        "Informations cadastrales",
                        "PLU et zonage",
                        "Risques naturels et technologiques",
                        "Distances aux réseaux",
                        "Potentiel photovoltaïque",
                        "Contraintes et recommandations"
                    ]
                },
                {
                    type: "Rapport commune",
                    contenu: "Vue d'ensemble d'une commune",
                    sections: [
                        "Données démographiques",
                        "Urbanisme général",
                        "Zones propices",
                        "Statistiques énergétiques",
                        "Parcelles prioritaires"
                    ]
                },
                {
                    type: "Rapport département",
                    contenu: "Analyse macro d'un département",
                    sections: [
                        "Statistiques globales",
                        "Communes à fort potentiel",
                        "Répartition géographique",
                        "Potentiel total estimé"
                    ]
                }
            ]
        },

        "authentification": {
            nom: "Système d'authentification",
            fonctions: [
                {
                    fonction: "Inscription",
                    description: "Création de compte utilisateur"
                },
                {
                    fonction: "Connexion",
                    description: "Email + mot de passe"
                },
                {
                    fonction: "Rôles",
                    types: ["Utilisateur standard", "Administrateur"]
                },
                {
                    fonction: "Isolation données",
                    description: "Chaque utilisateur voit uniquement ses propres prospects (sauf admin)"
                },
                {
                    fonction: "Récupération mot de passe",
                    description: "Email de réinitialisation"
                }
            ]
        }
    },

    // ===== QUESTIONS FRÉQUENTES =====
    faq: {
        "Comment faire une étude complète ?": "1. Recherchez une adresse ou commune 2. Générez le rapport point 3. Analysez les données (cadastre, PLU, risques) 4. Exportez vers CRM 5. Créez la fiche prospect 6. Suivez le projet dans le CRM",
        
        "Quelle est la différence entre rapport point et rapport commune ?": "Le rapport point analyse une adresse précise (parcelle, bâtiment) avec toutes les données détaillées. Le rapport commune donne une vue d'ensemble de toute la commune avec identification des zones propices.",
        
        "Comment ajouter un prospect ?": "Deux méthodes : 1) Générer un rapport puis cliquer 'Exporter vers CRM' 2) Dans le CRM, bouton 'Nouveau prospect' pour création manuelle",
        
        "Puis-je exporter les rapports ?": "Oui, chaque rapport peut être téléchargé en PDF via le bouton en haut du rapport. Il est aussi automatiquement sauvegardé si exporté vers un prospect.",
        
        "Comment suivre mes projets ?": "Dans le menu CRM, vous retrouvez tous vos prospects avec filtres par statut. Chaque fiche contient l'historique complet, les documents, le calendrier et les étapes du projet.",
        
        "Les données sont-elles sécurisées ?": "Oui, système d'isolation : chaque utilisateur ne voit que ses propres prospects. Seuls les administrateurs ont une vue globale.",
        
        "Quelles données sont analysées ?": "Cadastre, PLU, risques naturels, distances réseaux, potentiel solaire, environnement protégé, monuments historiques, et plus encore selon le type d'analyse.",
        
        "Comment planifier un rendez-vous avec un prospect ?": "Dans la fiche prospect (CRM), section Calendrier → Ajouter un rendez-vous. Indiquez la date, l'heure et le type de rendez-vous.",
        
        "Puis-je analyser plusieurs parcelles à la fois ?": "Pour une commune entière, utilisez le rapport commune qui identifie toutes les zones propices. Ensuite, analysez les parcelles intéressantes une par une avec le rapport point.",
        
        "Comment contacter le support ?": "Email: support@sunstice.com | Téléphone: +33 1 23 45 67 89 | Du lundi au vendredi, 9h-18h"
    },

    // ===== RACCOURCIS ET ASTUCES =====
    astuces: [
        "💡 Utilisez les filtres du CRM pour retrouver rapidement vos prospects",
        "💡 Ajoutez des notes détaillées à chaque étape pour un meilleur suivi",
        "💡 Exportez systématiquement vos rapports en PDF pour vos archives",
        "💡 Le rapport département permet d'identifier rapidement les communes prioritaires",
        "💡 Utilisez le calendrier CRM pour ne manquer aucun rendez-vous",
        "💡 Les coordonnées GPS permettent une localisation très précise",
        "💡 Le rapport point affiche les distances exactes aux postes sources",
        "💡 Changez le statut des prospects au fur et à mesure de l'avancement",
        "💡 Les admins voient tous les prospects de l'équipe pour coordination",
        "💡 L'autocomplétion des communes évite les erreurs de saisie"
    ],

    // ===== DÉPANNAGE =====
    troubleshooting: {
        "La carte ne s'affiche pas": "Vérifiez votre connexion internet. Rafraîchissez la page (F5). Videz le cache du navigateur si le problème persiste.",
        
        "Adresse introuvable": "Vérifiez l'orthographe. Essayez avec le code postal. En dernier recours, utilisez les coordonnées GPS.",
        
        "Rapport ne se génère pas": "Attendez quelques secondes, le calcul peut prendre du temps. Vérifiez que vous avez bien sélectionné un point sur la carte. Essayez de rafraîchir.",
        
        "Export CRM échoue": "Vérifiez que tous les champs obligatoires sont remplis (nom du prospect minimum). Vérifiez votre connexion. Réessayez.",
        
        "Je ne vois pas mes prospects": "Vérifiez que vous êtes bien connecté. Les prospects sont liés à votre compte utilisateur. Si vous êtes admin, vérifiez les filtres.",
        
        "Mot de passe oublié": "Page de connexion → 'Mot de passe oublié' → Entrez votre email → Suivez le lien reçu par email",
        
        "Données manquantes dans le rapport": "Certaines données peuvent ne pas être disponibles pour toutes les communes. C'est normal, le rapport affiche 'Non disponible' dans ce cas."
    }
};

// Export pour utilisation dans l'assistant
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SunsticeKnowledgeBase;
}
