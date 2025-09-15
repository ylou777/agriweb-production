#!/usr/bin/env python3
"""
Test simple de l'analyse SIRENE CRM
"""

def test_crm_integration():
    try:
        print("🔍 Test import CRM modules...")
        from agriweb_crm_bridge_intelligent import get_sirene_analysis_for_widget
        print("✅ Import get_sirene_analysis_for_widget OK")
        
        # Test avec données factices
        print("🧪 Test avec données factices...")
        fake_response_data = {
            "sirene_data": {
                "features": [
                    {
                        "properties": {
                            "activitePrincipale": "4711F",
                            "denominationSociale": "Test Enterprise 1",
                            "siret": "12345678901234"
                        }
                    },
                    {
                        "properties": {
                            "activitePrincipale": "6420Z",
                            "denominationSociale": "Test Bank",
                            "siret": "98765432109876"
                        }
                    }
                ]
            }
        }
        
        analysis = get_sirene_analysis_for_widget(fake_response_data)
        print(f"✅ Analyse SIRENE OK: {analysis}")
        
        print("🎯 TEST CRM RÉUSSI!")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR CRM: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_crm_integration()