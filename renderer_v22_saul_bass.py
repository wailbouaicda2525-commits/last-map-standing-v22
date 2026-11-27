"""
renderer_v22_saul_bass.py — V22.3 ANTI-TEMPLATE Multi-Theme Cinema Engine for Last Map Standing.
Supports 4 Distinct Broadcast Cartography Themes + 3 Editorial Thumbnail Layouts + Alternating Panels:
  - Theme 1: Saul Bass Archival Paper (Signature V22.1 look)
  - Theme 2: Dark Tactical Radar (Obsidian command slate + cyan radar rings + crimson alerts)
  - Theme 3: Ocean Blueprint (Architectural maritime blueprint + white drafting lines + sky-blue land)
  - Theme 4: Thermal Amber Atlas (Dark obsidian charcoal + burnished gold + volcanic vermilion)
Renders:
  1. 16:9 Editorial Poster Thumbnails (1280x720 — 3 clean Swiss poster layouts!)
  2. 9:16 Vertical Map Simulation Shorts (1080x1920, 30fps)
  3. 16:9 Full-Length Adaptive Documentaries (1920x1080, 24fps) with:
     - Live Paper-Cut Vector Map + Swiss Leaderboard (alternates left/right!) + Chapter Bar
     - Animated Horizontal Bar Charts (Chart 1 & Chart 2)
     - Full-Screen Split VS SHOWDOWN Arena (Runner-Up vs Winner)
     - Climax Winner Archival Stamp Poster Reveal
100% Python ($0/month on GitHub Actions). Python 3.11+ safe.
"""
import math
import os
import subprocess
import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from map_geometry_v22 import (
    load_arena_geometry,
    transform_pt,
    make_themed_bg,
    make_saul_bass_paper_bg,
    get_theme_for_scenario,
    get_layout_variant,
    get_font,
    draw_text_crisp,
    PALETTE,
    THEMES,
    FONT_ANTON,
    FONT_BLACK,
    FONT_BOLD,
    FONT_MONO,
)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def short_name(name):
    return (
        name.replace("United States of America", "USA")
        .replace("United Kingdom", "UK")
        .replace("United Arab Emirates", "UAE")
        .replace("Bosnia and Herz.", "Bosnia")
        .replace("North Macedonia", "N. Macedonia")
        .replace("Central African Rep.", "C.A.R.")
        .replace("Dominican Rep.", "Dominican Rep")
        .replace("Dem. Rep. Congo", "DR Congo")
    )


def build_caption_chunks(words, max_words=3):
    chunks = []
    cur = []
    for w in words:
        cur.append(w)
        ends_punct = w["word"].endswith((".", "?", "!", ","))
        if len(cur) >= max_words or ends_punct:
            chunks.append({
                "words": cur,
                "start": cur[0]["start"],
                "end": cur[-1]["end"] + 0.12,
            })
            cur = []
    if cur:
        chunks.append({"words": cur, "start": cur[0]["start"], "end": cur[-1]["end"] + 0.25})
    return chunks


def _wrap_headline(draw, text, font, max_w):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        cand = (cur + " " + w).strip()
        if draw.textlength(cand, font=font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_paper_cut_map_cv(frame_np, geom, box, status_map, zoom=1.0, focus=(0.5, 0.5),
                          shadow_offset=(7, 9), border_w=2, theme=None):
    """Ultra-fast crisp themed paper-cut vector polygon rendering onto RGB numpy array."""
    th = theme or THEMES["saul_bass_paper"]
    sh_dx, sh_dy = shadow_offset
    sh_col = th["shadow_warm"]
    gap_col = th["cut_gap"]

    # Pass 1: Tactile cut-paper cast shadow beneath ALL polygons
    for name, gdata in geom.items():
        for poly in gdata["polygons"]:
            pts = np.array(
                [(int(p[0] + sh_dx), int(p[1] + sh_dy))
                 for p in (transform_pt(nx, ny, box, zoom=zoom, focus=focus) for nx, ny in poly)],
                dtype=np.int32,
            )
            cv2.fillPoly(frame_np, [pts], sh_col, cv2.LINE_AA)

    # Pass 2: Main flat tactile paper polygons + cut-gap borders
    for name, gdata in geom.items():
        st = status_map.get(name, "alive")
        if st == "winner":
            fill = th["alive_blue"]
            bcol = th["vermilion"]
            bw = border_w + 3
        elif st == "just_fell":
            fill = th["vermilion"]
            bcol = gap_col
            bw = border_w + 1
        elif st == "warning":
            fill = th["warning_ochre"]
            bcol = gap_col
            bw = border_w
        elif st == "eliminated":
            fill = th["eliminated"]
            bcol = gap_col
            bw = border_w
        else:
            fill = th["alive_blue"]
            bcol = gap_col
            bw = border_w

        for poly in gdata["polygons"]:
            pts = np.array(
                [transform_pt(nx, ny, box, zoom=zoom, focus=focus) for nx, ny in poly],
                dtype=np.int32,
            )
            cv2.fillPoly(frame_np, [pts], fill, cv2.LINE_AA)
            cv2.polylines(frame_np, [pts], True, bcol, bw, cv2.LINE_AA)


def draw_mechanic_overlay_cv(frame_np, scenario, box, progress, zoom=1.0, focus=(0.5, 0.5), theme=None):
    """Draw shrinking danger circle or sweeping geometric laser line if scenario uses one."""
    th = theme or THEMES["saul_bass_paper"]
    mech = scenario.get("mechanic", "collapse")
    vermilion = th["vermilion"]
    cream = th["header_text"]

    if mech == "shrinking_zone":
        zcx, zcy = scenario.get("zone_center", [0.5, 0.45])
        px, py = transform_pt(zcx, zcy, box, zoom=zoom, focus=focus)
        max_r = int(max(box[2], box[3]) * 0.62 * zoom)
        min_r = int(min(box[2], box[3]) * 0.06 * zoom)
        r = int(lerp(max_r, min_r, smoothstep(progress)))
        cv2.circle(frame_np, (int(px), int(py)), r, th["ink_black"], 12, cv2.LINE_AA)
        cv2.circle(frame_np, (int(px), int(py)), r, vermilion, 7, cv2.LINE_AA)
        cv2.circle(frame_np, (int(px), int(py)), max(4, r - 12), cream, 2, cv2.LINE_AA)

    elif mech == "laser_line":
        ang = math.radians(scenario.get("line_angle_deg", 30))
        nx, ny = math.cos(ang), math.sin(ang)
        d = lerp(-0.08, 1.18, smoothstep(progress))
        cx_n = d * nx
        cy_n = d * ny
        p0_n = (cx_n - ny * 2.0, cy_n + nx * 2.0)
        p1_n = (cx_n + ny * 2.0, cy_n - nx * 2.0)
        p0 = transform_pt(p0_n[0], p0_n[1], box, zoom=zoom, focus=focus)
        p1 = transform_pt(p1_n[0], p1_n[1], box, zoom=zoom, focus=focus)
        ip0, ip1 = (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1]))
        cv2.line(frame_np, ip0, ip1, th["ink_black"], 16, cv2.LINE_AA)
        cv2.line(frame_np, ip0, ip1, vermilion, 10, cv2.LINE_AA)
        cv2.line(frame_np, ip0, ip1, cream, 3, cv2.LINE_AA)


