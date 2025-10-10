# 🐛 DEBUG RAPPORT DÉPARTEMENT - Guide de test

## Problème rapporté
❌ Après une recherche par département, le bouton "Générer rapport" ouvre `about:blank` et ne charge pas le rapport.

## Améliorations apportées

### 1. Logs de débogage JavaScript améliorés
✅ Ajout de `console.log` détaillés dans `generateDeptReport()` :
- Vérification de `window.lastDeptResults`
- Affichage du nombre de rapports
- Suivi de la requête POST
- Vérification de la taille du HTML reçu
- Message de chargement pendant la génération

### 2. Gestion d'erreurs améliorée
✅ Détection des erreurs HTTP (status codes)
✅ Vérification de la longueur du HTML reçu
✅ Messages d'erreur plus explicites

## 📝 Procédure de test

### Étape 1 : Faire une recherche par département
1. Ouvrir http://localhost:5000
2. Sélectionner l'onglet "Recherche par Département"
3. Saisir un code département (ex: `23` pour la Creuse)
4. Cliquer sur "Rechercher"
5. Attendre que toutes les communes soient traitées
6. ✅ Vérifier que des données apparaissent dans le panneau d'info

### Étape 2 : Ouvrir la console développeur
1. Appuyer sur **F12** (Chrome/Edge) ou **Ctrl+Shift+I** (Firefox)
2. Aller dans l'onglet **Console**

### Étape 3 : Générer le rapport
1. Cliquer sur "Générer Rapport Complet"
2. Observer les logs dans la console :

```javascript
[generateDeptReport] Début
[generateDeptReport] window.lastDeptResults: Array(XX)
[generateDeptReport] Nombre de rapports: XX
[generateDeptReport] Envoi requête POST
[generateDeptReport] Réponse reçue, status: 200
[generateDeptReport] HTML reçu, taille: XXXXX caractères
[generateDeptReport] Rapport affiché avec succès
```

### Étape 4 : Vérifier le rapport
✅ Une nouvelle fenêtre doit s'ouvrir
✅ Le message "Génération du rapport en cours..." doit apparaître brièvement
✅ Le rapport complet doit se charger

## 🔍 Diagnostics possibles

### Cas 1 : "Faites d'abord une recherche départementale !"
**Cause** : `window.lastDeptResults` est vide
**Solution** : Refaire la recherche par département complètement

### Cas 2 : `HTTP 500: Internal Server Error`
**Cause** : Erreur côté serveur Python
**Diagnostic** :
```bash
Get-Content error.log -Tail 50
```
Chercher les lignes `[RAPPORT_DEPT]`

### Cas 3 : HTML suspicieusement court (< 100 caractères)
**Cause** : Le template ne génère pas de contenu
**Vérifier** :
- Le template existe : `templates/rapport_departement_complet.html`
- Les données sont bien transmises dans les logs serveur

### Cas 4 : Popup bloquée
**Symptôme** : "Impossible d'ouvrir un nouvel onglet"
**Solution** : Autoriser les popups pour localhost:5000

## 🛠️ Logs serveur à surveiller

```bash
# Dans le terminal où tourne Flask :
[RAPPORT_DEPT] Traitement de XX rapports communaux
[RAPPORT_DEPT] Département détecté: XX
[RAPPORT_DEPT] XXX: Limité à 20 parcelles (sur XXX)
[RAPPORT_DEPT] Synthèse finale: XX éleveurs, XX parcelles
[RAPPORT_DEPT] TOP 50 avec 50 parcelles
[RAPPORT_DEPT] Taille HTML générée: X.XX MB
```

## 📊 Données de test recommandées

### Département petit (test rapide)
- Code : `48` (Lozère) - environ 185 communes
- Temps : ~5-10 minutes

### Département moyen
- Code : `23` (Creuse) - environ 256 communes
- Temps : ~10-15 minutes

### ⚠️ Éviter pour les tests
- Grandes métropoles (trop de données)
- Paris (75), Nord (59), Rhône (69)

## 🔧 Corrections appliquées dans le code

### JavaScript (`static/main.js`)
```javascript
// Avant :
fetch('/rapport_departement_post', ...)
  .then(res => res.text())
  .then(html => { w.document.write(html); })

// Après :
fetch('/rapport_departement_post', ...)
  .then(res => {
    console.log("status:", res.status);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.text();
  })
  .then(html => {
    console.log("taille:", html.length);
    w.document.write(html);
  })
```

### Python (`agriweb_hebergement_gratuit.py`)
Le code serveur était déjà robuste avec :
- Limitation des données (20 parcelles max par commune)
- Fallback sur template simplifié si > 10 MB
- Gestion d'erreurs complète

## 📞 Si le problème persiste

1. **Vérifier les logs console JavaScript** (F12)
2. **Vérifier les logs serveur Flask** (terminal)
3. **Vérifier les logs d'erreur** : `Get-Content error.log -Tail 50`
4. **Tester avec un département plus petit** (48, 09, 05...)
5. **Vider le cache navigateur** (Ctrl+Shift+Del)

## ✅ Commit et déploiement

Une fois les tests validés, n'oubliez pas de commiter :
```bash
git add static/main.js
git commit -m "Debug: Amélioration logs rapport département"
git push origin main
git push production main
```
