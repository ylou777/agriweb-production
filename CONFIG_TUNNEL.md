# 🎯 CONFIGURATION AGRIWEB - TUNNEL GEOSERVER

## � **PROCÉDURE NGROK SIMPLIFIÉE (TESTÉE ET FONCTIONNELLE)**

### **Commandes PowerShell pour démarrer ngrok :**

```powershell
# 1. Aller dans le dossier AgW3b
cd C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b

# 2. Lancer ngrok avec votre domaine réservé
.\ngrok.exe http --hostname=agriweb-prod.ngrok-free.app 8080
```

### **En une seule ligne :**
```powershell
cd C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b; .\ngrok.exe http --hostname=agriweb-prod.ngrok-free.app 8080
```

## 🌐 URLs disponibles

- **Interface GeoServer :** https://agriweb-prod.ngrok-free.app/geoserver
- **Interface Web :** https://agriweb-prod.ngrok-free.app/geoserver/web/
- **API REST :** https://agriweb-prod.ngrok-free.app/geoserver/rest/
- **WMS :** https://agriweb-prod.ngrok-free.app/geoserver/wms
- **WFS :** https://agriweb-prod.ngrok-free.app/geoserver/wfs

## ⚙️ Configuration automatique

L'AgriWeb va automatiquement :
1. ✅ Détecter et utiliser le domaine `agriweb-prod.ngrok-free.app`
2. ✅ Se connecter à votre GeoServer local via ngrok
3. ✅ Afficher les postes sur la carte

## 🔄 Étapes de redémarrage

### **À chaque redémarrage :**
1. **Lancer ngrok :** `cd C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b; .\ngrok.exe http --hostname=agriweb-prod.ngrok-free.app 8080`
2. **Lancer AgriWeb :** Dans VS Code → Task → "Run Flask app (run_app.py)"
3. **Tester :** Faire une recherche sur http://localhost:5000

## 📊 Statut du tunnel

- ✅ **Tunnel actif :** https://agriweb-prod.ngrok-free.app
- ✅ **GeoServer local :** localhost:8080 (accessible)
- ✅ **Commande testée :** `.\ngrok.exe http --hostname=agriweb-prod.ngrok-free.app 8080`

## ⚠️ Important
- **Gardez le terminal PowerShell avec ngrok ouvert** (ne pas fermer)
- **Le tunnel reste actif** tant que la commande tourne
- **Domaine réservé :** agriweb-prod.ngrok-free.app (permanent)
- **Syntaxe correcte :** `--hostname` (pas `--domain`)

---
**🚀 PROCÉDURE VALIDÉE ET FONCTIONNELLE !**
