import json, os, random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import textwrap, math
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════
#  DESIGN CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

C = type('Config', (), {
    'SIZE': 1024, 'MARGIN': 72, 'PAD_H': 48, 'PAD_V': 40,
    'LINE_GAP': 14, 'AUTHOR_GAP': 36, 'OVERLAY_ALPHA': 95, 'BOX_ALPHA': 165,
    'QUOTE_MIN': 24, 'QUOTE_MAX': 54, 'AUTHOR_SIZE': 34, 'MARK_SIZE': 80,
    'COUNTER_NUM': 70, 'COUNTER_DEN': 30,
    'GRADIENT_BOX': True, 'GLOW_EFFECT': True, 'PATTERN_OVERLAY': True,
    'DECOR_BORDERS': True,
})()

# Color schemes
SCHEMES = {
    "classic": {'text': (255,255,255), 'outline': (0,0,0), 'accent': (22,145,217)},
    "elegant": {'text': (255,248,225), 'outline': (0,0,0), 'accent': (212,175,55)},
    "modern":  {'text': (255,255,255), 'outline': (0,0,0), 'accent': (255,69,58)},
    "minimal": {'text': (240,240,240), 'outline': (0,0,0), 'accent': (128,128,128)},
    "royal":   {'text': (255,255,255), 'outline': (0,0,0), 'accent': (103,58,183)},
}
CURRENT = "classic"

def col(k): return SCHEMES[CURRENT].get(k, SCHEMES["classic"][k])

# ═══════════════════════════════════════════════════════════════════════════
#  FONT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class FontMgr:
    _fonts = {}
    def __init__(self):
        paths = ["./Kurale-Regular.ttf", "C:\\Windows\\Fonts\\georgia.ttf", 
                 "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"]
        self.path = next((p for p in paths if os.path.exists(p)), None)
    
    def get(self, size):
        if not self.path: return ImageFont.load_default()
        key = f"{self.path}_{size}"
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(self.path, size)
        return self._fonts[key]
    
    def width(self, font, text):
        try: return font.getbbox(text)[2] - font.getbbox(text)[0]
        except: return len(text) * 10
    
    def wrap(self, text, font, max_w):
        words, lines, cur = text.split(), [], []
        for w in words:
            test = ' '.join(cur + [w])
            if self.width(font, test) <= max_w: cur.append(w)
            else: lines.append(' '.join(cur)); cur = [w]
        if cur: lines.append(' '.join(cur))
        return lines or [text]
    
    def optimal(self, text, max_w, start=48):
        for sz in range(start, C.QUOTE_MIN-1, -2):
            f = self.get(sz)
            lines = self.wrap(text, f, max_w)
            if all(self.width(f, l) <= max_w for l in lines):
                return f, lines
        f = self.get(C.QUOTE_MIN)
        return f, self.wrap(text, f, max_w)

fm = FontMgr()

# ═══════════════════════════════════════════════════════════════════════════
#  TEXT RENDERER
# ═══════════════════════════════════════════════════════════════════════════

class TextRender:
    @staticmethod
    def outline(draw, xy, text, font, fill=None, outline=None, w=2):
        fill = fill or col('text')
        outline = outline or col('outline')
        x,y = xy
        for dx,dy in [(-w,-w),(-w,0),(-w,w),(0,-w),(0,w),(w,-w),(w,0),(w,w)]:
            draw.text((x+dx, y+dy), text, font=font, fill=outline)
        draw.text(xy, text, font=font, fill=fill)
    
    @staticmethod
    def height(font, text="Ag"):
        try: bbox = font.getbbox(text); return bbox[3] - bbox[1]
        except: return 30

tr = TextRender()

# ═══════════════════════════════════════════════════════════════════════════
#  BACKGROUND
# ═══════════════════════════════════════════════════════════════════════════

def process_bg(path):
    img = Image.open(path).convert('RGB')
    w,h = img.size
    m = min(w,h)
    img = img.crop(((w-m)//2, (h-m)//2, (w-m)//2+m, (h-m)//2+m))
    img = img.resize((C.SIZE, C.SIZE), Image.Resampling.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.58)
    img = ImageEnhance.Contrast(img).enhance(0.78)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    img = img.convert('RGBA')
    overlay = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0, C.OVERLAY_ALPHA))
    return Image.alpha_composite(img, overlay)

