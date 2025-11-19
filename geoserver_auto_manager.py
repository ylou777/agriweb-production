#!/usr/bin/env python3
"""
🚀 AUTO-REDÉPLOYMENT ET MONITORING GEOSERVER
Système automatique de surveillance et redéploiement
"""

import requests
import time
import json
from datetime import datetime, timedelta
import threading

class GeoServerAutoManager:
    def __init__(self):
        self.geoserver_url = "https://geoserver-agriweb-production.up.railway.app"
        self.monitoring_active = False
        self.last_successful_check = None
        self.crash_count = 0
        self.uptime_start = None
        
    def check_health(self):
        """Vérifie la santé de GeoServer"""
        
        endpoints = {
            "tomcat": f"{self.geoserver_url}/",
            "geoserver": f"{self.geoserver_url}/geoserver/web/",
            "rest": f"{self.geoserver_url}/geoserver/rest/"
        }
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "endpoints": {},
            "response_times": {}
        }
        
        healthy_count = 0
        
        for name, url in endpoints.items():
            start_time = time.time()
            try:
                response = requests.get(url, timeout=10)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    health_status["endpoints"][name] = "HEALTHY"
                    health_status["response_times"][name] = f"{response_time}ms"
                    healthy_count += 1
                else:
                    health_status["endpoints"][name] = f"ERROR_{response.status_code}"
                    health_status["response_times"][name] = f"{response_time}ms"
                    
            except requests.exceptions.Timeout:
                health_status["endpoints"][name] = "TIMEOUT"
                health_status["response_times"][name] = ">10000ms"
            except requests.exceptions.ConnectionError:
                health_status["endpoints"][name] = "CONNECTION_REFUSED"
                health_status["response_times"][name] = "N/A"
            except Exception as e:
                health_status["endpoints"][name] = f"ERROR: {str(e)[:30]}"
                health_status["response_times"][name] = "N/A"
        
        # Déterminer le statut global
        if healthy_count == 3:
            health_status["overall_status"] = "HEALTHY"
            self.last_successful_check = datetime.now()
            if not self.uptime_start:
                self.uptime_start = datetime.now()
        elif healthy_count >= 1:
            health_status["overall_status"] = "PARTIAL"
        else:
            health_status["overall_status"] = "DOWN"
            if self.last_successful_check:
                downtime = datetime.now() - self.last_successful_check
                health_status["downtime_duration"] = str(downtime)
        
        return health_status
    
    def log_status(self, status):
        """Log le statut dans un fichier"""
        
        log_entry = {
            "timestamp": status["timestamp"],
            "status": status["overall_status"],
            "endpoints": status["endpoints"],
            "response_times": status["response_times"]
        }
        
        # Affichage console
        timestamp = datetime.now().strftime("%H:%M:%S")
        overall = status["overall_status"]
        
        if overall == "HEALTHY":
            print(f"✅ {timestamp} - GeoServer SAIN")
            if self.uptime_start:
                uptime = datetime.now() - self.uptime_start
                print(f"   ⏱️ Uptime: {uptime}")
        elif overall == "PARTIAL":
            print(f"🟡 {timestamp} - GeoServer PARTIEL")
            for endpoint, state in status["endpoints"].items():
                icon = "✅" if state == "HEALTHY" else "❌"
                print(f"   {icon} {endpoint}: {state}")
        else:
            print(f"🔴 {timestamp} - GeoServer DOWN")
            self.crash_count += 1
            self.uptime_start = None
            
            if "downtime_duration" in status:
                print(f"   ⏱️ Downtime: {status['downtime_duration']}")
            print(f"   📊 Crash count: {self.crash_count}")
    
    def send_keepalive_ping(self):
        """Envoie un ping pour éviter le cold start"""
        
        try:
            response = requests.get(f"{self.geoserver_url}/", timeout=5)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"💓 {timestamp} - Keepalive ping envoyé")
            return True
        except:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"❌ {timestamp} - Keepalive ping échoué")
            return False
    
    def suggest_actions(self, status):
        """Suggère des actions basées sur le statut"""
        
        overall = status["overall_status"]
        
        if overall == "DOWN":
            if self.crash_count >= 3:
                print("🚨 ALERTE: Multiples crashes détectés")
                print("   → Problème persistant, investigation nécessaire")
                print("   → Considérer plan Railway payant")
            else:
                print("💡 SUGGESTION: Redéployer GeoServer")
                print("   → Railway Dashboard > Redeploy")
                print("   → Attendre 10-15 minutes")
        
        elif overall == "PARTIAL":
            tomcat_ok = status["endpoints"].get("tomcat") == "HEALTHY"
            if tomcat_ok:
                print("💡 SUGGESTION: GeoServer encore en démarrage")
                print("   → Attendre 5 minutes supplémentaires")
            else:
                print("💡 SUGGESTION: Problème réseau Railway")
                print("   → Vérifier statut Railway platform")
    
    def start_monitoring(self, interval_minutes=5, keepalive_minutes=15):
        """Démarre le monitoring automatique"""
        
        print("🚀 DÉMARRAGE MONITORING GEOSERVER")
        print("=" * 40)
        print(f"🔍 Vérification toutes les {interval_minutes} minutes")
        print(f"💓 Keepalive toutes les {keepalive_minutes} minutes")
        print("⏹️ Ctrl+C pour arrêter")
        print()
        
        self.monitoring_active = True
        last_keepalive = datetime.now()
        
        try:
            while self.monitoring_active:
                # Vérification santé
                status = self.check_health()
                self.log_status(status)
                self.suggest_actions(status)
                
                # Keepalive si nécessaire
                now = datetime.now()
                if (now - last_keepalive).total_seconds() >= keepalive_minutes * 60:
                    self.send_keepalive_ping()
                    last_keepalive = now
                
                print("-" * 40)
                
                # Attendre l'intervalle
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring arrêté par l'utilisateur")
            self.monitoring_active = False
    
    def quick_diagnosis(self):
        """Diagnostic rapide du statut actuel"""
        
        print("⚡ DIAGNOSTIC RAPIDE GEOSERVER")
        print("=" * 35)
        
        status = self.check_health()
        self.log_status(status)
        
        overall = status["overall_status"]
        
        if overall == "HEALTHY":
            print("\n✅ STATUT: OPÉRATIONNEL")
            print("🎯 Actions recommandées:")
            print("   - Procéder à la création du workspace GPU")
            print("   - Lancer l'importation des couches")
            return True
            
        elif overall == "PARTIAL":
            print("\n🟡 STATUT: EN COURS DE DÉMARRAGE")
            print("🎯 Actions recommandées:")
            print("   - Attendre 5-10 minutes")
            print("   - Relancer ce diagnostic")
            return False
            
        else:
            print("\n🔴 STATUT: HORS SERVICE")
            print("🎯 Actions recommandées:")
            print("   - Redéployer sur Railway")
            print("   - Attendre 15 minutes complètement")
            print("   - Relancer ce diagnostic")
            return False

