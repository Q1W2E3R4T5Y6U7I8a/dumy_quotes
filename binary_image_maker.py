import json, os, math, random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
#  DESIGN CONSTANTS (EDIT THESE)
# ═══════════════════════════════════════════════════════════════════════════

C = type('Config', (), {
    'SIZE': 512,
    'MARGIN': 120,
    'OVERLAY_ALPHA': 70,
    'BOX_ALPHA': 70,
    'GRADIENT_BOX': True,
    'GLOW_EFFECT': True,
    'PATTERN_OVERLAY': True,
    'DECOR_BORDERS': True,
    'GRID_OPACITY': 0.85,
    'EMBLEM_OPACITY': 1.0,
    'EMBLEM_SIZE': 140,
})()

# Black & white scheme
BW = {'accent': (255,255,255), 'dark': (0,0,0)}
def col(k): return BW[k]

# ═══════════════════════════════════════════════════════════════════════════
#  DETERMINISTIC SEED FROM BINARY DATA
# ═══════════════════════════════════════════════════════════════════════════

def get_seed(binary_str):
    clean = ''.join(c for c in binary_str if c in '01')
    if not clean:
        return 42
    seed = 0
    for i, bit in enumerate(clean[:256]):
        if bit == '1':
            seed ^= (i * 7919)
            seed = (seed << 1) ^ (seed >> 31)
    return seed % 100000

# ═══════════════════════════════════════════════════════════════════════════
#  VISIBLE FIBONACCI BACKGROUND DESIGNS
# ═══════════════════════════════════════════════════════════════════════════