def add_pattern(img):
    if not C.PATTERN_OVERLAY: return img
    p = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0,0))
    d = ImageDraw.Draw(p)
    for i in range(0, C.SIZE, 50):
        d.line([(i,0),(i,C.SIZE)], fill=(255,255,255,8), width=1)
        d.line([(0,i),(C.SIZE,i)], fill=(255,255,255,8), width=1)
    return Image.alpha_composite(img, p)

def add_vignette(img):
    v = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0,0))
    d = ImageDraw.Draw(v)
    cx = cy = C.SIZE//2
    for r in range(int(C.SIZE*0.75), 0, -15):
        alpha = int(30 * (1 - r/(C.SIZE*0.75))**1.5)
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(0,0,0,alpha))
    return Image.alpha_composite(img, v)

# ═══════════════════════════════════════════════════════════════════════════
#  DECORATIVE ELEMENTS (MINIMALISTIC)
# ═══════════════════════════════════════════════════════════════════════════

class Decor:
    @staticmethod
    def corner(draw, box, color, size=30):
        x1,y1,x2,y2 = box
        inset = 12
        # Top-left
        draw.line([(x1+inset, y1+4), (x1+inset+size, y1+4)], fill=color, width=2)
        draw.line([(x1+4, y1+inset), (x1+4, y1+inset+size)], fill=color, width=2)
        # Top-right
        draw.line([(x2-inset-size, y1+4), (x2-inset, y1+4)], fill=color, width=2)
        draw.line([(x2-4, y1+inset), (x2-4, y1+inset+size)], fill=color, width=2)
        # Bottom-left
        draw.line([(x1+inset, y2-4), (x1+inset+size, y2-4)], fill=color, width=2)
        draw.line([(x1+4, y2-inset-size), (x1+4, y2-inset)], fill=color, width=2)
        # Bottom-right
        draw.line([(x2-inset-size, y2-4), (x2-inset, y2-4)], fill=color, width=2)
        draw.line([(x2-4, y2-inset-size), (x2-4, y2-inset)], fill=color, width=2)
    
    @staticmethod
    def minimal_circle(draw, x, y, color, size=25):
        """Minimalistic circle decoration"""
        draw.ellipse([x-size, y-size, x+size, y+size], outline=color, width=2)
        draw.ellipse([x-3, y-3, x+3, y+3], fill=color)
    
    @staticmethod
    def minimal_diamond(draw, x, y, color, size=20):
        """Minimalistic diamond decoration"""
        points = [(x, y-size), (x+size, y), (x, y+size), (x-size, y)]
        draw.polygon(points, outline=color, width=2)
        draw.ellipse([x-2, y-2, x+2, y+2], fill=color)

# ═══════════════════════════════════════════════════════════════════════════
#  COUNTER (top-right)
# ═══════════════════════════════════════════════════════════════════════════

def draw_counter(draw, num, total):
    nf = fm.get(C.COUNTER_NUM)
    df = fm.get(C.COUNTER_DEN)
    ns, ds = str(num), f"/{total}"
    nw, dw = fm.width(nf, ns), fm.width(df, ds)
    
    x = C.SIZE - C.MARGIN - (nw + dw)
    y = 35
    
    tr.outline(draw, (x, y), ns, nf, fill=col('text'))
    dy = y + tr.height(nf) - tr.height(df) - 2
    draw.text((x + nw, dy), ds, font=df, fill=(180,180,180))
    
    # Minimal decoration below counter
    cx = x + (nw + dw)//2
    cy = y + tr.height(nf) + 12
    Decor.minimal_diamond(draw, cx, cy, col('accent'), 8)

# ═══════════════════════════════════════════════════════════════════════════
#  EMBLEM (bottom-left) - 75% BIGGER
# ═══════════════════════════════════════════════════════════════════════════

