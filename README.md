# 🌾 AgriWeb – Analyse Géospatiale Agricole

AgriWeb est une application interactive de visualisation et d'analyse géographique dédiée au secteur agricole. Elle permet :

- 🌍 La recherche par adresse, commune ou département
- 🐄 La détection des éleveurs dans une zone donnée
- 🛰️ L'affichage des parcelles cadastrales et RPG
- ⚡ L'analyse de proximité aux postes HTA / BT
- 🏭 L'intégration des entreprises via Sirene
- 🗺️ La génération de rapports cartographiques

---

## 🔧 Fonctionnalités principales

- **Carte interactive Leaflet** avec ajout dynamique de GeoJSON
- **Recherche unifiée** (coordonnées, adresse)
- **Recherche par commune** avec filtre surface et distances
- **Recherche SSE par département** (via SSE + EventSource)
- **Rapports dynamiques HTML ou DOCX**
- **Utilisation d'API IGN, cadastre, urbanisme (GPU), Sirene**

---

## ▶️ Lancer l'application

```bash
python agriweb_source.py
