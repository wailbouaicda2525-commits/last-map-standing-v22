"""
build_brand_assets.py — Official Behance Saul Bass Paper-Cut Atlas Branding for Last Map Standing.
Generates:
  1. brand/LastMapStanding-Avatar-1080x1080.png
  2. brand/LastMapStanding-YouTube-Banner-2560x1440.png (exact 1546x423 safe zone centered)
  3. brand/LastMapStanding-Watermark-150x150.png
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from map_geometry_v22 import (
    load_arena_geometry,
    make_saul_bass_paper_bg,
    get_font,
    PALETTE,
    FONT_ANTON,
    FONT_BLACK,
    FONT_MONO,
    BASE_DIR,
)
from renderer_v22_saul_bass import draw_paper_cut_map_cv, make_stamp_image

BRAND_DIR = os.path.join(BASE_DIR, "brand")
os.makedirs(BRAND_DIR, exist_ok=True)


def build_avatar():
    W, H = 1080, 1080
    bg = make_saul_bass_paper_bg(W, H, seed=31)
    arr = np.array(bg, dtype=np.uint8)
    geom = load_arena_geometry("us_states")
    status = {nm: ("alive" if nm in ("Montana", "Idaho", "Wyoming", "Texas", "North Dakota") else ("just_fell" if nm in ("California", "New York") else "eliminated")) for nm in geom}
    # Centered strictly inside YouTube circular avatar safe zone!
    draw_paper_cut_map_cv(arr, geom, (150, 355, W - 300, 370), status, shadow_offset=(10, 13), border_w=3)

    img = Image.fromarray(arr, "RGB").convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # Circle-safe Saul Bass frame bars top & bottom (100% legible even when cropped to a circle!)
    draw.rectangle([0, 0, W, 310], fill=PALETTE["ink_black"] + (255,))
    draw.rectangle([0, 310, W, 330], fill=PALETTE["vermilion"] + (255,))
    draw.text((W // 2, 224), "LAST MAP", font=get_font(FONT_ANTON, 146), fill=PALETTE["cream_text"], anchor="mm")

    draw.rectangle([0, H - 300, W, H], fill=PALETTE["ink_black"] + (255,))
    draw.rectangle([0, H - 318, W, H - 300], fill=PALETTE["warning_ochre"] + (255,))
    draw.text((W // 2, H - 208), "STANDING", font=get_font(FONT_ANTON, 140), fill=PALETTE["vermilion"], anchor="mm")

    out = os.path.join(BRAND_DIR, "LastMapStanding-Avatar-1080x1080.png")
    img.convert("RGB").save(out, optimize=True)
    print("SAVED AVATAR:", out)

    # Also crisp 150x150 YouTube Corner Watermark
    wm = Image.new("RGBA", (150, 150), PALETTE["ink_black"] + (235,))
    wd = ImageDraw.Draw(wm, "RGBA")
    wd.rectangle([0, 0, 150, 14], fill=PALETTE["vermilion"] + (255,))
    wd.rectangle([0, 136, 150, 150], fill=PALETTE["vermilion"] + (255,))
    wd.text((75, 68), "LMS", font=get_font(FONT_ANTON, 74), fill=PALETTE["cream_text"], anchor="mm")
    wd.text((75, 118), "ATLAS", font=get_font(FONT_MONO, 16), fill=PALETTE["warning_ochre"], anchor="mm")
    wm_out = os.path.join(BRAND_DIR, "LastMapStanding-Watermark-150x150.png")
    wm.save(wm_out, optimize=True)
    print("SAVED WATERMARK:", wm_out)


def build_banner():
    W, H = 2560, 1440
    # YouTube Mobile/Desktop Safe Area: centered 1546x423 -> x:[507..2053], y:[508..931]
    bg = make_saul_bass_paper_bg(W, H, seed=55)
    arr = np.array(bg, dtype=np.uint8)
    world = load_arena_geometry("world")
    status = {}
    for i, nm in enumerate(sorted(world.keys())):
        if nm in ("United States of America", "Canada", "Norway", "Australia", "Brazil", "Switzerland", "Algeria"):
            status[nm] = "alive"
        elif i % 9 == 0:
            status[nm] = "warning"
        elif i % 13 == 0:
            status[nm] = "just_fell"
        else:
            status[nm] = "eliminated"
    draw_paper_cut_map_cv(arr, world, (120, 160, W - 240, H - 320), status, shadow_offset=(10, 12), border_w=2)

    img = Image.fromarray(arr, "RGB").convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # Crisp dark Swiss editorial band spanning the full horizontal banner height [508..932]
    draw.rectangle([0, 504, W, 936], fill=(20, 20, 18, 242))
    draw.rectangle([0, 504, W, 520], fill=PALETTE["vermilion"] + (255,))
    draw.rectangle([0, 920, W, 936], fill=PALETTE["warning_ochre"] + (255,))

    # Safe-zone centered content (strictly inside x: [560..2000])
    draw.text((W // 2, 634), "LAST MAP STANDING", font=get_font(FONT_ANTON, 178), fill=PALETTE["cream_text"], anchor="mm")
    draw.text((W // 2, 766), "50 U.S. STATES & 195 NATIONS  •  DAY 0 TO DAY 365  •  ONLY 1 SURVIVES", font=get_font(FONT_MONO, 27), fill=PALETTE["warning_ochre"], anchor="mm")

    # Subtle pill badge bottom of safe area
    draw.rounded_rectangle([W // 2 - 260, 818, W // 2 + 260, 882], radius=8, fill=PALETTE["vermilion"] + (255,))
    draw.text((W // 2, 850), "DATA-DRIVEN MAP SIMULATIONS", font=get_font(FONT_BLACK, 26), fill=PALETTE["cream_text"], anchor="mm")

    out = os.path.join(BRAND_DIR, "LastMapStanding-YouTube-Banner-2560x1440.png")
    img.convert("RGB").save(out, optimize=True)
    print("SAVED BANNER:", out)


def build_fb_cover():
    """Official Facebook Page Cover (1640x624 — safe for Desktop & Mobile crop)."""
    W, H = 1640, 624
    bg = make_saul_bass_paper_bg(W, H, seed=62)
    arr = np.array(bg, dtype=np.uint8)
    world = load_arena_geometry("world")
    status = {}
    for i, nm in enumerate(sorted(world.keys())):
        if nm in ("United States of America", "Canada", "Norway", "Australia", "Brazil", "Switzerland", "Algeria"):
            status[nm] = "alive"
        elif i % 8 == 0:
            status[nm] = "warning"
        elif i % 11 == 0:
            status[nm] = "just_fell"
        else:
            status[nm] = "eliminated"
    draw_paper_cut_map_cv(arr, world, (120, 26, W - 240, H - 52), status, shadow_offset=(8, 10), border_w=2)

    img = Image.fromarray(arr, "RGB").convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # Crisp centered Saul Bass editorial band inside Facebook Mobile/Desktop Safe Area (1280x500 centered)
    draw.rectangle([0, 148, W, 476], fill=(20, 20, 18, 240))
    draw.rectangle([0, 148, W, 160], fill=PALETTE["vermilion"] + (255,))
    draw.rectangle([0, 464, W, 476], fill=PALETTE["warning_ochre"] + (255,))

    draw.text((W // 2, 248), "LAST MAP STANDING", font=get_font(FONT_ANTON, 128), fill=PALETTE["cream_text"] + (255,), anchor="mm")
    draw.text((W // 2, 344), "50 U.S. STATES & 195 NATIONS  •  ONLY 1 SURVIVES", font=get_font(FONT_MONO, 24), fill=PALETTE["warning_ochre"] + (255,), anchor="mm")

    draw.rounded_rectangle([W // 2 - 220, 386, W // 2 + 220, 438], radius=8, fill=PALETTE["vermilion"] + (255,))
    draw.text((W // 2, 412), "DATA-DRIVEN MAP SIMULATIONS", font=get_font(FONT_BLACK, 22), fill=PALETTE["cream_text"] + (255,), anchor="mm")

    out = os.path.join(BRAND_DIR, "LastMapStanding-Facebook-Cover-1640x624.png")
    img.convert("RGB").save(out, optimize=True)
    print("SAVED FB COVER:", out)


if __name__ == "__main__":
    build_avatar()
    build_banner()
    build_fb_cover()
