#!/usr/bin/env python3
"""
Analyse des IPs Railway - Fixe vs Dynamique
Impact critique sur la configuration GeoServer
"""

def explain_railway_ip_behavior():
    """Explique le comportement des IPs Railway"""
    
    print("🌐 IPS RAILWAY - FIXE OU DYNAMIQUE ?")
    print("="*45)
    
    print("\n❌ PAR DÉFAUT: IP DYNAMIQUE")
    print("   • L'IP change à chaque redémarrage/redéploiement")
    print("   • L'IP peut changer spontanément")
    print("   • Impossible à whitelister de manière fiable")
    
    print("\n✅ OPTION PAYANTE: IP STATIQUE")
    print("   • Static Outbound IP addon")
    print("   • Coût: ~5$/mois") 
    print("   • IP fixe garantie")
    print("   • Parfait pour whitelisting GeoServer")

def test_current_situation():
    """Test de la situation actuelle"""
    
    print(f"\n🔍 VOTRE SITUATION ACTUELLE")
    print("="*35)
    
    print(f"\n📊 Configuration GeoServer actuelle:")
    print(f"   • Protection anti-bruteforce: ✅ ACTIVÉE")
    print(f"   • Masques exclus: 127.0.0.1 (localhost seulement)")
    print(f"   • IP Railway: ❓ DYNAMIQUE (change régulièrement)")
    
    print(f"\n🚨 PROBLÈMES IDENTIFIÉS:")
    print(f"   1. IP Railway change → whitelist devient invalide")
    print(f"   2. Railway sera bloqué après changement d'IP")
    print(f"   3. Configuration manuelle répétitive requise")

def show_solutions():
    """Affiche les solutions possibles"""
    
    print(f"\n💡 SOLUTIONS POSSIBLES")
    print("="*25)
    
    print(f"\n🔧 SOLUTION 1: IP STATIQUE RAILWAY (RECOMMANDÉE)")
    print(f"   Avantages:")
    print(f"   ✅ IP fixe, configuration une seule fois")
    print(f"   ✅ Sécurité optimale avec whitelist")
    print(f"   ✅ Pas de blocages inattendus")
    
    print(f"   Inconvénients:")
    print(f"   💰 Coût: 5$/mois")
    
    print(f"   Configuration:")
    print(f"   railway add")
    print(f"   # Choisir 'Static Outbound IP'")
    print(f"   railway variables")
    print(f"   # Noter l'IP statique attribuée")

def show_alternative_solutions():
    """Solutions alternatives"""
    
    print(f"\n🔧 SOLUTION 2: DÉSACTIVER PROTECTION ANTI-BRUTEFORCE")
    print(f"   Avantages:")
    print(f"   ✅ Gratuit, pas de blocages")
    print(f"   ✅ Fonctionne avec IP dynamique")
    
    print(f"   Inconvénients:")
    print(f"   ⚠️ Moins sécurisé")
    print(f"   ⚠️ Vulnérable aux attaques par force brute")
    
    print(f"   Configuration GeoServer:")
    print(f"   Security → Authentication")
    print(f"   Paramètres de prévention des attaques: DÉSACTIVER")
    
    print(f"\n🔧 SOLUTION 3: AUGMENTER LES SEUILS")
    print(f"   Avantages:")
    print(f"   ✅ Gratuit, protection maintenue")
    print(f"   ✅ Plus tolérant aux erreurs")
    
    print(f"   Inconvénients:")
    print(f"   ⚠️ Toujours problématique au changement d'IP")
    
    print(f"   Configuration GeoServer:")
    print(f"   Délai minimum: 1 → 0.1 secondes")
    print(f"   Délai maximum: 5 → 2 secondes")
    print(f"   Nombre max échecs avant blocage: augmenter")

def show_hybrid_solution():
    """Solution hybride recommandée"""
    
    print(f"\n🎯 SOLUTION HYBRIDE RECOMMANDÉE")
    print("="*35)
    
    print(f"\n🔄 PHASE 1: CONFIGURATION IMMÉDIATE (GRATUITE)")
    print(f"   1. Désactiver temporairement la protection anti-bruteforce")
    print(f"   2. Créer l'utilisateur railway_user")
    print(f"   3. Tester que tout fonctionne")
    
    print(f"\n🔄 PHASE 2: SÉCURISATION (PAYANTE)")
    print(f"   1. Activer Static IP Railway (5$/mois)")
    print(f"   2. Réactiver la protection anti-bruteforce")
    print(f"   3. Whitelister l'IP statique Railway")

def create_test_commands():
    """Commandes de test"""
    
    print(f"\n🧪 COMMANDES DE TEST")
    print("="*20)
    
    print(f"\n📍 Tester l'IP actuelle Railway:")
    print(f"   # Après déploiement, visitez:")
    print(f"   https://votre-app.railway.app/debug/my-ip")
    
    print(f"\n📍 Vérifier si Railway a une IP statique:")
    print(f"   railway variables | findstr -i static")
    print(f"   railway variables | findstr -i ip")
    
    print(f"\n📍 Tester l'accès GeoServer depuis Railway:")
    print(f"   # Dans les logs Railway, chercher:")
    print(f"   railway logs | findstr -i geoserver")
    print(f"   railway logs | findstr -i 'auth'")

def cost_benefit_analysis():
    """Analyse coût/bénéfice"""
    
    print(f"\n📊 ANALYSE COÛT/BÉNÉFICE")
    print("="*25)
    
    print(f"\n💰 COÛTS:")
    print(f"   • IP Statique Railway: 5$/mois = 60$/an")
    print(f"   • Temps de debugging: 0h (pas de blocages)")
    print(f"   • Maintenance: minimale")
    
    print(f"\n🔄 VS GRATUIT (IP dynamique):")
    print(f"   • Coût: 0€")
    print(f"   • Temps de debugging: 2-5h/mois (blocages fréquents)")
    print(f"   • Maintenance: surveillance constante requise")
    print(f"   • Risque: service interrompu par blocages")
    
    print(f"\n🎯 RECOMMANDATION:")
    print(f"   Si votre app génère plus de 5€/mois de valeur,")
    print(f"   l'IP statique est rentable (temps = argent)")

def main():
    """Analyse principale"""
    
    explain_railway_ip_behavior()
    test_current_situation()
    show_solutions()
    show_alternative_solutions()
    show_hybrid_solution()
    create_test_commands()
    cost_benefit_analysis()
    
    print(f"\n🚨 RÉPONSE À VOTRE QUESTION:")
    print("="*35)
    print(f"❌ NON, l'IP Railway N'EST PAS fixe par défaut")
    print(f"✅ OUI, vous pouvez la rendre fixe pour 5$/mois")
    print(f"⚠️ SANS IP fixe: blocages GeoServer garantis")
    print(f"💡 SOLUTION IMMÉDIATE: désactiver protection anti-bruteforce")

if __name__ == "__main__":
    main()
