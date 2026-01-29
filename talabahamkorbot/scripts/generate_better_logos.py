from PIL import Image, ImageDraw
import os

def create_text_logo(text, bg_color, filename):
    # High resolution
    img = Image.new('RGBA', (200, 200), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Rounded Rect (Simulated via Circle + Rect or just Rect)
    # Background
    color = "#" + bg_color
    draw.rounded_rectangle((10, 10, 190, 190), radius=40, fill=color)
    
    # Text
    # Since we might not have a font, we'll draw simple shapes or try default load
    # Or just write text really simple
    # Attempt to load a ttf
    try:
        from PIL import ImageFont
        # Usually basic fonts exist
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        # Center Text
        # text_width = draw.textlength(text, font=font)
        # x = (200 - text_width) / 2
        # y = (200 - 40) / 2
        draw.text((40, 80), text, font=font, fill="white")
    except Exception as e:
        print(f"Font failed: {e}. Drawing fallback text.")
        # Fallback: Just draw a white rectangle in center as a "symbol"
        draw.rectangle((50, 90, 150, 110), fill="white")
    
    path = f"/var/www/talabahamkor_mobile/assets/images/{filename}"
    img.save(path, "PNG")
    print(f"Created {path}")

# Payme: Already downloaded real one? Check size. 
# If Payme is good (8KB), keep it. 1KB -> Placeholder.
if os.path.exists("/var/www/talabahamkor_mobile/assets/images/payme.png") and os.path.getsize("/var/www/talabahamkor_mobile/assets/images/payme.png") > 2000:
    print("Payme logo exists and seems valid.")
else:
    create_text_logo("Payme", "00CCCC", "payme.png")

# Click: Download failed, so generate.
create_text_logo("CLICK", "0047BA", "click.png")

# Uzum: 7000FF
# Re-try download or generate if fail
# I'll generate as backup
if not os.path.exists("/var/www/talabahamkor_mobile/assets/images/uzum.png"):
    create_text_logo("Uzum", "7000FF", "uzum.png")
