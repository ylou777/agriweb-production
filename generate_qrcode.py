#!/usr/bin/env python3
"""
🌾 Générateur de QR Code pour AgriWeb
Crée un QR code stylisé pour accéder directement à votre application
"""

import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def create_agriweb_qr_code():
    """Crée un QR code personnalisé pour AgriWeb"""
    
    # URL de votre application
    app_url = "https://aware-surprise-production.up.railway.app/"
    
    # Configuration du QR code
    qr = qrcode.QRCode(
        version=1,  # Contrôle la taille (1 = plus petit)
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Correction d'erreur moyenne
        box_size=10,  # Taille de chaque "boîte" du QR code
        border=4,  # Bordure autour du QR code
    )
    
    # Ajouter les données
    qr.add_data(app_url)
    qr.make(fit=True)
    
    # Créer l'image avec couleurs personnalisées
    qr_img = qr.make_image(
        fill_color="#2d5a27",  # Vert foncé pour les carrés
        back_color="#f8f9fa"   # Fond clair
    )
    
    # Créer une image plus grande pour ajouter du texte
    final_width = 400
    final_height = 500
    final_img = Image.new('RGB', (final_width, final_height), '#ffffff')
    
    # Redimensionner le QR code
    qr_size = 300
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    # Centrer le QR code
    qr_x = (final_width - qr_size) // 2
    qr_y = 50
    final_img.paste(qr_img, (qr_x, qr_y))
    
    # Ajouter du texte
    draw = ImageDraw.Draw(final_img)
    
    try:
        # Essayer d'utiliser une police système
        title_font = ImageFont.truetype("arial.ttf", 24)
        subtitle_font = ImageFont.truetype("arial.ttf", 16)
        url_font = ImageFont.truetype("arial.ttf", 12)
    except:
        # Police par défaut si arial n'est pas disponible
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        url_font = ImageFont.load_default()
    
    # Titre principal
    title_text = "🌾 AgriWeb"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (final_width - title_width) // 2
    draw.text((title_x, 15), title_text, fill="#2d5a27", font=title_font)
    
    # Sous-titre
    subtitle_text = "Scanner pour accéder"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (final_width - subtitle_width) // 2
    draw.text((subtitle_x, 360), subtitle_text, fill="#6c757d", font=subtitle_font)
    
    # URL
    url_bbox = draw.textbbox((0, 0), app_url, font=url_font)
    url_width = url_bbox[2] - url_bbox[0]
    url_x = (final_width - url_width) // 2
    draw.text((url_x, 385), app_url, fill="#0066cc", font=url_font)
    
    # Date de génération
    date_text = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    date_bbox = draw.textbbox((0, 0), date_text, font=url_font)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (final_width - date_width) // 2
    draw.text((date_x, 420), date_text, fill="#adb5bd", font=url_font)
    
    # Instructions
    instruction_text = "📱 Ouvrez l'appareil photo de votre téléphone"
    instruction_bbox = draw.textbbox((0, 0), instruction_text, font=url_font)
    instruction_width = instruction_bbox[2] - instruction_bbox[0]
    instruction_x = (final_width - instruction_width) // 2
    draw.text((instruction_x, 450), instruction_text, fill="#6c757d", font=url_font)
    
    # Sauvegarder
    filename = "AgriWeb_QRCode.png"
    final_img.save(filename, 'PNG', quality=95)
    
    return filename, app_url

def create_simple_qr_code():
    """Crée un QR code simple sans fioritures"""
    app_url = "https://aware-surprise-production.up.railway.app/"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    
    qr.add_data(app_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filename = "AgriWeb_QRCode_Simple.png"
    img.save(filename)
    
    return filename, app_url

if __name__ == "__main__":
    print("🌾 Génération des QR Codes pour AgriWeb...")
    print("=" * 50)
    
    # QR Code stylisé
    try:
        styled_file, url = create_agriweb_qr_code()
        print(f"✅ QR Code stylisé créé: {styled_file}")
    except Exception as e:
        print(f"⚠️ Erreur QR code stylisé: {e}")
        styled_file = None
    
    # QR Code simple (backup)
    try:
        simple_file, url = create_simple_qr_code()
        print(f"✅ QR Code simple créé: {simple_file}")
    except Exception as e:
        print(f"❌ Erreur QR code simple: {e}")
        simple_file = None
    
    print(f"\n🔗 URL: {url}")
    print(f"📱 Utilisez votre appareil photo pour scanner")
    print(f"🎯 Direction: Page d'accueil AgriWeb")
    
    if styled_file and os.path.exists(styled_file):
        print(f"\n📸 QR Code principal: {styled_file}")
        print(f"   Taille: {os.path.getsize(styled_file)} bytes")
    
    if simple_file and os.path.exists(simple_file):
        print(f"📸 QR Code simple: {simple_file}")
        print(f"   Taille: {os.path.getsize(simple_file)} bytes")
