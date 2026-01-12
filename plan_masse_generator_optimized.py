"""
Générateur de Plan de Masse Cadastral - Version Optimisée
Architecture modulaire et performante
v3.0 - 2026-01-12
"""

from reportlab.lib.pagesizes import A3
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from pyproj import Transformer
import io
import requests
from PIL import Image
import json
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# ============================================================================
# MODELS - Classes de données
# ============================================================================

@dataclass
class GPSBounds:
    """Limites géographiques GPS"""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    
    @property
    def center_lat(self) -> float:
        return (self.min_lat + self.max_lat) / 2
    
    @property
    def center_lon(self) -> float:
        return (self.min_lon + self.max_lon) / 2


@dataclass
class ModulesBBox:
    """Bounding box des modules PV"""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    width_meters: float
    height_meters: float
    
    @property
    def center_lat(self) -> float:
        return (self.min_lat + self.max_lat) / 2
    
    @property
    def center_lon(self) -> float:
        return (self.min_lon + self.max_lon) / 2


# ============================================================================
# SERVICES - Logique métier isolée
# ============================================================================

class GPSConverter:
    """Service de conversion GPS ↔ PDF avec projection Lambert 93"""
    
    EARTH_RADIUS = 6371000  # Rayon terrestre en mètres
    
    def __init__(self):
        self.to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    
    def meters_to_degrees(self, lat: float, lon: float, meters: float) -> Tuple[float, float]:
        """Convertit des mètres en degrés GPS autour d'un point"""
        delta_lat = (meters / self.EARTH_RADIUS) * (180 / math.pi)
        delta_lon = (meters / (self.EARTH_RADIUS * math.cos(lat * math.pi / 180))) * (180 / math.pi)
        return delta_lat, delta_lon
    
    def calculate_bounds(self, lat: float, lon: float, radius_meters: float) -> GPSBounds:
        """Calcule les limites GPS pour un rayon donné"""
        delta_lat, delta_lon = self.meters_to_degrees(lat, lon, radius_meters)
        return GPSBounds(
            min_lat=lat - delta_lat,
            max_lat=lat + delta_lat,
            min_lon=lon - delta_lon,
            max_lon=lon + delta_lon
        )
    
    def gps_to_pdf(self, lat: float, lon: float, gps_bounds: GPSBounds, 
                   plan_x: float, plan_y: float, plan_width: float, plan_height: float) -> Tuple[float, float]:
        """Convertit GPS → PDF avec projection Lambert 93"""
        try:
            # Conversion en Lambert 93
            min_x_l93, min_y_l93 = self.to_l93.transform(gps_bounds.min_lon, gps_bounds.min_lat)
            max_x_l93, max_y_l93 = self.to_l93.transform(gps_bounds.max_lon, gps_bounds.max_lat)
            x_l93, y_l93 = self.to_l93.transform(lon, lat)
            
            # Normalisation
            x_range = max_x_l93 - min_x_l93
            y_range = max_y_l93 - min_y_l93
            
            if x_range == 0 or y_range == 0:
                return (plan_x + plan_width / 2, plan_y + plan_height / 2)
            
            x_ratio = (x_l93 - min_x_l93) / x_range
            y_ratio = (y_l93 - min_y_l93) / y_range
            
            # Coordonnées PDF
            pdf_x = plan_x + x_ratio * plan_width
            pdf_y = plan_y + y_ratio * plan_height
            
            return (pdf_x, pdf_y)
        
        except Exception as e:
            # Fallback: conversion linéaire
            lat_range = gps_bounds.max_lat - gps_bounds.min_lat
            lon_range = gps_bounds.max_lon - gps_bounds.min_lon
            
            if lat_range == 0 or lon_range == 0:
                return (plan_x + plan_width / 2, plan_y + plan_height / 2)
            
            lat_ratio = (lat - gps_bounds.min_lat) / lat_range
            lon_ratio = (lon - gps_bounds.min_lon) / lon_range
            
            pdf_x = plan_x + lon_ratio * plan_width
            pdf_y = plan_y + lat_ratio * plan_height
            
            return (pdf_x, pdf_y)


