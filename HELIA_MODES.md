# 🔀 Modes de Fonctionnement Helia

## Vue d'ensemble

Helia propose **2 modes de fonctionnement** pour s'adapter à vos préférences :

### 🌟 Mode ASSISTÉ (par défaut)
**Icône :** ⭐ (étoiles)  
**Comportement :** **PROACTIF**

Helia est votre assistante proactive qui :
- ✅ **Agit automatiquement** sans attendre de confirmation
- ✅ **Utilise ses fonctions** dès qu'elle détecte un besoin
- ✅ **Suggère des actions** pertinentes
- ✅ **Propose la suite logique** de vos recherches
- ✅ **Crée des prospects** automatiquement si pertinent
- ✅ **Enrichit les données** de manière autonome

**Exemple de conversation :**
```
Utilisateur : "Cherche des toitures à Lyon"
Helia : "🔍 Je lance la recherche sur Lyon... 
         ✅ 152 toitures trouvées !
         🗺️ [Ouvrir la carte]
         
         💡 Je remarque 23 toitures >500m² près de postes HT.
         Voulez-vous que je crée des prospects pour ces opportunités ?"
```

---

### ✋ Mode MANUEL
**Icône :** 👆 (main)  
**Comportement :** **RÉACTIF**

Helia attend vos demandes explicites avant d'agir :
- ⏸️ **Attend vos instructions** avant toute action
- ⏸️ **N'utilise ses fonctions** que sur demande explicite
- ⏸️ **Répond aux questions** sans automatiser
- ⏸️ **Ne propose PAS** d'actions non demandées
- ⏸️ **Demande confirmation** avant les opérations importantes

**Exemple de conversation :**
```
Utilisateur : "Cherche des toitures à Lyon"
Helia : "Je peux rechercher les toitures à Lyon. 
         Voulez-vous que je lance cette recherche ?"

Utilisateur : "Oui"
Helia : "🔍 Recherche lancée..."
```

---

## 🔄 Comment changer de mode ?

### Dans l'interface chat Helia :

1. **Ouvrir le chat** en cliquant sur le bouton ☀️ en bas à droite
2. **Regarder en haut à droite** du header (à côté du bouton fermer ❌)
3. **Cliquer sur l'icône** correspondant au mode souhaité :
   - **⭐** = Mode Assisté (proactif)
   - **👆** = Mode Manuel (réactif)

Le bouton actif est **surligné en blanc** avec une ombre.

---

## 🎯 Cas d'usage recommandés

### Mode ASSISTÉ - Idéal pour :
- 🚀 **Prospection rapide** : Helia accélère votre workflow
- 📊 **Exploration de données** : Elle enrichit automatiquement
- 🗺️ **Recherches complexes** : Elle enchaîne les filtres intelligemment
- 💼 **Qualification de leads** : Création automatique de prospects
- 🎓 **Découverte de la plateforme** : Elle vous guide

### Mode MANUEL - Idéal pour :
- 🎯 **Contrôle total** : Vous validez chaque étape
- 📚 **Apprentissage** : Vous comprenez chaque action
- 🔍 **Recherches précises** : Pas d'actions non désirées
- 📝 **Documentation** : Besoin de justifier chaque opération
- 🛡️ **Sécurité** : Validation avant modification de données

---

## 🔧 API Technique

### Endpoint : `/api/helia/mode`

#### GET - Récupérer le mode actuel
```javascript
fetch('/api/helia/mode')
  .then(res => res.json())
  .then(data => console.log(data.mode)); // 'assiste' ou 'manuel'
```

**Réponse :**
```json
{
  "mode": "assiste"
}
```

#### POST - Changer le mode
```javascript
fetch('/api/helia/mode', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({mode: 'manuel'})
})
```

**Requête :**
```json
{
  "mode": "manuel"  // ou "assiste"
}
```

**Réponse :**
```json
{
  "success": true,
  "mode": "manuel",
  "message": "Mode changé avec succès"
}
```

