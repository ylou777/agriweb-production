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
class L93Bounds:
    """Limites géographiques Lambert 93"""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
        
    @property
    def height(self) -> float:
        return self.max_y - self.min_y


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
        self.from_l93 = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
    
    def calculate_l93_bounds(self, center_lat: float, center_lon: float, width_meters: float, height_meters: float) -> L93Bounds:
        """Calcule les limites Lambert 93 exactes pour un centre et des dimensions"""
        cx, cy = self.to_l93.transform(center_lon, center_lat)
        return L93Bounds(
            min_x=cx - width_meters/2,
            max_x=cx + width_meters/2,
            min_y=cy - height_meters/2,
            max_y=cy + height_meters/2
        )

    def l93_to_pdf(self, l93_x: float, l93_y: float, bounds: L93Bounds, 
                  plan_x: float, plan_y: float, plan_width: float, plan_height: float) -> Tuple[float, float]:
        """Convertit coordonnées L93 → PDF"""
        if bounds.width == 0 or bounds.height == 0:
             return (plan_x + plan_width / 2, plan_y + plan_height / 2)

        x_ratio = (l93_x - bounds.min_x) / bounds.width
        y_ratio = (l93_y - bounds.min_y) / bounds.height
        
        return (
            plan_x + x_ratio * plan_width,
            plan_y + y_ratio * plan_height
        )

    def gps_to_l93(self, lat: float, lon: float) -> Tuple[float, float]:
        """Convertit GPS (WGS84) vers Lambert 93"""
        return self.to_l93.transform(lon, lat)

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
    
    def calculate_rectangular_bounds(self, lat: float, lon: float, width_meters: float, height_meters: float) -> GPSBounds:
        """Calcule les limites GPS pour un rectangle (demi-largeur, demi-hauteur)"""
        # Demi-dimensions
        half_width = width_meters / 2
        half_height = height_meters / 2
        
        # Convertir en degrés
        delta_lat = (half_height / self.EARTH_RADIUS) * (180 / math.pi)
        delta_lon = (half_width / (self.EARTH_RADIUS * math.cos(lat * math.pi / 180))) * (180 / math.pi)
        
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
    def fetch(lat: float, lon: float, bounds, width: int = 1600, height: int = 1400) -> Optional[Image.Image]:
        """Télécharge image satellite pour une zone GPS (GPSBounds) ou Lambert 93 (L93Bounds)"""
        
        bbox_str = ""
        bbox_sr = '4326'
        image_sr = None  # None = default (usually 3857 for Esri World Imagery)
        
        if hasattr(bounds, 'min_x'): # L93Bounds checker
            bbox_str = f"{bounds.min_x},{bounds.min_y},{bounds.max_x},{bounds.max_y}"
            bbox_sr = '2154'
            image_sr = '2154' # Force output in Lambert 93 to match overlay
            print(f"[SATELLITE] 📍 Bbox L93: [{bounds.min_x:.1f}, {bounds.max_x:.1f}] x [{bounds.min_y:.1f}, {bounds.max_y:.1f}]")
        else:
            bbox_str = f"{bounds.min_lon},{bounds.min_lat},{bounds.max_lon},{bounds.max_lat}"
            print(f"[SATELLITE] 📍 Bbox GPS: [{bounds.min_lat:.6f}, {bounds.max_lat:.6f}] x [{bounds.min_lon:.6f}, {bounds.max_lon:.6f}]")
        
        # Tentative 1: Esri World Imagery
        try:
            url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            params = {
                'bbox': bbox_str,
                'bboxSR': bbox_sr,
                'size': f'{width},{height}',
                'format': 'png',
                'f': 'image'
            }
            if image_sr:
                params['imageSR'] = image_sr
            
            print(f"[SATELLITE] 🔍 Tentative Esri World Imagery (SR={image_sr or 'default'})...")
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200 and len(response.content) > 1000:
                print(f"[SATELLITE] ✅ Esri OK ({len(response.content)/1024:.1f} KB)")
                img = Image.open(io.BytesIO(response.content))
                # PAS DE FLIP - ReportLab gère l'orientation automatiquement
                return img
            else:
                print(f"[SATELLITE] ⚠️ Esri: HTTP {response.status_code}, taille={len(response.content)} bytes")
        
        except Exception as e:
            print(f"[SATELLITE] ❌ Esri échoué: {e}")
        
        # Tentative 2: Tuiles OSM
        try:
            print(f"[SATELLITE] 🔍 Tentative tuiles OSM...")
            # Conversion en GPSBounds si nécessaire pour OSM tiles (qui attendent lat/lon)
            gps_bounds = bounds
            if hasattr(bounds, 'min_x'):
                converter = GPSConverter()
                # Attention: L93(min_x, min_y) -> approx SW GPS
                lat_min, lon_min = converter.from_l93.transform(bounds.min_x, bounds.min_y)
                lat_max, lon_max = converter.from_l93.transform(bounds.max_x, bounds.max_y)
                gps_bounds = GPSBounds(min_lat=lat_min, max_lat=lat_max, min_lon=lon_min, max_lon=lon_max)
                
            img = SatelliteImageService._fetch_osm_tiles(lat, lon, gps_bounds, width, height)
            if img:
                print(f"[SATELLITE] ✅ OSM OK")
                return img
        except Exception as e:
            print(f"[SATELLITE] ❌ OSM échoué: {e}")
        
        return None
    
    @staticmethod
    def _fetch_osm_tiles(lat: float, lon: float, bounds: GPSBounds, width: int, height: int) -> Optional[Image.Image]:
        """Assemble des tuiles Esri pour créer l'image alignée sur bounds exact"""
        zoom = 18
        
        # Conversion lat/lon → tuile
        def deg2tile(lat_deg, lon_deg, z):
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** z
            xtile = (lon_deg + 180.0) / 360.0 * n
            ytile = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
            return (xtile, ytile)
        
        def tile2deg(xtile, ytile, z):
            """Conversion tuile → coordonnées GPS du coin NW"""
            n = 2.0 ** z
            lon = xtile / n * 360.0 - 180.0
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
            lat = math.degrees(lat_rad)
            return (lat, lon)
        
        # Calculer tuiles couvrant les bounds
        x_min_f, y_min_f = deg2tile(bounds.max_lat, bounds.min_lon, zoom)  # NW corner
        x_max_f, y_max_f = deg2tile(bounds.min_lat, bounds.max_lon, zoom)  # SE corner
        
        x_min, y_min = int(x_min_f), int(y_min_f)
        x_max, y_max = int(x_max_f) + 1, int(y_max_f) + 1
        
        print(f"[SATELLITE] 📦 Tuiles: x[{x_min}-{x_max}] y[{y_min}-{y_max}]")
        
        # Télécharger les tuiles
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
            if row:
                tiles.append(row)
        
        if not tiles or not tiles[0]:
            return None
        
        # Assembler l'image complète
        tile_cols = len(tiles[0])
        tile_rows = len(tiles)
        assembled = Image.new('RGB', (tile_cols * 256, tile_rows * 256))
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                assembled.paste(tile, (x * 256, y * 256))
        
        # CROP pour correspondre exactement aux bounds GPS demandés
        # Calculer les coordonnées pixel des bounds dans l'image assemblée
        tiles_nw_lat, tiles_nw_lon = tile2deg(x_min, y_min, zoom)  # Coin NW des tuiles
        tiles_se_lat, tiles_se_lon = tile2deg(x_max + 1, y_max + 1, zoom)  # Coin SE des tuiles
        
        total_width = assembled.size[0]
        total_height = assembled.size[1]
        
        # Pixel du coin NW des bounds demandés
        px_left = int((bounds.min_lon - tiles_nw_lon) / (tiles_se_lon - tiles_nw_lon) * total_width)
        px_top = int((tiles_nw_lat - bounds.max_lat) / (tiles_nw_lat - tiles_se_lat) * total_height)
        
        # Pixel du coin SE des bounds demandés
        px_right = int((bounds.max_lon - tiles_nw_lon) / (tiles_se_lon - tiles_nw_lon) * total_width)
        px_bottom = int((tiles_nw_lat - bounds.min_lat) / (tiles_nw_lat - tiles_se_lat) * total_height)
        
        # Clamp aux limites de l'image
        px_left = max(0, px_left)
        px_top = max(0, px_top)
        px_right = min(total_width, px_right)
        px_bottom = min(total_height, px_bottom)
        
        print(f"[SATELLITE] ✂️ Crop: ({px_left},{px_top}) → ({px_right},{px_bottom})")
        
        # Crop et redimensionner
        cropped = assembled.crop((px_left, px_top, px_right, px_bottom))
        final = cropped.resize((width, height), Image.Resampling.LANCZOS)
        
        print(f"[SATELLITE] ✅ Image assemblée et alignée ({final.size[0]}x{final.size[1]}, {tile_cols}x{tile_rows} tuiles)")
        
        return final


