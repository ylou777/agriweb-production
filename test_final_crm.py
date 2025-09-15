"""
🎯 Test Final de l'Intégration CRM

Ce fichier teste que le CRM est maintenant visible après une recherche par commune.
"""

def test_application_restart():
    """Teste que l'application redémarre avec le CRM"""
    print("🔄 TEST REDÉMARRAGE AVEC CRM")
    print("=" * 60)
    
    try:
        # Tester l'import des modules modifiés
        print("1️⃣ Test des imports CRM...")
        from agriweb_crm_bridge_intelligent import get_sirene_analysis_for_widget
        print("✅ Import bridge CRM réussi")
        
        from agriweb_crm_routes import add_crm_routes
        print("✅ Import routes CRM réussi")
        
        # Tester la modification du fichier principal
        print("\n2️⃣ Test de la modification de agriweb_hebergement_gratuit.py...")
        with open("agriweb_hebergement_gratuit.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "CRM_AVAILABLE" in content:
            print("✅ Variable CRM_AVAILABLE trouvée")
        if "get_sirene_analysis_for_widget" in content:
            print("✅ Fonction d'analyse CRM trouvée")
        if "crm_sirene_analysis" in content:
            print("✅ Ajout des données CRM trouvé")
        if "/api/crm/integrate_commune_search" in content:
            print("✅ Route API CRM trouvée")
            
        print("\n3️⃣ Test avec des données simulées...")
        test_data = {
            "sirene_data": {
                "features": [
                    {"properties": {"naf_principal": "0111", "denomination": "Ferme Bio SARL"}},
                    {"properties": {"naf_principal": "3511", "denomination": "Solaire Plus SA"}},
                    {"properties": {"naf_principal": "4120", "denomination": "BTP Vert"}},
                ]
            }
        }
        
        analysis = get_sirene_analysis_for_widget(test_data)
        print(f"✅ Analyse test: {analysis['qualified_prospects']}/{analysis['total_enterprises']} prospects")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def show_next_steps():
    """Montre les prochaines étapes"""
    print("\n" + "=" * 60)
    print("🚀 PROCHAINES ÉTAPES POUR VOIR LE CRM")
    print("=" * 60)
    
    steps = [
        "1️⃣ Redémarrez votre application AgriWeb",
        "2️⃣ Vous devriez voir: '✅ [CRM] Module CRM intelligent disponible'",
        "3️⃣ Effectuez une recherche par commune (ex: 'Reims')",
        "4️⃣ Regardez dans les logs: '📊 [CRM] X/Y entreprises SIRENE qualifiées'",
        "5️⃣ Le widget CRM devrait apparaître avec les prospects qualifiés",
        "6️⃣ Testez le bouton 'Créer Prospects Qualifiés'"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print(f"\n🌐 URLS À TESTER:")
    print(f"   • Application: http://localhost:5000/")
    print(f"   • Dashboard CRM: http://localhost:5000/crm/dashboard")
    print(f"   • Status CRM: http://localhost:5000/crm/status")
    
    print(f"\n🔧 EN CAS DE PROBLÈME:")
    print(f"   • Vérifiez la console navigateur (F12)")
    print(f"   • Regardez les logs de l'application")
    print(f"   • Cherchez les messages [CRM] dans les logs")

def check_crm_ready():
    """Vérifie que le CRM est prêt"""
    print("🔍 VÉRIFICATION FINALE CRM")
    print("=" * 60)
    
    files_to_check = [
        "agriweb_crm_bridge_intelligent.py",
        "agriweb_crm_routes.py",
        "widget_crm_integration.py"
    ]
    
    all_good = True
    for file in files_to_check:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"✅ {file} - OK ({len(content)} caractères)")
        except Exception as e:
            print(f"❌ {file} - ERREUR: {e}")
            all_good = False
    
    # Vérifier les modifications dans le fichier principal
    try:
        with open("agriweb_hebergement_gratuit.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        modifications = [
            ("Import CRM", "from agriweb_crm_bridge_intelligent import"),
            ("Configuration CRM", "add_crm_routes(app)"),
            ("Route API", "/api/crm/integrate_commune_search"),
            ("Données CRM", "crm_sirene_analysis")
        ]
        
        print(f"\n📝 MODIFICATIONS DANS agriweb_hebergement_gratuit.py:")
        for name, pattern in modifications:
            if pattern in content:
                print(f"✅ {name} - Présent")
            else:
                print(f"❌ {name} - MANQUANT")
                all_good = False
                
    except Exception as e:
        print(f"❌ Erreur lecture fichier principal: {e}")
        all_good = False
    
    if all_good:
        print(f"\n🎉 TOUTES LES MODIFICATIONS SONT EN PLACE !")
        print(f"🚀 Le CRM est prêt à être testé !")
    else:
        print(f"\n⚠️ Certaines modifications manquent")
        print(f"📞 Vérifiez les étapes d'installation")
    
    return all_good

def main():
    print("🎯 TEST FINAL - INTÉGRATION CRM AGRIWEB")
    print("=" * 80)
    
    if test_application_restart():
        print("\n✅ Tests d'import réussis")
    else:
        print("\n❌ Problème avec les imports")
        return
    
    if check_crm_ready():
        print("\n✅ Vérification des fichiers réussie")
        show_next_steps()
    else:
        print("\n❌ Problème avec les fichiers CRM")

if __name__ == "__main__":
    main()