---

## 💾 Persistance

Le mode sélectionné est **stocké en session** :
- ✅ Persiste pendant toute la durée de votre session
- ✅ Indépendant pour chaque utilisateur
- ⏱️ Réinitialisé à "assisté" après déconnexion

---

## 🧠 Fonctionnement Technique

### Backend (`helia_ai.py`)

Deux prompts système distincts :

```python
# Mode ASSISTÉ
HELIA_SYSTEM_PROMPT_ASSISTE = """
MODE ASSISTÉ - Tu es PROACTIF
- UTILISE tes fonctions AUTOMATIQUEMENT
- SUGGÈRE des actions pertinentes
- PROPOSE la suite logique
"""

# Mode MANUEL  
HELIA_SYSTEM_PROMPT_MANUEL = """
MODE MANUEL - Tu ATTENDS les demandes
- UTILISE tes fonctions UNIQUEMENT sur demande explicite
- RÉPONDS aux questions sans automatiser
- NE PROPOSE PAS d'actions non demandées
"""
```

Injection dynamique dans `generate_response()` :
```python
helia_mode = session.get('helia_mode', 'assiste')
system_prompt = (HELIA_SYSTEM_PROMPT_ASSISTE 
                 if helia_mode == 'assiste' 
                 else HELIA_SYSTEM_PROMPT_MANUEL)
```

### Frontend (`sunstice-assistant.js`)

Boutons toggle avec appel API :
```javascript
async switchMode(mode) {
    const response = await fetch('/api/helia/mode', {
        method: 'POST',
        body: JSON.stringify({ mode: mode })
    });
    
    if (response.ok) {
        this.updateModeUI(mode);
        this.addMessage('bot', `🔄 Mode changé : ${mode}`);
    }
}
```

---

## 📊 Comparaison Rapide

| Caractéristique | Mode ASSISTÉ ⭐ | Mode MANUEL 👆 |
|----------------|----------------|----------------|
| **Proactivité** | ✅ Automatique | ❌ Sur demande |
| **Vitesse** | 🚀 Rapide | 🐢 Contrôlée |
| **Suggestions** | ✅ Constantes | ❌ Aucune |
| **Créations automatiques** | ✅ Oui | ❌ Non |
| **Enrichissement données** | ✅ Automatique | ❌ Manuel |
| **Contrôle utilisateur** | ⚖️ Moyen | ✅ Total |
| **Courbe d'apprentissage** | 📉 Facile | 📈 Plus longue |

---

## 🐛 Dépannage

**Le mode ne change pas ?**
- Vérifiez votre connexion réseau
- Rafraîchissez la page (F5)
- Vérifiez la console navigateur (F12)

**Le bouton n'apparaît pas ?**
- Vérifiez que vous êtes dans l'interface chat Helia
- Cache du navigateur à vider (Ctrl+Shift+Delete)

**L'API retourne une erreur ?**
- Vérifiez que vous êtes connecté
- Session peut-être expirée → Reconnectez-vous

---

## 📝 Changelog

### Version 1.0 (23/01/2026)
- ✅ Création des 2 modes (Assisté/Manuel)
- ✅ Route API `/api/helia/mode`
- ✅ Boutons toggle dans l'interface
- ✅ Indicateur visuel du mode actif
- ✅ Notification lors du changement

---

## 🔮 Évolutions Futures

- [ ] Mode **EXPERT** : Helia ultra-technique avec jargon PV
- [ ] Mode **PÉDAGOGIQUE** : Explications détaillées à chaque étape
- [ ] **Raccourcis clavier** : Ctrl+M pour switcher
- [ ] **Paramètres avancés** : Ajuster le niveau de proactivité
- [ ] **Historique des modes** : Statistiques d'utilisation

---

**Commit :** `a5b9184` - 23/01/2026  
**Auteur :** AgriWeb Development Team  
**Fichiers :** `helia_ai.py`, `sunstice-assistant.js`