class ModulesAnalyzer:
    """Analyse les modules PV du calpinage"""
    
    @staticmethod
    def calculate_bbox(calpinage_data: dict) -> Optional[GPSBounds]:
        """Calcule le bounding box des modules PV en utilisant L93 pour les dimensions"""
        if not calpinage_data or 'zones' not in calpinage_data:
            return None
        
        all_lps_x = []
        all_lps_y = []
        all_lats = []
        all_lons = []
        
        converter = GPSConverter() # Use standardized L93 conversion
        
        for zone in calpinage_data['zones']:
            positions = zone.get('modulesPositions', [])
            for module in positions:
                corners = module.get('corners', [])
                for corner in corners:
                    lat, lon = corner['lat'], corner['lng']
                    all_lats.append(lat)
                    all_lons.append(lon)
                    
                    lx, ly = converter.gps_to_l93(lat, lon)
                    all_lps_x.append(lx)
                    all_lps_y.append(ly)
        
        if not all_lats:
            return None
            
        # Bounds en GPS (pour center)
        min_lat, max_lat = min(all_lats), max(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        
        # Dimensions précises en L93
        min_x, max_x = min(all_lps_x), max(all_lps_x)
        min_y, max_y = min(all_lps_y), max(all_lps_y)
        
        width_m = max_x - min_x
        height_m = max_y - min_y
        
        print(f"[ANALYZER] 📐 Modules BBox L93: {width_m:.2f}m x {height_m:.2f}m (Ratio: {width_m/height_m:.2f})")
        
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
    MARGIN_FACTOR = 3.0  # 3x taille modules = modules occupent 33% du plan
    
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
        
        # RATIO du plan PDF (important pour éviter déformation)
        plan_ratio = plan_width / plan_height
        print(f"[PLAN] 📐 Plan PDF: {plan_width/cm:.1f}×{plan_height/cm:.1f}cm, ratio={plan_ratio:.2f}")
        
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
            
            # ÉCHELLE 1/500 FIXE basée sur dimensions RÉELLES du plan
            self.actual_scale = 500
            # Convertir dimensions plan PDF en mètres réels à l'échelle 1/500
            # 1cm sur plan = 5m réels (échelle 1/500)
            plan_width_meters = (plan_width / cm) * 5  # cm × 5m/cm
            plan_height_meters = (plan_height / cm) * 5
            
            print(f"[PLAN] 📍 Modules: {modules_bbox.width_meters:.0f}×{modules_bbox.height_meters:.0f}m, centre: ({lat:.6f}, {lon:.6f})")
            print(f"[PLAN] 📐 ÉCHELLE 1/500: Plan couvre {plan_width_meters:.0f}m × {plan_height_meters:.0f}m")
        else:
            lat = self.data.get('latitude')
            lon = self.data.get('longitude')
            plan_width_meters = (plan_width / cm) * 5
            plan_height_meters = (plan_height / cm) * 5
            self.actual_scale = 500
            print(f"[PLAN] ⚠️ Pas de modules - centre depuis adresse")
        
        # Calculer bounds L93 exactes pour l'échelle
        self.l93_bounds = self.gps_converter.calculate_l93_bounds(lat, lon, plan_width_meters, plan_height_meters)
        
        print(f"[PLAN] 🎯 L93 bounds: x[{self.l93_bounds.min_x:.1f}, {self.l93_bounds.max_x:.1f}] y[{self.l93_bounds.min_y:.1f}, {self.l93_bounds.max_y:.1f}]")
        
        # Calcul dimensions image pour éviter distorsion (pixel carré)
        target_dpi = 200 # Réduit de 300 à 200 pour éviter "Data not available"
        img_width_px = int((plan_width / 72) * target_dpi)
        img_height_px = int((plan_height / 72) * target_dpi)
        
        # VERIFICATION RESOLUTION SOL (GSD)
        # 1 pixel ne doit jamais représenter moins de 15cm (0.15m) sinon ESRI bloque
        min_gsd = 0.15 
        current_gsd_x = plan_width_meters / img_width_px
        
        if current_gsd_x < min_gsd:
            print(f"[PLAN] ⚠️ Resolution demandée trop haute ({current_gsd_x*100:.1f} cm/px) -> Ajustement à {min_gsd*100:.0f} cm/px")
            img_width_px = int(plan_width_meters / min_gsd)
            img_height_px = int(plan_height_meters / min_gsd)
        
        # Limite API max absolue
        if img_width_px > 3000: 
            ratio = 3000 / img_width_px
            img_width_px = 3000
            img_height_px = int(img_height_px * ratio)

        print(f"[PLAN] 📷 Image demandée: {img_width_px}x{img_height_px}px (Couverture: {plan_width_meters:.1f}m, GSD: {(plan_width_meters/img_width_px)*100:.1f} cm/px)")

        # Télécharger image satellite avec bounds L93
        satellite_img = self.sat_service.fetch(lat, lon, self.l93_bounds, width=img_width_px, height=img_height_px)
        
        if satellite_img:
            # Vérifier que le serveur n'a pas renvoyé une image "Data Not Available" (souvent grise ou avec texte)
            # Difficile à détecter automatiquement sans OCR, mais on vérifie la taille min
            if satellite_img.size[0] < 100:
                print(f"[PLAN] ⚠️ Image reçue très petite ({satellite_img.size}), probable erreur")
            
            c.drawImage(ImageReader(satellite_img),
                       plan_x, plan_y,
                       width=plan_width, height=plan_height,
                       preserveAspectRatio=False, mask='auto',
                       anchorAtCentroid=True) # Ensure centering
            print(f"[PLAN] ✅ Image satellite L93 dessinée ({satellite_img.size[0]}x{satellite_img.size[1]}px)")
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
        self._draw_scale_bar(c, plan_x, plan_y, plan_width, plan_height)

    def _draw_scale_bar(self, c: canvas.Canvas, plan_x: float, plan_y: float, plan_width: float, plan_height: float):
        """Dessine une barre d'échelle graphique pour validation 1/500"""
        bar_x = plan_x + plan_width - 4 * cm
        bar_y = plan_y + 1 * cm
        
        # 10m à l'échelle 1/500 = 2cm
        bar_width_m = 10 
        bar_width_cm = 2 
        
        c.setLineWidth(1)
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.black)
        
        # Ligne principale
        c.line(bar_x, bar_y, bar_x + bar_width_cm * cm, bar_y)
        
        # Ticks
        c.line(bar_x, bar_y - 2, bar_x, bar_y + 2)
        c.line(bar_x + bar_width_cm * cm, bar_y - 2, bar_x + bar_width_cm * cm, bar_y + 2)
        
        # Texte
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(bar_x + (bar_width_cm * cm) / 2, bar_y + 4, "10 mètres")
        c.setFont("Helvetica", 6)
        c.drawCentredString(bar_x + (bar_width_cm * cm) / 2, bar_y - 8, "(Échelle 1/500)")
    
    def _draw_modules_pv(self, c: canvas.Canvas):
        """Dessine les modules PV depuis leurs coordonnées GPS"""
        if not self.calpinage or 'zones' not in self.calpinage or not hasattr(self, 'l93_bounds'):
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
                
                # Convertir GPS → L93 → PDF
                path = c.beginPath()
                first = True
                
                for corner in corners:
                    mx, my = self.gps_converter.gps_to_l93(corner['lat'], corner['lng'])
                    
                    pdf_x, pdf_y = self.gps_converter.l93_to_pdf(
                        mx, my,
                        self.l93_bounds,
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