def main():
    """Menu principal"""
    
    manager = GeoServerAutoManager()
    
    print("🔧 GEOSERVER AUTO-MANAGER")
    print("=" * 25)
    print("1. 🩺 Diagnostic rapide")
    print("2. 📊 Monitoring continu")
    print("3. 💓 Test keepalive")
    print("4. 🔍 Analyse stabilité")
    print()
    
    choice = input("Choisir une option (1-4): ").strip()
    
    if choice == "1":
        print("\n🩺 DIAGNOSTIC RAPIDE")
        print("-" * 20)
        success = manager.quick_diagnosis()
        
        if success:
            print("\n💡 GeoServer opérationnel ! Vous pouvez:")
            print("   - python setup_geoserver_workspace.py")
            print("   - python import_all_layers.py")
        else:
            print("\n⏳ Attendre ou redéployer selon les recommandations")
    
    elif choice == "2":
        print("\n📊 MONITORING CONTINU")
        print("-" * 22)
        manager.start_monitoring()
    
    elif choice == "3":
        print("\n💓 TEST KEEPALIVE")
        print("-" * 16)
        success = manager.send_keepalive_ping()
        if success:
            print("✅ Ping réussi - serveur accessible")
        else:
            print("❌ Ping échoué - serveur inaccessible")
    
    elif choice == "4":
        print("\n🔍 LANCEMENT ANALYSE STABILITÉ")
        print("-" * 32)
        import subprocess
        subprocess.run(["python", "geoserver_stability_analyzer.py"])
    
    else:
        print("❌ Option invalide")

if __name__ == "__main__":
    main()
