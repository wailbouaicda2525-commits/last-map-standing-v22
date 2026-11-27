"""
renderer_v23_geocine.py — Last Map Standing V23 GEO-CINEMA SATELLITE EDITION.
Drop-in upgrade for renderer_v22_saul_bass.py featuring:
  - @geomapstories-grade full-bleed Esri Satellite Earth + multi-pass Neon Bloom glow
  - Animated white dashed curved city routes + pulsing GPS pins + 3D city labels
  - Tilted real documentary Polaroid photo cards + 2.4s full-screen B-Roll cutaway (Pixabay / Wikimedia $0/mo)
  - High-CTR Satellite Miniatures for ALL 3 PLATFORMS:
      * YouTube Long-Form (1280x720 16:9) & Facebook Long-Form Video (1280x720 16:9)
      * TikTok Cover + Frame-0 Hook Lock (1080x1920 9:16), YouTube Shorts (9:16), Facebook Reels (9:16)
      * Facebook 3-Slide Satellite Photo Carousel (1080x1080 1:1)
"""
import math
import os
import subprocess
import time

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from map_geometry_v22 import (
    FONT_ANTON,
    FONT_BLACK,
    FONT_BOLD,
    FONT_MONO,
    get_font,
)
from satellite_engine_v23 import (
    SatelliteAtlas,
    draw_city_routes_and_pins,
    draw_floating_cinema_captions,
    draw_giant_stat_badge,
    fetch_scenario_photos,
    get_satellite_atlas,
    make_polaroid_card,
    project_pt,
    render_broll_cutaway_frame,
    render_satellite_map_layer,
)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def short_name(name: str) -> str:
    rep = {
        "United States of America": "USA",
        "United Kingdom": "UK",
        "South Africa": "S. Africa",
        "Saudi Arabia": "Saudi",
        "United Arab Emirates": "UAE",
        "New Zealand": "New Zealand",
        "North Dakota": "N. Dakota",
        "South Dakota": "S. Dakota",
        "North Carolina": "N. Carolina",
        "South Carolina": "S. Carolina",
        "West Virginia": "W. Virginia",
        "New Hampshire": "N. Hampshire",
        "Massachusetts": "Mass.",
        "Pennsylvania": "Penn.",
        "Trinidad and Tobago": "Trinidad",
        "Bosnia and Herzegovina": "Bosnia",
        "Dominican Republic": "Dom. Rep.",
        "Central African Republic": "C.A.R.",
        "Democratic Republic of the Congo": "DR Congo",
        "Papua New Guinea": "Papua N.G.",
    }
    res = rep.get(name, name)
    return res[:15] + "." if len(res) > 16 else res


def _ease_out_back(x: float) -> float:
    x = max(0.0, min(1.0, float(x)))
    c1, c3 = 1.70158, 2.70158
    return 1.0 + c3 * ((x - 1.0) ** 3) + c1 * ((x - 1.0) ** 2)


def _ease_in_out(x: float) -> float:
    x = max(0.0, min(1.0, float(x)))
    return x * x * (3.0 - 2.0 * x)


def _pick_neon_palette(sc: dict):
    """Distinct vivid neon palettes matched to scenario topic (still pure satellite cinema!)."""
    txt = f"{sc.get('id', '')} {sc.get('title_long', '')}".lower()
    mech = sc.get("mechanic", "collapse")
    if mech == "elevation_flood" or any(k in txt for k in ("ocean", "flood", "sea", "water", "freeze", "ice")):
        # Electric sky-cyan alive, deep coral-red danger, golden survivor
        return (255, 210, 20), (62, 54, 255), (38, 212, 255)
    if any(k in txt for k in ("oil", "fuel", "heat", "hot", "fire", "desert")):
        # Bright emerald-cyan alive, volcanic orange-red danger, blazing gold survivor
        return (215, 232, 30), (35, 78, 255), (30, 205, 255)
    if mech == "laser_line" or any(k in txt for k in ("electric", "power", "grid", "cyber", "internet")):
        # Classic @geomapstories electric cyan alive, molten crimson danger, radiant gold survivor!
        return (255, 214, 0), (54, 34, 255), (36, 214, 255)
    return (255, 212, 0), (58, 40, 255), (38, 212, 255)


def _compute_states_at_progress(sim: dict, prog: float):
    """Return (alive_set, eliminated_set, flashing_set, alive_count, day_num)."""
    sc = sim["scenario"]
    winner = sim["winner"]["name"]
    max_day = int(sc.get("max_day", 365))
    day_num = max(1, min(max_day, int(round(prog * max_day))))

    alive = set()
    elim = set()
    flash = set()
    for e in sim["entities"]:
        nm = e["name"]
        ef = float(e["elim_frac"])
        if nm == winner or prog < ef:
            alive.add(nm)
        elif prog < ef + 0.045:
            flash.add(nm)
            elim.add(nm)
        else:
            elim.add(nm)
    return alive, elim, flash, len(alive), day_num


def _draw_curved_arrow(draw: ImageDraw.ImageDraw, p0, p1, color=(255, 255, 255, 255), width=10):
    """Draws a bold high-CTR YouTube thumbnail curved arrow pointing right at the surviving region."""
    x0, y0 = p0
    x1, y1 = p1
    mx, my = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    dx, dy = x1 - x0, y1 - y0
    dist = max(1.0, math.hypot(dx, dy))
    cx = mx - (dy / dist) * min(90.0, dist * 0.25)
    cy = my + (dx / dist) * min(90.0, dist * 0.25)

    pts = []
    for k in range(28):
        t = k / 27.0
        px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x1
        py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y1
        pts.append((px, py))

    # Heavy dark outline then bright core
    draw.line(pts, fill=(10, 14, 24, 245), width=width + 10, joint="curve")
    draw.line(pts, fill=color, width=width, joint="curve")

    # Arrowhead at p1
    ang = math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0])
    hl = width * 3.1
    a1 = ang + math.radians(150)
    a2 = ang - math.radians(150)
    head = [
        (x1, y1),
        (x1 + math.cos(a1) * hl, y1 + math.sin(a1) * hl),
        (x1 + math.cos(a2) * hl, y1 + math.sin(a2) * hl),
    ]
    draw.polygon(head, fill=color, outline=(10, 14, 24, 255))