class SatelliteImageService:
    """Service de téléchargement d'images satellite"""
    
    @staticmethod
    def fetch(lat: float, lon: float, bounds: GPSBounds, width: int = 1600, height: int = 1400) -> Optional[Image.Image]:
        """Télécharge image satellite pour une zone GPS"""
        
        # Construire bbox
        bbox_str = f"{bounds.min_lon},{bounds.min_lat},{bounds.max_lon},{bounds.max_lat}"
        
        print(f"[SATELLITE] 📍 Bbox: [{bounds.min_lat:.6f}, {bounds.max_lat:.6f}] x [{bounds.min_lon:.6f}, {bounds.max_lon:.6f}]")
        
        # Tentative 1: Esri World Imagery
        try:
            url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            params = {
                'bbox': bbox_str,
                'bboxSR': '4326',
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            
            print(f"[SATELLITE] 🔍 Tentative Esri World Imagery...")
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200 and len(response.content) > 1000:
                print(f"[SATELLITE] ✅ Esri OK ({len(response.content)/1024:.1f} KB)")
                return Image.open(io.BytesIO(response.content))
            else:
                print(f"[SATELLITE] ⚠️ Esri: HTTP {response.status_code}, taille={len(response.content)} bytes")
        
        except Exception as e:
            print(f"[SATELLITE] ❌ Esri échoué: {e}")
        
        # Tentative 2: Tuiles OSM
        try:
            print(f"[SATELLITE] 🔍 Tentative tuiles OSM...")
            img = SatelliteImageService._fetch_osm_tiles(lat, lon, bounds, width, height)
            if img:
                print(f"[SATELLITE] ✅ OSM OK")
                return img
        except Exception as e:
            print(f"[SATELLITE] ❌ OSM échoué: {e}")
        
        return None
    
    @staticmethod
    def _fetch_osm_tiles(lat: float, lon: float, bounds: GPSBounds, width: int, height: int) -> Optional[Image.Image]:
        """Assemble des tuiles OSM pour créer l'image"""
        zoom = 18
        
        # Conversion lat/lon → tuile
        def deg2tile(lat, lon, zoom):
            lat_rad = math.radians(lat)
            n = 2.0 ** zoom
            xtile = int((lon + 180.0) / 360.0 * n)
            ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return (xtile, ytile)
        
        x_min, y_min = deg2tile(bounds.max_lat, bounds.min_lon, zoom)
        x_max, y_max = deg2tile(bounds.min_lat, bounds.max_lon, zoom)
        
        # Assembler 3x3 tuiles
        tiles = []
        for y in range(y_min, y_max + 1):
            row = []
            for x in range(x_min, x_max + 1):
                try:
                    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        row.append(Image.open(io.BytesIO(resp.content)))
                    else:
                        row.append(Image.new('RGB', (256, 256), color='gray'))
                except:
                    row.append(Image.new('RGB', (256, 256), color='gray'))
            tiles.append(row)
        
        if not tiles:
            return None
        
        # Assembler
        tile_width = len(tiles[0])
        tile_height = len(tiles)
        
        assembled = Image.new('RGB', (tile_width * 256, tile_height * 256))
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                assembled.paste(tile, (x * 256, y * 256))
        
        # Redimensionner
        assembled = assembled.resize((width, height), Image.Resampling.LANCZOS)
        print(f"[SATELLITE] ✅ Image OSM assemblée ({assembled.size[0]}x{assembled.size[1]}, {len(tiles[0])}x{len(tiles)} tuiles)")
        
        return assembled


class ModulesAnalyzer:
    """Analyse les modules PV du calpinage"""
    
    @staticmethod
    def calculate_bbox(calpinage_data: dict) -> Optional[ModulesBBox]:
        """Calcule le bounding box des modules PV"""
        if not calpinage_data or 'zones' not in calpinage_data:
            return None
        
        all_lats = []
        all_lons = []
        
        for zone in calpinage_data['zones']:
            positions = zone.get('modulesPositions', [])
            for module in positions:
                corners = module.get('corners', [])
                for corner in corners:
                    all_lats.append(corner['lat'])
                    all_lons.append(corner['lng'])
        
        if not all_lats:
            return None
        
        min_lat, max_lat = min(all_lats), max(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        
        # Calculer dimensions en mètres
        R = 6371000
        lat_center = (min_lat + max_lat) / 2
        
        height_m = (max_lat - min_lat) * (math.pi / 180) * R
        width_m = (max_lon - min_lon) * (math.pi / 180) * R * math.cos(lat_center * math.pi / 180)
        
        return ModulesBBox(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            width_meters=width_m,
            height_meters=height_m
        )


# ============================================================================
# GENERATOR - Classe principale refactorisée
# ============================================================================

class PlanMasseGenerator:
    """Générateur de plan de masse cadastral optimisé"""
    
    # Constantes
    PAGE_SIZE = A3
    PLAN_MARGIN = 2 * cm
    PLAN_Y_OFFSET = 15 * cm
    SCALE_RATIO = 500  # Échelle 1/500
    MARGIN_FACTOR = 1.5  # 50% de marge autour des modules
    
    def __init__(self, prospect_data: dict, calpinage_data: Optional[dict] = None):
        self.data = prospect_data
        self.calpinage = calpinage_data
        self.width, self.height = self.PAGE_SIZE
        
        # Services
        self.gps_converter = GPSConverter()
        self.sat_service = SatelliteImageService()
        
        # État
        self.gps_bounds: Optional[GPSBounds] = None
        self.plan_bbox: Optional[dict] = None
    
    def generate(self) -> io.BytesIO:
        """Génère le PDF du plan de masse"""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=self.PAGE_SIZE)
        
        self._draw_header(c)
        self._draw_plan_cadastral(c)
        self._draw_legend(c)
        self._draw_cartouche(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def _draw_header(self, c: canvas.Canvas):
        """En-tête du document"""
        y = self.height - 2 * cm
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(3 * cm, y, "PLAN DE MASSE - INSTALLATION PHOTOVOLTAÏQUE")
        
        y -= 0.7 * cm
        c.setFont("Helvetica", 10)
        c.drawString(3 * cm, y, f"{self.data.get('adresse', '')}, {self.data.get('commune', '')}")
        
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.drawRightString(self.width - 3 * cm, y, "Échelle 1/500")
        c.setFillColor(colors.black)
    
    def _draw_plan_cadastral(self, c: canvas.Canvas):
        """Dessine le plan cadastral principal"""
        # Dimensions du plan
        plan_x = self.PLAN_MARGIN
        plan_y = self.PLAN_Y_OFFSET
        plan_width = self.width - 2 * self.PLAN_MARGIN
        plan_height = self.height - self.PLAN_Y_OFFSET - 3 * cm
        
        # Cadre
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(plan_x, plan_y, plan_width, plan_height)
        
        # Fond gris clair
        c.setFillColor(colors.HexColor('#F5F5F5'))
        c.rect(plan_x, plan_y, plan_width, plan_height, fill=1, stroke=0)
        
        # Calculer centre et bounds
        modules_bbox = ModulesAnalyzer.calculate_bbox(self.calpinage)
        
        if modules_bbox:
            lat, lon = modules_bbox.center_lat, modules_bbox.center_lon
            bbox_size = max(modules_bbox.width_meters, modules_bbox.height_meters) * self.MARGIN_FACTOR
            
            print(f"[PLAN] 📍 Modules: {modules_bbox.width_meters:.0f}x{modules_bbox.height_meters:.0f}m")
            print(f"[PLAN] 📍 Image satellite: {bbox_size:.0f}m (marge {self.MARGIN_FACTOR}x)")
        else:
            lat = self.data.get('latitude')
            lon = self.data.get('longitude')
            bbox_size = 100  # Défaut 100m
            print(f"[PLAN] ⚠️ Pas de modules - bbox par défaut: {bbox_size}m")
        
        # Calculer GPS bounds
        self.gps_bounds = self.gps_converter.calculate_bounds(lat, lon, bbox_size / 2)
        
        print(f"[PLAN] 🎯 GPS bounds: lat[{self.gps_bounds.min_lat:.6f}, {self.gps_bounds.max_lat:.6f}] lon[{self.gps_bounds.min_lon:.6f}, {self.gps_bounds.max_lon:.6f}]")
        
        # Télécharger image satellite
        satellite_img = self.sat_service.fetch(lat, lon, self.gps_bounds)
        
        if satellite_img:
            c.drawImage(ImageReader(satellite_img),
                       plan_x, plan_y,
                       width=plan_width, height=plan_height,
                       preserveAspectRatio=True, anchor='c', mask='auto')
            print(f"[PLAN] ✅ Image satellite dessinée")
        else:
            print(f"[PLAN] ⚠️ Image satellite non disponible - fond gris")
        
        # Stocker bbox du plan
        self.plan_bbox = {
            'x': plan_x,
            'y': plan_y,
            'width': plan_width,
            'height': plan_height
        }
        
        # Dessiner éléments
        if self.calpinage:
            self._draw_modules_pv(c)
        
        self._draw_compass(c, plan_x, plan_y, plan_width, plan_height)
    
    def _draw_modules_pv(self, c: canvas.Canvas):
        """Dessine les modules PV depuis leurs coordonnées GPS"""
        if not self.calpinage or 'zones' not in self.calpinage:
            return
        
        for zone in self.calpinage['zones']:
            positions = zone.get('modulesPositions', [])
            
            if not positions:
                continue
            
            print(f"[PLAN] 📍 Dessin {len(positions)} modules zone {zone.get('numero', '?')}")
            
            c.setStrokeColor(colors.HexColor('#1565C0'))
            c.setFillColor(colors.HexColor('#2196F3'))
            c.setLineWidth(0.5)
            
            for module in positions:
                corners = module.get('corners', [])
                
                if len(corners) < 4:
                    continue
                
                # Convertir GPS → PDF
                path = c.beginPath()
                first = True
                
                for corner in corners:
                    pdf_x, pdf_y = self.gps_converter.gps_to_pdf(
                        corner['lat'], corner['lng'],
                        self.gps_bounds,
                        self.plan_bbox['x'], self.plan_bbox['y'],
                        self.plan_bbox['width'], self.plan_bbox['height']
                    )
                    
                    if first:
                        path.moveTo(pdf_x, pdf_y)
                        first = False
                    else:
                        path.lineTo(pdf_x, pdf_y)
                
                path.close()
                c.drawPath(path, stroke=1, fill=1)
            
            print(f"[PLAN] ✅ Zone {zone.get('numero')} dessinée")
    
    def _draw_compass(self, c: canvas.Canvas, plan_x: float, plan_y: float, plan_width: float, plan_height: float):
        """Rose des vents"""
        compass_x = plan_x + 1 * cm
        compass_y = plan_y + plan_height - 3 * cm
        compass_size = 2 * cm
        
        # Cercle blanc
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.5)
        c.circle(compass_x, compass_y, compass_size / 2, fill=1, stroke=1)
        
        # Flèche Nord (rouge)
        c.setFillColor(colors.HexColor('#D32F2F'))
        c.setStrokeColor(colors.HexColor('#D32F2F'))
        north_path = c.beginPath()
        north_path.moveTo(compass_x, compass_y + compass_size / 2 - 0.2 * cm)
        north_path.lineTo(compass_x - 0.3 * cm, compass_y)
        north_path.lineTo(compass_x + 0.3 * cm, compass_y)
        north_path.close()
        c.drawPath(north_path, stroke=1, fill=1)
        
        # Texte N
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(compass_x, compass_y + compass_size / 2 + 0.2 * cm, "N")
    
    def _draw_legend(self, c: canvas.Canvas):
        """Légende du plan"""
        x = 2 * cm
        y = 12 * cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, "LÉGENDE :")
        
        y -= 0.5 * cm
        items = [
            (colors.HexColor('#FF00FF'), "Limites parcellaires cadastrales", "--"),
            (colors.HexColor('#2196F3'), "Modules photovoltaïques (position réelle)", ""),
            (colors.HexColor('#D32F2F'), "Contour zone PV", "--"),
        ]
        
        for color, label, style in items:
            c.setStrokeColor(color)
            c.setFillColor(color)
            
            if style == "--":
                c.setDash(4, 2)
            
            c.setLineWidth(2)
            c.line(x, y, x + 1 * cm, y)
            c.setDash()
            
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 8)
            c.drawString(x + 1.3 * cm, y - 0.15 * cm, label)
            y -= 0.4 * cm
    
    def _draw_cartouche(self, c: canvas.Canvas):
        """Cartouche technique"""
        x = self.width - 18 * cm
        y = 2 * cm
        w = 16 * cm
        h = 10 * cm
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, w, h)
        
        c.setFillColor(colors.HexColor('#1976D2'))
        c.rect(x, y + h - 1 * cm, w, 1 * cm, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x + w / 2, y + h - 0.7 * cm, "CARACTÉRISTIQUES TECHNIQUES")
        
        # Infos projet
        info_y = y + h - 1.5 * cm
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 0.3 * cm, info_y, "Projet :")
        
        info_y -= 0.35 * cm
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.5 * cm, info_y, f"• {self.data.get('adresse', 'N/A')}")
        info_y -= 0.3 * cm
        c.drawString(x + 0.5 * cm, info_y, f"• {self.data.get('commune', 'N/A')}")
        info_y -= 0.5 * cm
        
        # Installation PV
        if self.calpinage and 'zones' in self.calpinage:
            total_modules = sum(z.get('nbModules', 0) for z in self.calpinage['zones'])
            puissance_module = self.calpinage.get('module', {}).get('puissance', 560)
            puissance_totale = total_modules * float(puissance_module) / 1000
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.3 * cm, info_y, "Installation photovoltaïque :")
            info_y -= 0.35 * cm
            c.setFont("Helvetica", 8)
            c.drawString(x + 0.5 * cm, info_y, f"• {total_modules} modules de {puissance_module}W")
            info_y -= 0.3 * cm
            c.drawString(x + 0.5 * cm, info_y, f"• Puissance : {puissance_totale:.2f} kWc")
            info_y -= 0.3 * cm
            c.drawString(x + 0.5 * cm, info_y, f"• {len(self.calpinage['zones'])} zone(s) PV")


# ============================================================================
# FONCTION PUBLIQUE - Point d'entrée
# ============================================================================

def generate_plan_masse(prospect_data: dict, calpinage_data: Optional[dict] = None) -> io.BytesIO:
    """
    Génère un plan de masse cadastral au format PDF
    
    Args:
        prospect_data: Données du prospect (adresse, GPS, parcelles...)
        calpinage_data: Données du calpinage (zones, modules...)
    
    Returns:
        Buffer PDF du plan de masse
    """
    generator = PlanMasseGenerator(prospect_data, calpinage_data)
    return generator.generate()
