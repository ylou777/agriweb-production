"""Script pour corriger l'espacement des étiquettes dans plan_masse_generator.py"""

# Lire le fichier
with open('plan_masse_generator.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

# Modifications ligne par ligne
output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Modifier max_attempts
    if 'max_attempts=8)' in line:
        line = line.replace('max_attempts=8)', 'max_attempts=16)')
    
    # Modifier les offsets
    if 'offsets = [' in line and i < len(lines) - 10:
        # Remplacer tout le bloc offsets
        output_lines.append(line)  # offsets = [
        output_lines.append('            (0, 0),             # Position originale\n')
        output_lines.append('            (2*cm, 0),          # Décalé droite\n')
        output_lines.append('            (-2*cm, 0),         # Décalé gauche\n')
        output_lines.append('            (0, 2*cm),          # Décalé haut\n')
        output_lines.append('            (0, -2*cm),         # Décalé bas\n')
        output_lines.append('            (2*cm, 2*cm),       # Décalé haut-droite\n')
        output_lines.append('            (-2*cm, 2*cm),      # Décalé haut-gauche\n')
        output_lines.append('            (2*cm, -2*cm),      # Décalé bas-droite\n')
        output_lines.append('            (-2*cm, -2*cm),     # Décalé bas-gauche\n')
        output_lines.append('            (4*cm, 0),          # Décalé droite (large)\n')
        output_lines.append('            (-4*cm, 0),         # Décalé gauche (large)\n')
        output_lines.append('            (0, 4*cm),          # Décalé haut (large)\n')
        output_lines.append('            (0, -4*cm),         # Décalé bas (large)\n')
        output_lines.append('            (3*cm, 3*cm),       # Diagonale haut-droite\n')
        output_lines.append('            (-3*cm, 3*cm),      # Diagonale haut-gauche\n')
        output_lines.append('            (3*cm, -3*cm),      # Diagonale bas-droite\n')
        output_lines.append('        ]\n')
        # Sauter les anciennes lignes
        i += 1
        while i < len(lines) and ']' not in lines[i]:
            i += 1
        i += 1
        continue
    
    # Ajouter réinitialisation LabelManager
    if 'c = canvas.Canvas(buffer, pagesize=A3)' in line:
        output_lines.append(line)
        i += 1
        # Ajouter ligne vide si elle existe
        if i < len(lines) and lines[i].strip() == '':
            output_lines.append(lines[i])
            i += 1
        # Ajouter réinitialisation avant le commentaire En-tête
        output_lines.append('        # Réinitialiser le gestionnaire d\'étiquettes\n')
        output_lines.append('        self.label_manager = LabelManager()\n')
        output_lines.append('        \n')
        continue
    
    output_lines.append(line)
    i += 1

# Écrire le fichier modifié
with open('plan_masse_generator.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print('✓ Fichier modifié avec succès:')
print('  - max_attempts augmenté de 8 à 16')
print('  - Espacements augmentés (2cm, 3cm, 4cm au lieu de 0.5cm, 1cm)')
print('  - Réinitialisation de LabelManager à chaque génération ajoutée')
