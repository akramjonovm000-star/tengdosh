import base64
import os

# Payme (Teal-ish placeholder or real small logo if I had one. I'll make a colored square with text if possible, or just a known valid small PNG base64)
# I'll use a 1x1 pixel or small icon.
# Actually I will use a simple Base64 of a generic "Card" icon or similar if I can't find real logo.
# Better: I will create a simple colored PNG using python.

from PIL import Image, ImageDraw, ImageFont

def create_logo(name, color_hex, filename):
    img = Image.new('RGBA', (100, 100), color=(255, 255, 255, 0)) # Transparent
    draw = ImageDraw.Draw(img)
    # Draw rounded rectangle (simulated) or circle
    color = "#" + color_hex
    draw.ellipse((10, 10, 90, 90), fill=color)
    # Text
    try:
        # Default font
        draw.text((30, 40), name[:1], fill="white")
    except:
        pass
    
    path = f"/var/www/talabahamkor_mobile/assets/images/{filename}"
    img.save(path, "PNG")
    print(f"Created {path}")

# Payme: 00CCCC
create_logo("P", "00CCCC", "payme.png")
# Click: 0047BA
create_logo("C", "0047BA", "click.png")
# Uzum: 7000FF
create_logo("U", "7000FF", "uzum.png")