def add_fibonacci_design(img, seed):
    """Add highly visible Fibonacci-based design elements to background"""
    random.seed(seed)
    
    # Create overlay for Fibonacci design
    design = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0,0))
    draw = ImageDraw.Draw(design)
    
    # Fibonacci numbers for design elements
    fib = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
    
    # Choose design type based on seed (VISIBLE designs)
    design_type = random.randint(0, 4)
    
    # Higher alpha so designs are visible (40-80 range)
    alpha = random.randint(40, 80)
    color = (255, 255, 255, alpha)
    
    print(f"   Fibonacci Design Type: {design_type} (alpha={alpha})")
    
    if design_type == 0:  # Fibonacci Spiral (Golden Ratio)
        cx, cy = C.SIZE//2, C.SIZE//2
        golden = (1 + math.sqrt(5)) / 2
        points = []
        # Draw spiral with visible thickness
        for t in range(0, 720, 4):
            rad = t * math.pi / 180
            r = 5 * math.exp(rad / (golden * 1.5))
            if r > C.SIZE//2 - 50:
                break
            x = cx + r * math.cos(rad)
            y = cy + r * math.sin(rad)
            points.append((int(x), int(y)))
        
        if len(points) > 1:
            for i in range(len(points)-1):
                draw.line([points[i], points[i+1]], fill=color, width=3)
        
        # Add Fibonacci dots along spiral
        for r in fib:
            if r < C.SIZE//2:
                angle = r * golden
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                draw.ellipse([x-3, y-3, x+3, y+3], fill=color)
    
    elif design_type == 1:  # Golden Rectangles (Fibonacci tiling)
        x, y = C.SIZE//4, C.SIZE//4
        max_size = C.SIZE//2
        for i, size in enumerate(fib):
            if size > max_size:
                break
            if i % 2 == 0:
                draw.rectangle([x, y, x+size, y+size], outline=color, width=2)
                x += size
            else:
                draw.rectangle([x, y, x+size, y+size], outline=color, width=2)
                y += size
        
        # Add second spiral in bottom-right
        x, y = C.SIZE - C.SIZE//4, C.SIZE - C.SIZE//4
        for i, size in enumerate(fib):
            if size > max_size:
                break
            if i % 2 == 0:
                draw.rectangle([x-size, y-size, x, y], outline=color, width=2)
                x -= size
            else:
                draw.rectangle([x-size, y-size, x, y], outline=color, width=2)
                y -= size
    
    elif design_type == 2:  # Fibonacci Circles (Sunflower pattern)
        cx, cy = C.SIZE//2, C.SIZE//2
        golden = (1 + math.sqrt(5)) / 2
        num_circles = random.choice([55, 89, 144])
        
        for i in range(num_circles):
            radius = math.sqrt(i) * 4
            if radius > C.SIZE//2 - 30:
                break
            angle = i * 2 * math.pi * golden
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            circle_size = 2 + (i % 5)
            draw.ellipse([x-circle_size, y-circle_size, x+circle_size, y+circle_size], 
                        fill=color, outline=color)
    
    elif design_type == 3:  # Fibonacci Waves (Sinusoidal)
        amplitude = random.randint(30, 80)
        frequency = random.choice([0.01, 0.02, 0.03, 0.05, 0.08, 0.13])
        
        # Draw multiple waves
        for y_offset in range(50, C.SIZE-50, random.choice([21, 34, 55])):
            points = []
            for x in range(0, C.SIZE, 5):
                y = y_offset + amplitude * math.sin(x * frequency) + amplitude * math.cos(x * frequency * golden)
                points.append((x, int(y)))
            for i in range(len(points)-1):
                draw.line([points[i], points[i+1]], fill=color, width=2)
    
    else:  # design_type == 4: Golden Triangles
        center_x, center_y = C.SIZE//2, C.SIZE//2
        radius = C.SIZE//3
        
        # Draw Fibonacci triangles
        for angle in range(0, 360, random.choice([36, 45, 60, 72])):
            rad = angle * math.pi / 180
            x1 = center_x + radius * math.cos(rad)
            y1 = center_y + radius * math.sin(rad)
            
            # Second point with golden ratio offset
            angle2 = angle + 137.5  # Golden angle
            rad2 = angle2 * math.pi / 180
            x2 = center_x + radius * math.cos(rad2)
            y2 = center_y + radius * math.sin(rad2)
            
            # Third point closer to center
            rad3 = (angle + 72) * math.pi / 180
            x3 = center_x + (radius//2) * math.cos(rad3)
            y3 = center_y + (radius//2) * math.sin(rad3)
            
            draw.polygon([(x1, y1), (x2, y2), (x3, y3)], outline=color, width=2)
    
    # Add Fibonacci grid overlay (always present but subtle)
    grid_alpha = alpha // 2
    grid_color = (255, 255, 255, grid_alpha)
    spacing = random.choice([21, 34, 55])
    for i in range(0, C.SIZE, spacing):
        draw.line([(i, 0), (i, C.SIZE)], fill=grid_color, width=1)
        draw.line([(0, i), (C.SIZE, i)], fill=grid_color, width=1)
    
    return Image.alpha_composite(img, design)

# ═══════════════════════════════════════════════════════════════════════════
#  BACKGROUND PROCESSING
# ═══════════════════════════════════════════════════════════════════════════

def process_background(path, seed):
    """Load, crop, blur, darken background image."""
    img = Image.open(path).convert('L')
    img = img.convert('RGB')
    w, h = img.size
    m = min(w, h)
    img = img.crop(((w-m)//2, (h-m)//2, (w-m)//2+m, (h-m)//2+m))
    img = img.resize((C.SIZE, C.SIZE), Image.Resampling.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.58)
    img = ImageEnhance.Contrast(img).enhance(0.78)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.0))
    img = img.convert('RGBA')
    overlay = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0,C.OVERLAY_ALPHA))
    img = Image.alpha_composite(img, overlay)
    
    # Add visible Fibonacci design
    if C.PATTERN_OVERLAY:
        img = add_fibonacci_design(img, seed)
    
    return img

def add_vignette(img, seed):
    """Darken edges, keep center bright."""
    random.seed(seed)
    v = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0,0))
    draw = ImageDraw.Draw(v)
    cx = cy = C.SIZE//2
    max_r = int(C.SIZE * 0.75)
    for r in range(max_r, 0, -30):
        alpha = int(25 * (1 - r/max_r)**1.5)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(0,0,0,alpha))
    return Image.alpha_composite(img, v)

# ═══════════════════════════════════════════════════════════════════════════
#  BINARY GRID – NO OVERLAP, PERFECT ALIGNMENT
# ═══════════════════════════════════════════════════════════════════════════

