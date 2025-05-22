
---

## ✅ ATTENTES POUR CODEX

- 🛠️ Corriger le fonctionnement des boutons "recherche commune" et "recherche département".
- 🧪 Vérifier que `mapFrame.contentWindow.addGeoJsonToMap` est bien accessible.
- ✅ Garantir que les couches GeoJSON sont bien injectées dynamiquement dans Leaflet.

---

## 🧪 CONSEILS DE TEST

- Lancer `python agriweb_source.py`
- Accéder à : http://127.0.0.1:5000
- Utiliser les boutons "Recherche commune" ou "Département"
- Observer la console (JS + Flask)
- Vérifier si `data.rpg`, `data.eleveurs`, etc. sont bien reçus
- Tester manuellement : `/search_by_commune?commune=Sedan&...`

---

## 📧 CONTACT

- Auteur : Ylau (GitHub: [ylou777](https://github.com/ylou777))
- Email : ylaurent.perso@gmail.com
