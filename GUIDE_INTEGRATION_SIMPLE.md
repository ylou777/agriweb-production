
# 🚀 GUIDE D'INTÉGRATION CRM SIMPLE

## Étapes pour ajouter le CRM à votre AgriWeb existant :

### 1. Ajouter les routes CRM
Dans votre fichier `agriweb_hebergement_gratuit.py`, ajoutez au début :
```python
# Import CRM
try:
    from agriweb_crm_routes import add_crm_routes
    CRM_AVAILABLE = True
except ImportError:
    CRM_AVAILABLE = False

# Après app = Flask(__name__)
if CRM_AVAILABLE:
    add_crm_routes(app)
```

### 2. Ajouter le widget dans votre template HTML
- Copiez le contenu de `crm_widget_template.html`
- Collez-le dans votre template de résultats de recherche
- Placez-le après vos résultats de carte/tableaux

### 3. Connecter les résultats de recherche
Dans votre fonction JavaScript qui traite les résultats de recherche, ajoutez :
```javascript
// Après avoir reçu et affiché vos résultats normaux
onSearchComplete(searchResults);
```

### 4. Tester
1. Démarrez votre application AgriWeb normale
2. Connectez-vous au CRM via `/crm/login`
3. Effectuez une recherche
4. Le widget CRM apparaîtra avec un bouton pour créer des prospects

## URLs importantes :
- `/crm/login` - Connexion CRM
- `/crm/dashboard` - Dashboard des prospects
- `/api/crm/integrate_search` - API d'intégration

## Comptes de test :
- admin@agriweb.com / admin123
- directeur@agriweb.com / director123
- commercial@agriweb.com / commercial123

## Avantages de cette approche :
✅ Aucune modification majeure de votre code existant
✅ Widget optionnel qui n'apparaît que si connecté au CRM
✅ Intégration progressive possible
✅ Fonctionne en parallèle de votre système actuel
