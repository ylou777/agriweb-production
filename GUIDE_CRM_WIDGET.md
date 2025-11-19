# 🎯 GUIDE D'UTILISATION DU WIDGET CRM INTELLIGENT

## ✅ STATUT DE L'INTÉGRATION

**INTÉGRATION TERMINÉE AVEC SUCCÈS !** 🎉

Le widget CRM intelligent a été intégré avec succès dans AgriWeb. Voici comment l'utiliser :

---

## 📋 COMMENT VOIR LE WIDGET CRM

### 1️⃣ **Ouvrir l'application**
- Allez sur : **http://localhost:5000**
- L'application affiche le message ✅ "CRM Commercial Intelligent" au démarrage

### 2️⃣ **Faire une recherche par commune**
Dans le panneau de recherche de commune :
- **Saisissez une grande ville** (ex: Lyon, Paris, Marseille, Toulouse)
- **Cochez "Données SIRENE"** pour activer la recherche d'entreprises
- **Cliquez sur "Rechercher commune"**

### 3️⃣ **Le widget CRM apparaît automatiquement**
Après la recherche, vous verrez :
```
🎯 CRM Commercial Intelligent [X prospects qualifiés]
```

Un grand encadré vert avec :
- 📊 **Statistiques SIRENE** (nombre d'entreprises analysées)
- ✅ **Prospects qualifiés** avec priorité (haute/moyenne/faible)
- 🔘 **Boutons d'action** :
  - "Créer Prospects Qualifiés"
  - "Analyser SIRENE Détaillé"
  - "Dashboard CRM"

---

## 🎯 FONCTIONNALITÉS DU WIDGET

### **Qualification Intelligente**
Le système analyse automatiquement toutes les entreprises SIRENE et ne retient que :
- 🏭 **Agriculture** (codes NAF 01xx) - Priorité HAUTE
- ⚡ **Énergie** (codes NAF 35xx) - Priorité HAUTE  
- 🏗️ **BTP** (codes NAF 41-43xx) - Priorité MOYENNE
- 💼 **Services spécialisés** - Priorité FAIBLE

### **Actions Disponibles**

1. **🎯 Créer Prospects Qualifiés**
   - Enregistre automatiquement les entreprises qualifiées dans le CRM
   - Applique la priorisation commerciale
   - Affiche un résumé des prospects créés

2. **🔍 Analyser SIRENE Détaillé**
   - Analyse approfondie des entreprises trouvées
   - Répartition par secteur d'activité
   - Scoring et taille moyenne des entreprises

3. **📊 Dashboard CRM**
   - Vue d'ensemble de tous les prospects
   - Gestion des contacts qualifiés
   - Suivi commercial

---

## 📍 COMMUNES DE TEST RECOMMANDÉES

Pour voir le widget avec de nombreux prospects :

| Commune | Prospects attendus | Secteurs principaux |
|---------|-------------------|-------------------|
| **Lyon** | 50-100+ | Énergie, BTP, Agriculture |
| **Paris** | 100+ | Tous secteurs |
| **Toulouse** | 30-80 | Agriculture, Énergie |
| **Marseille** | 40-90 | BTP, Agriculture |

---

## 🔧 DÉPANNAGE

### **Widget n'apparaît pas ?**
1. ✅ Vérifiez que "Données SIRENE" est coché
2. ✅ Utilisez une grande ville (plus d'entreprises)
3. ✅ Ouvrez la console navigateur (F12) pour voir les logs CRM
4. ✅ Recherchez les messages : `🎯 [CRM] Widget CRM intelligent`

### **Pas de prospects détectés ?**
- Essayez une commune plus grande
- Augmentez le rayon SIRENE (0.1 km minimum)
- Vérifiez les logs : `📊 [CRM] X/Y entreprises SIRENE qualifiées`

### **Erreur dans le widget ?**
- Vérifiez les logs JavaScript (console F12)
- Vérifiez que les routes CRM répondent : `/api/crm/dashboard`

---

## 🎉 RÉSULTAT ATTENDU

Quand tout fonctionne, vous verrez :

```
🎯 CRM Commercial Intelligent [42 prospects qualifiés]

🏢 Qualification SIRENE :
📊 Total entreprises : 180
✅ Qualifiées : 42
📈 Taux de qualification : 23%

🔥 Priorité haute : 15
⚡ Priorité moyenne : 20  
💡 Priorité faible : 7

🎯 Qualification automatique réussie !
42 prospects commerciaux ont été identifiés et pré-qualifiés...

[Créer Prospects Qualifiés] [Analyser SIRENE] [Dashboard CRM]
```

---

## ✅ INTÉGRATION TECHNIQUE RÉALISÉE

**Backend :**
- ✅ Module CRM intelligent (`agriweb_crm_bridge_intelligent.py`)
- ✅ Routes API CRM (`agriweb_crm_routes.py`)
- ✅ Intégration dans l'application principale
- ✅ Données CRM ajoutées aux réponses JSON

**Frontend :**
- ✅ Widget JavaScript intégré dans `static/main.js`
- ✅ Affichage automatique après recherche commune
- ✅ Interface utilisateur complète avec actions
- ✅ Gestion des erreurs et feedback utilisateur

**Fonctionnalités :**
- ✅ Qualification SIRENE intelligente par codes NAF
- ✅ Priorisation commerciale automatique
- ✅ Création de prospects dans le CRM
- ✅ Dashboard de suivi commercial
- ✅ Analyse détaillée des entreprises

---

**🎯 Le widget CRM est maintenant pleinement opérationnel et prêt à être utilisé !**