def draw_emblem(img):
    if not os.path.exists("emblem.png"): return
    try:
        em = Image.open("emblem.png").convert("RGBA")
        # 75% bigger = original size * 1.75
        new_size = int(140 * 1.75)  # 140 * 1.75 = 245
        em = em.resize((new_size, new_size), Image.Resampling.LANCZOS)
        x = C.MARGIN - 25
        y = C.SIZE - em.size[1] - 35
        img.paste(em, (x, y), em)
    except: pass

# ═══════════════════════════════════════════════════════════════════════════
#  MIRROR DECORATIONS AT OPPOSITE CORNERS (MINIMALISTIC)
# ═══════════════════════════════════════════════════════════════════════════

def draw_mirror_decorations(draw):
    """Minimalistic decorative elements at corners OPPOSITE to emblem and counter"""
    
    # Mirror decoration at TOP-LEFT (opposite from emblem which is bottom-left)
    Decor.minimal_circle(draw, C.MARGIN + 50, C.MARGIN + 50, col('accent'), 18)
    
    # Mirror decoration at BOTTOM-RIGHT (opposite from counter which is top-right)
    Decor.minimal_circle(draw, C.SIZE - C.MARGIN - 50, C.SIZE - C.MARGIN - 50, col('accent'), 18)

# ═══════════════════════════════════════════════════════════════════════════
#  QUOTE MARKS
# ═══════════════════════════════════════════════════════════════════════════

def draw_quote_marks(draw, layout):
    first_w = layout['widths'][0]
    first_x = (C.SIZE - first_w)//2
    font = fm.get(C.MARK_SIZE)
    tr.outline(draw, (first_x - 45, layout['start_y'] - 12), "“", font, fill=col('accent'))
    
    last_w = layout['widths'][-1]
    last_x = (C.SIZE - last_w)//2
    last_y = layout['start_y'] + layout['total_h'] - layout['heights'][-1]
    tr.outline(draw, (last_x + last_w + 30, last_y - 8), "”", font, fill=col('accent'))

# ═══════════════════════════════════════════════════════════════════════════
#  LAYOUT CALCULATION
# ═══════════════════════════════════════════════════════════════════════════

def calc_layout(quote, author):
    box_l, box_r = C.MARGIN, C.SIZE - C.MARGIN
    inner_w = (box_r - box_l) - (2 * C.PAD_H)
    
    start = C.QUOTE_MAX if len(quote) < 80 else 46
    qf, lines = fm.optimal(quote, inner_w, start)
    
    heights = [tr.height(qf, l) for l in lines]
    widths = [fm.width(qf, l) for l in lines]
    total_h = sum(heights) + C.LINE_GAP * (len(lines)-1)
    
    af = fm.get(C.AUTHOR_SIZE)
    aw, ah = fm.width(af, author), tr.height(af, author)
    
    content_h = total_h + C.AUTHOR_GAP + ah
    box_h = content_h + 2 * C.PAD_V
    
    usable_top, usable_bottom = 110, C.SIZE - 100
    box_y1 = usable_top + ((usable_bottom - usable_top) - box_h)//2
    box_y2 = box_y1 + box_h
    if box_y1 < usable_top: box_y1, box_y2 = usable_top, usable_top+box_h
    if box_y2 > usable_bottom: box_y2, box_y1 = usable_bottom, usable_bottom-box_h
    
    actual_h = box_y2 - box_y1
    start_y = box_y1 + (actual_h - content_h)//2
    
    return {
        'box': (box_l, box_y1, box_r, box_y2),
        'start_y': start_y, 'qf': qf, 'af': af,
        'lines': lines, 'heights': heights, 'widths': widths,
        'total_h': total_h, 'aw': aw, 'ah': ah
    }

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN CREATOR
# ═══════════════════════════════════════════════════════════════════════════

