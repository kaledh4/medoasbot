import os
from PIL import Image, ImageDraw, ImageFont
import uuid

# Safe imports for Arabic support
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_SUPPORT = True
except ImportError:
    print("⚠️ Arabic libraries not found. Text will be disconnected.")
    HAS_ARABIC_SUPPORT = False

class ImageGenService:
    def __init__(self):
        self.static_dir = "static/offers"
        self.templates_dir = "static/offers/templates"
        os.makedirs(self.static_dir, exist_ok=True)
        
        # Load Fonts - Bundled "Amiri" (Royal Arabic Style)
        font_path = os.path.join("static/fonts", "Amiri-Bold.ttf")
        
        self.font_title = self._load_font(font_path, 44)
        self.font_price = self._load_font(font_path, 80)
        self.font_meta = self._load_font(font_path, 28)
        self.font_stars = self._load_font(font_path, 34)

    def _load_font(self, font_name, size):
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            print(f"⚠️ Could not load font {font_name}. Fallback to default.")
            return ImageFont.load_default()

    def _fix_text(self, text):
        """Reshapes Arabic text if libraries are available."""
        if not HAS_ARABIC_SUPPORT:
            return text
        try:
            reshaped = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped)
            return bidi_text
        except Exception as e:
            print(f"⚠️ Error reshaping Arabic: {e}")
            return text

    def generate_offer_card(self, vendor_name, price, request_id, design_id=4):
        """
        Generates the '3D Green Card' (Design v2 - Vertical) with Smart Layout.
        """
        import re
        import textwrap

        # Load Template (3D Green Vertical)
        img_path = os.path.join(self.templates_dir, "t8.png")
        if os.path.exists(img_path):
            img = Image.open(img_path).convert('RGB')
        else:
            # Fallback Green Background
            img = Image.new('RGB', (500, 650), color=(6, 78, 59))

        d = ImageDraw.Draw(img)
        W, H = img.size

        # COLORS
        white_color = (255, 255, 255)
        accent_color = (110, 231, 183) # Light Green
        gold_color = (255, 193, 7) # Amber
        dark_text = (31, 41, 55) # Gray-800 for details

        # FONT LOADING
        font_dir = "static/fonts"
        # Increase sizes slightly for legibility
        font_main = self._load_font(os.path.join(font_dir, "Tajawal-Bold.ttf"), 36)
        font_large = self._load_font(os.path.join(font_dir, "Tajawal-Bold.ttf"), 42)
        font_price = self._load_font(os.path.join(font_dir, "Tajawal-Bold.ttf"), 50)
        font_detail = self._load_font(os.path.join(font_dir, "Tajawal-Regular.ttf"), 24)
        
        # --- 1. SMART DATA PREP ---
        
        # A. Split Price & Extra Text
        # Input: "1600 includes delivery" -> Price: "1600", Extra: "includes delivery"
        full_price_str = str(price)
        price_number = ""
        price_extra = ""
        
        # Regex to find the first large number (price)
        match = re.search(r'(\d+)', full_price_str)
        if match:
            price_number = match.group(1)
            # Remove the number from the string to get the "extra" part
            price_extra = full_price_str.replace(price_number, "", 1).strip()
        else:
            # No number found? Use whole string as details fallback
            price_number = "---"
            price_extra = full_price_str

        # B. Construct Details Text
        # Combine the default message with the "Extra" price info
        base_details = "عرض خاص يشمل الخدمة كاملة"
        if price_extra and len(price_extra) > 2:
            final_details = f"{base_details}\n{price_extra}"
        else:
            final_details = base_details

        # --- 2. DRAWING ---

        # A. Vendor Name (Top Area: Y=140-190)
        # Shifted up slightly to fit better
        name_text = self._fix_text(vendor_name)
        bbox = d.textbbox((0,0), name_text, font=font_main)
        w_text = bbox[2] - bbox[0]
        d.text(((W - w_text)/2, 150), name_text, font=font_main, fill=accent_color)

        # B. Rating (Below Name: Y=200)
        star_y = 210
        start_x = (W - (5 * 25)) / 2
        for i in range(5):
            self._draw_star(d, (start_x + (i*25), star_y), size=10, fill=gold_color)
        
        # C. Details (White Card Body: Y=260 - 480)
        # We need to WRAP the text so it fits the 400px wide card
        reshaped_details = self._fix_text(final_details)
        
        # Simple wrapping logic for PIL (approximate chars)
        # Arabic is tricky, so we split by newlines first
        lines = reshaped_details.split('\n')
        wrapped_lines = []
        for line in lines:
            wrapped_lines.extend(textwrap.wrap(line, width=30)) # 30 chars approx width

        # Draw lines centered
        current_y = 300 # Start inside white card
        line_height = 35
        for line in wrapped_lines:
            bbox_l = d.textbbox((0,0), line, font=font_detail)
            w_l = bbox_l[2] - bbox_l[0]
            d.text(((W - w_l)/2, current_y), line, font=font_detail, fill=dark_text)
            current_y += line_height

        # D. Price (Bottom Floating Box: Y=550+)
        # Price Number
        p_val = self._fix_text(price_number)
        bbox_p = d.textbbox((0,0), p_val, font=font_price)
        w_p = bbox_p[2] - bbox_p[0]
        
        # Price Label (RIYAL)
        curr_val = self._fix_text("ريال")
        bbox_c = d.textbbox((0,0), curr_val, font=font_detail)
        w_c = bbox_c[2] - bbox_c[0]
        
        # Calculate total width to center both
        gap = 10
        total_w = w_p + gap + w_c
        start_x = (W - total_w) / 2
        
        # Draw Price
        d.text((start_x, 555), p_val, font=font_price, fill=white_color)
        # Draw Currency next to it
        d.text((start_x + w_p + gap, 575), curr_val, font=font_detail, fill=white_color)

        # Save
        filename = f"offer_final_{uuid.uuid4()}.png"
        filepath = os.path.join(self.static_dir, filename)
        img.save(filepath)
        
        return filename

    def _draw_star(self, draw, center, size, fill):
        """Draws a 5-point star polygon."""
        import math
        cx, cy = center
        points = []
        # 5 points, outer radius = size, inner radius = size/2.5
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            r = size if i % 2 == 0 else size / 2.5
            x = cx + math.cos(angle) * r
            y = cy + math.sin(angle) * r
            points.append((x, y))
        draw.polygon(points, fill=fill)

image_service = ImageGenService()
