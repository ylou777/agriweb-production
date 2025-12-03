"""
Vérifier que le template crm.html contient la colonne Propriétaire
"""
import os

template_path = os.path.join(os.path.dirname(__file__), 'templates', 'crm.html')

print(f"📁 Vérification de: {template_path}")
print(f"✅ Fichier existe: {os.path.exists(template_path)}")

if os.path.exists(template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher les modifications
    has_column_header = '<th>Propriétaire</th>' in content
    has_proprietaire_siren = 'proprietaire_siren' in content
    has_proprietaire_denomination = 'proprietaire_denomination' in content
    
    print(f"✅ Colonne header 'Propriétaire': {has_column_header}")
    print(f"✅ Variable 'proprietaire_siren': {has_proprietaire_siren}")
    print(f"✅ Variable 'proprietaire_denomination': {has_proprietaire_denomination}")
    
    # Compter les occurrences
    count_siren = content.count('proprietaire_siren')
    count_denomination = content.count('proprietaire_denomination')
    
    print(f"\n📊 Statistiques:")
    print(f"   - 'proprietaire_siren' apparaît {count_siren} fois")
    print(f"   - 'proprietaire_denomination' apparaît {count_denomination} fois")
    
    if has_column_header and has_proprietaire_siren:
        print("\n🎉 Template correctement modifié!")
    else:
        print("\n⚠️ Template incomplet!")
else:
    print("❌ Fichier non trouvé!")