def create_quote(quote_data, img_path, out_path, num, total=365):
    img = process_bg(img_path)
    img = add_pattern(img)
    
    quote = quote_data.get("quote", "").strip().rstrip('.')
    author = quote_data.get("author", "").strip().rstrip('.')
    
    layout = calc_layout(quote, author)
    
    # Draw text box
    box_layer = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0,0))
    db = ImageDraw.Draw(box_layer)
    box = layout['box']
    
    if C.GRADIENT_BOX:
        for i in range(10):
            alpha = int(C.BOX_ALPHA * (1 - i/20))
            off = i//2
            db.rounded_rectangle([box[0]-off, box[1]-off, box[2]+off, box[3]+off],
                                 radius=12, fill=(0,0,0,alpha))
    else:
        db.rounded_rectangle(box, radius=12, fill=(0,0,0, C.BOX_ALPHA))
    
    if C.DECOR_BORDERS:
        Decor.corner(db, box, col('accent'), 35)
    
    img = Image.alpha_composite(img, box_layer)
    draw = ImageDraw.Draw(img)
    
    # Quote marks
    draw_quote_marks(draw, layout)
    
    # Quote text
    y = layout['start_y']
    for i, line in enumerate(layout['lines']):
        x = (C.SIZE - layout['widths'][i])//2
        if C.GLOW_EFFECT:
            for r in range(2,0,-1):
                draw.text((x-r, y), line, font=layout['qf'], fill=(*col('accent'), 40))
                draw.text((x+r, y), line, font=layout['qf'], fill=(*col('accent'), 40))
        tr.outline(draw, (x, y), line, layout['qf'])
        y += layout['heights'][i] + C.LINE_GAP
    
    # Author with lines on same level
    ay = layout['start_y'] + layout['total_h'] + C.AUTHOR_GAP
    ax = (C.SIZE - layout['aw'])//2
    line_y = ay + (layout['ah']//2)
    line_len = 60
    
    draw.line([(ax - line_len - 15, line_y), (ax - 15, line_y)], fill=col('accent'), width=1)
    draw.line([(ax + layout['aw'] + 15, line_y), (ax + layout['aw'] + line_len + 15, line_y)], fill=col('accent'), width=1)
    draw.ellipse([ax - line_len - 19, line_y-2, ax - line_len - 15, line_y+2], fill=col('accent'))
    draw.ellipse([ax + layout['aw'] + line_len + 15, line_y-2, ax + layout['aw'] + line_len + 19, line_y+2], fill=col('accent'))
    
    tr.outline(draw, (ax, ay), author, layout['af'])
    
    # Counter (top-right)
    draw_counter(draw, num, total)
    
    # Emblem (bottom-left) - 75% bigger
    draw_emblem(img)
    
    # Minimalist mirror decorations at opposite corners
    draw_mirror_decorations(draw)
    
    # Final touches
    img = add_vignette(img)
    rgb = Image.new('RGB', img.size, (0,0,0))
    rgb.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
    rgb.save(out_path, 'JPEG', quality=95, optimize=True)

# ═══════════════════════════════════════════════════════════════════════════
#  IMAGE POOL
# ═══════════════════════════════════════════════════════════════════════════

class ImagePool:
    def __init__(self, folder):
        self.folder = folder
        self.used = set()
        self.images = []
        self._refresh()
    
    def _refresh(self):
        try:
            self.images = [f for f in os.listdir(self.folder) 
                          if f.lower().endswith(('.jpg','.jpeg','.png'))]
        except: 
            self.images = []
    
    def get_random(self):
        if not self.images: 
            return None
        avail = [f for f in self.images if f not in self.used] or self.images
        if len(avail) == len(self.images): 
            self.used.clear()
        chosen = random.choice(avail)
        self.used.add(chosen)
        return os.path.join(self.folder, chosen), chosen
    
    def has_images(self):
        """Check if any images available"""
        return len(self.images) > 0
# ═══════════════════════════════════════════════════════════════════════════
#  QUOTE CHANGER - SPECIFIC DAY GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Configuration
    JSON_FILE = "quotes.json"
    IMAGE_FOLDER = "downloaded_images"
    OUTPUT_FOLDER = "output_quotes"
    VARIANTS_PER_QUOTE = 3
    TOTAL_QUOTES_DISPLAY = 365
    
    # Load quotes
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            quotes_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {JSON_FILE} not found!")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return
    
    if not quotes_data:
        print("❌ No quotes found in JSON file!")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Initialize image pool
    image_pool = ImagePool(IMAGE_FOLDER)
    
    if not image_pool.has_images():
        print(f"❌ Error: No images found in '{IMAGE_FOLDER}' folder!")
        return
    
    # Print header
    print("═" * 60)
    print("🎨 QUOTE CHANGER - Specific Day Generator")
    print("═" * 60)
    print(f"📚 Available quotes: {len(quotes_data)}")
    print(f"🎨 Using FIRST quote from JSON: \"{quotes_data[0].get('quote', '')[:60]}...\"")
    print(f"👤 Author: {quotes_data[0].get('author', 'Unknown')}")
    print("═" * 60)
    
    # Ask for day number
    while True:
        try:
            day_input = input(f"\n📅 Which day (1-{TOTAL_QUOTES_DISPLAY}) do you want to generate? ")
            if day_input.lower() in ['q', 'quit', 'exit']:
                print("❌ Cancelled.")
                return
            
            day_num = int(day_input)
            
            if 1 <= day_num <= TOTAL_QUOTES_DISPLAY:
                break
            else:
                print(f"⚠️ Please enter a number between 1 and {TOTAL_QUOTES_DISPLAY}")
        except ValueError:
            print("⚠️ Please enter a valid number!")
    
    # Ask for number of variants
    while True:
        try:
            variants_input = input(f"\n🎲 How many variants? (1-5, default {VARIANTS_PER_QUOTE}): ")
            if not variants_input:
                variants = VARIANTS_PER_QUOTE
                break
            
            variants = int(variants_input)
            if 1 <= variants <= 5:
                break
            else:
                print("⚠️ Please enter a number between 1 and 5")
        except ValueError:
            print("⚠️ Please enter a valid number!")
    
    # Ask for custom output folder
    custom_folder = input(f"\n📁 Output folder (default '{OUTPUT_FOLDER}'): ").strip()
    if custom_folder:
        output_folder = custom_folder
        os.makedirs(output_folder, exist_ok=True)
    else:
        output_folder = OUTPUT_FOLDER
    
    # Use the FIRST quote from the JSON file
    quote_data = quotes_data[0]
    quote_preview = quote_data.get('quote', '')[:50] + "..."
    
    print("\n" + "═" * 60)
    print(f"📝 Generating Day {day_num}/{TOTAL_QUOTES_DISPLAY}")
    print(f"   Quote: {quote_preview}")
    print(f"   Author: {quote_data.get('author', 'Unknown')}")
    print(f"🎲 Variants: {variants}")
    print(f"📁 Output: {output_folder}")
    print("═" * 60)
    
    success = 0
    failed = 0
    start_time = datetime.now()
    
    # Track used images for this session
    used_images = set()
    
    for variant in range(1, variants + 1):
        # Get random image
        image_result = image_pool.get_random()
        if not image_result:
            print(f"   ⚠️ No image available for variant {variant}")
            failed += 1
            continue
        
        image_path, image_name = image_result
        
        # Create output filename
        if variants > 1:
            output_name = f"day_{day_num:03d}_v{variant}.jpg"
        else:
            output_name = f"day_{day_num:03d}.jpg"
        
        output_path = os.path.join(output_folder, output_name)
        
        try:
            create_quote(quote_data, image_path, output_path, day_num, TOTAL_QUOTES_DISPLAY)
            success += 1
            print(f"   ✓ {output_name} (bg: {image_name})")
        except Exception as e:
            failed += 1
            print(f"   ✗ {output_name} failed: {str(e)[:50]}")
    
    # Final statistics
    elapsed = datetime.now() - start_time
    print("\n" + "═" * 60)
    print("✅ GENERATION COMPLETE")
    print("═" * 60)
    print(f"📊 Successful: {success}")
    print(f"⚠️  Failed: {failed}")
    print(f"⏱️  Time elapsed: {elapsed.total_seconds():.1f} seconds")
    print(f"📁 Output folder: {output_folder}")
    print(f"📅 Day: {day_num}/{TOTAL_QUOTES_DISPLAY}")
    print("═" * 60)

if __name__ == "__main__":
    main()