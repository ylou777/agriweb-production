#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage du token de vérification pour ylaurent.perso@gmail.com
Résout le problème de "Token de vérification invalide ou expiré"
"""

import urllib.request
import urllib.parse
import json
import time

def clean_ylaurent_token():
    """Nettoie le token de vérification résiduel pour ylaurent.perso@gmail.com"""
    
    print("🔧 NETTOYAGE DU TOKEN DE VÉRIFICATION")
    print("=====================================")
    print()
    
    # 1. Vérifier l'état actuel
    print("1. Vérification de l'état actuel...")
    try:
        url = "https://ample-manifestation-production-7b1a.up.railway.app/debug/database"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        ylaurent_user = None
        for user in data.get('users', []):
            if user['email'] == 'ylaurent.perso@gmail.com':
                ylaurent_user = user
                break
        
        if not ylaurent_user:
            print("❌ Compte ylaurent.perso@gmail.com non trouvé")
            return False
            
        print(f"✅ Compte trouvé (ID: {ylaurent_user.get('id')})")
        print(f"   Vérifié: {ylaurent_user.get('verified')}")
        print(f"   Token présent: {ylaurent_user.get('has_token')}")
        print(f"   Statut: {ylaurent_user.get('status')}")
        print()
        
        # Si pas de token, pas besoin de nettoyer
        if not ylaurent_user.get('has_token'):
            print("✅ Aucun token résiduel trouvé. Le compte devrait fonctionner.")
            print("💡 Essayez de vous connecter directement sur:")
            print("   https://ample-manifestation-production-7b1a.up.railway.app/auth/login")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    # 2. Tenter le nettoyage via réinitialisation de mot de passe
    print("2. Nettoyage via réinitialisation de mot de passe...")
    try:
        reset_url = "https://ample-manifestation-production-7b1a.up.railway.app/auth/reset-password"
        data = {'email': 'ylaurent.perso@gmail.com'}
        
        post_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(reset_url, data=post_data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            result = response.read().decode('utf-8')
            
        if 'envoyé' in result.lower() or 'success' in result.lower():
            print("✅ Email de réinitialisation envoyé!")
            print("📧 Vérifiez votre boîte mail ylaurent.perso@gmail.com")
            print("🔗 Cliquez sur le lien dans l'email pour définir un nouveau mot de passe")
            print()
            print("📋 ÉTAPES SUIVANTES:")
            print("   1. Ouvrez votre email ylaurent.perso@gmail.com")
            print("   2. Cherchez l'email 'Réinitialisation de votre mot de passe AgriWeb'")
            print("   3. Cliquez sur le bouton 'Réinitialiser mon mot de passe'")
            print("   4. Définissez un nouveau mot de passe")
            print("   5. Connectez-vous avec le nouveau mot de passe")
            return True
        else:
            print("❌ Erreur lors de l'envoi de l'email de réinitialisation")
            print("📄 Réponse:", result[:200] + "...")
            return False
            
    except urllib.error.HTTPError as e:
        print(f"❌ Erreur HTTP: {e.code}")
        try:
            error_data = e.read().decode('utf-8')
            print(f"   Détails: {error_data[:200]}")
        except:
            pass
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 RÉSOLUTION DU PROBLÈME D'AUTHENTIFICATION")
    print("============================================")
    print("Compte: ylaurent.perso@gmail.com")
    print("Problème: Token de vérification invalide ou expiré")
    print()
    
    success = clean_ylaurent_token()
    
    print()
    print("=" * 50)
    if success:
        print("✅ SUCCÈS! Le problème devrait être résolu.")
        print()
        print("🚀 CONNEXION:")
        print("   URL: https://ample-manifestation-production-7b1a.up.railway.app/auth/login")
        print("   Email: ylaurent.perso@gmail.com")
        print("   Mot de passe: [nouveau mot de passe défini via email]")
    else:
        print("❌ ÉCHEC. Veuillez contacter le support.")
        print()
        print("🔄 ALTERNATIVES:")
        print("   1. Créer un nouveau compte avec un autre email")
        print("   2. Utiliser le compte admin pour tester:")
        print("      Email: admin@test.com")
        print("      Mot de passe: admin123")

if __name__ == "__main__":
    main()
