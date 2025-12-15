"""
Générateur de plans de strings détaillés par zone
Un plan technique par champ PV avec tracé exact des strings
"""

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from datetime import datetime
import math

class PlansStrings:
    """Générateur de plans techniques de strings par zone"""
    
    def __init__(self, calpinage_data, prospect_data):
        self.calpinage = calpinage_data
        self.prospect = prospect_data
        self.zones = calpinage_data.get('zones', [])
        self.module = calpinage_data.get('module', {})
        self.config_elec = calpinage_data.get('configuration_electrique', {})
        
        # Dimensions module (en mètres)
        self.module_longueur = float(self.module.get('longueur', 2.278))  # m
        self.module_largeur = float(self.module.get('largeur', 1.134))  # m
        
    def generer_plans_pdf(self, output_path=None):
        """Génère le PDF complet avec un plan par zone"""
        
        if output_path is None:
            output_path = f"plans_strings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Format A3 paysage pour avoir de l'espace
        page_width, page_height = landscape(A3)
        
        c = canvas.Canvas(output_path, pagesize=landscape(A3))
        
        # Page de garde
        self._page_garde(c, page_width, page_height)
        c.showPage()
        
        # Une page par zone
        for zone in self.zones:
            self._plan_zone(c, zone, page_width, page_height)
            c.showPage()
        
        c.save()
        print(f"✅ Plans de strings générés: {output_path}")
        return output_path
    
    def _page_garde(self, c, width, height):
        """Page de garde du document"""
        
        # Cadre
        c.setStrokeColor(colors.HexColor('#003d7a'))
        c.setLineWidth(2)
        c.rect(1*cm, 1*cm, width - 2*cm, height - 2*cm)
        
        # Titre
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.HexColor('#003d7a'))
        c.drawCentredString(width/2, height - 5*cm, "PLANS DE CÂBLAGE DC - STRINGS")
        
        c.setFont("Helvetica", 16)
        c.setFillColor(colors.black)
        c.drawCentredString(width/2, height - 6.5*cm, "Installation Photovoltaïque")
        
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor('#2ecc71'))
        c.drawCentredString(width/2, height - 7.5*cm, "🔌 Parcours optimisé en serpentin pour minimiser les câbles DC")
        
        # Informations client
        y = height - 10*cm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(5*cm, y, "CLIENT:")
        c.setFont("Helvetica", 11)
        c.drawString(5*cm, y - 0.6*cm, f"{self.prospect.get('nom', '')} {self.prospect.get('prenom', '')}")
        c.drawString(5*cm, y - 1.2*cm, f"{self.prospect.get('adresse', '')}")
        c.drawString(5*cm, y - 1.8*cm, f"{self.prospect.get('commune', '')}")
        
        # Caractéristiques installation
        y = height - 15*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(5*cm, y, "CARACTÉRISTIQUES INSTALLATION:")
        
        nb_zones = len(self.zones)
        nb_modules_total = sum(z.get('nbModules', 0) for z in self.zones)
        puissance_totale = nb_modules_total * float(self.module.get('puissance', 550)) / 1000
        
        # Calculer longueur totale câbles optimisée
        longueur_cable_total = 0.0
        for zone in self.zones:
            strings_config = self._calculer_strings_zone(zone)
            for string in strings_config:
                longueur_cable_total += string['longueur_cable']
        
        info_data = [
            ['Nombre de zones:', str(nb_zones)],
            ['Nombre total de modules:', str(nb_modules_total)],
            ['Puissance unitaire module:', f"{self.module.get('puissance', 550)} Wc"],
            ['Puissance totale:', f"{puissance_totale:.2f} kWc"],
            ['Tension Voc module:', f"{self.module.get('voc', 49.5)} V"],
            ['Tension Vmpp module:', f"{self.module.get('vmpp', 41.8)} V"],
            ['Courant Isc module:', f"{self.module.get('isc', 13.9)} A"],
            ['Section câble strings:', f"{self.config_elec.get('section_cable_strings', 6)} mm²"],
            ['🎯 Câble DC total optimisé:', f"{longueur_cable_total:.1f} m"],
        ]
        
        y_info = y - 1*cm
        for label, value in info_data:
            c.setFont("Helvetica", 10)
            c.drawString(6*cm, y_info, label)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(15*cm, y_info, value)
            y_info -= 0.6*cm
        
        # Note technique
        y = 6*cm
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#d9534f'))
        c.drawString(3*cm, y, "⚠ ATTENTION - COURANT CONTINU ≤ 1000V DC")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 9)
        c.drawString(3*cm, y - 0.6*cm, "• Respecter les polarités + et - lors du câblage")
        c.drawString(3*cm, y - 1.2*cm, "• Ne jamais déconnecter sous charge")
        c.drawString(3*cm, y - 1.8*cm, "• Utiliser uniquement connecteurs MC4 certifiés")
        c.drawString(3*cm, y - 2.4*cm, "• Conformité NF C 15-712-1:2017")
        
        # Date et référence
        c.setFont("Helvetica", 8)
        c.drawString(width - 10*cm, 2*cm, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
        c.drawString(width - 10*cm, 1.5*cm, f"Réf: STRINGS-{self.prospect.get('id', '000')}")
    
    def _plan_zone(self, c, zone, width, height):
        """Dessine le plan détaillé d'une zone avec ses strings"""
        
        # === CARTOUCHE ===
        self._dessiner_cartouche_zone(c, zone, width, height)
        
        # === ZONE DE DESSIN PRINCIPALE ===
        # Réserver espace pour légende en bas (7cm)
        dessin_x = 2*cm
        dessin_y = 8*cm
        dessin_width = width - 4*cm
        dessin_height = height - 15*cm
        
        # Cadre zone de dessin
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(dessin_x, dessin_y, dessin_width, dessin_height)
        
        # Récupérer données zone
        nb_modules = zone.get('nbModules', 0)
        nb_cols = zone.get('nbCols', 1)
        nb_rows = zone.get('nbRows', 1)
        orientation_mod = zone.get('moduleOrientation', 'paysage')
        
        # Calculer strings (configuration série/parallèle optimale)
        strings_config = self._calculer_strings_zone(zone)
        
        # Dessiner le champ de modules avec numérotation
        self._dessiner_champ_modules(c, zone, strings_config, 
                                     dessin_x, dessin_y, dessin_width, dessin_height)
        
        # === LÉGENDE STRINGS ===
        self._dessiner_legende_strings(c, strings_config, width, height)
    
    def _dessiner_cartouche_zone(self, c, zone, width, height):
        """Cartouche en-tête de la page zone"""
        
        cart_height = 6*cm
        cart_y = height - cart_height - 0.5*cm
        
        # Fond cartouche
        c.setFillColor(colors.HexColor('#f0f0f0'))
        c.rect(1*cm, cart_y, width - 2*cm, cart_height, fill=1, stroke=0)
        
        # Bordure
        c.setStrokeColor(colors.HexColor('#003d7a'))
        c.setLineWidth(2)
        c.rect(1*cm, cart_y, width - 2*cm, cart_height, fill=0, stroke=1)
        
        # Titre zone
        c.setFillColor(colors.HexColor('#003d7a'))
        c.setFont("Helvetica-Bold", 20)
        c.drawString(2*cm, cart_y + cart_height - 1.5*cm, 
                    f"ZONE {zone.get('numero', '?')} - PLAN DE CÂBLAGE STRINGS")
        
        # Caractéristiques zone
        y = cart_y + cart_height - 3*cm
        
        zone_data = [
            ['<b>Surface:</b>', f"{zone.get('surfaceM2', 0):.1f} m²"],
            ['<b>Modules:</b>', f"{zone.get('nbModules', 0)} unités ({zone.get('nbCols', 0)}×{zone.get('nbRows', 0)})"],
            ['<b>Puissance:</b>', f"{zone.get('puissanceKw', 0):.2f} kWc"],
            ['<b>Orientation:</b>', f"{zone.get('orientation', 'N/A')}° / Inclinaison {zone.get('inclinaison', 'N/A')}°"],
            ['<b>Disposition modules:</b>', zone.get('moduleOrientation', 'paysage').title()],
        ]
        
        x_col1 = 2*cm
        x_col2 = 15*cm
        col = 0
        
        for label, value in zone_data:
            x = x_col1 if col == 0 else x_col2
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.black)
            c.drawString(x, y, label.replace('<b>', '').replace('</b>', ''))
            c.setFont("Helvetica", 9)
            c.drawString(x + 3.5*cm, y, value)
            
            col = (col + 1) % 2
            if col == 0:
                y -= 0.7*cm
    
    def _calculer_strings_zone(self, zone):
        """Calcule la configuration optimale des strings pour une zone"""
        
        nb_modules = zone.get('nbModules', 0)
        nb_cols = zone.get('nbCols', 1)
        nb_rows = zone.get('nbRows', 1)
        
        # Configuration série optimale (10-20 modules par string)
        modules_par_string = 20  # Standard
        
        # Ajuster selon tension max onduleur (1000V DC max)
        v_oc = float(self.module.get('voc', 49.5))
        max_modules_series = int(1000 / v_oc * 0.9)  # Marge sécurité 10%
        modules_par_string = min(modules_par_string, max_modules_series)
        
        # Nombre de strings
        nb_strings = math.ceil(nb_modules / modules_par_string)
        
        # Ajuster pour distribution équilibrée
        modules_par_string = math.ceil(nb_modules / nb_strings)
        
        # Créer configuration strings avec ordre optimisé pour câblage
        strings = []
        
        # Créer un parcours en serpentin pour minimiser longueur câbles
        module_order = self._calculer_parcours_serpentin(nb_rows, nb_cols, nb_modules)
        
        modules_restants = nb_modules
        start_idx = 0
        
        for i in range(nb_strings):
            nb_mod_string = min(modules_par_string, modules_restants)
            
            # Récupérer les indices des modules pour ce string dans l'ordre optimisé
            module_indices = module_order[start_idx:start_idx + nb_mod_string]
            
            # Calculer tension et courant
            v_oc_string = v_oc * nb_mod_string
            v_mpp_string = float(self.module.get('vmpp', 41.8)) * nb_mod_string
            i_sc_string = float(self.module.get('isc', 13.9))
            i_mpp_string = float(self.module.get('impp', 13.2))
            
            # Calculer longueur de câble pour ce string (en mètres)
            longueur_cable = self._calculer_longueur_cable_string(module_indices, nb_cols)
            
            strings.append({
                'numero': i + 1,
                'nb_modules': nb_mod_string,
                'module_indices': module_indices,  # Ordre réel des modules
                'v_oc': v_oc_string,
                'v_mpp': v_mpp_string,
                'i_sc': i_sc_string,
                'i_mpp': i_mpp_string,
                'longueur_cable': longueur_cable,
                'color': self._get_string_color(i)
            })
            
            modules_restants -= nb_mod_string
            start_idx += nb_mod_string
        
        return strings
    
    def _calculer_parcours_serpentin(self, nb_rows, nb_cols, nb_modules):
        """
        Calcule un parcours en serpentin (boustrophédon) pour minimiser les câbles.
        Parcourt ligne par ligne en alternant le sens (gauche→droite puis droite→gauche).
        
        Exemple 3×4:
        →→→
        ←←←
        →→→
        
        Retourne: liste ordonnée des indices de modules
        """
        parcours = []
        module_idx = 0
        
        for row in range(nb_rows):
            if row % 2 == 0:  # Lignes paires: gauche → droite
                for col in range(nb_cols):
                    if module_idx < nb_modules:
                        # Indice dans grille standard (row, col)
                        grid_idx = row * nb_cols + col
                        parcours.append(grid_idx)
                        module_idx += 1
            else:  # Lignes impaires: droite → gauche (serpentin)
                for col in range(nb_cols - 1, -1, -1):
                    if module_idx < nb_modules:
                        grid_idx = row * nb_cols + col
                        parcours.append(grid_idx)
                        module_idx += 1
        
        return parcours
    
    def _calculer_longueur_cable_string(self, module_indices, nb_cols):
        """
        Calcule la longueur totale de câble DC nécessaire pour un string.
        
        Args:
            module_indices: Liste des indices de modules dans l'ordre de câblage
            nb_cols: Nombre de colonnes dans la zone
        
        Returns:
            Longueur totale en mètres
        """
        if len(module_indices) < 2:
            return 0.0
        
        longueur_totale = 0.0
        
        for i in range(len(module_indices) - 1):
            idx1 = module_indices[i]
            idx2 = module_indices[i + 1]
            
            # Position dans la grille
            row1 = idx1 // nb_cols
            col1 = idx1 % nb_cols
            row2 = idx2 // nb_cols
            col2 = idx2 % nb_cols
            
            # Distance en nombre de modules
            delta_row = abs(row2 - row1)
            delta_col = abs(col2 - col1)
            
            # Longueur réelle (en tenant compte dimensions modules)
            # Connexion entre modules adjacents = largeur ou longueur module
            if delta_row == 0 and delta_col == 1:  # Adjacents horizontalement
                longueur_totale += self.module_longueur
            elif delta_row == 1 and delta_col == 0:  # Adjacents verticalement
                longueur_totale += self.module_largeur
            else:  # Non adjacents (saut) - câble de raccordement
                longueur_totale += math.sqrt(
                    (delta_col * self.module_longueur) ** 2 + 
                    (delta_row * self.module_largeur) ** 2
                )
        
        # Ajouter 10% pour connecteurs et marge
        longueur_totale *= 1.1
        
        return round(longueur_totale, 2)
    
    def _get_string_color(self, index):
        """Retourne une couleur unique pour chaque string"""
        colors_list = [
            colors.HexColor('#e74c3c'),  # Rouge
            colors.HexColor('#3498db'),  # Bleu
            colors.HexColor('#2ecc71'),  # Vert
            colors.HexColor('#f39c12'),  # Orange
            colors.HexColor('#9b59b6'),  # Violet
            colors.HexColor('#1abc9c'),  # Turquoise
            colors.HexColor('#e67e22'),  # Orange foncé
            colors.HexColor('#34495e'),  # Gris foncé
        ]
        return colors_list[index % len(colors_list)]
    
    def _dessiner_champ_modules(self, c, zone, strings_config, x, y, width, height):
        """Dessine le champ de modules avec numérotation des strings"""
        
        nb_cols = zone.get('nbCols', 1)
        nb_rows = zone.get('nbRows', 1)
        orientation_mod = zone.get('moduleOrientation', 'paysage')
        
        # Dimensions d'un module dans le dessin (échelle)
        # Ajuster pour tenir dans la zone
        if orientation_mod == 'paysage':
            mod_w_reel = self.module_longueur
            mod_h_reel = self.module_largeur
        else:
            mod_w_reel = self.module_largeur
            mod_h_reel = self.module_longueur
        
        # Calculer échelle pour tenir dans la zone
        echelle_x = (width - 2*cm) / (nb_cols * mod_w_reel)
        echelle_y = (height - 2*cm) / (nb_rows * mod_h_reel)
        echelle = min(echelle_x, echelle_y)
        
        mod_w = mod_w_reel * echelle
        mod_h = mod_h_reel * echelle
        
        # Centrer le champ
        total_w = nb_cols * mod_w
        total_h = nb_rows * mod_h
        start_x = x + (width - total_w) / 2
        start_y = y + (height - total_h) / 2
        
        # Attribution modules aux strings selon ordre optimisé
        module_to_string = {}
        
        for string in strings_config:
            for grid_idx in string['module_indices']:
                module_to_string[grid_idx] = string
        
        # Dessiner chaque module dans la grille
        for grid_idx in range(zone.get('nbModules', 0)):
            row = grid_idx // nb_cols
            col = grid_idx % nb_cols
            
            mx = start_x + col * mod_w
            my = start_y + (nb_rows - 1 - row) * mod_h  # Inverser Y
            
            # Couleur selon string
            string_info = module_to_string.get(grid_idx)
            if string_info:
                c.setFillColor(string_info['color'])
                c.setStrokeColor(string_info['color'])
            else:
                c.setFillColor(colors.lightgrey)
                c.setStrokeColor(colors.grey)
            
            # Rectangle module avec transparence
            if string_info:
                c.setFillColorRGB(string_info['color'].red, 
                                 string_info['color'].green, 
                                 string_info['color'].blue, 
                                 alpha=0.3)
                c.rect(mx, my, mod_w, mod_h, fill=1, stroke=1)
                
                # Numéro module (position dans le string)
                # Trouver position dans le string
                string_position = string_info['module_indices'].index(grid_idx) + 1
                
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 6 if mod_w < 2*cm else 8)
                c.drawCentredString(mx + mod_w/2, my + mod_h/2 + 2*mm, 
                                   f"#{string_position}")
                
                # Numéro string
                c.setFont("Helvetica", 5 if mod_w < 2*cm else 6)
                c.setFillColor(string_info['color'])
                c.drawCentredString(mx + mod_w/2, my + mod_h/2 - 2*mm, 
                                   f"S{string_info['numero']}")
            else:
                c.rect(mx, my, mod_w, mod_h, fill=1, stroke=1)
        
        # Flèches de câblage pour chaque string
        self._dessiner_cablage_strings(c, zone, strings_config, module_to_string,
                                       start_x, start_y, mod_w, mod_h, nb_cols, nb_rows)
    
    def _dessiner_cablage_strings(self, c, zone, strings_config, module_to_string,
                                  start_x, start_y, mod_w, mod_h, nb_cols, nb_rows):
        """Dessine les flèches de câblage entre modules d'un même string selon parcours optimisé"""
        
        c.setLineWidth(1.5)
        
        for string in strings_config:
            c.setStrokeColor(string['color'])
            
            # Utiliser l'ordre optimisé des modules dans le string
            modules_string = string['module_indices']
            
            # Dessiner ligne continue entre modules du string dans l'ordre
            for i in range(len(modules_string) - 1):
                mod1_idx = modules_string[i]
                mod2_idx = modules_string[i + 1]
                
                # Position des modules
                row1 = mod1_idx // nb_cols
                col1 = mod1_idx % nb_cols
                row2 = mod2_idx // nb_cols
                col2 = mod2_idx % nb_cols
                
                x1 = start_x + col1 * mod_w + mod_w/2
                y1 = start_y + (nb_rows - 1 - row1) * mod_h + mod_h/2
                x2 = start_x + col2 * mod_w + mod_w/2
                y2 = start_y + (nb_rows - 1 - row2) * mod_h + mod_h/2
                
                # Ligne avec flèche
                c.line(x1, y1, x2, y2)
                
                # Petite flèche à la fin
                self._draw_arrow(c, x1, y1, x2, y2, string['color'])
    
    def _draw_arrow(self, c, x1, y1, x2, y2, color):
        """Dessine une petite flèche directionnelle"""
        # Angle de la ligne
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 3*mm
        arrow_angle = 25 * math.pi / 180
        
        # Point de la flèche (80% du trajet)
        px = x1 + (x2 - x1) * 0.8
        py = y1 + (y2 - y1) * 0.8
        
        # Pointes de la flèche
        p1x = px - arrow_len * math.cos(angle - arrow_angle)
        p1y = py - arrow_len * math.sin(angle - arrow_angle)
        p2x = px - arrow_len * math.cos(angle + arrow_angle)
        p2y = py - arrow_len * math.sin(angle + arrow_angle)
        
        c.setFillColor(color)
        p = c.beginPath()
        p.moveTo(px, py)
        p.lineTo(p1x, p1y)
        p.lineTo(p2x, p2y)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    
    def _dessiner_legende_strings(self, c, strings_config, width, height):
        """Dessine la légende des strings en bas de page"""
        
        # Positionner sous la zone de dessin avec marge
        leg_y = 6.5*cm
        leg_x = 2*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.black)
        c.drawString(leg_x, leg_y + 1.5*cm, "LÉGENDE STRINGS:")
        
        # Table des strings avec longueur câble
        strings_data = [
            ['<b>String</b>', '<b>Modules</b>', '<b>Câble DC</b>', '<b>Voc</b>', '<b>Vmpp</b>', '<b>Isc</b>', '<b>Impp</b>']
        ]
        
        for string in strings_config:
            strings_data.append([
                f"String {string['numero']}",
                f"{string['nb_modules']} modules",
                f"{string['longueur_cable']:.1f} m",
                f"{string['v_oc']:.1f} V",
                f"{string['v_mpp']:.1f} V",
                f"{string['i_sc']:.1f} A",
                f"{string['i_mpp']:.1f} A"
            ])
        
        strings_table = Table(strings_data, colWidths=[2.5*cm, 2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        
        # Style avec couleurs
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]
        
        # Ajouter couleurs des strings
        for i, string in enumerate(strings_config):
            style.append(('BACKGROUND', (0, i+1), (0, i+1), string['color']))
            style.append(('TEXTCOLOR', (0, i+1), (0, i+1), colors.whitesmoke))
        
        strings_table.setStyle(TableStyle(style))
        
        # Calculer hauteur de la table
        strings_table.wrapOn(c, width, height)
        table_height = strings_table._height
        
        # Dessiner table
        strings_table.drawOn(c, leg_x, leg_y - table_height)
