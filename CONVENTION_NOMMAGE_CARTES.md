# Convention de Nommage des Cartes Sauvegardées

## Date de mise à jour
10 octobre 2025

## Objectif
Améliorer l'identification et la recherche des cartes sauvegardées en incluant l'objet de la recherche dans le nom du fichier.

## Ancienne convention (avant)
- Recherche par adresse : `map_1760086706_777502053410357141.html` ❌
- Rapport par adresse : `rapport_point_20251010_105837.html` ❌
- Commune : `commune_map_Moutier-d'Ahun_20251009_123150.html` ✅ (déjà bien)

**Problème** : Impossible de savoir quelle adresse a été recherchée sans ouvrir la carte.

## Nouvelle convention (après)
- Recherche par adresse : `recherche_15_rue_de_Paris_Nice_20251010_143022.html` ✅
- Rapport par adresse : `rapport_15_rue_de_Paris_Nice_20251010_143022.html` ✅
- Commune : `commune_Moutier_d_Ahun_20251010_143022.html` ✅

**Avantages** :
- 🔍 Recherche facile dans la liste des cartes
- 📝 Identification immédiate de l'objet de la recherche
- 🗂️ Organisation naturelle par type (recherche/rapport/commune)
- 📅 Horodatage pour éviter les doublons

## Fonction de nettoyage

```python
def clean_filename(text, max_length=50):
    """
    Nettoie un texte pour en faire un nom de fichier valide.
    - Supprime les accents
    - Remplace espaces et caractères spéciaux par des underscores
    - Limite la longueur à 50 caractères
    """
    import re
    import unicodedata
    
    # Supprimer les accents
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Remplacer les espaces et caractères spéciaux
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '_', text)
    text = text.strip('_')
    
    # Limiter la longueur
    if len(text) > max_length:
        text = text[:max_length]
    
    return text
```

## Exemples de transformation

| Entrée | Sortie |
|--------|--------|
| "15 rue de la République, Nice" | "15_rue_de_la_Republique_Nice" |
| "Château-d'Oléron" | "Chateau_d_Oleron" |
| "Saint-Étienne" | "Saint_Etienne" |
| "123, avenue des Champs-Élysées, Paris 75008" | "123_avenue_des_Champs_Elysees_Paris_75008" |

## Modification du code

### 1. Recherche par adresse (ligne ~11948)
```python
# AVANT
carte_filename = f"map_{int(time.time())}_{abs(hash((lat, lon, address)))}.html"

# APRÈS
clean_addr = clean_filename(address)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
carte_filename = f"recherche_{clean_addr}_{timestamp}.html"
```

### 2. Rapport par adresse (ligne ~10416)
```python
# AVANT
carte_filename = f"rapport_point_{timestamp}.html"

# APRÈS
clean_addr = clean_filename(address)
carte_filename = f"rapport_{clean_addr}_{timestamp}.html"
```

### 3. Recherche par commune (ligne ~8696)
```python
# AVANT
carte_filename = f"commune_map_{commune.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

# APRÈS
clean_commune = clean_filename(commune)
carte_filename = f"commune_{clean_commune}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
```

## Impact sur l'interface

### Page "Mes cartes sauvegardées" (`/saved_maps`)

Les cartes s'afficheront avec des noms lisibles :
- Badge coloré selon le type (recherche/rapport/commune)
- Tri automatique par date
- Recherche par nom facilitée
- Filtres par type disponibles

### Exemple d'affichage

```
🔍 recherche_15_rue_de_Paris_Nice
   📅 10/10/2025 14:30
   🏷️ Recherche | 234 KB

📄 rapport_15_rue_de_Paris_Nice
   📅 10/10/2025 14:35
   🏷️ Rapport | 512 KB

🏘️ commune_Moutier_d_Ahun
   📅 10/10/2025 15:00
   🏷️ Commune | 1.2 MB
```

## Gestion des anciennes cartes

Les cartes existantes (avec ancienne convention) restent accessibles et fonctionnelles. Elles coexistent avec les nouvelles cartes sans problème.

Pour faire le ménage :
1. Utiliser le bouton "Nettoyer anciennes cartes (>7 jours)"
2. Ou supprimer manuellement les cartes non désirées via l'interface

## Tests recommandés

1. ✅ Recherche d'une adresse avec caractères spéciaux (accents, apostrophes)
2. ✅ Recherche d'une très longue adresse (>100 caractères)
3. ✅ Génération de rapport sur la même adresse (vérifier horodatage)
4. ✅ Recherche par commune avec tirets et espaces
5. ✅ Vérifier l'affichage dans `/saved_maps`

## Maintenance future

- Surveiller la taille du dossier `static/cartes/`
- Envisager un nettoyage automatique des cartes >30 jours
- Possibilité d'ajouter le code postal dans le nom pour plus de précision
- Considérer une compression des anciennes cartes

## Notes techniques

- La fonction `clean_filename()` est définie dans `agriweb_hebergement_gratuit.py` ligne ~451
- Tous les fichiers sont sauvegardés dans `static/cartes/`
- Format timestamp : `YYYYMMDD_HHMMSS`
- Limite de longueur : 50 caractères pour l'objet de recherche
- Extension toujours : `.html`
