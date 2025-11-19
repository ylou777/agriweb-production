# 🚀 Guide de configuration ngrok Pay-as-you-go

## Étape 1: Créer un domaine permanent
1. Allez sur : https://dashboard.ngrok.com/domains
2. Cliquez sur "Create Domain"
3. Choisissez un nom (ex: agriweb-geoserver)
4. Votre domaine sera : VOTRE-NOM.ngrok-free.app

## Étape 2: Lancer ngrok avec votre domaine
Une fois le domaine créé, utilisez cette commande :
```
ngrok http --domain=VOTRE-DOMAINE.ngrok-free.app 8080
```

## Étape 3: Mettre à jour Railway
Mettez à jour la variable d'environnement Railway :
```
GEOSERVER_URL=https://VOTRE-DOMAINE.ngrok-free.app/geoserver
```

## Domaines suggérés :
- agriweb-geoserver.ngrok-free.app
- geoserver-agriweb.ngrok-free.app
- mon-geoserver.ngrok-free.app

## Note importante :
Une fois créé, le domaine est permanent et ne changera plus !
