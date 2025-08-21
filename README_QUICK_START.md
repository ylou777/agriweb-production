# 🚀 AgriWeb - Guide de démarrage rapide

## ⚡ DÉMARRAGE EN 30 SECONDES

### Option 1 : Script automatique (Recommandé)
```powershell
.\start_agriweb.ps1
```

### Option 2 : Démarrage manuel
```bash
# Terminal 1 : Tunnel ngrok
python ngrok_manager.py

# Terminal 2 : Application (nouveau terminal)
.venv\Scripts\Activate.ps1
python agriweb_hebergement_gratuit.py
```

## 🌐 ACCÈS RAPIDE

- **Application :** http://localhost:5000
- **Admin :** http://localhost:5000/admin (admin@test.com / admin123)
- **Production :** https://aware-surprise-production.up.railway.app

## 🔍 VÉRIFICATION
```bash
python check_status.py
```

## 📖 DOCUMENTATION COMPLÈTE
Voir `TUTORIEL_DEMARRAGE.md` pour le guide détaillé.

## 🛑 ARRÊT
Appuyez sur `Ctrl+C` dans chaque terminal ouvert.