def _draw_angled_stamp(canvas_rgba: Image.Image, text: str, cx: int, cy: int,
                       angle: float = -7.0, bg=(235, 34, 56, 245), font_size: int = 38):
    f = get_font(FONT_BLACK, font_size)
    tmp = Image.new("RGBA", (10, 10))
    d0 = ImageDraw.Draw(tmp)
    bb = d0.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pad_x, pad_y = 30, 18
    w, h = tw + pad_x * 2, th + pad_y * 2
    box = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    d.rounded_rectangle((12, 16, 12 + w, 16 + h), radius=14, fill=(8, 12, 22, 175))
    d.rounded_rectangle((10, 10, 10 + w, 10 + h), radius=14, fill=bg, outline=(255, 255, 255, 255), width=5)
    d.text((10 + w // 2, 10 + h // 2 - 1), text, font=f, fill=(255, 255, 255, 255), anchor="mm")
    rot = box.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas_rgba.alpha_composite(rot, (cx - rot.width // 2, cy - rot.height // 2))


def _draw_bold_headline(draw: ImageDraw.ImageDraw, lines: list, cx: int, top_y: int,
                        max_w: int, base_size: int = 96, line_colors=None, anchor="mt"):
    """Draws massive YouTube/TikTok/Reels viral headline with heavy 3D outline & auto-fit."""
    colors = line_colors or [(255, 255, 255, 255), (255, 224, 27, 255)]
    y = top_y
    for idx, line in enumerate(lines):
        sz = base_size
        f = get_font(FONT_BLACK, sz)
        lw = draw.textlength(line, font=f)
        if lw > max_w:
            sz = max(36, int(sz * (max_w / lw)))
            f = get_font(FONT_BLACK, sz)
        col = colors[idx % len(colors)]
        sw = max(8, sz // 8)
        draw.text((cx, y + 8), line, font=f, fill=(8, 12, 22, 210), stroke_width=sw + 3, stroke_fill=(8, 12, 22, 210), anchor=anchor)
        draw.text((cx, y), line, font=f, fill=col, stroke_width=sw, stroke_fill=(9, 13, 24, 255), anchor=anchor)
        y += int(sz * 1.12)
    return y


def _split_thumb_lines(sc: dict):
    raw = (sc.get("thumb_top") or sc.get("title_short") or "ONLY 1 SURVIVES").upper().strip()
    if "." in raw and len(raw.split(".")) >= 2:
        parts = [p.strip() for p in raw.split(".") if p.strip()]
        if len(parts) >= 2:
            return [parts[0] + ".", " ".join(parts[1:]) + "."]
    words = raw.split()
    if len(words) <= 3:
        return [raw]
    mid = (len(words) + 1) // 2
    return [" ".join(words[:mid]), " ".join(words[mid:])]


def _pick_key_cities(atlas: SatelliteAtlas, sim: dict, max_n: int = 4):
    """Pick 3-4 dramatic real cities across first_out + runner_up + winner for dashed routes."""
    names = []
    for e in (sim.get("first_out") or [])[:2]:
        names.append(e["name"])
    if sim.get("runner_up"):
        names.append(sim["runner_up"]["name"])
    if sim.get("winner"):
        names.append(sim["winner"]["name"])
    pts = []
    seen = set()
    for nm in names:
        cands = atlas.get_entity_city_points(nm)
        if cands:
            c = cands[0]
            if c[0] not in seen:
                seen.add(c[0])
                pts.append(c)
        if len(pts) >= max_n:
            break
    return pts


# =====================================================================
# 1) VIRAL SATELLITE THUMBNAIL 16:9 — YOUTUBE LONG-FORM + FACEBOOK VIDEO!
# =====================================================================
def render_thumbnail_16x9(sim: dict, out_jpg: str, photos=None) -> str:
    W, H = 1280, 720
    sc = sim["scenario"]
    atlas = get_satellite_atlas(sc.get("arena", "world"))
    c_alive, c_danger, c_win = _pick_neon_palette(sc)

    # Dramatic late-stage crisis snapshot (~82% collapsed -> 5 glowing crimson hotspots, 1 radiant survivor!)
    alive, elim, flash, _, _ = _compute_states_at_progress(sim, 0.84)
    win_name = sim["winner"]["name"]
    # Highlight top 5 collapsing threats in blazing red so map has explosive contrast!
    hot_red = set(e["name"] for e in (sim.get("first_out") or [])[:8]) | flash | {sim["runner_up"]["name"]}
    hot_red.discard(win_name)

    fc_lon, fc_lat = atlas.cfg["default_center"]
    focus_px = atlas.lonlat_to_px(fc_lon, fc_lat)
    # Shift focus slightly up so top headline sits in clean sky/northern backdrop while arena fills center-bottom
    focus_px = (focus_px[0], focus_px[1] - atlas.H * 0.04)

    frame_bgr, M, _ = render_satellite_map_layer(
        atlas, W, H, focus_px, zoom=atlas.cfg["default_zoom_16x9"] * 1.06,
        alive_set=alive, eliminated_set=elim, flashing_set=hot_red,
        winner_name=win_name,
        highlight_color_bgr=c_alive, danger_color_bgr=c_danger, winner_color_bgr=c_win,
        mechanic=sc.get("mechanic", "collapse"), mech_prog=0.62, scenario=sc, vignette=True,
    )
    canvas = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")

    # Subtle top gradient scrim so giant headline explodes off the thumbnail on mobile & desktop!
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(250):
        a = int(195 * ((1.0 - y / 250.0) ** 1.4))
        gd.line([(0, y), (W, y)], fill=(6, 10, 20, a))
    canvas.alpha_composite(grad)

    # Draw dashed crisis routes between 3 real cities
    draw = ImageDraw.Draw(canvas)
    key_cities = _pick_key_cities(atlas, sim, max_n=3)
    scr_cities = [(nm, *project_pt((px, py), M)) for nm, px, py in key_cities]
    scr_cities = [(nm, sx, sy) for nm, sx, sy in scr_cities if 80 <= sx <= W - 80 and 180 <= sy <= H - 80]
    if scr_cities:
        draw_city_routes_and_pins(draw, scr_cities, progress=1.0, pin_color=(255, 224, 27, 255))

    # Point bold curved white arrow right at the radiant glowing survivor (zero pill/arrow overlap!)
    win_ent = atlas.entities.get(win_name)
    if win_ent:
        wx, wy = project_pt(win_ent["centroid_px"], M)
        wx = max(140, min(W - 140, wx))
        wy = max(255, min(H - 135, wy))
        dir_x = 1 if wx < W * 0.52 else -1
        ax = max(210, min(W - 210, wx + dir_x * 260))
        ay = max(290, wy + 125) if wy < 430 else max(275, wy - 140)
        _draw_curved_arrow(draw, (ax, ay + (-32 if ay > wy else 32)), (wx + dir_x * 32, wy + (16 if ay > wy else -16)), color=(255, 255, 255, 255), width=11)
        pill = (sc.get("thumb_pill") or "ONLY 1 SURVIVES").upper()
        f_p = get_font(FONT_BLACK, 36)
        pb = draw.textbbox((0, 0), pill, font=f_p)
        pw = pb[2] - pb[0] + 54
        px0 = max(30, min(W - pw - 30, int(ax - pw // 2)))
        py0 = max(240, min(H - 95, int(ay - 29)))
        draw.rounded_rectangle((px0, py0 + 6, px0 + pw, py0 + 64), radius=28, fill=(8, 12, 22, 190))
        draw.rounded_rectangle((px0, py0, px0 + pw, py0 + 58), radius=28,
                               fill=(255, 212, 18, 255), outline=(10, 14, 24, 255), width=5)
        draw.text((px0 + pw // 2, py0 + 29), pill, font=f_p, fill=(10, 14, 24, 255), anchor="mm")

    # Optional tilted documentary Polaroid photo tucked cleanly in bottom-right corner!
    if photos is None:
        photos = fetch_scenario_photos(sim, max_photos=1)
    if photos:
        pol = make_polaroid_card(photos[0], target_w=275, angle_deg=7.5, label=sc.get("elim_tag", "CRISIS"))
        canvas.alpha_composite(pol, (W - pol.width - 18, H - pol.height - 10))

    # Giant High-CTR Top Headline (2 bold lines!)
    lines = _split_thumb_lines(sc)
    _draw_bold_headline(draw, lines, cx=W // 2, top_y=24, max_w=W - 90, base_size=88,
                        line_colors=[(255, 255, 255, 255), (255, 224, 27, 255)])

    # Crimson Danger Stamp on bottom-left (leaves YouTube duration badge bottom-right completely clear!)
    stamp_txt = (sc.get("thumb_stamp") or f"{sim['total'] - 1} COLLAPSED").upper()
    _draw_angled_stamp(canvas, stamp_txt, cx=225, cy=H - 76, angle=-5.5, font_size=36)

    os.makedirs(os.path.dirname(os.path.abspath(out_jpg)), exist_ok=True)
    canvas.convert("RGB").save(out_jpg, "JPEG", quality=93, optimize=True)
    return out_jpg


# =====================================================================
# 2) VIRAL SATELLITE COVER 9:16 — TIKTOK + YOUTUBE SHORTS + FACEBOOK REELS!
# =====================================================================
def render_short_thumbnail_9x16(sim: dict, out_jpg: str, photos=None) -> str:
    """
    Renders a jaw-dropping 1080x1920 Satellite Cinema Cover AND returns the PIL RGBA image
    (also baked cleanly into Frame 0..0.45s so TikTok thumbnailOffset=100ms, FB Reels, & YT Shorts
    ALL display this exact viral miniature!).
    """
    img = _build_short_cover_rgba(sim, photos=photos)
    os.makedirs(os.path.dirname(os.path.abspath(out_jpg)), exist_ok=True)
    img.convert("RGB").save(out_jpg, "JPEG", quality=93, optimize=True)
    return out_jpg


def _build_short_cover_rgba(sim: dict, photos=None) -> Image.Image:
    W, H = 1080, 1920
    sc = sim["scenario"]
    atlas = get_satellite_atlas(sc.get("arena", "world"))
    c_alive, c_danger, c_win = _pick_neon_palette(sc)

    alive, elim, flash, _, _ = _compute_states_at_progress(sim, 0.80)
    win_name = sim["winner"]["name"]
    hot_red = set(e["name"] for e in (sim.get("first_out") or [])[:10]) | flash | {sim["runner_up"]["name"]}
    hot_red.discard(win_name)

    fc_lon, fc_lat = atlas.cfg["default_center"]
    center_px = atlas.lonlat_to_px(fc_lon, fc_lat)
    win_ent = atlas.entities.get(win_name)
    # Center 9:16 portrait cleanly between arena center & radiant winner so glowing winner is ALWAYS dead-center!
    if win_ent:
        wcx, wcy = win_ent["centroid_px"]
        focus_px = (wcx * 0.65 + center_px[0] * 0.35, wcy * 0.55 + center_px[1] * 0.45)
    else:
        focus_px = center_px

    frame_bgr, M, _ = render_satellite_map_layer(
        atlas, W, H, focus_px, zoom=1.02,
        alive_set=alive, eliminated_set=elim, flashing_set=hot_red,
        winner_name=win_name,
        highlight_color_bgr=c_alive, danger_color_bgr=c_danger, winner_color_bgr=c_win,
        mechanic=sc.get("mechanic", "collapse"), mech_prog=0.58, scenario=sc, vignette=True,
    )
    canvas = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")

    # Top & bottom cinematic gradient scrims (keeps center satellite glowing & vibrant!)
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(520):
        a = int(205 * ((1.0 - y / 520.0) ** 1.35))
        gd.line([(0, y), (W, y)], fill=(6, 10, 20, a))
    for y in range(440):
        a = int(195 * ((y / 440.0) ** 1.35))
        gd.line([(0, H - 440 + y), (W, H - 440 + y)], fill=(6, 10, 20, a))
    canvas.alpha_composite(grad)

    draw = ImageDraw.Draw(canvas)

    # Curved white dotted routes across top 3 real cities
    key_cities = _pick_key_cities(atlas, sim, max_n=3)
    scr_cities = [(nm, *project_pt((px, py), M)) for nm, px, py in key_cities]
    scr_cities = [(nm, sx, sy) for nm, sx, sy in scr_cities if 90 <= sx <= W - 90 and 580 <= sy <= 1320]
    if scr_cities:
        draw_city_routes_and_pins(draw, scr_cities, progress=1.0, pin_color=(255, 224, 27, 255))

    # Bold white arrow pointing cleanly to radiant glowing survivor (zero pill/arrow overlap!)
    if win_ent:
        wx, wy = project_pt(win_ent["centroid_px"], M)
        wx = max(140, min(W - 140, wx))
        wy = max(650, min(1220, wy))
        dir_x = 1 if wx < W * 0.50 else -1
        ax = max(210, min(W - 210, wx + dir_x * 265))
        ay = max(635, wy - 195) if wy > 840 else min(1160, wy + 205)
        # Arrow starts cleanly from pill edge and terminates right beside survivor!
        tip_x = wx + dir_x * 34
        tip_y = wy - 18 if ay < wy else wy + 18
        _draw_curved_arrow(draw, (ax, ay + (26 if ay < wy else -26)), (tip_x, tip_y), width=12)
        f_w = get_font(FONT_BLACK, 38)
        wtxt = "WHO SURVIVES?"
        wb = draw.textbbox((0, 0), wtxt, font=f_w)
        ww = wb[2] - wb[0] + 52
        px0 = max(40, min(W - ww - 40, int(ax - ww // 2)))
        py0 = int(ay - 30)
        draw.rounded_rectangle((px0, py0 + 6, px0 + ww, py0 + 66), radius=30, fill=(8, 12, 22, 185))
        draw.rounded_rectangle((px0, py0, px0 + ww, py0 + 60), radius=30,
                               fill=(255, 224, 27, 255), outline=(10, 14, 24, 255), width=5)
        draw.text((px0 + ww // 2, py0 + 30), wtxt, font=f_w, fill=(10, 14, 24, 255), anchor="mm")

    # Real Documentary Polaroid Photo tucked neatly on lower-left above TikTok caption safe zone!
    if photos is None:
        photos = fetch_scenario_photos(sim, max_photos=1)
    if photos:
        pol = make_polaroid_card(photos[0], target_w=320, angle_deg=-7.5, label=sc.get("elim_tag", "COLLAPSE"))
        canvas.alpha_composite(pol, (46, 1215))

    # Giant High-CTR Top Headline (ZERO missing emoji glyphs -> crisp drawn live beacon dot!)
    f_kicker = get_font(FONT_BLACK, 29)
    ktxt = f"LIVE MAP  •  {sc.get('rule_label', 'SATELLITE SIMULATION').upper()}"
    kb = draw.textbbox((0, 0), ktxt, font=f_kicker)
    kw = min(W - 80, kb[2] - kb[0] + 84)
    kx0 = (W - kw) // 2
    draw.rounded_rectangle((kx0, 168, kx0 + kw, 224), radius=28,
                           fill=(10, 16, 30, 228), outline=(0, 212, 255, 255), width=3)
    draw.ellipse((kx0 + 22, 188, kx0 + 38, 204), fill=(255, 48, 66, 255))
    draw.text((W // 2 + 12, 196), ktxt, font=f_kicker, fill=(56, 220, 255, 255), anchor="mm")

    lines = _split_thumb_lines(sc)
    _draw_bold_headline(draw, lines, cx=W // 2, top_y=252, max_w=W - 90, base_size=106,
                        line_colors=[(255, 255, 255, 255), (255, 224, 27, 255)])

    # Massive Bottom Stat + Crimson Danger Stamp (above TikTok UI bottom safe bar y <= 1560!)
    stamp_txt = (sc.get("thumb_stamp") or f"{sim['total'] - 1} COLLAPSED").upper()
    _draw_angled_stamp(canvas, stamp_txt, cx=735, cy=1390, angle=6.0, font_size=40)

    pill = (sc.get("thumb_pill") or "ONLY 1 SURVIVES").upper()
    f_p = get_font(FONT_BLACK, 48)
    pb = draw.textbbox((0, 0), pill, font=f_p)
    pw = pb[2] - pb[0] + 84
    px0 = (W - pw) // 2
    py0 = 1520
    draw.rounded_rectangle((px0, py0 + 8, px0 + pw, py0 + 88), radius=40, fill=(8, 12, 22, 200))
    draw.rounded_rectangle((px0, py0, px0 + pw, py0 + 80), radius=40,
                           fill=(235, 34, 56, 255), outline=(255, 255, 255, 255), width=5)
    draw.text((W // 2, py0 + 40), pill, font=f_p, fill=(255, 255, 255, 255), anchor="mm")

    return canvas


# =====================================================================
# 3) FACEBOOK 3-SLIDE SATELLITE PHOTO CAROUSEL (1080x1080)
# =====================================================================
def render_fb_carousel_slides_v23(sim: dict, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    W, H = 1080, 1080
    sc = sim["scenario"]
    atlas = get_satellite_atlas(sc.get("arena", "world"))
    c_alive, c_danger, c_win = _pick_neon_palette(sc)
    photos = fetch_scenario_photos(sim, max_photos=2)
    win = short_name(sim["winner"]["name"])
    ru = short_name(sim["runner_up"]["name"])
    f1 = short_name(sim["first_out"][0]["name"])
    fc_lon, fc_lat = atlas.cfg["default_center"]
    center_px = atlas.lonlat_to_px(fc_lon, fc_lat)

    out_paths = []
    configs = [
        (0.25, "SLIDE 1 / 3  •  THE SCENARIO", _split_thumb_lines(sc), "SWIPE TO SEE WHO FALLS FIRST  >>", False),
        (0.68, "SLIDE 2 / 3  •  FIRST TO COLLAPSE", [f"{f1.upper()} FALLS FIRST!", f"{int(sim['total']*0.68)} GONE ALREADY"], "SWIPE FOR THE FINAL 2 SHOWDOWN  >>", False),
        (1.00, "SLIDE 3 / 3  •  LAST MAP STANDING", [f"{win.upper()} SURVIVES!", f"BEATS {ru.upper()} IN FINAL 2"], "WOULD YOUR HOME SURVIVE? COMMENT!", True),
    ]

    for idx, (prog, kicker, hlines, cta, is_win) in enumerate(configs, 1):
        alive, elim, flash, _, _ = _compute_states_at_progress(sim, prog)
        wname = sim["winner"]["name"] if is_win else ""
        focus = atlas.entities.get(sim["winner"]["name"], {}).get("centroid_px", center_px) if is_win else center_px
        zm = 1.75 if is_win else 1.25
        frame_bgr, M, _ = render_satellite_map_layer(
            atlas, W, H, focus, zoom=zm,
            alive_set=alive, eliminated_set=elim, flashing_set=flash, winner_name=wname,
            highlight_color_bgr=c_alive, danger_color_bgr=c_danger, winner_color_bgr=c_win,
            mechanic=sc.get("mechanic", "collapse"), mech_prog=prog, scenario=sc, vignette=True,
        )
        canvas = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
        # Top & bottom gradient scrims
        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for y in range(300):
            gd.line([(0, y), (W, y)], fill=(6, 10, 20, int(190 * (1.0 - y / 300.0))))
        for y in range(220):
            gd.line([(0, H - 220 + y), (W, H - 220 + y)], fill=(6, 10, 20, int(205 * (y / 220.0))))
        canvas.alpha_composite(grad)
        d = ImageDraw.Draw(canvas)

        key_cities = _pick_key_cities(atlas, sim, max_n=3)
        scr_c = [(nm, *project_pt((px, py), M)) for nm, px, py in key_cities]
        scr_c = [(nm, sx, sy) for nm, sx, sy in scr_c if 80 <= sx <= W - 80 and 240 <= sy <= H - 200]
        draw_city_routes_and_pins(d, scr_c, progress=1.0)

        if photos and idx <= 2:
            pol = make_polaroid_card(photos[(idx - 1) % len(photos)], target_w=260, angle_deg=-7 if idx == 1 else 7)
            canvas.alpha_composite(pol, (W - pol.width - 28, H - pol.height - 125))

        f_k = get_font(FONT_BLACK, 26)
        d.text((W // 2, 46), kicker, font=f_k, fill=(56, 220, 255, 255), stroke_width=5, stroke_fill=(8, 12, 22, 255), anchor="mm")
        _draw_bold_headline(d, hlines, cx=W // 2, top_y=84, max_w=W - 90, base_size=72)

        f_c = get_font(FONT_BLACK, 32)
        cb = d.textbbox((0, 0), cta, font=f_c)
        cw = min(W - 80, cb[2] - cb[0] + 64)
        d.rounded_rectangle(((W - cw) // 2, H - 104, (W + cw) // 2, H - 36), radius=34,
                            fill=(235, 34, 56, 245) if not is_win else (255, 212, 18, 255),
                            outline=(255, 255, 255, 255), width=4)
        d.text((W // 2, H - 70), cta, font=f_c,
               fill=(255, 255, 255, 255) if not is_win else (10, 14, 24, 255), anchor="mm")

        p = os.path.join(out_dir, f"fb_slide{idx}_{sc['id']}.jpg")
        canvas.convert("RGB").save(p, "JPEG", quality=92, optimize=True)
        out_paths.append(p)
    return out_paths


# =====================================================================
# 4) V23 FULL-BLEED GEO-CINEMA SATELLITE 9:16 RENDERER (SHORTS / REELS / TIKTOK 65s!)
# =====================================================================
def render_short_9x16(
    sim: dict,
    words: list,
    mixed_audio_path: str,
    total_dur: float,
    out_mp4: str,
    fps: int = 30,
    show_vs_showdown: bool = False,
    cta_label: str = "NEXT MAP TOMORROW  •  SUBSCRIBE",
):
    t0_wall = time.time()
    W, H = 1080, 1920
    sc = sim["scenario"]
    atlas = get_satellite_atlas(sc.get("arena", "world"))
    c_alive, c_danger, c_win = _pick_neon_palette(sc)

    # Fetch real documentary photos ONCE (for Polaroid pop-ups + 2.4s B-Roll cutaway!)
    photos = fetch_scenario_photos(sim, max_photos=4)
    polaroids = []
    angles = [-8.5, 7.5, -6.0, 9.0]
    labels = [sc.get("elim_tag", "IMPACT"), "REAL FOOTAGE", "INFRASTRUCTURE", "SURVIVAL ZONE"]
    for i, ph in enumerate(photos):
        polaroids.append(make_polaroid_card(ph, target_w=340, angle_deg=angles[i % len(angles)], label=labels[i % len(labels)]))

    # Pre-build exact Viral Cover Poster for Frame 0.00s -> 0.45s (locks TikTok/Reels/Shorts miniature!)
    hook_poster_rgba = _build_short_cover_rgba(sim, photos=photos[:1])
    hook_poster_bgr = cv2.cvtColor(np.array(hook_poster_rgba.convert("RGB")), cv2.COLOR_RGB2BGR)

    # Key focal GPS waypoints for smooth cinematic camera flight!
    fc_lon, fc_lat = atlas.cfg["default_center"]
    home_px = atlas.lonlat_to_px(fc_lon, fc_lat)
    f1_name = sim["first_out"][0]["name"]
    ru_name = sim["runner_up"]["name"]
    win_name = sim["winner"]["name"]
    f1_px = atlas.entities.get(f1_name, {}).get("centroid_px", home_px)
    ru_px = atlas.entities.get(ru_name, {}).get("centroid_px", home_px)
    win_px = atlas.entities.get(win_name, {}).get("centroid_px", home_px)

    key_cities = _pick_key_cities(atlas, sim, max_n=4)
    base_z = atlas.cfg["default_zoom_9x16"]

    # Smooth camera keyframes: (time_frac, focus_px, zoom)
    cam_keys = [
        (0.00, home_px, base_z * 1.00),
        (0.16, f1_px,   base_z * 1.48),
        (0.38, home_px, base_z * 1.12),
        (0.62, ru_px,   base_z * 1.44),
        (0.78, ((ru_px[0] + win_px[0]) * 0.5, (ru_px[1] + win_px[1]) * 0.5), base_z * 1.38),
        (0.90, win_px,  base_z * 1.88),
        (1.00, win_px,  base_z * 2.02),
    ]

    def sample_camera(u: float):
        for i in range(len(cam_keys) - 1):
            u0, p0, z0 = cam_keys[i]
            u1, p1, z1 = cam_keys[i + 1]
            if u0 <= u <= u1:
                a = _ease_in_out((u - u0) / max(1e-5, u1 - u0))
                return (p0[0] + (p1[0] - p0[0]) * a, p0[1] + (p1[1] - p0[1]) * a), z0 + (z1 - z0) * a
        return cam_keys[-1][1], cam_keys[-1][2]

    # Timeline milestones
    t_hook_end = 0.45
    t_broll_start = total_dur * 0.44 if photos else -99.0
    t_broll_end = t_broll_start + 2.35 if photos else -99.0
    t_vs_start = total_dur - 12.2 if show_vs_showdown else total_dur + 99.0
    t_win_start = total_dur - 5.2

    total_frames = int(round(total_dur * fps))
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    cmd = [
        FFMPEG, "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0",
        "-i", mixed_audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-shortest", "-movflags", "+faststart",
        out_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    f_hud = get_font(FONT_BLACK, 32)
    f_cta = get_font(FONT_BLACK, 34)
    f_vs_h = get_font(FONT_BLACK, 44)
    f_vs_row = get_font(FONT_BLACK, 28)

    try:
        for fidx in range(total_frames):
            t = fidx / float(fps)
            u = min(1.0, t / max(0.1, total_dur))

            # --- PHASE 0: INSTANT-HOOK VIRAL SATELLITE COVER (0.00s -> 0.45s) ---
            # Guarantees TikTok (thumbnailOffset=100ms), FB Reels, & YT Shorts lock the viral miniature!
            if t < t_hook_end:
                hu = t / t_hook_end
                sc_z = 1.0 + 0.05 * hu
                nh, nw = int(round(H * sc_z)), int(round(W * sc_z))
                zoomed = cv2.resize(hook_poster_bgr, (nw, nh), interpolation=cv2.INTER_LINEAR)
                y0, x0 = (nh - H) // 2, (nw - W) // 2
                proc.stdin.write(zoomed[y0 : y0 + H, x0 : x0 + W].tobytes())
                continue

            # --- PHASE B-ROLL: 2.35s FULL-SCREEN REAL DOCUMENTARY CUTAWAY ---
            if t_broll_start <= t <= t_broll_end and photos:
                bu = (t - t_broll_start) / max(0.1, t_broll_end - t_broll_start)
                broll_rgba = render_broll_cutaway_frame(
                    photos[min(1, len(photos) - 1)], W, H, bu,
                    ticker_label=f"LIVE IMPACT  •  {sc.get('elim_tag', 'CRISIS').upper()}",
                )
                bd = ImageDraw.Draw(broll_rgba)
                draw_floating_cinema_captions(bd, words, t, W // 2, 1365, max_width=940, font_size=62)
                proc.stdin.write(cv2.cvtColor(np.array(broll_rgba.convert("RGB")), cv2.COLOR_RGB2BGR).tobytes())
                continue

            # --- MAIN PHASE: FULL-BLEED SATELLITE EARTH + NEON GLOW + ROUTES + POLAROIDS ---
            sim_u = min(1.0, max(0.0, (t - t_hook_end) / max(0.1, t_win_start - t_hook_end)))
            is_winner_phase = (t >= t_win_start)
            alive, elim, flash, n_alive, day_num = _compute_states_at_progress(sim, 1.0 if is_winner_phase else sim_u)
            focus_px, zoom = sample_camera(u)

            frame_bgr, M, _ = render_satellite_map_layer(
                atlas, W, H, focus_px, zoom,
                alive_set=alive, eliminated_set=elim, flashing_set=flash,
                winner_name=win_name if is_winner_phase else "",
                highlight_color_bgr=c_alive, danger_color_bgr=c_danger, winner_color_bgr=c_win,
                mechanic=sc.get("mechanic", "collapse"), mech_prog=sim_u, scenario=sc, vignette=True,
            )
            canvas = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            d = ImageDraw.Draw(canvas, "RGBA")

            # 1) Animated curved dotted routes connecting real cities!
            if key_cities:
                scr_c = [(nm, *project_pt((px, py), M)) for nm, px, py in key_cities]
                scr_c = [(nm, sx, sy) for nm, sx, sy in scr_c if 55 <= sx <= W - 55 and 220 <= sy <= 1480]
                if scr_c:
                    route_p = min(1.0, max(0.0, (sim_u - 0.06) / 0.55))
                    draw_city_routes_and_pins(d, scr_c, progress=route_p,
                                              pin_color=(255, 224, 27, 255), pulse_t=t)

            # 2) Pattern-Interrupt Tilted Polaroid Documentary Photo Cards popping smoothly over map!
            if polaroids and not is_winner_phase and t < t_vs_start:
                # Show Polaroid #0 at 14%..26%, Polaroid #2 at 56%..66% (never overlaps 74% stat badge!)
                pol_windows = [
                    (total_dur * 0.14, total_dur * 0.25, 0, (66, 350)),
                    (total_dur * 0.55, total_dur * 0.65, min(2, len(polaroids) - 1), (W - 430, 350)),
                ]
                for ps, pe, pidx, (px, py) in pol_windows:
                    if ps <= t <= pe:
                        age = t - ps
                        rem = pe - t
                        sc_pop = _ease_out_back(age / 0.28) if age < 0.28 else (max(0.01, rem / 0.22) if rem < 0.22 else 1.0)
                        pol = polaroids[pidx]
                        nw = max(8, int(round(pol.width * sc_pop)))
                        nh = max(8, int(round(pol.height * sc_pop)))
                        pr = pol.resize((nw, nh), Image.BILINEAR)
                        cx_p = px + pol.width // 2
                        cy_p = py + pol.height // 2
                        canvas.paste(pr, (cx_p - nw // 2, cy_p - nh // 2), pr)

            # 3) Giant Glowing @geomapstories Stat Callouts at dramatic beats!
            if not is_winner_phase and t < t_vs_start:
                elim_count = max(0, sim["total"] - n_alive)
                if 0.28 <= sim_u <= 0.38 and elim_count > 0:
                    pop = _ease_out_back((sim_u - 0.28) / 0.03)
                    draw_giant_stat_badge(d, W // 2, 520, f"{elim_count} FALL",
                                          sc.get("elim_tag", "ELIMINATED").upper(),
                                          accent=(255, 76, 86, 255), scale=min(1.0, pop))
                elif 0.74 <= sim_u <= 0.84:
                    pop = _ease_out_back((sim_u - 0.74) / 0.03)
                    draw_giant_stat_badge(d, W // 2, 520, f"{n_alive} LEFT",
                                          f"OUT OF {sim['total']} TERRITORIES",
                                          accent=(255, 224, 27, 255), scale=min(1.0, pop))

            # 4) Sleek Floating Glass Top Pill (minimal — leaves 96% of satellite Earth completely visible!)
            hud_txt = f"DAY {day_num}   •   {n_alive} LEFT" if not is_winner_phase else f"WINNER  •  {short_name(win_name).upper()} SURVIVES"
            hb = d.textbbox((0, 0), hud_txt, font=f_hud)
            hw = min(W - 80, hb[2] - hb[0] + 64)
            hx0 = (W - hw) // 2
            d.rounded_rectangle((hx0, 148, hx0 + hw, 212), radius=32,
                                fill=(10, 15, 28, 215),
                                outline=(255, 212, 18, 255) if is_winner_phase else (0, 212, 255, 255), width=3)
            d.text((W // 2, 180), hud_txt, font=f_hud,
                   fill=(255, 224, 27, 255) if is_winner_phase else (255, 255, 255, 255), anchor="mm")

            # 5) Optional Glassmorphic FINAL 2 VS SHOWDOWN overlay (TikTok 65s retention hook!)
            if show_vs_showdown and t_vs_start <= t < t_win_start:
                vu = min(1.0, (t - t_vs_start) / 0.35)
                cx0, cy0, cx1, cy1 = 68, 460, W - 68, 1080
                d.rounded_rectangle((cx0, cy0, cx1, cy1), radius=32,
                                    fill=(10, 16, 30, int(224 * vu)), outline=(0, 212, 255, 255), width=4)
                d.text((W // 2, cy0 + 52), f"{short_name(ru_name).upper()}   VS   {short_name(win_name).upper()}",
                       font=f_vs_h, fill=(255, 224, 27, 255), anchor="mm")
                for ri, row in enumerate((sim.get("vs_metrics") or [])[:4]):
                    ry = cy0 + 132 + ri * 116
                    d.text((W // 2, ry), row["label"], font=f_vs_row, fill=(210, 232, 248, 255), anchor="mm")
                    lv, rv = float(row["left_val"]), float(row["right_val"])
                    mx = max(100.0, lv, rv)
                    bw_max = 360
                    lw_bar = int((lv / mx) * bw_max * vu)
                    rw_bar = int((rv / mx) * bw_max * vu)
                    # Left bar (Runner-up — Crimson)
                    d.rounded_rectangle((W // 2 - 20 - lw_bar, ry + 26, W // 2 - 20, ry + 62), radius=10, fill=(235, 58, 72, 255))
                    d.text((W // 2 - 32 - lw_bar, ry + 44), f"{int(lv)}", font=f_vs_row, fill=(255, 255, 255, 255), anchor="rm")
                    # Right bar (Winner — Radiant Cyan/Gold)
                    d.rounded_rectangle((W // 2 + 20, ry + 26, W // 2 + 20 + rw_bar, ry + 62), radius=10, fill=(0, 212, 255, 255))
                    d.text((W // 2 + 32 + rw_bar, ry + 44), f"{int(rv)}", font=f_vs_row, fill=(255, 224, 27, 255), anchor="lm")

            # 6) Winner Crown Badge + Follow/Subscribe CTA Pill in final 5 seconds
            if is_winner_phase:
                wu = min(1.0, (t - t_win_start) / 0.35)
                pop = _ease_out_back(wu)
                draw_giant_stat_badge(d, W // 2, 430, short_name(win_name).upper(),
                                      "LAST MAP STANDING", accent=(255, 218, 28, 255), scale=min(0.86, 0.86 * pop))
                cb = d.textbbox((0, 0), cta_label, font=f_cta)
                cw = min(W - 80, cb[2] - cb[0] + 72)
                d.rounded_rectangle(((W - cw) // 2, 1520, (W + cw) // 2, 1592), radius=36,
                                    fill=(235, 34, 56, 245), outline=(255, 255, 255, 255), width=4)
                d.text((W // 2, 1556), cta_label, font=f_cta, fill=(255, 255, 255, 255), anchor="mm")

            # 7) Clean Floating @geomapstories Word-Synced Captions (NO black box!)
            draw_floating_cinema_captions(d, words, t, W // 2, 1365, max_width=940, font_size=62)

            proc.stdin.write(cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR).tobytes())
    finally:
        proc.stdin.close()

    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"FFmpeg V23 Short failed with rc={rc}")
    dt_s = time.time() - t0_wall
    print(f"[V23 SHORT] Rendered {total_frames}f ({total_dur:.1f}s) in {dt_s:.1f}s ({total_frames/max(0.1,dt_s):.1f} f/s) -> {out_mp4}", flush=True)
    return out_mp4


# =====================================================================
# 5) V23 FULL-BLEED GEO-CINEMA SATELLITE 16:9 LONG-FORM RENDERER (1920x1080)
# =====================================================================
def render_longform_16x9(
    sim: dict,
    act_spans: list,
    words: list,
    mixed_audio_path: str,
    total_dur: float,
    out_mp4: str,
    fps: int = 24,
):
    t0_wall = time.time()
    W, H = 1920, 1080
    sc = sim["scenario"]
    atlas = get_satellite_atlas(sc.get("arena", "world"))
    c_alive, c_danger, c_win = _pick_neon_palette(sc)

    photos = fetch_scenario_photos(sim, max_photos=4)
    polaroids = [make_polaroid_card(ph, target_w=360, angle_deg=(-7 if i % 2 == 0 else 7)) for i, ph in enumerate(photos)]

    fc_lon, fc_lat = atlas.cfg["default_center"]
    home_px = atlas.lonlat_to_px(fc_lon, fc_lat)
    f1_px = atlas.entities.get(sim["first_out"][0]["name"], {}).get("centroid_px", home_px)
    ru_px = atlas.entities.get(sim["runner_up"]["name"], {}).get("centroid_px", home_px)
    win_name = sim["winner"]["name"]
    win_px = atlas.entities.get(win_name, {}).get("centroid_px", home_px)
    ru_name = sim["runner_up"]["name"]
    key_cities = _pick_key_cities(atlas, sim, max_n=4)
    base_z = atlas.cfg["default_zoom_16x9"]

    total_frames = int(round(total_dur * fps))
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    cmd = [
        FFMPEG, "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0",
        "-i", mixed_audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-shortest", "-movflags", "+faststart",
        out_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    f_act = get_font(FONT_BLACK, 26)
    f_hud = get_font(FONT_BLACK, 34)
    f_ch_t = get_font(FONT_BLACK, 42)
    f_row = get_font(FONT_BLACK, 26)
    f_side = get_font(FONT_BOLD, 22)

    def draw_glass_chart(d, chart_data, cx0, cy0, cw, ch, anim_u):
        d.rounded_rectangle((cx0, cy0, cx0 + cw, cy0 + ch), radius=28,
                            fill=(8, 14, 26, 228), outline=(0, 212, 255, 255), width=4)
        d.text((cx0 + cw // 2, cy0 + 48), chart_data["title"].upper(), font=f_ch_t, fill=(255, 224, 27, 255), anchor="mm")
        rows = (chart_data.get("rows") or [])[:6]
        mx = max([float(r["value"]) for r in rows] + [1.0])
        for i, r in enumerate(rows):
            ry = cy0 + 115 + i * 74
            nm = short_name(r["name"])
            val = float(r["value"])
            surv = bool(r.get("survived"))
            d.text((cx0 + 36, ry + 20), nm, font=f_row, fill=(255, 255, 255, 255), anchor="lm")
            bx0 = cx0 + 305
            bw = int(((val / mx) * (cw - 415)) * anim_u)
            col = (0, 212, 255, 255) if surv else (235, 52, 68, 255)
            d.rounded_rectangle((bx0, ry + 4, bx0 + max(16, bw), ry + 38), radius=10, fill=col)
            d.text((bx0 + max(16, bw) + 16, ry + 20), f"{int(round(val))}", font=f_row,
                   fill=(255, 224, 27, 255) if surv else (255, 160, 165, 255), anchor="lm")

    try:
        for fidx in range(total_frames):
            t = fidx / float(fps)
            u = min(1.0, t / max(0.1, total_dur))

            # Active act lookup
            cur_act = act_spans[-1]
            for sp in act_spans:
                if sp["start"] <= t <= sp["end"]:
                    cur_act = sp
                    break
            st = cur_act.get("scene_type", "map")
            act_u = min(1.0, max(0.0, (t - cur_act["start"]) / max(0.1, cur_act["dur"])))

            # Brief 2.5s B-Roll cutaway in Act II for cinematic pacing!
            if photos and cur_act["act_id"] == 1 and 0.35 <= act_u <= 0.62:
                bu = (act_u - 0.35) / 0.27
                br = render_broll_cutaway_frame(photos[0], W, H, bu, ticker_label=cur_act["label"])
                draw_floating_cinema_captions(ImageDraw.Draw(br), words, t, W // 2, H - 96, max_width=1520, font_size=54)
                proc.stdin.write(cv2.cvtColor(np.array(br.convert("RGB")), cv2.COLOR_RGB2BGR).tobytes())
                continue

            is_winner_phase = (st == "vs_and_winner" and act_u >= 0.56)
            sim_prog = 1.0 if is_winner_phase else min(0.98, u * 1.08)
            alive, elim, flash, n_alive, day_num = _compute_states_at_progress(sim, sim_prog)

            # Smooth camera flight across acts
            if is_winner_phase:
                focus_px, zoom = win_px, base_z * (1.72 + 0.18 * act_u)
            elif cur_act["act_id"] == 1:
                focus_px = (home_px[0] + (f1_px[0] - home_px[0]) * act_u, home_px[1] + (f1_px[1] - home_px[1]) * act_u)
                zoom = base_z * (1.08 + 0.28 * act_u)
            elif cur_act["act_id"] == 4:
                focus_px = (home_px[0] + (ru_px[0] - home_px[0]) * act_u, home_px[1] + (ru_px[1] - home_px[1]) * act_u)
                zoom = base_z * (1.18 + 0.25 * act_u)
            else:
                focus_px, zoom = home_px, base_z * (1.02 + 0.08 * math.sin(u * math.pi))

            frame_bgr, M, _ = render_satellite_map_layer(
                atlas, W, H, focus_px, zoom,
                alive_set=alive, eliminated_set=elim, flashing_set=flash,
                winner_name=win_name if is_winner_phase else "",
                highlight_color_bgr=c_alive, danger_color_bgr=c_danger, winner_color_bgr=c_win,
                mechanic=sc.get("mechanic", "collapse"), mech_prog=sim_prog, scenario=sc, vignette=True,
            )
            canvas = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            d = ImageDraw.Draw(canvas, "RGBA")

            # Animated dashed real city routes
            if key_cities:
                scr_c = [(nm, *project_pt((px, py), M)) for nm, px, py in key_cities]
                scr_c = [(nm, sx, sy) for nm, sx, sy in scr_c if 80 <= sx <= W - 360 and 120 <= sy <= H - 140]
                if scr_c:
                    draw_city_routes_and_pins(d, scr_c, progress=min(1.0, u * 1.8), pulse_t=t)

            # Top-Left Floating Act Pill + Top-Right Day/Remaining Glass Pill
            d.rounded_rectangle((36, 32, 470, 86), radius=26, fill=(10, 15, 28, 215), outline=(0, 212, 255, 255), width=3)
            d.text((253, 59), cur_act["label"][:32], font=f_act, fill=(56, 220, 255, 255), anchor="mm")

            hud_txt = f"DAY {day_num}  •  {n_alive} / {sim['total']} LEFT"
            hb = d.textbbox((0, 0), hud_txt, font=f_hud)
            hw = hb[2] - hb[0] + 64
            d.rounded_rectangle((W - hw - 36, 30, W - 36, 92), radius=30, fill=(10, 15, 28, 215),
                                outline=(255, 212, 18, 255) if is_winner_phase else (235, 52, 68, 255), width=3)
            d.text((W - 36 - hw // 2, 61), hud_txt, font=f_hud, fill=(255, 255, 255, 255), anchor="mm")

            # Sleek Right-Side Translucent Top-5 Survivors Live Tracker (during map acts)
            if st == "map" and not is_winner_phase:
                d.rounded_rectangle((W - 320, 120, W - 36, 405), radius=22, fill=(10, 15, 28, 195), outline=(56, 189, 248, 180), width=2)
                d.text((W - 178, 150), "TOP SURVIVORS", font=f_act, fill=(255, 224, 27, 255), anchor="mm")
                for ti, te in enumerate((sim.get("top5") or [])[:5]):
                    ty = 196 + ti * 40
                    tnm = short_name(te["name"])
                    st_col = (56, 220, 255, 255) if te["name"] in alive else (130, 140, 155, 200)
                    d.text((W - 298, ty), f"{ti+1}. {tnm}", font=f_side, fill=st_col, anchor="lm")
                    d.text((W - 56, ty), f"{te['score']:.0f}", font=f_side, fill=(255, 224, 27, 255), anchor="rm")
                # Subtle Polaroid story card bottom-left during Act 1 & Act 4
                if polaroids and cur_act["act_id"] in (0, 4) and 0.25 <= act_u <= 0.85:
                    pol = polaroids[cur_act["act_id"] % len(polaroids)]
                    canvas.paste(pol, (40, H - pol.height - 135), pol)

            # Chart overlays (Act III & Act IV)
            if st == "chart1":
                draw_glass_chart(d, sim["chart1"], (W - 960) // 2, 190, 960, 580, min(1.0, act_u * 2.5))
            elif st == "map_and_chart2" and act_u >= 0.40:
                draw_glass_chart(d, sim["chart2"], (W - 960) // 2, 190, 960, 580, min(1.0, (act_u - 0.40) * 3.0))
            elif st == "vs_and_winner" and not is_winner_phase:
                # Glassmorphic Final 2 VS comparison panel
                vu = min(1.0, act_u * 3.0)
                vx0, vy0, vw, vh = (W - 1040) // 2, 190, 1040, 590
                d.rounded_rectangle((vx0, vy0, vx0 + vw, vy0 + vh), radius=28,
                                    fill=(8, 14, 26, 232), outline=(255, 212, 18, 255), width=4)
                vs_title = f"FINAL SHOWDOWN:  {short_name(ru_name).upper()}  VS  {short_name(win_name).upper()}"
                f_vt = f_ch_t
                if d.textlength(vs_title, font=f_vt) > vw - 70:
                    f_vt = get_font(FONT_BLACK, max(26, int(42 * ((vw - 70) / d.textlength(vs_title, font=f_vt)))))
                d.text((W // 2, vy0 + 52), vs_title, font=f_vt, fill=(255, 224, 27, 255), anchor="mm")
                for ri, row in enumerate((sim.get("vs_metrics") or [])[:4]):
                    ry = vy0 + 135 + ri * 108
                    d.text((W // 2, ry), row["label"], font=f_row, fill=(210, 232, 248, 255), anchor="mm")
                    lv, rv = float(row["left_val"]), float(row["right_val"])
                    mx = max(100.0, lv, rv)
                    lb = int((lv / mx) * 390 * vu)
                    rb = int((rv / mx) * 390 * vu)
                    d.rounded_rectangle((W // 2 - 24 - lb, ry + 24, W // 2 - 24, ry + 58), radius=10, fill=(235, 58, 72, 255))
                    d.text((W // 2 - 36 - lb, ry + 41), f"{int(lv)}", font=f_row, fill=(255, 255, 255, 255), anchor="rm")
                    d.rounded_rectangle((W // 2 + 24, ry + 24, W // 2 + 24 + rb, ry + 58), radius=10, fill=(0, 212, 255, 255))
                    d.text((W // 2 + 36 + rb, ry + 41), f"{int(rv)}", font=f_row, fill=(255, 224, 27, 255), anchor="lm")
            elif is_winner_phase:
                draw_giant_stat_badge(d, W // 2, 270, short_name(win_name).upper(),
                                      "LAST MAP STANDING  •  SURVIVOR", accent=(255, 218, 28, 255), scale=0.92)

            # Clean Floating Cinema Captions
            draw_floating_cinema_captions(d, words, t, W // 2, H - 96, max_width=1540, font_size=54)

            proc.stdin.write(cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR).tobytes())
    finally:
        proc.stdin.close()

    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"FFmpeg V23 Long-Form failed with rc={rc}")
    dt_s = time.time() - t0_wall
    print(f"[V23 LONGFORM] Rendered {total_frames}f ({total_dur:.1f}s) in {dt_s:.1f}s ({total_frames/max(0.1,dt_s):.1f} f/s) -> {out_mp4}", flush=True)
    return out_mp4
