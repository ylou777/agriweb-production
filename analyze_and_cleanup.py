#!/usr/bin/env python3
"""
Script de nettoyage intelligent du workspace AgriWeb
Analyse les fichiers et propose une suppression sécurisée des fichiers inutiles
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

class AgriWebCleaner:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.analysis_results = {
            'essential_files': set(),
            'active_files': set(),
            'backup_files': set(),
            'debug_files': set(),
            'test_files': set(),
            'obsolete_files': set(),
            'config_files': set(),
            'docker_files': set(),
            'documentation_files': set(),
            'temporary_files': set(),
            'unknown_files': set()
        }
        
        # Fichiers absolument essentiels à préserver
        self.essential_patterns = {
            'run_app.py',
            'agriweb_hebergement_gratuit.py',  # Fichier principal actuel
            'requirements.txt',
            'config.py',
            '.env',
            '.env.example',
            '.gitignore',
            'README.md',
            'main.py',
            'models.py'
        }
        
        # Patterns pour identifier les types de fichiers
        self.file_patterns = {
            'backup': [
                r'.*_BACKUP_\d+.*',
                r'backup_\d+.*',
                r'.*\.backup$',
                r'.*_backup\.py$',
                r'.*_original\.py$'
            ],
            'debug': [
                r'debug_.*\.py$',
                r'.*_debug\.py$',
                r'diagnostic_.*\.py$',
                r'test_debug.*\.py$'
            ],
            'test': [
                r'test_.*\.py$',
                r'.*_test\.py$',
                r'test\.py$',
                r'.*test.*\.html$',
                r'.*test.*\.json$'
            ],
            'obsolete': [
                r'agriweb_.*\.py$',  # Anciennes versions sauf le principal
                r'serveur_.*\.py$',
                r'.*_old\.py$',
                r'.*_deprecated\.py$',
                r'temp_.*',
                r'.*\.tmp$'
            ],
            'docker': [
                r'Dockerfile.*',
                r'.*\.dockerignore$',
                r'docker-compose.*'
            ],
            'config': [
                r'.*\.yml$',
                r'.*\.yaml$',
                r'.*\.toml$',
                r'.*\.json$',
                r'.*\.env.*',
                r'railway.*',
                r'ngrok.*',
                r'.*config.*\.py$'
            ],
            'documentation': [
                r'.*\.md$',
                r'.*\.txt$',
                r'GUIDE_.*',
                r'README.*',
                r'.*_GUIDE\.md$',
                r'INSTRUCTIONS.*'
            ],
            'temporary': [
                r'.*\.log$',
                r'.*\.cache$',
                r'.*\.pid$',
                r'error\.log',
                r'__pycache__',
                r'\.pytest_cache',
                r'\.tmp\..*'
            ]
        }

    def analyze_files(self) -> Dict[str, Set[str]]:
        """Analyse tous les fichiers du workspace et les catégorise"""
        print("🔍 Analyse des fichiers en cours...")
        
        for item in self.workspace_path.rglob('*'):
            if item.is_file():
                self._categorize_file(item)
        
        # Post-traitement : vérifier les dépendances
        self._check_dependencies()
        
        return self.analysis_results

    def _categorize_file(self, file_path: Path):
        """Catégorise un fichier selon ses caractéristiques"""
        relative_path = str(file_path.relative_to(self.workspace_path))
        filename = file_path.name
        
        # Fichiers essentiels (à préserver absolument)
        if filename in self.essential_patterns:
            self.analysis_results['essential_files'].add(relative_path)
            return
        
        # Vérifier les patterns par catégorie
        categorized = False
        
        for category, patterns in self.file_patterns.items():
            for pattern in patterns:
                if re.match(pattern, filename, re.IGNORECASE):
                    self.analysis_results[f'{category}_files'].add(relative_path)
                    categorized = True
                    break
            if categorized:
                break
        
        # Cas spéciaux
        if not categorized:
            if self._is_active_file(file_path):
                self.analysis_results['active_files'].add(relative_path)
            else:
                self.analysis_results['unknown_files'].add(relative_path)

    def _is_active_file(self, file_path: Path) -> bool:
        """Détermine si un fichier est activement utilisé"""
        # Fichiers dans des dossiers actifs
        active_dirs = {'static', 'templates', 'modules', 'utils', 'scripts', 'tools'}
        if any(part in active_dirs for part in file_path.parts):
            return True
        
        # Extensions de fichiers actifs
        active_extensions = {'.py', '.html', '.css', '.js', '.png', '.jpg', '.json'}
        if file_path.suffix.lower() in active_extensions:
            # Vérifier si ce n'est pas un fichier de test ou debug
            filename = file_path.name.lower()
            if not any(keyword in filename for keyword in ['test', 'debug', 'backup', 'old']):
                return True
        
        return False

    def _check_dependencies(self):
        """Vérifie les dépendances entre fichiers pour éviter de supprimer des fichiers importés"""
        print("🔗 Vérification des dépendances...")
        
        # Lire les imports du fichier principal
        main_file = self.workspace_path / 'agriweb_hebergement_gratuit.py'
        if main_file.exists():
            imports = self._extract_imports(main_file)
            for imp in imports:
                # Chercher le fichier correspondant
                potential_file = f"{imp}.py"
                if potential_file in [f for files in self.analysis_results.values() for f in files]:
                    # Déplacer vers active_files si trouvé dans obsolete
                    for category in ['obsolete_files', 'unknown_files']:
                        if potential_file in self.analysis_results[category]:
                            self.analysis_results[category].discard(potential_file)
                            self.analysis_results['active_files'].add(potential_file)

    def _extract_imports(self, file_path: Path) -> List[str]:
        """Extrait les imports d'un fichier Python"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Rechercher les imports locaux
                import_patterns = [
                    r'from\s+(\w+)\s+import',
                    r'import\s+(\w+)',
                ]
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    imports.extend(matches)
        except Exception as e:
            print(f"⚠️ Erreur lecture {file_path}: {e}")
        
        return imports

    def generate_report(self) -> str:
        """Génère un rapport détaillé de l'analyse"""
        report = []
        report.append("📊 RAPPORT D'ANALYSE DU WORKSPACE AGRIWEB")
        report.append("=" * 50)
        report.append(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_files = sum(len(files) for files in self.analysis_results.values())
        report.append(f"📁 Total des fichiers analysés: {total_files}")
        report.append("")
        
        for category, files in self.analysis_results.items():
            if files:
                category_name = category.replace('_', ' ').title()
                report.append(f"📂 {category_name}: {len(files)} fichiers")
                
                # Afficher quelques exemples
                examples = list(files)[:5]
                for example in examples:
                    report.append(f"   • {example}")
                if len(files) > 5:
                    report.append(f"   ... et {len(files) - 5} autres")
                report.append("")
        
        return "\n".join(report)

    def get_safe_to_delete(self) -> Set[str]:
        """Retourne la liste des fichiers sûrs à supprimer"""
        safe_to_delete = set()
        
        # Catégories considérées comme sûres à supprimer
        safe_categories = [
            'backup_files',
            'debug_files', 
            'test_files',
            'temporary_files'
        ]
        
        for category in safe_categories:
            safe_to_delete.update(self.analysis_results[category])
        
        # Ajouter certains fichiers obsolètes après vérification
        obsolete_safe = set()
        for file in self.analysis_results['obsolete_files']:
            # Ne pas supprimer le fichier principal ni les fichiers actifs
            if file != 'agriweb_hebergement_gratuit.py' and file not in self.analysis_results['active_files']:
                obsolete_safe.add(file)
        
        safe_to_delete.update(obsolete_safe)
        
        return safe_to_delete

    def suggest_cleanup(self) -> Dict[str, List[str]]:
        """Suggère un plan de nettoyage par phases"""
        cleanup_plan = {
            'phase_1_safe': [],      # Suppression immédiate sûre
            'phase_2_review': [],    # À réviser manuellement
            'phase_3_keep': []       # À conserver
        }
        
        # Phase 1: Suppression immédiate sûre
        safe_files = self.get_safe_to_delete()
        cleanup_plan['phase_1_safe'] = list(safe_files)
        
        # Phase 2: À réviser
        review_categories = ['obsolete_files', 'docker_files', 'unknown_files']
        for category in review_categories:
            for file in self.analysis_results[category]:
                if file not in safe_files:
                    cleanup_plan['phase_2_review'].append(file)
        
        # Phase 3: À conserver
        keep_categories = ['essential_files', 'active_files', 'config_files']
        for category in keep_categories:
            cleanup_plan['phase_3_keep'].extend(self.analysis_results[category])
        
        return cleanup_plan

def main():
    workspace_path = r"c:\Users\Utilisateur\Desktop\AG32.1\ag3reprise\AgW3b"
    
    cleaner = AgriWebCleaner(workspace_path)
    
    # Analyser les fichiers
    results = cleaner.analyze_files()
    
    # Générer le rapport
    report = cleaner.generate_report()
    print(report)
    
    # Générer le plan de nettoyage
    cleanup_plan = cleaner.suggest_cleanup()
    
    print("\n" + "="*50)
    print("🧹 PLAN DE NETTOYAGE SUGGÉRÉ")
    print("="*50)
    
    print(f"\n✅ PHASE 1 - Suppression immédiate sûre ({len(cleanup_plan['phase_1_safe'])} fichiers):")
    for file in cleanup_plan['phase_1_safe'][:10]:  # Afficher les 10 premiers
        print(f"   🗑️ {file}")
    if len(cleanup_plan['phase_1_safe']) > 10:
        print(f"   ... et {len(cleanup_plan['phase_1_safe']) - 10} autres")
    
    print(f"\n⚠️ PHASE 2 - À réviser manuellement ({len(cleanup_plan['phase_2_review'])} fichiers):")
    for file in cleanup_plan['phase_2_review'][:5]:
        print(f"   ❓ {file}")
    if len(cleanup_plan['phase_2_review']) > 5:
        print(f"   ... et {len(cleanup_plan['phase_2_review']) - 5} autres")
    
    print(f"\n🔒 PHASE 3 - À conserver absolument ({len(cleanup_plan['phase_3_keep'])} fichiers)")
    
    # Sauvegarder le rapport
    report_file = Path(workspace_path) / 'cleanup_analysis_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
        f.write("\n\n" + "="*50)
        f.write("\n🧹 PLAN DE NETTOYAGE DÉTAILLÉ")
        f.write("\n" + "="*50)
        
        for phase, files in cleanup_plan.items():
            f.write(f"\n\n{phase.upper()}:\n")
            for file in files:
                f.write(f"  - {file}\n")
    
    print(f"\n📋 Rapport détaillé sauvegardé: {report_file}")
    
    return cleanup_plan

if __name__ == "__main__":
    cleanup_plan = main()