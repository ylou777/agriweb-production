/**
 * Base de connaissances HELIA ☀️
 * Culture photovoltaïque approfondie et expertise solaire
 * Votre guide complet pour maîtriser l'énergie du soleil
 */

const SunsticeKnowledgeBase = {
    // ===== PRÉSENTATION HELIA =====
    helia: {
        nom: "Helia",
        rôle: "Experte en énergie solaire et assistante photovoltaïque",
        passion: "Rendre l'énergie solaire accessible à tous",
        devise: "☀️ L'énergie du futur brille déjà au-dessus de nos têtes !",
        personnalité: {
            traits: ["Chaleureuse", "Pédagogue", "Passionnée", "Optimiste"],
            style: "Vulgarise les concepts techniques avec des exemples concrets",
            approche: "Accompagne avec bienveillance du débutant à l'expert"
        },
        saviez_vous: [
            "☀️ Le soleil envoie en 1 heure plus d'énergie que l'humanité n'en consomme en 1 an !",
            "🌍 Les panneaux solaires fonctionnent même par temps nuageux (30-50% de rendement) !",
            "♻️ Un panneau solaire peut être recyclé à 95% en fin de vie (25-30 ans) !",
            "� Le prix du solaire a baissé de 90% en 10 ans !",
            "⚡ 1 kWc produit environ 1000-1400 kWh/an en France selon les régions !",
            "🏭 Une centrale solaire peut alimenter des milliers de foyers !",
            "🔋 Les panneaux solaires produisent de l'électricité sans bruit ni pollution !",
            "🏠 L'autoconsommation permet d'économiser jusqu'à 70% sur sa facture d'électricité !",
            "🏘️ L'autoconsommation collective peut regrouper jusqu'à 500 participants dans un rayon de 2 km !",
            "💼 Les PPA (Power Purchase Agreement) sécurisent les prix de l'électricité sur 10-25 ans !",
            "🌐 Amazon, Orange et SNCF utilisent des PPA pour décarboner leur consommation !",
            "📊 Un taux d'autoconsommation de 30-70% est typique pour une installation résidentielle !"
        ]
    },

    // ===== CULTURE PHOTOVOLTAÏQUE =====
    culture_pv: {
        "histoire": {
            titre: "L'histoire du photovoltaïque",
            événements: [
                {
                    année: 1839,
                    événement: "Découverte de l'effet photovoltaïque",
                    auteur: "Alexandre Edmond Becquerel",
                    description: "Physicien français, observe l'effet photovoltaïque sur des électrodes plongées dans un électrolyte"
                },
                {
                    année: 1954,
                    événement: "Première cellule photovoltaïque moderne",
                    auteur: "Laboratoires Bell (USA)",
                    description: "Rendement de 6% - révolution pour l'époque !"
                },
                {
                    année: 1958,
                    événement: "Premier satellite à panneaux solaires",
                    auteur: "Vanguard 1",
                    description: "Le spatial adopte le solaire pour l'alimentation des satellites"
                },
                {
                    année: "2000-2020",
                    événement: "Démocratisation mondiale",
                    description: "Le coût du solaire chute de 90%, rendant l'énergie solaire compétitive"
                },
                {
                    année: 2024,
                    événement: "Rendements records > 26%",
                    description: "Les panneaux actuels atteignent des rendements jamais vus"
                }
            ]
        },
        "vocabulaire": {
            "kWc": {
                terme: "Kilowatt-crête",
                explication: "Puissance maximale que peut produire un panneau solaire dans des conditions optimales standard (1000 W/m², 25°C)",
                exemple: "Un panneau de 400 Wc (0,4 kWc) produit 400W dans les conditions idéales"
            },
            "kWh": {
                terme: "Kilowatt-heure",
                explication: "Énergie produite ou consommée. 1 kWh = 1000W pendant 1 heure",
                exemple: "Un sèche-linge consomme environ 2-3 kWh par cycle"
            },
            "Rendement": {
                terme: "Efficacité de conversion",
                explication: "Pourcentage de l'énergie solaire reçue qui est transformée en électricité",
                exemple: "Un panneau à 20% de rendement transforme 200W en électricité pour 1000W de soleil reçu"
            },
            "Onduleur": {
                terme: "Convertisseur DC/AC",
                explication: "Transforme le courant continu des panneaux en courant alternatif utilisable",
                exemple: "Comme un traducteur entre le langage des panneaux et celui de votre maison"
            },
            "Orientation": {
                terme: "Direction du panneau",
                explication: "Plein sud = optimal en France. Sud-Est ou Sud-Ouest = bon compromis",
                exemple: "Un panneau plein sud produit 100%, plein est/ouest = 70-80%"
            },
            "Inclinaison": {
                terme: "Angle du panneau",
                explication: "30° = optimal en France. Suit la latitude pour maximiser la production annuelle",
                exemple: "Trop plat = perte en hiver, trop vertical = perte en été"
            },
            "Autoconsommation": {
                terme: "Consommation directe",
                explication: "Utiliser l'électricité produite immédiatement dans votre bâtiment",
                exemple: "Produire et consommer en même temps = économies maximales !"
            },
            "Revente": {
                terme: "Vente surplus ou totale",
                explication: "Injecter l'électricité dans le réseau contre rémunération",
                exemple: "Le surplus non consommé peut être vendu à EDF OA"
            },
            "Trackers": {
                terme: "Suiveurs solaires",
                explication: "Panneaux qui suivent la course du soleil pour maximiser la production (+20-30%)",
                exemple: "Comme une tournesol qui suit le soleil toute la journée"
            }
        },
        "types_installations": {
            "Toiture résidentielle": {
                description: "Installation sur toit de maison individuelle",
                puissance_typique: "3-9 kWc",
                usage: "Autoconsommation avec revente surplus",
                avantages: ["Pas de terrain nécessaire", "Économies électricité", "Valorisation patrimoine"]
            },
            "Centrale au sol": {
                description: "Parc solaire sur terrain agricole ou friche",
                puissance_typique: "500 kWc - 50 MWc+",
                usage: "Revente totale de la production",
                avantages: ["Grande production", "Rentabilité élevée", "Valorisation terrain inutilisé"]
            },
            "Ombriere parking": {
                description: "Structure solaire au-dessus de places de stationnement",
                puissance_typique: "100-500 kWc",
                usage: "Autoconsommation entreprise + bornes recharge",
                avantages: ["Double usage", "Protection véhicules", "Image verte"]
            },
            "Agrivoltaïque": {
                description: "Panneaux surelevés permettant culture/pâturage dessous",
                puissance_typique: "100 kWc - 5 MWc",
                usage: "Double revenu : agriculture + électricité",
                avantages: ["Diversification revenus", "Protection cultures", "Innovation"]
            },
            "Bâtiment tertiaire": {
                description: "Toitures entrepôts, supermarchés, bâtiments industriels",
                puissance_typique: "50-500 kWc",
                usage: "Autoconsommation professionnelle",
                avantages: ["Réduction facture énergie", "RSE", "Grandes surfaces disponibles"]
            }
        },
        "modeles_economiques": {
            "Autoconsommation individuelle": {
                description: "Consommation directe de l'électricité produite par ses propres panneaux solaires",
                principe: "Produire et consommer son électricité sur place, sans passer par le réseau",
                avantages: [
                    "Économies sur la facture d'électricité",
                    "Indépendance énergétique partielle",
                    "Valorisation du surplus possible (revente)",
                    "Autoconsommation typique : 30-70% de la production",
                    "Rentabilité immédiate sur l'électricité consommée"
                ],
                fonctionnement: "Panneaux → Onduleur → Consommation directe → Surplus vers réseau ou stockage",
                exemple: "Une maison avec 6 kWc produit 7500 kWh/an. Si consommation = 5000 kWh autoconsommés + 2500 kWh revendus",
                taux_typique: "30-70% d'autoconsommation selon profil de consommation",
                optimisation: "Synchroniser consommation avec production (machines le jour, chauffe-eau solaire, domotique)"
            },
            "Autoconsommation collective": {
                description: "Partage de la production solaire entre plusieurs consommateurs via le réseau public",
                principe: "Un ou plusieurs producteurs alimentent plusieurs consommateurs dans un périmètre défini (≤ 2 km)",
                cadre_legal: "Défini par l'Ordonnance n°2021-236 du 3 mars 2021",
                participants: {
                    "Producteurs": "Peuvent être consommateurs ou non",
                    "Consommateurs": "Bénéficient de l'électricité produite localement",
                    "Gestionnaire": "Personne morale organisant l'opération (syndic, collectivité, société dédiée)"
                },
                perimetre: "≤ 2 km entre les points les plus éloignés de l'opération",
                avantages: [
                    "Mutualisation des coûts d'installation",
                    "Accès au solaire pour ceux sans toiture adaptée",
                    "Valorisation optimale de la production locale",
                    "Réduction des pertes en ligne (proximité)",
                    "Création de lien social et solidarité énergétique",
                    "Tarif d'utilisation du réseau réduit (TURPE)"
                ],
                exemples: [
                    "Immeuble résidentiel : toiture partagée entre copropriétaires",
                    "Zone d'activité : centrale solaire pour plusieurs entreprises",
                    "Quartier : ombrières de parking alimentant commerces et logements",
                    "Commune : centrale au sol pour bâtiments publics + habitants"
                ],
                cles_de_repartition: "Fixe, dynamique ou mixte selon clé définie collectivement"
            },
            "PPA (Power Purchase Agreement)": {
                description: "Contrat d'achat d'électricité de long terme entre un producteur et un consommateur",
                definition_complete: "Accord contractuel où un acheteur (corporate) s'engage à acheter l'électricité produite par une centrale solaire à un prix fixe sur une durée déterminée (10-25 ans)",
                types: {
                    "PPA On-site (sur site)": {
                        description: "Installation sur le site du consommateur",
                        exemple: "Panneaux sur toiture d'usine, électricité consommée directement",
                        avantage: "Pas de transport, autoconsommation maximale"
                    },
                    "PPA Off-site (hors site)": {
                        description: "Centrale distante, électricité livrée via le réseau",
                        exemple: "Entreprise achète production d'une centrale au sol à 50 km",
                        avantage: "Grandes quantités possibles, pas de contrainte foncière"
                    },
                    "PPA virtuel (VPPA)": {
                        description: "Pas de livraison physique, garanties d'origine échangées",
                        usage: "Compensation carbone, engagement RSE",
                        avantage: "Flexibilité géographique totale"
                    }
                },
                acteurs: {
                    "Producteur": "Développeur/propriétaire de la centrale solaire",
                    "Acheteur (offtaker)": "Entreprise, collectivité consommant l'électricité",
                    "Intermédiaires": "Agrégateurs, traders facilitant le contrat"
                },
                avantages_acheteur: [
                    "Prix de l'électricité sécurisé sur long terme",
                    "Protection contre volatilité des prix du marché",
                    "Décarbonation de la consommation",
                    "Atteinte objectifs RSE et neutralité carbone",
                    "Traçabilité de l'origine renouvelable"
                ],
                avantages_producteur: [
                    "Revenus garantis et prévisibles sur durée du PPA",
                    "Sécurisation du financement du projet",
                    "Visibilité économique long terme",
                    "Indépendance vis-à-vis des tarifs réglementés"
                ],
                duree_typique: "10-25 ans",
                prix: "Fixe, indexé ou formule mixte selon négociation",
                exemples_concrets: [
                    "Amazon : PPA pour 100 MW solaires en France",
                    "Orange : PPA 400 GWh/an sur 20 ans",
                    "SNCF : Multiples PPA pour alimenter les gares",
                    "Grands groupes industriels : sécurisation approvisionnement électrique"
                ]
            }
        }
    },

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
        "💡 L'autocomplétion des communes évite les erreurs de saisie",
        "☀️ Un panneau solaire de 400 Wc mesure environ 1,7 m² - comme une petite table !",
        "🌍 La France a installé plus de 16 GW de solaire en 2023 - de quoi alimenter 8 millions de foyers !",
        "⚡ 1 kWc bien orienté produit de quoi faire 10 000 machines à laver par an !",
        "🌡️ Les panneaux solaires produisent PLUS par temps frais et ensoleillé que par grande chaleur",
        "🔋 Une installation de 3 kWc peut couvrir 30-70% des besoins d'un foyer selon la consommation",
        "💰 Le retour sur investissement d'une installation solaire est généralement de 8-12 ans",
        "🌞 Le Sud de la France reçoit jusqu'à 1700 kWh/m²/an - comme l'Espagne !",
        "📈 Le solaire est devenu l'énergie la moins chère de l'histoire en 2020",
        "♻️ L'énergie nécessaire à fabriquer un panneau est remboursée en 1-3 ans de production",
        "🏠 Une toiture de 30 m² peut accueillir environ 5-6 kWc de panneaux solaires"
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
