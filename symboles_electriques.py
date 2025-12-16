"""
Bibliothèque de symboles électriques normalisés pour schémas unifilaires
Conforme aux normes françaises NF C 03-201 et NF C 15-100
"""

from reportlab.lib.units import cm, mm
from reportlab.lib import colors

class SymbolesElectriques:
    """Dessine les symboles électriques normalisés"""
    
    @staticmethod
    def module_pv(c, x, y, size=1*cm):
        """
        Dessine un symbole de module photovoltaïque
        Symbol: Carré avec diagonales (cellule PV)
        """
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        
        # Carré principal
        c.rect(x - size/2, y - size/2, size, size, stroke=1, fill=0)
        
        # Diagonales (représentant la cellule)
        c.line(x - size/2, y - size/2, x + size/2, y + size/2)
        c.line(x - size/2, y + size/2, x + size/2, y - size/2)
        
        # Flèches photon (3 flèches à gauche)
        arrow_x = x - size/2 - 4*mm
        c.setLineWidth(1.5)
        for i in range(3):
            ay = y + size/3 - i*size/4
            c.line(arrow_x, ay, arrow_x + 3*mm, ay - 2*mm)
            c.line(arrow_x + 3*mm, ay - 2*mm, arrow_x + 2*mm, ay - 1*mm)
            c.line(arrow_x + 3*mm, ay - 2*mm, arrow_x + 2.5*mm, ay - 3*mm)
        
        # Réinitialiser
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
        
    @staticmethod
    def string_pv(c, x, y, nb_modules=20, compact=True):
        """
        Dessine un string de modules PV en série
        """
        if compact:
            # Version compacte: un seul symbole + annotation
            SymbolesElectriques.module_pv(c, x, y, size=0.8*cm)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x, y - 0.8*cm, f"×{nb_modules}")
        else:
            # Version détaillée: plusieurs symboles
            for i in range(min(3, nb_modules)):
                SymbolesElectriques.module_pv(c, x + i*1.2*cm, y, size=0.6*cm)
                if i < 2:
                    c.line(x + (i+0.5)*1.2*cm, y, x + (i+0.7)*1.2*cm, y)
            
            if nb_modules > 3:
                c.setFont("Helvetica", 7)
                c.drawString(x + 3.6*cm, y, f"... ×{nb_modules}")
    
    @staticmethod
    def sectionneur(c, x, y, orientation='horizontal'):
        """
        Dessine un symbole de sectionneur
        Symbol: Trait avec coupure en biais
        """
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
        
        if orientation == 'horizontal':
            # Ligne entrée
            c.line(x - 8*mm, y, x - 3*mm, y)
            # Partie mobile (biais)
            c.line(x - 3*mm, y, x + 2*mm, y + 4*mm)
            # Ligne sortie
            c.line(x + 3*mm, y, x + 8*mm, y)
            # Point de contact
            c.circle(x - 3*mm, y, 1.5*mm, fill=1, stroke=0)
            c.circle(x + 3*mm, y, 1.5*mm, fill=1, stroke=0)
        else:  # vertical
            c.line(x, y - 8*mm, x, y - 3*mm)
            c.line(x, y - 3*mm, x + 4*mm, y + 2*mm)
            c.line(x, y + 3*mm, x, y + 8*mm)
            c.circle(x, y - 3*mm, 1.5*mm, fill=1, stroke=0)
            c.circle(x, y + 3*mm, 1.5*mm, fill=1, stroke=0)
        
        # Réinitialiser
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
    
    @staticmethod
    def disjoncteur(c, x, y, orientation='horizontal'):
        """
        Dessine un symbole de disjoncteur
        Symbol: Sectionneur + rectangle (déclencheur thermique)
        """
        # Sectionneur de base
        SymbolesElectriques.sectionneur(c, x, y, orientation)
        
        # Rectangle déclencheur
        if orientation == 'horizontal':
            c.rect(x - 2*mm, y - 4*mm, 4*mm, 8*mm)
        else:
            c.rect(x - 4*mm, y - 2*mm, 8*mm, 4*mm)
    
    @staticmethod
    def differentiel(c, x, y, orientation='horizontal'):
        """
        Dessine un symbole de différentiel
        Symbol: Disjoncteur + cercle avec Δ
        """
        # Disjoncteur de base
        SymbolesElectriques.disjoncteur(c, x, y, orientation)
        
        # Cercle différentiel
        if orientation == 'horizontal':
            c.circle(x, y + 7*mm, 3*mm)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(x, y + 6*mm, "Δ")
        else:
            c.circle(x + 7*mm, y, 3*mm)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(x + 7*mm, y - 1*mm, "Δ")
    
    @staticmethod
    def parafoudre(c, x, y, orientation='vertical'):
        """
        Dessine un symbole de parafoudre
        Symbol: Flèche vers bas + trait horizontal (terre)
        """
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        
        if orientation == 'vertical':
            # Flèche vers bas
            c.line(x, y + 5*mm, x, y - 5*mm)
            # Pointe flèche
            c.line(x, y - 5*mm, x - 2*mm, y - 2*mm)
            c.line(x, y - 5*mm, x + 2*mm, y - 2*mm)
            # Ligne haute
            c.line(x - 3*mm, y + 5*mm, x + 3*mm, y + 5*mm)
            # Ligne basse (terre)
            c.line(x - 4*mm, y - 6*mm, x + 4*mm, y - 6*mm)
            c.line(x - 2*mm, y - 7*mm, x + 2*mm, y - 7*mm)
        else:
            # Version horizontale
            c.line(x - 5*mm, y, x + 5*mm, y)
            c.line(x + 5*mm, y, x + 2*mm, y - 2*mm)
            c.line(x + 5*mm, y, x + 2*mm, y + 2*mm)
    
    @staticmethod
    def onduleur(c, x, y, width=4*cm, height=3*cm):
        """
        Dessine un symbole d'onduleur NF C 15-712
        Symbol: Rectangle DC (gauche) + Résistance (centre) + Partie AC (droite)
        """
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        
        # Rectangle principal (contour global)
        c.rect(x - width/2, y - height/2, width, height)
        
        # Rectangle partie DC (gauche, 1/3 de la largeur)
        dc_width = width / 3
        c.rect(x - width/2, y - height/2, dc_width, height)
        
        # Texte DC
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x - width/2 + dc_width/2, y + 2*mm, "DC")
        
        # Flèche DC → AC (entre partie DC et résistance)
        arrow_x = x - width/6
        arrow_y = y + 2*mm
        c.line(arrow_x - 3*mm, arrow_y, arrow_x + 3*mm, arrow_y)
        c.line(arrow_x + 3*mm, arrow_y, arrow_x + 1*mm, arrow_y - 2*mm)
        c.line(arrow_x + 3*mm, arrow_y, arrow_x + 1*mm, arrow_y + 2*mm)
        
        # Résistance (zigzag au centre, sous la flèche)
        c.setLineWidth(1.5)
        resist_y = y - 2*mm
        resist_start_x = x - 8*mm
        resist_end_x = x + 8*mm
        resist_height = 4*mm
        
        # Dessiner le zigzag de la résistance
        path = c.beginPath()
        path.moveTo(resist_start_x, resist_y)
        num_peaks = 8
        for i in range(num_peaks + 1):
            px = resist_start_x + (resist_end_x - resist_start_x) * i / num_peaks
            py = resist_y + (resist_height if i % 2 else -resist_height)
            path.lineTo(px, py)
        path.lineTo(resist_end_x, resist_y)
        c.drawPath(path, stroke=1, fill=0)
        
        # Texte AC (côté droit)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + width/3, y + 2*mm, "AC")
        
        # Symbole ~ (sinusoïde, en bas à droite)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x + width/4, y - height/4, "~")
    
    @staticmethod
    def fusible(c, x, y, orientation='vertical'):
        """
        Dessine un symbole de fusible
        Symbol: Rectangle avec trait au centre
        """
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        
        if orientation == 'vertical':
            # Lignes connexion
            c.line(x, y - 8*mm, x, y - 4*mm)
            c.line(x, y + 4*mm, x, y + 8*mm)
            # Rectangle fusible
            c.rect(x - 2.5*mm, y - 4*mm, 5*mm, 8*mm, stroke=1, fill=1)
            # Trait interne
            c.setLineWidth(1.5)
            c.line(x, y - 3*mm, x, y + 3*mm)
        else:
            c.line(x - 8*mm, y, x - 4*mm, y)
            c.line(x + 4*mm, y, x + 8*mm, y)
            c.rect(x - 4*mm, y - 2.5*mm, 8*mm, 5*mm, stroke=1, fill=1)
            c.setLineWidth(1.5)
            c.line(x - 3*mm, y, x + 3*mm, y)
        
        # Réinitialiser
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
    
    @staticmethod
    def compteur(c, x, y, size=1.5*cm):
        """
        Dessine un symbole de compteur électrique
        Symbol: Cercle avec kWh
        """
        c.setLineWidth(2)
        c.setStrokeColor(colors.black)
        c.circle(x, y, size/2)
        
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x, y + 1*mm, "kWh")
    
    @staticmethod
    def terre(c, x, y):
        """
        Dessine un symbole de mise à la terre
        Symbol: Trois barres horizontales décroissantes
        """
        c.setLineWidth(1.5)
        c.setStrokeColor(colors.black)
        
        # Ligne verticale
        c.line(x, y, x, y - 6*mm)
        
        # Trois barres
        c.line(x - 4*mm, y - 6*mm, x + 4*mm, y - 6*mm)
        c.line(x - 3*mm, y - 8*mm, x + 3*mm, y - 8*mm)
        c.line(x - 2*mm, y - 10*mm, x + 2*mm, y - 10*mm)
    
    @staticmethod
    def boite_jonction(c, x, y, width=3*cm, height=2*cm, label=""):
        """
        Dessine une boîte de jonction
        """
        c.setLineWidth(1.5)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.white)
        
        # Rectangle
        c.roundRect(x - width/2, y - height/2, width, height, 2*mm, fill=1)
        
        # Label
        if label:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.black)
            c.drawCentredString(x, y - 2*mm, label)
    
    @staticmethod
    def cable_dc(c, x1, y1, x2, y2, section, label_pos='middle'):
        """
        Dessine un câble DC (rouge) avec section
        """
        c.setStrokeColor(colors.red)
        c.setLineWidth(2)
        c.line(x1, y1, x2, y2)
        
        # Annotation section
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.red)
        c.drawString(mid_x + 2*mm, mid_y + 2*mm, f"{section}mm² Cu")
        c.setFillColor(colors.black)
    
    @staticmethod
    def cable_ac(c, x1, y1, x2, y2, section, nb_phases=1):
        """
        Dessine un câble AC (noir/bleu) avec section
        """
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.line(x1, y1, x2, y2)
        
        # Annotation
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.blue)
        phases_str = f"{nb_phases}P+" if nb_phases > 1 else ""
        c.drawString(mid_x + 2*mm, mid_y + 2*mm, f"{phases_str}{section}mm² Cu")
        c.setFillColor(colors.black)
    
    @staticmethod
    def annotation(c, x, y, text, font_size=7, color=colors.black):
        """
        Ajoute une annotation textuelle
        """
        c.setFont("Helvetica", font_size)
        c.setFillColor(color)
        c.drawString(x, y, text)
        c.setFillColor(colors.black)