def draw_binary_grid(draw, binary_str, box, seed):
    """Draw exact, non‑overlapping binary squares."""
    binary = ''.join(c for c in binary_str if c in '01')
    if not binary:
        binary = '1010' * 16
    total = len(binary)
    random.seed(seed)

    x1, y1, x2, y2 = box
    w = x2 - x1
    h = y2 - y1

    # Determine grid dimensions (square-ish)
    cols = math.ceil(math.sqrt(total))
    rows = (total + cols - 1) // cols

    # Cell size (square cells)
    cell = min(w // cols, h // rows)
    # Center the grid inside the box
    offset_x = x1 + (w - cols * cell) // 2
    offset_y = y1 + (h - rows * cell) // 2

    opacity = int(255 * C.GRID_OPACITY)
    light = (255,255,255,opacity)
    dark = (0,0,0,opacity//2)

    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= total:
                break
            px = offset_x + col * cell
            py = offset_y + row * cell
            rect = [px, py, px + cell, py + cell]

            if binary[idx] == '1':
                if C.GLOW_EFFECT:
                    for r in range(2,0,-1):
                        glow = [px - r, py - r, px + cell + r, py + cell + r]
                        draw.rectangle(glow, fill=(255,255,255,opacity//4))
                draw.rectangle(rect, fill=light)
            else:
                draw.rectangle(rect, fill=dark)
            idx += 1
        if idx >= total:
            break

# ═══════════════════════════════════════════════════════════════════════════
#  DECORATIONS (CORNER, CIRCLES, DIAMONDS, ARROWS)
# ═══════════════════════════════════════════════════════════════════════════

class Decor:
    @staticmethod
    def corner(draw, box, color, seed):
        random.seed(seed)
        x1,y1,x2,y2 = box
        inset = random.choice([6,8,10])
        size = random.choice([13,21,34])
        
        # Top-left
        draw.line([(x1+inset, y1+2), (x1+inset+size, y1+2)], fill=color, width=2)
        draw.line([(x1+2, y1+inset), (x1+2, y1+inset+size)], fill=color, width=2)
        # Top-right
        draw.line([(x2-inset-size, y1+2), (x2-inset, y1+2)], fill=color, width=2)
        draw.line([(x2-2, y1+inset), (x2-2, y1+inset+size)], fill=color, width=2)
        # Bottom-left
        draw.line([(x1+inset, y2-2), (x1+inset+size, y2-2)], fill=color, width=2)
        draw.line([(x1+2, y2-inset-size), (x1+2, y2-inset)], fill=color, width=2)
        # Bottom-right
        draw.line([(x2-inset-size, y2-2), (x2-inset, y2-2)], fill=color, width=2)
        draw.line([(x2-2, y2-inset-size), (x2-2, y2-inset)], fill=color, width=2)

    @staticmethod
    def arrow(draw, cx, y, color, length=35):
        """Draw a horizontal arrow with two circles at ends."""
        # Thicker arrow for visibility
        draw.line([(cx - length - 10, y), (cx - 10, y)], fill=color, width=2)
        draw.line([(cx + 10, y), (cx + length + 10, y)], fill=color, width=2)
        # End circles
        draw.ellipse([cx - length - 15, y - 3, cx - length - 9, y + 3], fill=color)
        draw.ellipse([cx + length + 9, y - 3, cx + length + 15, y + 3], fill=color)
        # Center diamond
        draw.ellipse([cx - 3, y - 3, cx + 3, y + 3], fill=color)

    @staticmethod
    def diamond(draw, x, y, color, seed):
        random.seed(seed)
        size = random.choice([8,12,16])
        pts = [(x, y-size), (x+size, y), (x, y+size), (x-size, y)]
        draw.polygon(pts, outline=color, width=2)
        draw.ellipse([x-3, y-3, x+3, y+3], fill=color)

# ═══════════════════════════════════════════════════════════════════════════
#  GRADIENT BOX (TRANSPARENT AT BOTTOM)
# ═══════════════════════════════════════════════════════════════════════════

def draw_gradient_box(box_layer, box, seed):
    random.seed(seed)
    draw = ImageDraw.Draw(box_layer)
    if C.GRADIENT_BOX:
        for i, alpha_val in enumerate([10,8,5,3,2]):
            alpha = int(C.BOX_ALPHA * alpha_val / 10)
            off = i // 2
            draw.rounded_rectangle(
                [box[0]-off, box[1]-off, box[2]+off, box[3]+off],
                radius=10, fill=(0,0,0,alpha)
            )
    else:
        draw.rounded_rectangle(box, radius=10, fill=(0,0,0,C.BOX_ALPHA))
    return box_layer

# ═══════════════════════════════════════════════════════════════════════════
#  EMBLEM (BOTTOM‑LEFT)
# ═══════════════════════════════════════════════════════════════════════════

def draw_emblem(img, seed):
    if not os.path.exists("emblem.png"):
        return
    try:
        em = Image.open("emblem.png").convert("RGBA")
        if C.EMBLEM_OPACITY < 1.0:
            alpha = em.split()[3]
            alpha = alpha.point(lambda p: int(p * C.EMBLEM_OPACITY))
            em.putalpha(alpha)
        em = em.resize((C.EMBLEM_SIZE, C.EMBLEM_SIZE), Image.Resampling.LANCZOS)
        x = 20
        y = C.SIZE - C.EMBLEM_SIZE - 20
        img.paste(em, (x, y), em)
    except Exception as e:
        print(f"Emblem error: {e}")

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def create_binary_image(entry, bg_path, out_path):
    binary = entry.get("binary_message", "").strip()
    seed = get_seed(binary)

    print(f"   Design Seed: {seed}")
    
    # Background with visible Fibonacci design
    img = process_background(bg_path, seed)

    # Box for the binary grid (kept away from emblem)
    box_l = C.MARGIN
    box_r = C.SIZE - C.MARGIN
    # Reserve space at bottom for arrows + emblem
    bottom_reserve = C.EMBLEM_SIZE + 40
    box_y1 = 120
    box_y2 = C.SIZE - bottom_reserve
    box = (box_l, box_y1, box_r, box_y2)

    # Gradient overlay for the box
    box_layer = Image.new('RGBA', (C.SIZE, C.SIZE), (0,0,0,0))
    draw_gradient_box(box_layer, box, seed)
    
    if C.DECOR_BORDERS:
        # Create a draw object for the box_layer to add corners
        box_draw = ImageDraw.Draw(box_layer)
        Decor.corner(box_draw, box, col('accent'), seed)
    
    img = Image.alpha_composite(img, box_layer)

    # Draw binary grid inside the box
    draw = ImageDraw.Draw(img)
    draw_binary_grid(draw, binary, box, seed)

    # ----- ARROWS BELOW THE BINARY SQUARE (outside the box) -----
    arrow_y = box_y2 + 30   # below the box
    Decor.arrow(draw, C.SIZE//2, arrow_y, col('accent'), length=40)

    # Top‑right diamond
    Decor.diamond(draw, C.SIZE - C.MARGIN - 20, 40, col('accent'), seed+2000)

    # Mirror circle decorations
    circle_positions = [(C.MARGIN + 40, C.MARGIN + 30), 
                        (C.SIZE - C.MARGIN - 40, C.SIZE - C.MARGIN - 30)]
    for x, y in circle_positions:
        draw.ellipse([x-8, y-8, x+8, y+8], outline=col('accent'), width=2)
        draw.ellipse([x-2, y-2, x+2, y+2], fill=col('accent'))

    # Emblem (bottom‑left)
    draw_emblem(img, seed+3000)

    # Final darkening of edges
    img = add_vignette(img, seed+5000)

    # Save as JPEG
    rgb = Image.new('RGB', img.size, (0,0,0))
    rgb.paste(img, mask=img.split()[3])
    rgb.save(out_path, 'JPEG', quality=95, optimize=True)
    return True

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════

def main():
    try:
        with open("binary_quote.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ binary_quote.json not found")
        return
    except json.JSONDecodeError as e:
        print(f"❌ JSON error: {e}")
        return

    if isinstance(data, dict):
        data = [data]

    os.makedirs("binary_images", exist_ok=True)
    bg = "binary_quote_image.jpg"
    if not os.path.exists(bg):
        print(f"❌ Background missing: {bg}")
        return

    total = len(data)
    print(f"\n⚫⚪ BINARY GRID WITH FIBONACCI DESIGNS – {total} entries")
    print(f"   Grid opacity: {C.GRID_OPACITY} | Emblem: {C.EMBLEM_SIZE}px\n")

    success = failed = 0
    start = datetime.now()

    for idx, entry in enumerate(data, 1):
        preview = entry.get("binary_message", "")[:30] + "..."
        print(f"\n[{idx}/{total}] {preview}")
        out = os.path.join("binary_images", f"binary_{idx:03d}.jpg")
        try:
            create_binary_image(entry, bg, out)
            success += 1
            print(f"   ✓ Saved: {out}")
        except Exception as e:
            failed += 1
            print(f"   ✗ Error: {str(e)[:80]}")
            import traceback
            traceback.print_exc()

    elapsed = datetime.now() - start
    print(f"\n✅ Done – {success} ok, {failed} failed in {elapsed.total_seconds():.1f}s\n")

if __name__ == "__main__":
    main()