def make_stamp_image(text, w=420, h=110, color=None, angle=11, paper_fill=True, theme=None):
    """Create a physical ink rubber stamp overlay calibrated to the episode's visual theme."""
    th = theme or THEMES["saul_bass_paper"]
    col = color or th["vermilion"]
    rgba = (col[0], col[1], col[2], 246)
    stamp = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp, "RGBA")
    if paper_fill:
        sd.rectangle([6, 6, w - 6, h - 6], fill=th["stamp_bg"])
    sd.rectangle([6, 6, w - 6, h - 6], outline=rgba, width=8)
    sd.rectangle([16, 16, w - 16, h - 16], outline=rgba, width=2)
    f = get_font(FONT_ANTON, int(h * 0.48))
    while sd.textlength(text, font=f) > w - 46 and f.size > 24:
        f = get_font(FONT_ANTON, f.size - 3)
    sd.text((w // 2, h // 2), text, font=f, fill=rgba, anchor="mm")
    return stamp.rotate(angle, expand=True, resample=Image.BICUBIC)


# =====================================================================
# 1) 16:9 YOUTUBE THUMBNAIL GENERATOR (4 THEMES x 3 SWISS POSTER LAYOUTS!)
# =====================================================================
def render_thumbnail_16x9(sim, out_jpg):
    W, H = 1280, 720
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    layout = get_layout_variant(sc)
    geom = load_arena_geometry(sc["arena"])
    bg = make_themed_bg(W, H, theme=th, seed=77)
    arr = np.array(bg, dtype=np.uint8)

    ents = sim["entities"]
    total = len(ents)
    status_map = {}
    for i, e in enumerate(ents):
        u = i / max(1, total - 1)
        if u > 0.84:
            status_map[e["name"]] = "alive"
        elif u > 0.72:
            status_map[e["name"]] = "warning"
        elif u > 0.62:
            status_map[e["name"]] = "just_fell"
        else:
            status_map[e["name"]] = "eliminated"

    top_txt = sc.get("thumb_top", "ZERO POWER. 50 STATES.")[:28]
    pill_txt = sc.get("thumb_pill", "1 SURVIVES")[:14]
    stamp_txt = sc.get("thumb_stamp", f"{total - 1} ELIMINATED")
    unit = "50 STATES" if sc["arena"] == "us_states" else f"{total} NATIONS"

    if layout == 1:
        # LAYOUT 1: Split Left Editorial Magazine Column + Right Full-Height Dramatic Map
        sidebar_w = 438
        map_box = (sidebar_w + 26, 46, W - sidebar_w - 52, H - 92)
        draw_paper_cut_map_cv(arr, geom, map_box, status_map, shadow_offset=(9, 11), border_w=3, theme=th)
        draw_mechanic_overlay_cv(arr, sc, map_box, progress=0.68, theme=th)

        img = Image.fromarray(arr, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        draw.rectangle([0, 0, sidebar_w, H], fill=th["ink_black"] + (255,))
        draw.rectangle([sidebar_w, 0, sidebar_w + 12, H], fill=th["vermilion"] + (255,))

        # Top kicker badge
        draw.text((38, 48), f"DATA SIMULATION // {unit}", font=get_font(FONT_MONO, 20), fill=th["warning_ochre"] + (255,))
        draw.rectangle([38, 86, 168, 94], fill=th["vermilion"] + (255,))

        # Stacked giant editorial title
        f_stack = get_font(FONT_ANTON, 84)
        lines = _wrap_headline(draw, top_txt, f_stack, sidebar_w - 76)
        while len(lines) > 3 and f_stack.size > 54:
            f_stack = get_font(FONT_ANTON, f_stack.size - 6)
            lines = _wrap_headline(draw, top_txt, f_stack, sidebar_w - 76)
        ty = 130
        for ln in lines[:3]:
            draw.text((38, ty), ln, font=f_stack, fill=th["header_text"] + (255,))
            ty += int(f_stack.size * 1.12)

        # Bold Vermilion Pill + Sub-rule
        py0 = max(ty + 28, 446)
        draw.rounded_rectangle([38, py0, sidebar_w - 38, py0 + 96], radius=10, fill=th["vermilion"] + (255,))
        draw.text((sidebar_w // 2, py0 + 48), pill_txt, font=get_font(FONT_ANTON, 58), fill=th["header_text"] + (255,), anchor="mm")

        draw.text((38, H - 54), f"DAY 0–{sc.get('max_day', 365)}  //  LAST MAP STANDING",
                  font=get_font(FONT_MONO, 17), fill=th["warning_ochre"] + (255,))

        stamp = make_stamp_image(stamp_txt, w=410, h=104, angle=-8, theme=th)
        img.alpha_composite(stamp, (W - stamp.width - 28, H - stamp.height - 22))

    elif layout == 2:
        # LAYOUT 2: Full-Bleed Top Map Cinema Poster + Bold Bottom Headline Strip
        map_box = (44, 34, W - 88, H - 208)
        draw_paper_cut_map_cv(arr, geom, map_box, status_map, shadow_offset=(9, 11), border_w=3, theme=th)
        draw_mechanic_overlay_cv(arr, sc, map_box, progress=0.68, theme=th)

        img = Image.fromarray(arr, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        # Bottom heavy editorial poster strip
        draw.rectangle([0, H - 158, W, H], fill=th["ink_black"] + (255,))
        draw.rectangle([0, H - 170, W, H - 158], fill=th["vermilion"] + (255,))

        f_bot = get_font(FONT_ANTON, 82)
        while draw.textlength(top_txt, font=f_bot) > W - 430:
            f_bot = get_font(FONT_ANTON, f_bot.size - 4)
        draw.text((44, H - 79), top_txt, font=f_bot, fill=th["header_text"] + (255,), anchor="lm")

        draw.rounded_rectangle([W - 356, H - 124, W - 36, H - 34], radius=10, fill=th["vermilion"] + (255,))
        draw.text((W - 196, H - 79), pill_txt, font=get_font(FONT_ANTON, 56), fill=th["header_text"] + (255,), anchor="mm")

        # Floating top-right angled stamp
        stamp = make_stamp_image(stamp_txt, w=450, h=110, angle=-9, theme=th)
        img.alpha_composite(stamp, (W - stamp.width - 30, 24))

    else:
        # LAYOUT 0: Classic Approved V22.1 Saul Bass Top Swiss Editorial Banner!
        map_box = (48, 170, W - 96, H - 195)
        draw_paper_cut_map_cv(arr, geom, map_box, status_map, shadow_offset=(9, 11), border_w=3, theme=th)
        draw_mechanic_overlay_cv(arr, sc, map_box, progress=0.68, theme=th)

        img = Image.fromarray(arr, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        draw.rectangle([0, 0, W, 142], fill=th["ink_black"] + (255,))
        draw.rectangle([0, 142, W, 154], fill=th["vermilion"] + (255,))

        f_top = get_font(FONT_ANTON, 82)
        while draw.textlength(top_txt, font=f_top) > W - 440:
            f_top = get_font(FONT_ANTON, f_top.size - 4)
        draw.text((44, 71), top_txt, font=f_top, fill=th["header_text"] + (255,), anchor="lm")

        draw.rounded_rectangle([W - 360, 26, W - 36, 116], radius=10, fill=th["vermilion"] + (255,))
        draw.text((W - 198, 71), pill_txt, font=get_font(FONT_ANTON, 56), fill=th["header_text"] + (255,), anchor="mm")

        stamp = make_stamp_image(stamp_txt, w=470, h=118, angle=10, theme=th)
        img.alpha_composite(stamp, (W - stamp.width - 36, H - stamp.height - 26))

    img.convert("RGB").save(out_jpg, quality=94, optimize=True)
    return out_jpg


# =====================================================================
# 1B) 9:16 YOUTUBE SHORTS & FACEBOOK REELS CUSTOM MINIATURE (1080x1920)
# Uses 4 V22.3 Themes x 3 Vertical Poster Layouts (high-CTR mobile grid!)
# =====================================================================
def _fit_map_box(x, y, w, h, arena):
    ratio = 1.78 if arena == "world" else (1.42 if arena == "us_states" else 1.35)
    if (w / max(1.0, float(h))) > ratio:
        nw = int(h * ratio)
        return (x + (w - nw) // 2, y, nw, h)
    nh = int(w / ratio)
    return (x, y + (h - nh) // 2, w, nh)


def render_short_thumbnail_9x16(sim, out_jpg):
    """Render a bold, ultra-readable 1080x1920 (9:16) vertical poster thumbnail for Shorts & FB Reels."""
    W, H = 1080, 1920
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    layout = get_layout_variant(sc)
    geom = load_arena_geometry(sc["arena"])
    bg = make_themed_bg(W, H, theme=th, seed=88)
    arr = np.array(bg, dtype=np.uint8)

    ents = sim["entities"]
    total = len(ents)
    status_map = {}
    for i, e in enumerate(ents):
        u = i / max(1, total - 1)
        if u > 0.85:
            status_map[e["name"]] = "alive"
        elif u > 0.72:
            status_map[e["name"]] = "warning"
        elif u > 0.60:
            status_map[e["name"]] = "just_fell"
        else:
            status_map[e["name"]] = "eliminated"

    top_txt = sc.get("thumb_top", "ZERO POWER. 50 STATES.")[:28]
    pill_txt = sc.get("thumb_pill", "1 SURVIVES")[:14]
    stamp_txt = sc.get("thumb_stamp", f"{total - 1} ELIMINATED")
    unit = "STATES" if sc["arena"] == "us_states" else "NATIONS"

    if layout == 1:
        # VERTICAL LAYOUT 1: Dramatic Map Upper Canvas + Heavy Center-Bottom Magazine Block
        map_box = _fit_map_box(36, 210, W - 72, 760, sc["arena"])
        draw_paper_cut_map_cv(arr, geom, map_box, status_map, shadow_offset=(10, 12), border_w=3, theme=th)
        draw_mechanic_overlay_cv(arr, sc, map_box, progress=0.68, theme=th)

        img = Image.fromarray(arr, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        # Top slim ticker strip
        draw.rectangle([0, 0, W, 138], fill=th["ink_black"] + (255,))
        draw.rectangle([0, 138, W, 150], fill=th["vermilion"] + (255,))
        draw.text((W // 2, 69), f"LAST MAP STANDING  //  {total} {unit}", font=get_font(FONT_MONO, 32), fill=th["warning_ochre"] + (255,), anchor="mm")

        # Bottom heavy Swiss poster typography block
        blk_y0 = 1040
        draw.rectangle([0, blk_y0, W, H], fill=th["ink_black"] + (255,))
        draw.rectangle([0, blk_y0 - 14, W, blk_y0], fill=th["vermilion"] + (255,))

        f_big = get_font(FONT_ANTON, 134)
        lines = _wrap_headline(draw, top_txt, f_big, W - 150)
        while len(lines) > 2 and f_big.size > 90:
            f_big = get_font(FONT_ANTON, f_big.size - 8)
            lines = _wrap_headline(draw, top_txt, f_big, W - 150)
        ty = blk_y0 + 72
        for ln in lines[:2]:
            draw.text((W // 2, ty), ln, font=f_big, fill=th["header_text"] + (255,), anchor="ma")
            ty += int(f_big.size * 1.14)

        py0 = max(ty + 46, 1480)
        draw.rounded_rectangle([140, py0, W - 140, py0 + 148], radius=16, fill=th["vermilion"] + (255,))
        draw.text((W // 2, py0 + 74), pill_txt, font=get_font(FONT_ANTON, 96), fill=th["header_text"] + (255,), anchor="mm")
        draw.text((W // 2, H - 110), f"DAY 0 → DAY {sc.get('max_day', 365)}  •  ONLY 1 SURVIVES",
                  font=get_font(FONT_MONO, 32), fill=th["warning_ochre"] + (255,), anchor="mm")

        stamp = make_stamp_image(stamp_txt, w=520, h=126, angle=-9, theme=th)
        img.alpha_composite(stamp, (W - stamp.width - 36, blk_y0 - stamp.height - 28))

    elif layout == 2:
        # VERTICAL LAYOUT 2: Giant Top Stacked Poster Banner + Centered High-Impact Map + Bottom CTA Pill
        map_box = _fit_map_box(36, 650, W - 72, 780, sc["arena"])
        draw_paper_cut_map_cv(arr, geom, map_box, status_map, shadow_offset=(10, 12), border_w=3, theme=th)
        draw_mechanic_overlay_cv(arr, sc, map_box, progress=0.68, theme=th)

        img = Image.fromarray(arr, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        draw.rectangle([0, 0, W, 560], fill=th["ink_black"] + (255,))
        draw.rectangle([0, 560, W, 578], fill=th["vermilion"] + (255,))
        draw.text((64, 72), f"MAP SIMULATION  //  {total} {unit}", font=get_font(FONT_MONO, 32), fill=th["warning_ochre"] + (255,))

        f_big = get_font(FONT_ANTON, 146)
        lines = _wrap_headline(draw, top_txt, f_big, W - 128)
        while len(lines) > 2 and f_big.size > 96:
            f_big = get_font(FONT_ANTON, f_big.size - 8)
            lines = _wrap_headline(draw, top_txt, f_big, W - 128)
        ty = 148
        for ln in lines[:2]:
            draw.text((64, ty), ln, font=f_big, fill=th["header_text"] + (255,))
            ty += int(f_big.size * 1.14)

        # Bottom massive pill + footer bar
        draw.rectangle([0, H - 340, W, H], fill=th["ink_black"] + (255,))
        draw.rectangle([0, H - 354, W, H - 340], fill=th["vermilion"] + (255,))
        draw.rounded_rectangle([120, H - 286, W - 120, H - 142], radius=16, fill=th["vermilion"] + (255,))
        draw.text((W // 2, H - 214), pill_txt, font=get_font(FONT_ANTON, 94), fill=th["header_text"] + (255,), anchor="mm")
        draw.text((W // 2, H - 72), "LAST MAP STANDING  •  DATA SIMULATION",
                  font=get_font(FONT_MONO, 30), fill=th["warning_ochre"] + (255,), anchor="mm")

        stamp = make_stamp_image(stamp_txt, w=540, h=130, angle=9, theme=th)
        img.alpha_composite(stamp, (W - stamp.width - 36, H - 360 - stamp.height - 16))

    else:
        # VERTICAL LAYOUT 0: Classic Saul Bass Editorial Header + Center Map + Huge Bottom Verdict Strip
        map_box = _fit_map_box(36, 560, W - 72, 820, sc["arena"])
        draw_paper_cut_map_cv(arr, geom, map_box, status_map, shadow_offset=(10, 12), border_w=3, theme=th)
        draw_mechanic_overlay_cv(arr, sc, map_box, progress=0.68, theme=th)

        img = Image.fromarray(arr, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        draw.rectangle([0, 0, W, 490], fill=th["ink_black"] + (255,))
        draw.rectangle([0, 490, W, 508], fill=th["vermilion"] + (255,))

        # Centered huge pill at top + bold title with clean breathing margin above red bar
        draw.rounded_rectangle([250, 42, W - 250, 138], radius=14, fill=th["vermilion"] + (255,))
        draw.text((W // 2, 90), pill_txt, font=get_font(FONT_ANTON, 70), fill=th["header_text"] + (255,), anchor="mm")

        f_big = get_font(FONT_ANTON, 122)
        lines = _wrap_headline(draw, top_txt, f_big, W - 130)
        while len(lines) > 2 and f_big.size > 86:
            f_big = get_font(FONT_ANTON, f_big.size - 8)
            lines = _wrap_headline(draw, top_txt, f_big, W - 130)
        ty = 166 if len(lines) == 2 else 236
        for ln in lines[:2]:
            draw.text((W // 2, ty), ln, font=f_big, fill=th["header_text"] + (255,), anchor="ma")
            ty += int(f_big.size * 1.14)

        stamp = make_stamp_image(stamp_txt, w=540, h=132, angle=10, theme=th)
        img.alpha_composite(stamp, (W - stamp.width - 42, 1340))

        draw.rectangle([0, H - 240, W, H], fill=th["ink_black"] + (255,))
        draw.rectangle([0, H - 252, W, H - 240], fill=th["vermilion"] + (255,))
        draw.text((W // 2, H - 146), f"ONLY 1 OF {total} {unit} SURVIVES",
                  font=get_font(FONT_ANTON, 72), fill=th["header_text"] + (255,), anchor="mm")
        draw.text((W // 2, H - 64), "LAST MAP STANDING  //  REAL DATA SIMULATION",
                  font=get_font(FONT_MONO, 28), fill=th["warning_ochre"] + (255,), anchor="mm")

    img.convert("RGB").save(out_jpg, quality=94, optimize=True)
    return out_jpg


# =====================================================================
# 2) 9:16 VERTICAL SHORT & TIKTOK RENDERER (V22.8 VS SHOWDOWN + CTA)
# =====================================================================
def _draw_vs_showdown_vertical_9x16(img, draw, W, H, sim, local_u, theme):
    """V22.8 Vertical 9:16 FINAL 2 VS SHOWDOWN data-bar scene (y=304..1346 viewport).
    Drives massive pauses, rewatches, comments & TikTok Additional Reward RPM!"""
    th = theme
    ru_n = short_name(sim["runner_up"]["name"]).upper()
    win_n = short_name(sim["winner"]["name"]).upper()
    cx = W // 2

    # Two high-contrast Contender Cards + central VS medallion
    draw.rectangle([44, 338, cx - 54, 496], fill=th["ink_black"] + (255,))
    draw.rectangle([44, 338, 64, 496], fill=th["warning_ochre"] + (255,))
    draw.text((88, 370), "FINALIST A", font=get_font(FONT_MONO, 24), fill=th["warning_ochre"] + (255,))
    f_cn_l = get_font(FONT_ANTON, 54 if len(ru_n) <= 10 else 44)
    draw.text((88, 412), ru_n[:14], font=f_cn_l, fill=th["header_text"] + (255,))

    draw.rectangle([cx + 54, 338, W - 44, 496], fill=th["ink_black"] + (255,))
    draw.rectangle([W - 64, 338, W - 44, 496], fill=th["alive_blue"] + (255,))
    draw.text((W - 88, 370), "FINALIST B", font=get_font(FONT_MONO, 24), fill=th["stat_ok"] + (255,), anchor="ra")
    f_cn_r = get_font(FONT_ANTON, 54 if len(win_n) <= 10 else 44)
    draw.text((W - 88, 412), win_n[:14], font=f_cn_r, fill=th["header_text"] + (255,), anchor="ra")

    draw.ellipse([cx - 56, 361, cx + 56, 473], fill=th["vermilion"] + (255,), outline=th["ink_black"] + (255,), width=6)
    draw.text((cx, 417), "VS", font=get_font(FONT_ANTON, 58), fill=th["header_text"] + (255,), anchor="mm")

    # 4 Animated Real-Data Comparison Bars (cleanly inside y=542..1296!)
    y0 = 548
    gap = 190
    max_half = 360
    f_metric = get_font(FONT_BLACK, 28)
    f_score = get_font(FONT_ANTON, 46)

    for idx, vm in enumerate(sim["vs_metrics"][:4]):
        my = y0 + idx * gap
        bu = ease_out_cubic(max(0.0, min(1.0, (local_u * 2.3) - idx * 0.14)))
        lw = max(14, int((vm["left_val"] / 100.0) * max_half * bu))
        rw = max(14, int((vm["right_val"] / 100.0) * max_half * bu))

        # Centered Metric Label Pill
        draw.rectangle([cx - 190, my, cx + 190, my + 46], fill=th["ink_black"] + (255,))
        draw.text((cx, my + 23), vm["label"], font=f_metric, fill=th["header_text"] + (255,), anchor="mm")

        # Left Contender Bar (expanding leftward from center)
        by0, by1 = my + 66, my + 132
        lx1 = cx - 18
        lx0 = lx1 - lw
        draw.rectangle([lx0 - 6, by0 + 6, lx1 - 6, by1 + 6], fill=th["shadow_warm"] + (255,))
        draw.rectangle([lx0, by0, lx1, by1], fill=th["warning_ochre"] + (255,), outline=th["ink_black"] + (255,), width=3)
        draw.text((lx0 - 16, (by0 + by1) // 2), f"{int(vm['left_val'] * bu)}", font=f_score, fill=th["body_text"] + (255,), anchor="rm")

        # Right Contender Bar (expanding rightward from center)
        rx0 = cx + 18
        rx1 = rx0 + rw
        draw.rectangle([rx0 + 6, by0 + 6, rx1 + 6, by1 + 6], fill=th["shadow_warm"] + (255,))
        draw.rectangle([rx0, by0, rx1, by1], fill=th["alive_blue"] + (255,), outline=th["ink_black"] + (255,), width=3)
        draw.text((rx1 + 16, (by0 + by1) // 2), f"{int(vm['right_val'] * bu)}", font=f_score, fill=th["body_text"] + (255,), anchor="lm")


def render_short_9x16(
    sim,
    words,
    audio_m4a,
    total_dur,
    out_mp4,
    fps=30,
    show_vs_showdown=False,
    cta_label="NEXT MAP TOMORROW  •  SUBSCRIBE",
):
    W, H = 1080, 1920
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    geom = load_arena_geometry(sc["arena"])
    ents = sim["entities"]
    total = len(ents)
    max_day = sc.get("max_day", 365)
    winner = sim["winner"]
    runner_up = sim["runner_up"]

    t_hook_end = 0.92
    t_start_elim = 1.25
    t_winner = max(t_start_elim + 4.0, total_dur - (5.4 if show_vs_showdown else 4.2))
    t_vs_start = max(t_start_elim + 8.0, t_winner - 7.8) if show_vs_showdown else 99999.0
    t_vs_end = (t_winner - 0.25) if show_vs_showdown else -1.0
    t_cta_start = max(t_winner + 0.3, total_dur - 3.8)
    elim_time = {}
    elim_cutoff_t = (t_vs_start - 0.4) if show_vs_showdown else (t_winner - 1.6)
    for i, e in enumerate(ents):
        if e["name"] == winner["name"]:
            elim_time[e["name"]] = 99999.0
        elif e["name"] == runner_up["name"]:
            elim_time[e["name"]] = t_winner - 0.15
        else:
            u = i / max(1, total - 2)
            elim_time[e["name"]] = t_start_elim + (u ** 1.15) * max(1.0, elim_cutoff_t - t_start_elim)

    f0 = sim["first_out"][0]["centroid"]
    fmid = ents[total // 2]["centroid"]
    fru = runner_up["centroid"]
    fwin = winner["centroid"]
    cam_keys = [
        (0.0, 1.08, 0.50, 0.48),
        (t_hook_end, 1.18, max(0.26, min(0.74, f0[0])), max(0.26, min(0.74, f0[1]))),
        (t_start_elim, 1.03, 0.50, 0.48),
        (t_start_elim + 2.5, 1.38, max(0.22, min(0.78, f0[0])), max(0.22, min(0.78, f0[1]))),
        (lerp(t_start_elim, t_winner, 0.48), 1.18, max(0.22, min(0.78, fmid[0])), max(0.22, min(0.78, fmid[1]))),
        (t_winner - 2.5, 1.36, max(0.22, min(0.78, fru[0])), max(0.22, min(0.78, fru[1]))),
        (t_winner, 1.56, max(0.22, min(0.78, fwin[0])), max(0.22, min(0.78, fwin[1]))),
        (total_dur, 1.64, max(0.22, min(0.78, fwin[0])), max(0.22, min(0.78, fwin[1]))),
    ]

    def sample_cam(t):
        if t <= cam_keys[0][0]:
            return cam_keys[0][1], (cam_keys[0][2], cam_keys[0][3])
        for i in range(len(cam_keys) - 1):
            t0, z0, x0, y0 = cam_keys[i]
            t1, z1, x1, y1 = cam_keys[i + 1]
            if t0 <= t <= t1:
                u = smoothstep((t - t0) / max(0.001, t1 - t0))
                return lerp(z0, z1, u), (lerp(x0, x1, u), lerp(y0, y1, u))
        return cam_keys[-1][1], (cam_keys[-1][2], cam_keys[-1][3])

    elim_tag = sc.get("elim_tag", "ELIMINATED")
    spotlights = [
        (sim["first_out"][0]["name"], elim_time[sim["first_out"][0]["name"]], elim_time[sim["first_out"][0]["name"]] + 2.5, elim_tag, False),
        (ents[total // 3]["name"], elim_time[ents[total // 3]["name"]], elim_time[ents[total // 3]["name"]] + 2.5, elim_tag, False),
        (ents[(total * 2) // 3]["name"], elim_time[ents[(total * 2) // 3]["name"]], elim_time[ents[(total * 2) // 3]["name"]] + 2.5, elim_tag, False),
        (runner_up["name"], elim_time[runner_up["name"]] - 0.2, t_winner - 0.1, elim_tag, False),
        (winner["name"], t_winner - 0.1, total_dur + 1.0, "LAST STANDING", True),
    ]

    base_bg = make_themed_bg(W, H, theme=th, seed=22)
    base_arr = np.array(base_bg, dtype=np.uint8)
    map_box = (18, 360, W - 36, 940)
    chunks = build_caption_chunks(words, max_words=3)

    f_rule = get_font(FONT_MONO, 30)
    f_day = get_font(FONT_ANTON, 108)
    f_left = get_font(FONT_ANTON, 92)
    f_pin = get_font(FONT_BLACK, 34)
    f_sub = get_font(FONT_ANTON, 82)
    f_foot = get_font(FONT_MONO, 28)

    win_stamp = make_stamp_image("LAST STANDING", w=460, h=110, color=th["alive_blue"], angle=-7, theme=th)
    hook_stamp = make_stamp_image(f"{total - 1} FALL  •  1 SURVIVES", w=760, h=136, color=th["vermilion"], angle=-4, theme=th)

    ff_cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-",
        "-i", audio_m4a,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-shortest",
        out_mp4,
    ]
    proc = subprocess.Popen(ff_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    total_frames = int(total_dur * fps)

    for fi in range(total_frames):
        t = fi / fps
        zoom, focus = sample_cam(t)
        is_short_hook = (t < t_hook_end)
        is_vs_scene = (show_vs_showdown and (t_vs_start <= t < t_vs_end))

        status_map = {}
        rem = 0
        if is_vs_scene:
            rem = 2
            day_num = max(1, int(max_day * 0.96))
            frame_np = base_arr.copy()
        elif is_short_hook:
            # V22.5 Frame-0 Scroll-Stopper Flash-Forward: collapse map immediately without spoiling winner!
            hook_u = smoothstep(t / max(0.05, t_hook_end - 0.04))
            prog = 0.25 + 0.72 * hook_u
            day_num = int(prog * max_day)
            cutoff = int(prog * max(1, total - 2))
            for idx_e, e in enumerate(ents):
                nm = e["name"]
                if idx_e < cutoff:
                    status_map[nm] = "just_fell" if (cutoff - idx_e) <= max(3, total // 14) else "eliminated"
                else:
                    rem += 1
                    status_map[nm] = "warning" if rem <= 6 else "alive"
            frame_np = base_arr.copy()
            draw_paper_cut_map_cv(frame_np, geom, map_box, status_map, zoom=zoom, focus=focus, shadow_offset=(8, 10), border_w=2, theme=th)
            draw_mechanic_overlay_cv(frame_np, sc, map_box, progress=prog, zoom=zoom, focus=focus, theme=th)
            # Expanding shockwave pulse on First Casualty from Frame 0!
            cx0, cy0 = transform_pt(*f0, map_box, zoom=zoom, focus=focus)
            for ring_i in range(2):
                rr = int(((t * 2.2 + ring_i * 0.45) % 1.0) * 160 + 18)
                cv2.circle(frame_np, (int(cx0), int(cy0)), rr, th["vermilion"], 5, cv2.LINE_AA)
        else:
            prog = max(0.0, min(1.0, (t - t_start_elim) / max(0.1, t_winner - t_start_elim)))
            day_num = int(prog * max_day) if t >= t_start_elim else 0
            for e in ents:
                nm = e["name"]
                et = elim_time[nm]
                if t < et:
                    rem += 1
                    if nm == winner["name"] and t >= t_winner - 0.1:
                        status_map[nm] = "winner"
                    elif et - t < 1.2:
                        status_map[nm] = "warning"
                    else:
                        status_map[nm] = "alive"
                else:
                    status_map[nm] = "just_fell" if (t - et) < 0.9 else "eliminated"
            frame_np = base_arr.copy()
            draw_paper_cut_map_cv(frame_np, geom, map_box, status_map, zoom=zoom, focus=focus, shadow_offset=(8, 10), border_w=2, theme=th)
            draw_mechanic_overlay_cv(frame_np, sc, map_box, progress=prog, zoom=zoom, focus=focus, theme=th)
            for e in ents:
                et = elim_time[e["name"]]
                age = t - et
                if 0.0 <= age < 0.7:
                    cx, cy = transform_pt(*e["centroid"], map_box, zoom=zoom, focus=focus)
                    rr = int(16 + age * 120)
                    cv2.circle(frame_np, (int(cx), int(cy)), rr, th["vermilion"], 4, cv2.LINE_AA)

        # Clean editorial viewport clip: never bleed under caption card/footer
        frame_np[:304, :] = base_arr[:304, :]
        frame_np[1346:, :] = base_arr[1346:, :]
        cv2.line(frame_np, (0, 1346), (W, 1346), th["vermilion"] if th["is_dark"] else th["ink_black"], 4)

        img = Image.fromarray(frame_np, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        # Bold Top Editorial Header
        draw.rectangle([0, 0, W, 286], fill=th["ink_black"] + (255,))
        draw.rectangle([0, 286, W, 304], fill=th["vermilion"] + (255,))
        if is_vs_scene:
            draw.text((52, 46), "FINAL 2 SHOWDOWN  //  REAL DATA VERDICT", font=f_rule, fill=th["warning_ochre"] + (255,))
            draw.text((52, 98), "FINAL 2", font=f_day, fill=th["header_text"] + (255,))
            draw.text((W - 52, 114), "DATA VS", font=f_left, fill=th["warning_ochre"] + (255,), anchor="ra")
            vs_u = max(0.0, min(1.0, (t - t_vs_start) / max(0.2, t_vs_end - t_vs_start)))
            _draw_vs_showdown_vertical_9x16(img, draw, W, H, sim, vs_u, th)
        else:
            rule_hdr = "FLASH-FORWARD PREVIEW // WHO SURVIVES?" if is_short_hook else sc.get("rule_label", "MAP SIMULATION // LIVE")
            draw.text((52, 46), rule_hdr, font=f_rule, fill=th["warning_ochre"] + (255,))
            day_lbl = f"ROUND {day_num:02d}" if sc["mechanic"] in ("laser_line", "shrinking_zone") else f"DAY {day_num:03d}"
            draw.text((52, 98), day_lbl, font=f_day, fill=th["header_text"] + (255,))
            rem_col = th["vermilion"] if rem <= 10 else th["header_text"]
            if rem == 1:
                rem_col = th["warning_ochre"]
            draw.text((W - 52, 114), f"{rem} LEFT", font=f_left, fill=rem_col + (255,), anchor="ra")

            if is_short_hook:
                # Frame-0 bold kinetic hook stamp centered cleanly in lower map viewport
                hx = (W - hook_stamp.width) // 2
                hy = 1130
                img.alpha_composite(hook_stamp, (hx, hy))
            else:
                # Spotlight callout badges
                for sp_name, t0, t1, sp_tag, is_win in spotlights:
                    if t0 <= t <= t1 and sp_name in geom:
                        px, py = transform_pt(*geom[sp_name]["centroid"], map_box, zoom=zoom, focus=focus)
                        if 60 < px < W - 60 and 330 < py < 1230:
                            badge_col = th["alive_blue"] if is_win else th["vermilion"]
                            txt_lbl = f"{short_name(sp_name).upper()} — {sp_tag}"
                            tw = int(draw.textlength(txt_lbl, font=f_pin)) + 52
                            bx0 = max(36, min(W - tw - 36, int(px - tw // 2)))
                            by0 = max(336, min(1160, int(py - 92)))
                            draw.line([(px, py), (bx0 + tw // 2, by0 + 68)], fill=th["body_text"] + (220,), width=5)
                            draw.ellipse([px - 10, py - 10, px + 10, py + 10], fill=badge_col + (255,), outline=th["ink_black"] + (255,), width=3)
                            draw.rectangle([bx0, by0, bx0 + tw, by0 + 68], fill=badge_col + (250,), outline=th["ink_black"] + (255,), width=4)
                            draw.text((bx0 + tw // 2, by0 + 34), txt_lbl, font=f_pin, fill=th["header_text"] + (255,), anchor="mm")

            if t >= t_winner:
                img.alpha_composite(win_stamp, (W - win_stamp.width - 44, 340))

            # V22.8 Smart Open-Loop Subscribe / Follow CTA Pill (final 3.8s, cleanly above divider!)
            if cta_label and t >= t_cta_start:
                pill_x0, pill_x1 = 110, W - 110
                pill_y0, pill_y1 = 1244, 1322
                draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=14,
                                       fill=th["ink_black"] + (245,), outline=th["vermilion"] + (255,), width=5)
                draw.rounded_rectangle([pill_x0 + 14, pill_y0 + 14, pill_x0 + 32, pill_y1 - 14], radius=6,
                                       fill=th["vermilion"] + (255,))
                draw.text((W // 2 + 12, (pill_y0 + pill_y1) // 2), cta_label,
                          font=get_font(FONT_ANTON, 40), fill=th["header_text"] + (255,), anchor="mm")

        # Bottom Editorial Caption Card
        card_y0, card_y1 = 1380, 1690
        draw.rectangle([44, card_y0, W - 44, card_y1], fill=th["ink_black"] + (255,))
        draw.rectangle([44, card_y0, 72, card_y1], fill=th["vermilion"] + (255,))
        active = None
        for ch in chunks:
            if ch["start"] <= t <= ch["end"]:
                active = ch
                break
        if active:
            witems = active["words"]
            pieces = [w["word"].upper() for w in witems]
            full_s = " ".join(pieces)
            if draw.textlength(full_s, font=f_sub) > W - 200 and len(pieces) >= 2:
                mid = len(pieces) // 2
                lines_w = [witems[:mid], witems[mid:]]
            else:
                lines_w = [witems]
            by = card_y0 + (58 if len(lines_w) == 2 else 108)
            for li, lw in enumerate(lines_w):
                cur_x = 104
                cy_t = by + li * 102
                for wobj in lw:
                    wt = wobj["word"].upper()
                    is_now = (wobj["start"] <= t <= wobj["end"] + 0.08)
                    col = th["warning_ochre"] if is_now else th["header_text"]
                    draw.text((cur_x, cy_t), wt, font=f_sub, fill=col + (255,))
                    cur_x += draw.textlength(wt + " ", font=f_sub)

        # Bottom Progress Strip
        unit = "STATES" if sc["arena"] == "us_states" else "COUNTRIES"
        draw.text((W // 2, 1744), f"REMAINING: {rem} OF {total} {unit}  •  LAST MAP STANDING",
                  font=f_foot, fill=th["body_text"] + (255,), anchor="mm")
        bar_bg = th["row_bg"] if th["is_dark"] else th["shadow_warm"]
        draw.rectangle([52, 1784, W - 52, 1814], fill=bar_bg + (255,), outline=th["body_text"] + (180,), width=3)
        fw = max(16, int((W - 110) * (rem / max(1, total))))
        draw.rectangle([55, 1787, 55 + fw, 1811], fill=th["vermilion"] + (255,))

        proc.stdin.write(img.convert("RGB").tobytes())

    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("FFmpeg Short render failed")
    return out_mp4


# =====================================================================
# 3) 16:9 LONG-FORM DOCUMENTARY RENDERER (4 THEMES + ALTERNATING PANELS!)
# =====================================================================
def _draw_animated_bar_chart_scene(W, H, base_arr, chart_data, local_u, act_label, sub_text, theme=None):
    """Scene Type 2: Full-Screen Animated Horizontal Bar Chart (theme-calibrated)."""
    th = theme or THEMES["saul_bass_paper"]
    img = Image.fromarray(base_arr.copy(), "RGB").convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    draw.rectangle([0, 0, W, 118], fill=th["ink_black"] + (255,))
    draw.rectangle([0, 118, W, 128], fill=th["vermilion"] + (255,))
    draw.text((54, 59), f"DATA BREAKDOWN // {chart_data['title']}", font=get_font(FONT_ANTON, 58), fill=th["header_text"] + (255,), anchor="lm")
    draw.text((W - 54, 59), act_label[:34], font=get_font(FONT_MONO, 24), fill=th["warning_ochre"] + (255,), anchor="rm")

    rows = chart_data["rows"]
    max_val = max([r["value"] for r in rows] + [1.0])

    y0 = 186
    row_h = 112
    bar_x0 = 420
    bar_max_w = W - 620

    for pct in [0.0, 0.25, 0.5, 0.75, 1.0]:
        gx = int(bar_x0 + pct * bar_max_w)
        draw.line([(gx, y0 - 18), (gx, y0 + len(rows) * row_h - 16)], fill=th["chart_grid"], width=2)

    f_lbl = get_font(FONT_BLACK, 34)
    f_val = get_font(FONT_ANTON, 44)
    f_tag = get_font(FONT_MONO, 20)

    for idx, row in enumerate(rows):
        ry = y0 + idx * row_h
        bu = ease_out_cubic(max(0.0, min(1.0, (local_u * 2.6) - idx * 0.12)))
        bw = max(14, int((row["value"] / max_val) * bar_max_w * bu))
        bcol = th["alive_blue"] if row["survived"] else th["vermilion"]
        tag = "SURVIVOR TIER" if row["survived"] else "VULNERABLE"

        draw.text((bar_x0 - 32, ry + 34), row["name"].upper()[:18], font=f_lbl, fill=th["body_text"] + (255,), anchor="rm")
        draw.text((bar_x0 - 32, ry + 66), tag, font=f_tag, fill=bcol + (255,), anchor="rm")

        draw.rectangle([bar_x0 + 8, ry + 16, bar_x0 + bw + 8, ry + 78], fill=th["shadow_warm"] + (255,))
        draw.rectangle([bar_x0, ry + 10, bar_x0 + bw, ry + 72], fill=bcol + (255,), outline=th["ink_black"] + (255,), width=3)

        disp_v = row["value"] * bu
        draw.text((bar_x0 + bw + 22, ry + 41), f"{disp_v:.1f}", font=f_val, fill=th["body_text"] + (255,), anchor="lm")

    draw.rectangle([0, H - 104, W, H], fill=th["ink_black"] + (255,))
    draw.rectangle([0, H - 104, 18, H], fill=th["vermilion"] + (255,))
    if sub_text:
        draw.text((W // 2, H - 52), sub_text[:86], font=get_font(FONT_BOLD, 34), fill=th["header_text"] + (255,), anchor="mm")

    return img.convert("RGB")


def _draw_vs_showdown_scene(W, H, base_arr, sim, local_u, sub_text, theme=None):
    """Scene Type 3: Full-Screen Split VS SHOWDOWN Arena (theme-calibrated)."""
    th = theme or THEMES["saul_bass_paper"]
    img = Image.fromarray(base_arr.copy(), "RGB").convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    ru = sim["runner_up"]
    win = sim["winner"]
    ru_n = short_name(ru["name"]).upper()
    win_n = short_name(win["name"]).upper()

    draw.rectangle([0, 0, W, 118], fill=th["ink_black"] + (255,))
    draw.rectangle([0, 118, W, 128], fill=th["vermilion"] + (255,))
    draw.text((W // 2, 59), f"FINAL 2 SHOWDOWN  —  {ru_n}  VS  {win_n}", font=get_font(FONT_ANTON, 62), fill=th["header_text"] + (255,), anchor="mm")

    draw.rectangle([64, 168, W // 2 - 70, 310], fill=th["ink_black"] + (255,))
    draw.rectangle([64, 168, 86, 310], fill=th["warning_ochre"] + (255,))
    draw.text((116, 200), "CHALLENGER #2", font=get_font(FONT_MONO, 24), fill=th["warning_ochre"] + (255,))
    draw.text((116, 232), ru_n[:16], font=get_font(FONT_ANTON, 62), fill=th["header_text"] + (255,))

    draw.rectangle([W // 2 + 70, 168, W - 64, 310], fill=th["ink_black"] + (255,))
    draw.rectangle([W - 86, 168, W - 64, 310], fill=th["alive_blue"] + (255,))
    draw.text((W - 116, 200), "FINAL CONTENDER", font=get_font(FONT_MONO, 24), fill=th["stat_ok"] + (255,), anchor="ra")
    draw.text((W - 116, 232), win_n[:16], font=get_font(FONT_ANTON, 62), fill=th["header_text"] + (255,), anchor="ra")

    cx = W // 2
    draw.ellipse([cx - 58, 180, cx + 58, 296], fill=th["vermilion"] + (255,), outline=th["ink_black"] + (255,), width=6)
    draw.text((cx, 238), "VS", font=get_font(FONT_ANTON, 64), fill=th["header_text"] + (255,), anchor="mm")

    y0 = 374
    gap = 142
    max_half = 660
    f_metric = get_font(FONT_BLACK, 28)
    f_score = get_font(FONT_ANTON, 46)

    for idx, vm in enumerate(sim["vs_metrics"]):
        my = y0 + idx * gap
        bu = ease_out_cubic(max(0.0, min(1.0, (local_u * 2.4) - idx * 0.16)))
        lw = int((vm["left_val"] / 100.0) * max_half * bu)
        rw = int((vm["right_val"] / 100.0) * max_half * bu)

        draw.rectangle([cx - 170, my - 26, cx + 170, my + 12], fill=th["ink_black"] + (255,))
        draw.text((cx, my - 7), vm["label"], font=f_metric, fill=th["header_text"] + (255,), anchor="mm")

        lx1 = cx - 22
        lx0 = lx1 - max(12, lw)
        draw.rectangle([lx0 - 6, my + 28, lx1 - 6, my + 84], fill=th["shadow_warm"] + (255,))
        draw.rectangle([lx0, my + 22, lx1, my + 78], fill=th["warning_ochre"] + (255,), outline=th["ink_black"] + (255,), width=3)
        draw.text((lx0 - 18, my + 50), f"{int(vm['left_val'] * bu)}", font=f_score, fill=th["body_text"] + (255,), anchor="rm")

        rx0 = cx + 22
        rx1 = rx0 + max(12, rw)
        draw.rectangle([rx0 + 6, my + 28, rx1 + 6, my + 84], fill=th["shadow_warm"] + (255,))
        draw.rectangle([rx0, my + 22, rx1, my + 78], fill=th["alive_blue"] + (255,), outline=th["ink_black"] + (255,), width=3)
        draw.text((rx1 + 18, my + 50), f"{int(vm['right_val'] * bu)}", font=f_score, fill=th["body_text"] + (255,), anchor="lm")

    draw.rectangle([0, H - 104, W, H], fill=th["ink_black"] + (255,))
    draw.rectangle([0, H - 104, 18, H], fill=th["vermilion"] + (255,))
    if sub_text:
        draw.text((W // 2, H - 52), sub_text[:86], font=get_font(FONT_BOLD, 34), fill=th["header_text"] + (255,), anchor="mm")

    return img.convert("RGB")


def render_longform_16x9(sim, act_spans, all_words, audio_m4a, total_dur, out_mp4, fps=24):
    """Render full adaptive 9-18 minute 1920x1080 themed map documentary directly to FFmpeg."""
    W, H = 1920, 1080
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    layout = get_layout_variant(sc)
    lb_on_left = (layout == 1)  # Varies editorial framing between episodes!

    geom = load_arena_geometry(sc["arena"])
    ents = sim["entities"]
    total = len(ents)
    max_day = sc.get("max_day", 365)
    winner = sim["winner"]
    runner_up = sim["runner_up"]

    t_cold_ff_end = 4.35
    t_cold_end = 5.20
    t_elim_start = max(t_cold_end + 0.4, act_spans[0]["start"] + min(8.0, act_spans[0]["dur"] * 0.45))
    t_final_act = act_spans[-1]["start"]
    t_winner_reveal = t_final_act + act_spans[-1]["dur"] * 0.56

    elim_time = {}
    for i, e in enumerate(ents):
        if e["name"] == winner["name"]:
            elim_time[e["name"]] = 99999.0
        elif e["name"] == runner_up["name"]:
            elim_time[e["name"]] = t_winner_reveal - 0.5
        else:
            u = i / max(1, total - 2)
            elim_time[e["name"]] = t_elim_start + (u ** 1.18) * (t_final_act - t_elim_start)

    chunks = build_caption_chunks(all_words, max_words=8)

    base_bg = make_themed_bg(W, H, theme=th, seed=99)
    base_arr = np.array(base_bg, dtype=np.uint8)

    lb_w = 390
    if lb_on_left:
        lb_x0, lb_x1 = 0, lb_w
        map_x_min, map_x_max = lb_w, W
        map_box = (lb_w + 36, 152, W - lb_w - 72, H - 270)
    else:
        lb_x0, lb_x1 = W - lb_w, W
        map_x_min, map_x_max = 0, W - lb_w
        map_box = (36, 152, W - lb_w - 72, H - 270)

    win_stamp = make_stamp_image("LAST MAP STANDING", w=540, h=124, color=th["vermilion"], angle=-7, theme=th)

    f_hdr = get_font(FONT_ANTON, 54)
    f_lb_hdr = get_font(FONT_MONO, 21)
    f_lb_row = get_font(FONT_BOLD, 24)
    f_lb_pct = get_font(FONT_MONO, 23)
    f_pin = get_font(FONT_BLACK, 26)
    f_sub = get_font(FONT_BOLD, 34)
    f_chap = get_font(FONT_MONO, 17)

    ff_cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-",
        "-i", audio_m4a,
        "-c:v", "libx264", "-preset", "fast", "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-shortest",
        out_mp4,
    ]
    proc = subprocess.Popen(ff_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    total_frames = int(total_dur * fps)

    chunk_idx = 0
    for fi in range(total_frames):
        t = fi / fps

        while chunk_idx + 1 < len(chunks) and chunks[chunk_idx]["end"] < t:
            chunk_idx += 1
        sub_text = ""
        if chunk_idx < len(chunks) and chunks[chunk_idx]["start"] <= t <= chunks[chunk_idx]["end"]:
            sub_text = " ".join(w["word"] for w in chunks[chunk_idx]["words"])

        cur_act = act_spans[-1]
        for sp in act_spans:
            if sp["start"] <= t < sp["end"]:
                cur_act = sp
                break
        local_u = max(0.0, min(1.0, (t - cur_act["start"]) / max(0.1, cur_act["dur"])))
        stype = cur_act["scene_type"]

        if stype == "chart1" and 0.08 <= local_u <= 0.92:
            rgb = _draw_animated_bar_chart_scene(W, H, base_arr, sim["chart1"], (local_u - 0.08) / 0.84, cur_act["label"], sub_text, theme=th)
            proc.stdin.write(rgb.tobytes())
            continue

        if stype == "map_and_chart2" and 0.50 <= local_u <= 0.88:
            rgb = _draw_animated_bar_chart_scene(W, H, base_arr, sim["chart2"], (local_u - 0.50) / 0.38, cur_act["label"], sub_text, theme=th)
            proc.stdin.write(rgb.tobytes())
            continue

        if stype == "vs_and_winner" and t < t_winner_reveal:
            vs_u = (t - cur_act["start"]) / max(0.1, t_winner_reveal - cur_act["start"])
            rgb = _draw_vs_showdown_scene(W, H, base_arr, sim, vs_u, sub_text, theme=th)
            proc.stdin.write(rgb.tobytes())
            continue

        # V22.5 5.2-Second Cold-Open Flash-Forward + Rewind Hook (never spoils winner!)
        is_cold_ff = (t < t_cold_ff_end)
        is_cold_rw = (t_cold_ff_end <= t < t_cold_end)
        is_cold_open = is_cold_ff or is_cold_rw

        if is_cold_ff:
            prog = smoothstep(t / max(0.1, t_cold_ff_end - 0.1)) * 0.96
            day_num = int(prog * max_day)
            zoom = 1.03 + 0.08 * prog
            focus = (0.50, 0.50)
        elif is_cold_rw:
            rw_u = smoothstep((t - t_cold_ff_end) / max(0.1, t_cold_end - t_cold_ff_end))
            prog = (1.0 - rw_u) * 0.96
            day_num = int(prog * max_day)
            zoom = 1.11 - 0.10 * rw_u
            focus = (0.50, 0.50)
        else:
            prog = max(0.0, min(1.0, (t - t_elim_start) / max(0.1, t_winner_reveal - t_elim_start)))
            day_num = int(prog * max_day) if t >= t_elim_start else 0
            if t >= t_winner_reveal:
                wu = smoothstep((t - t_winner_reveal) / max(0.5, total_dur - t_winner_reveal))
                zoom = lerp(1.04, 1.55, wu)
                focus = (lerp(0.50, max(0.24, min(0.76, winner["centroid"][0])), wu),
                         lerp(0.50, max(0.24, min(0.76, winner["centroid"][1])), wu))
            else:
                zoom = 1.0 + 0.06 * math.sin(t * 0.08) ** 2
                focus = (0.50 + 0.02 * math.sin(t * 0.05), 0.50 + 0.015 * math.cos(t * 0.04))

        status_map = {}
        alive_list = []
        recent_out = []
        if is_cold_open:
            cutoff = int(prog * max(1, total - 2))
            for idx_e, e in enumerate(ents):
                nm = e["name"]
                if idx_e < cutoff:
                    if is_cold_ff and (cutoff - idx_e) <= max(3, total // 14):
                        status_map[nm] = "just_fell"
                        recent_out.append((0.25, e))
                    else:
                        status_map[nm] = "eliminated"
                else:
                    alive_list.append(e)
                    status_map[nm] = "warning" if len(ents) - cutoff <= 6 else "alive"
        else:
            for e in ents:
                nm = e["name"]
                et = elim_time[nm]
                if t < et:
                    alive_list.append(e)
                    if nm == winner["name"] and t >= t_winner_reveal:
                        status_map[nm] = "winner"
                    elif et - t < 2.2:
                        status_map[nm] = "warning"
                    else:
                        status_map[nm] = "alive"
                else:
                    age = t - et
                    if age < 1.6:
                        status_map[nm] = "just_fell"
                        recent_out.append((age, e))
                    else:
                        status_map[nm] = "eliminated"

        frame_np = base_arr.copy()
        draw_paper_cut_map_cv(frame_np, geom, map_box, status_map, zoom=zoom, focus=focus, shadow_offset=(8, 10), border_w=2, theme=th)
        draw_mechanic_overlay_cv(frame_np, sc, map_box, progress=prog, zoom=zoom, focus=focus, theme=th)

        for age, e in recent_out[:3]:
            cx, cy = transform_pt(*e["centroid"], map_box, zoom=zoom, focus=focus)
            rr = int(16 + age * 85)
            cv2.circle(frame_np, (int(cx), int(cy)), rr, th["vermilion"], 4, cv2.LINE_AA)

        img = Image.fromarray(frame_np, "RGB").convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        # Top Swiss Editorial Header
        draw.rectangle([0, 0, W, 106], fill=th["ink_black"] + (255,))
        draw.rectangle([0, 106, W, 114], fill=th["vermilion"] + (255,))
        draw.text((40, 53), sc.get("thumb_top", "LAST MAP STANDING"), font=f_hdr, fill=th["header_text"] + (255,), anchor="lm")

        if is_cold_rw:
            day_str = "<< REWIND"
        else:
            day_str = f"ROUND {day_num:02d}" if sc["mechanic"] in ("laser_line", "shrinking_zone") else f"DAY {day_num:03d}"
        pill_rx1 = (W - 28) if lb_on_left else (lb_x0 - 28)
        pill_rx0 = pill_rx1 - 247
        pill_col = th["warning_ochre"] if is_cold_rw else th["vermilion"]
        pill_txt_col = th["ink_black"] if is_cold_rw else th["header_text"]
        draw.rounded_rectangle([pill_rx0, 22, pill_rx1, 84], radius=8, fill=pill_col + (255,))
        draw.text(((pill_rx0 + pill_rx1) // 2, 53), day_str, font=get_font(FONT_ANTON, 44), fill=pill_txt_col + (255,), anchor="mm")

        # Chapter Progress Bar across the map region
        ch_span_w = (map_x_max - map_x_min - 40)
        ch_w = ch_span_w // len(act_spans)
        for ci, sp in enumerate(act_spans):
            cx0 = map_x_min + 20 + ci * ch_w
            cx1 = cx0 + ch_w - 8
            is_cur = (sp["act_id"] == cur_act["act_id"])
            is_done = (t >= sp["end"])
            idle_bg = th["row_bg"] if th["is_dark"] else th["shadow_warm"]
            bg_c = th["vermilion"] if is_cur else (th["alive_blue"] if is_done else idle_bg)
            txt_c = th["header_text"] if (is_cur or is_done or th["is_dark"]) else th["ink_black"]
            draw.rectangle([cx0, 120, cx1, 146], fill=bg_c + (255,))
            draw.text(((cx0 + cx1) // 2, 133), f"ACT {ci + 1}", font=f_chap, fill=txt_c + (255,), anchor="mm")

        if is_cold_open:
            # Cold-Open Editorial Banner across upper map viewport (never obscures map center)
            bn_x0 = map_x_min + 36
            bn_x1 = map_x_max - 36
            bn_y0, bn_y1 = 160, 224
            if is_cold_ff:
                draw.rectangle([bn_x0, bn_y0, bn_x1, bn_y1], fill=th["ink_black"] + (238,))
                draw.rectangle([bn_x0, bn_y0, bn_x0 + 16, bn_y1], fill=th["vermilion"] + (255,))
                bn_txt = f"FLASH-FORWARD  //  {total - 1} FALL — WHO SURVIVES TO DAY {max_day}?"
                draw.text(((bn_x0 + bn_x1) // 2, (bn_y0 + bn_y1) // 2), bn_txt,
                          font=get_font(FONT_ANTON, 36), fill=th["header_text"] + (255,), anchor="mm")
            else:
                draw.rectangle([bn_x0, bn_y0, bn_x1, bn_y1], fill=th["vermilion"] + (245,))
                bn_txt = "<<  REWINDING TO DAY 000  —  START OF SIMULATION  <<"
                draw.text(((bn_x0 + bn_x1) // 2, (bn_y0 + bn_y1) // 2), bn_txt,
                          font=get_font(FONT_ANTON, 38), fill=th["header_text"] + (255,), anchor="mm")
        elif recent_out:
            # Callout pin on most recently eliminated entity
            recent_out.sort(key=lambda x: x[0])
            _, fallen = recent_out[0]
            px, py = transform_pt(*fallen["centroid"], map_box, zoom=zoom, focus=focus)
            if (map_x_min + 60) < px < (map_x_max - 60) and 170 < py < H - 150:
                lbl = f"{short_name(fallen['name']).upper()} — {sc.get('elim_tag', 'OUT')}"
                tw = int(draw.textlength(lbl, font=f_pin)) + 36
                bx0 = max(map_x_min + 30, min(map_x_max - tw - 30, int(px - tw // 2)))
                by0 = max(164, min(H - 220, int(py - 74)))
                draw.rectangle([bx0, by0, bx0 + tw, by0 + 48], fill=th["vermilion"] + (248,), outline=th["ink_black"] + (255,), width=3)
                draw.text((bx0 + tw // 2, by0 + 24), lbl, font=f_pin, fill=th["header_text"] + (255,), anchor="mm")

        # Swiss Editorial Leaderboard Panel (Right OR Left depending on episode!)
        draw.rectangle([lb_x0, 114, lb_x1, H - 104], fill=th["ink_black"] + (255,))
        div_x = lb_x1 if lb_on_left else lb_x0
        draw.line([(div_x, 114), (div_x, H - 104)], fill=th["vermilion"] + (255,), width=5)

        if is_cold_open:
            draw.text((lb_x0 + 24, 144), f"FLASH-FORWARD ({len(alive_list)}/{total})", font=f_lb_hdr, fill=th["warning_ochre"] + (255,))
            yy = 192
            for rank_i in range(min(10, max(2, len(alive_list)))):
                is_final2 = (rank_i < 2)
                row_bg = th["vermilion"] if (rank_i == 0 and len(alive_list) <= 4) else (th["alive_blue"] if (rank_i == 1 and len(alive_list) <= 4) else th["row_bg"])
                draw.rectangle([lb_x0 + 22, yy, lb_x1 - 22, yy + 58], fill=row_bg + (255,))
                lbl_row = f"{rank_i + 1:02d}  FINALIST  ???" if is_final2 else f"{rank_i + 1:02d}  SURVIVOR  ???"
                draw.text((lb_x0 + 36, yy + 29), lbl_row, font=f_lb_row, fill=th["header_text"] + (255,), anchor="lm")
                draw.text((lb_x1 - 32, yy + 29), "LOCKED", font=f_lb_pct, fill=th["warning_ochre"] + (255,), anchor="rm")
                yy += 68
        else:
            draw.text((lb_x0 + 24, 144), f"STILL STANDING ({len(alive_list)}/{total})", font=f_lb_hdr, fill=th["warning_ochre"] + (255,))
            leaders = list(reversed(alive_list[-10:]))
            yy = 192
            for rank_i, ent in enumerate(leaders[:10]):
                is_top1 = (rank_i == 0 and len(alive_list) == 1)
                row_bg = th["alive_blue"] if is_top1 else th["row_bg"]
                draw.rectangle([lb_x0 + 22, yy, lb_x1 - 22, yy + 58], fill=row_bg + (255,))
                draw.text((lb_x0 + 36, yy + 29), f"{rank_i + 1:02d}  {short_name(ent['name']).upper()[:13]}", font=f_lb_row, fill=th["header_text"] + (255,), anchor="lm")
                sc_pct = min(99, max(12, int(ent["score"])))
                vcol = th["warning_ochre"] if status_map.get(ent["name"]) == "warning" else th["stat_ok"]
                draw.text((lb_x1 - 32, yy + 29), f"{sc_pct}%", font=f_lb_pct, fill=vcol + (255,), anchor="rm")
                yy += 68

        if t >= t_winner_reveal:
            img.alpha_composite(win_stamp, (map_x_max - win_stamp.width - 36, 170))
            draw.rectangle([map_x_min + 44, H - 224, map_x_max - 44, H - 126], fill=th["alive_blue"] + (248,), outline=th["ink_black"] + (255,), width=4)
            draw.text(((map_x_min + map_x_max) // 2, H - 175), f"SURVIVOR #1:  {short_name(winner['name']).upper()}",
                      font=get_font(FONT_ANTON, 58), fill=th["header_text"] + (255,), anchor="mm")

        # Bottom Editorial Subtitle Bar
        draw.rectangle([0, H - 104, W, H], fill=th["ink_black"] + (255,))
        draw.rectangle([0, H - 104, 18, H], fill=th["vermilion"] + (255,))
        if sub_text:
            draw.text((W // 2, H - 52), sub_text[:86], font=f_sub, fill=th["header_text"] + (255,), anchor="mm")

        proc.stdin.write(img.convert("RGB").tobytes())

    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("FFmpeg Long-Form render failed")
    return out_mp4
