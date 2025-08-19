#!/usr/bin/env python3
"""
🔧 DIAGNOSTIC ET REDÉPLOIEMENT GEOSERVER
Analyse des causes d'instabilité et redéploiement automatique
"""

import requests
import time
import json
from datetime import datetime

class GeoServerStabilityAnalyzer:
    def __init__(self):
        self.geoserver_url = "https://geoserver-agriweb-production.up.railway.app"
        self.tomcat_url = f"{self.geoserver_url}/"
        self.geoserver_admin_url = f"{self.geoserver_url}/geoserver/web/"
        self.rest_api_url = f"{self.geoserver_url}/geoserver/rest/"
    
    def analyze_crash_causes(self):
        """Analyse les causes potentielles de crash"""
        
        print("🔍 ANALYSE DES CAUSES D'INSTABILITÉ GEOSERVER")
        print("=" * 55)
        print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        causes_probables = {
            "💾 Mémoire insuffisante": {
                "description": "GeoServer Java nécessite beaucoup de RAM",
                "solution": "Railway gratuit limite à 512MB-1GB",
                "severity": "HIGH"
            },
            "⏱️ Timeout Railway": {
                "description": "Railway peut redémarrer après inactivité",
                "solution": "Ping automatique toutes les 10-15min",
                "severity": "MEDIUM"
            },
            "🔄 Cold Start": {
                "description": "GeoServer + Tomcat = démarrage lent",
                "solution": "Attendre 5-10min complètement",
                "severity": "MEDIUM"
            },
            "📦 Ressources limitées": {
                "description": "CPU/IO limités sur plan gratuit",
                "solution": "Optimiser configuration GeoServer",
                "severity": "HIGH"
            },
            "🌐 Réseau instable": {
                "description": "Connexions perdues côté Railway",
                "solution": "Retry automatique + monitoring",
                "severity": "LOW"
            }
        }
        
        print("🚨 CAUSES PROBABLES D'INSTABILITÉ :")
        print("-" * 35)
        
        for cause, details in causes_probables.items():
            severity_icon = "🔴" if details["severity"] == "HIGH" else "🟡" if details["severity"] == "MEDIUM" else "🟢"
            print(f"{severity_icon} {cause}")
            print(f"   📝 {details['description']}")
            print(f"   💡 {details['solution']}")
            print()
        
        return causes_probables
    
    def test_current_status(self):
        """Teste l'état actuel de GeoServer"""
        
        print("📊 TEST DE L'ÉTAT ACTUEL")
        print("-" * 25)
        
        tests = {
            "🏠 Tomcat Base": self.tomcat_url,
            "🌐 GeoServer Admin": self.geoserver_admin_url,
            "🔧 REST API": self.rest_api_url,
        }
        
        results = {}
        
        for name, url in tests.items():
            try:
                print(f"Testing {name}...")
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    print(f"✅ {name}: OK")
                    results[name] = "OK"
                else:
                    print(f"❌ {name}: Status {response.status_code}")
                    results[name] = f"ERROR_{response.status_code}"
                    
            except requests.exceptions.ConnectTimeout:
                print(f"⏰ {name}: Timeout")
                results[name] = "TIMEOUT"
            except requests.exceptions.ConnectionError:
                print(f"🔌 {name}: Connexion refusée")
                results[name] = "CONNECTION_REFUSED"
            except Exception as e:
                print(f"❌ {name}: {str(e)[:50]}")
                results[name] = "ERROR"
        
        return results
    
    def recommend_solutions(self, test_results):
        """Recommande des solutions basées sur les tests"""
        
        print("\n💡 RECOMMANDATIONS")
        print("-" * 18)
        
        all_failed = all(status != "OK" for status in test_results.values())
        tomcat_ok = test_results.get("🏠 Tomcat Base") == "OK"
        geoserver_failed = test_results.get("🌐 GeoServer Admin") != "OK"
        
        if all_failed:
            print("🔴 CRASH COMPLET DÉTECTÉ")
            print("   → Redéploiement Railway nécessaire")
            print("   → Attendre 10-15 minutes après redéploiement")
            return "FULL_REDEPLOY"
            
        elif tomcat_ok and geoserver_failed:
            print("🟡 TOMCAT OK, GEOSERVER DÉFAILLANT")
            print("   → GeoServer peut encore démarrer")
            print("   → Attendre 5 minutes supplémentaires")
            return "WAIT_GEOSERVER"
            
        elif tomcat_ok:
            print("✅ SYSTÈME PARTIELLEMENT FONCTIONNEL")
            print("   → Continuer les tests périodiques")
            return "MONITOR"
        
        else:
            print("🔴 PROBLÈME RÉSEAU OU PLATFORM")
            print("   → Vérifier statut Railway")
            return "CHECK_PLATFORM"
    
    def create_monitoring_schedule(self):
        """Crée un plan de monitoring"""
        
        print("\n📅 PLAN DE MONITORING RECOMMANDÉ")
        print("-" * 32)
        
        schedule = {
            "🔄 Test toutes les 5 min": "Vérification basique disponibilité",
            "💓 Ping toutes les 15 min": "Éviter cold start Railway",
            "🔍 Diagnostic quotidien": "Analyse complète stabilité",
            "📊 Log des crashs": "Historique pour identifier patterns"
        }
        
        for action, description in schedule.items():
            print(f"{action}: {description}")
        
        return schedule

def main():
    """Fonction principale d'analyse"""
    
    analyzer = GeoServerStabilityAnalyzer()
    
    # 1. Analyse des causes
    causes = analyzer.analyze_crash_causes()
    
    # 2. Test de l'état actuel
    results = analyzer.test_current_status()
    
    # 3. Recommandations
    recommendation = analyzer.recommend_solutions(results)
    
    # 4. Plan de monitoring
    schedule = analyzer.create_monitoring_schedule()
    
    print("\n" + "=" * 55)
    print("📋 RÉSUMÉ EXÉCUTIF")
    print("=" * 15)
    
    print(f"🎯 Diagnostic: {recommendation}")
    
    if recommendation == "FULL_REDEPLOY":
        print("\n🚀 ACTIONS IMMÉDIATES RECOMMANDÉES :")
        print("1. 🔄 Redéployer GeoServer sur Railway")
        print("2. ⏱️ Attendre 10-15 minutes complètement")
        print("3. 🔍 Tester uniquement Tomcat d'abord")
        print("4. ⏳ Puis tester GeoServer admin après 5min")
        print("5. 📱 Mettre en place monitoring automatique")
        
    elif recommendation == "WAIT_GEOSERVER":
        print("\n⏳ ACTIONS RECOMMANDÉES :")
        print("1. ⏱️ Attendre 5-10 minutes")
        print("2. 🔄 Relancer ce diagnostic")
        print("3. 🚫 Ne pas redéployer pour l'instant")
        
    elif recommendation == "MONITOR":
        print("\n✅ SYSTÈME STABLE")
        print("1. 📊 Continuer monitoring régulier")
        print("2. 🎯 Procéder à la création workspace")
        
    print("\n💡 OPTIMISATIONS LONG TERME :")
    print("- 📦 Utiliser images GeoServer plus légères")
    print("- ⚙️ Optimiser configuration JVM")
    print("- 🔄 Automatiser redéploiement en cas de crash")
    print("- 📈 Considérer plan Railway payant pour stabilité")

if __name__ == "__main__":
    main()
