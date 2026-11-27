"""
map_geometry_v22.py — Real Natural Earth GeoJSON loader & Saul Bass Paper-Cut Atlas palette/utilities.
Supports 4 geographic arenas natively from local GeoJSON files ($0/mo, zero external API calls).
"""
import hashlib
import json
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, "maps")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

FONT_ANTON = os.path.join(FONTS_DIR, "Anton-Regular.ttf")
FONT_BLACK = os.path.join(FONTS_DIR, "Montserrat-Black.ttf")
FONT_BOLD = os.path.join(FONTS_DIR, "Montserrat-Bold.ttf")
FONT_MONO = os.path.join(FONTS_DIR, "JetBrainsMono-Bold.ttf")

# Official SAUL BASS PAPER-CUT ATLAS Palette (Style C — Theme 1 Signature Identity)
PALETTE = {
    "sea_cream":      (243, 237, 224),  # Warm archival cotton paper
    "sea_grid":       (42, 36, 30),     # Subtle drafting grid
    "ink_black":      (20, 20, 18),     # Bold Swiss header & footer ink
    "ink_dark":       (34, 33, 30),     # Secondary matte charcoal
    "eliminated":     (48, 45, 42),     # Eliminated territory charcoal
    "alive_blue":     (25, 82, 138),    # Prussian Blue (Surviving)
    "alive_teal":     (22, 114, 128),   # Winner / Top-tier accent
    "warning_ochre":  (228, 166, 44),   # Warm Ochre (Critical)
    "vermilion":      (224, 58, 36),    # Iconic Saul Bass Vermilion (Elimination/Laser/Stamp)
    "cut_gap":        (243, 237, 224),  # Paper-cut gap border
    "shadow_warm":    (195, 186, 170),  # Cast drop shadow on cream paper
    "cream_text":     (243, 237, 224),  # Light ink on dark headers
    "muted_cream":    (184, 176, 162),  # Secondary light text
}

# =====================================================================
# V22.3 ANTI-TEMPLATE MULTI-THEME CARTOGRAPHY SYSTEM (4 Distinct Looks)
# Every theme is calibrated for maximum broadcast readability & zero-repeat grid aesthetics.
# =====================================================================
THEMES = {
    "saul_bass_paper": {
        "name": "saul_bass_paper",
        "is_dark": False,
        "bg":            (243, 237, 224),  # Warm archival cotton paper
        "grid_rgba":     (42, 36, 30, 18),
        "chart_grid":    (42, 36, 30, 55),
        "ink_black":     (20, 20, 18),     # Headers / footers / card backgrounds
        "row_bg":        (34, 33, 30),     # Leaderboard row background
        "body_text":     (20, 20, 18),     # Text drawn directly on canvas bg
        "header_text":   (243, 237, 224),  # Light text on dark headers/cards
        "alive_blue":    (25, 82, 138),    # Prussian Blue
        "warning_ochre": (228, 166, 44),   # Warm Ochre
        "vermilion":     (224, 58, 36),    # Saul Bass Vermilion
        "eliminated":    (48, 45, 42),     # Matte charcoal
        "cut_gap":       (243, 237, 224),  # Crisp paper cut border
        "shadow_warm":   (195, 186, 170),  # Tactile drop shadow
        "stamp_bg":      (243, 237, 224, 230),
        "stat_ok":       (118, 232, 184),
        "bg_style":      "paper",
    },
    "tactical_radar": {
        "name": "tactical_radar",
        "is_dark": True,
        "bg":            (13, 20, 30),     # Deep obsidian radar slate
        "grid_rgba":     (42, 196, 198, 24),
        "chart_grid":    (120, 190, 210, 48),
        "ink_black":     (7, 11, 17),      # Matte jet-black command chrome
        "row_bg":        (19, 29, 43),     # Tactical panel row
        "body_text":     (236, 244, 250),  # Crisp ice-white on dark canvas
        "header_text":   (240, 246, 252),
        "alive_blue":    (18, 166, 158),   # Electric tactical teal-emerald
        "warning_ochre": (244, 178, 42),   # Radar amber alert
        "vermilion":     (235, 56, 62),    # High-contrast tactical crimson
        "eliminated":    (31, 41, 55),     # Darkened offline territory
        "cut_gap":       (11, 17, 26),     # Dark precision border
        "shadow_warm":   (5, 8, 14),       # Deep elevation shadow
        "stamp_bg":      (13, 20, 30, 236),
        "stat_ok":       (78, 240, 214),
        "bg_style":      "radar",
    },
    "ocean_blueprint": {
        "name": "ocean_blueprint",
        "is_dark": True,
        "bg":            (17, 46, 74),     # Deep architectural maritime blueprint
        "grid_rgba":     (210, 236, 255, 24),
        "chart_grid":    (200, 232, 255, 50),
        "ink_black":     (10, 26, 44),     # Deep navy header/footer
        "row_bg":        (20, 52, 82),     # Blueprint leaderboard row
        "body_text":     (242, 248, 254),  # Blueprint chalk white
        "header_text":   (244, 249, 254),
        "alive_blue":    (74, 176, 226),   # Bright surveyor sky-blue
        "warning_ochre": (246, 174, 52),   # Signal buoy gold
        "vermilion":     (238, 72, 64),    # Maritime distress coral-red
        "eliminated":    (28, 62, 92),     # Submerged blueprint navy
        "cut_gap":       (196, 228, 248),  # Crisp white blueprint line!
        "shadow_warm":   (9, 26, 44),      # Deep water shadow
        "stamp_bg":      (10, 26, 44, 236),
        "stat_ok":       (130, 236, 255),
        "bg_style":      "blueprint",
    },
    "thermal_amber": {
        "name": "thermal_amber",
        "is_dark": True,
        "bg":            (26, 21, 18),     # Rich dark obsidian charcoal
        "grid_rgba":     (224, 162, 76, 20),
        "chart_grid":    (224, 162, 76, 46),
        "ink_black":     (14, 11, 10),     # Deep espresso editorial bar
        "row_bg":        (38, 31, 27),     # Warm dark card row
        "body_text":     (245, 236, 220),  # Warm archival ivory text
        "header_text":   (248, 240, 226),
        "alive_blue":    (216, 158, 48),   # Burnished gold (Surviving)
        "warning_ochre": (236, 122, 38),   # Molten orange (Warning)
        "vermilion":     (224, 54, 36),    # Volcanic vermilion (Eliminated)
        "eliminated":    (49, 43, 39),     # Matte ash charcoal
        "cut_gap":       (22, 18, 15),     # Dark etched seam
        "shadow_warm":   (10, 8, 7),       # Grounded warm black shadow
        "stamp_bg":      (20, 16, 14, 236),
        "stat_ok":       (248, 214, 112),
        "bg_style":      "thermal",
    },
}

THEME_ORDER = ["saul_bass_paper", "tactical_radar", "ocean_blueprint", "thermal_amber"]


def get_theme_for_scenario(scenario):
    """Deterministically assign one of 4 distinct broadcast cartography themes matched to the scenario."""
    if not scenario:
        return THEMES["saul_bass_paper"]
    explicit = scenario.get("visual_theme")
    if explicit in THEMES:
        return THEMES[explicit]

    sid = (scenario.get("id", "") + " " + scenario.get("title_long", "")).lower()
    mech = scenario.get("mechanic", "collapse")

    # Semantic theme matching so visuals match the story AND channel grid looks hand-directed!
    if mech == "elevation_flood" or any(k in sid for k in ("ocean", "flood", "sea", "water", "drought", "freeze", "ice", "river", "coast", "rain", "arctic", "glacier")):
        return THEMES["ocean_blueprint"]
    if mech == "laser_line" or any(k in sid for k in ("electric", "grid", "blackout", "power", "internet", "cyber", "gps", "satellite", "laser", "nuclear")):
        return THEMES["tactical_radar"]
    if mech == "shrinking_zone" or any(k in sid for k in ("oil", "fuel", "heat", "hot", "desert", "fire", "solar", "volcan", "gas", "coal", "warming")):
        return THEMES["thermal_amber"]
    if any(k in sid for k in ("import", "border", "salary", "50k", "100k", "trade", "cargo", "food", "debt", "tax", "recession", "dollar")):
        return THEMES["saul_bass_paper"]

    # Deterministic balanced hash across all 4 themes for remaining combinatorial scenarios
    h = int(hashlib.md5(scenario.get("id", "default").encode("utf-8")).hexdigest()[:8], 16)
    return THEMES[THEME_ORDER[h % len(THEME_ORDER)]]


def get_layout_variant(scenario):
    """Deterministically choose layout variant (0, 1, or 2) for thumbnails & leaderboard side."""
    if not scenario:
        return 0
    if "layout_variant" in scenario:
        return int(scenario["layout_variant"]) % 3
    sid = scenario.get("id", "default")
    # Keep first flagship scenario on exact classic V22.1 layout 0
    if sid == "us_zero_electricity":
        return 0
    h = int(hashlib.sha1(sid.encode("utf-8")).hexdigest()[:8], 16)
    return h % 3

_FONT_CACHE = {}
_ARENA_CACHE = {}


def get_font(path, size):
    key = (path, int(size))
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, int(size))
    return _FONT_CACHE[key]


def load_arena_geometry(arena="us_states"):
    """Load polygon geometry normalized to (0..1, 0..1) for:
       'us_states', 'world', 'europe', 'americas'
    """
    if arena in _ARENA_CACHE:
        return _ARENA_CACHE[arena]

    if arena == "us_states":
        with open(os.path.join(MAPS_DIR, "us_states.geojson"), "r", encoding="utf-8") as f:
            data = json.load(f)
        cos_lat = math.cos(math.radians(38.0))
        max_x = (-66.2 - (-125.5)) * cos_lat
        max_y = (50.0 - 24.0)
        canvas_w = max_x
        canvas_h = max_y * 1.12
        out = {}
        for feat in data["features"]:
            name = feat["properties"]["name"]
            if name in ("Puerto Rico", "District of Columbia"):
                continue
            geom = feat["geometry"]
            raw_polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
            polys = []
            for poly in raw_polys:
                ring = poly[0]
                if name == "Alaska":
                    pts = []
                    for lon, lat in ring:
                        if lon > 0:
                            lon -= 360.0
                        nx = 0.02 + ((lon - (-172.0)) / 42.0) * 0.21
                        ny = 0.72 + ((71.5 - lat) / 17.5) * 0.24
                        pts.append((nx, ny))
                    if len(pts) >= 3:
                        polys.append(pts)
                elif name == "Hawaii":
                    pts = []
                    for lon, lat in ring:
                        nx = 0.24 + ((lon - (-160.5)) / 6.0) * 0.10
                        ny = 0.80 + ((22.4 - lat) / 3.8) * 0.15
                        pts.append((nx, ny))
                    if len(pts) >= 3:
                        polys.append(pts)
                else:
                    pts = []
                    for lon, lat in ring:
                        px = (lon - (-125.5)) * cos_lat
                        py = (50.0 - lat)
                        nx = 0.02 + (px / canvas_w) * 0.96
                        ny = 0.02 + (py / canvas_h) * 0.90
                        pts.append((nx, ny))
                    if len(pts) >= 3:
                        polys.append(pts)
            if polys:
                largest = max(polys, key=lambda p: len(p))
                cx = sum(p[0] for p in largest) / len(largest)
                cy = sum(p[1] for p in largest) / len(largest)
                out[name] = {"polygons": polys, "centroid": (cx, cy)}
        _ARENA_CACHE[arena] = out
        return out

    # World or Regional Subsets from world_110m.geojson
    with open(os.path.join(MAPS_DIR, "world_110m.geojson"), "r", encoding="utf-8") as f:
        data = json.load(f)

    if arena == "europe":
        lon_min, lon_max, lat_min, lat_max = -25.0, 42.0, 34.5, 71.5
        cos_lat = math.cos(math.radians(52.0))
        cw = (lon_max - lon_min) * cos_lat
        ch = (lat_max - lat_min)
        out = {}
        for feat in data["features"]:
            props = feat["properties"]
            name = props.get("NAME") or props.get("ADMIN") or "Unknown"
            cont = props.get("CONTINENT", "")
            if cont != "Europe" and name not in ("Turkey", "Cyprus"):
                continue
            if name == "Russia":
                continue
            geom = feat["geometry"]
            raw_polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
            polys = []
            for poly in raw_polys:
                ring = poly[0]
                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]
                if max(lons) - min(lons) > 90:
                    continue
                if max(lons) < lon_min or min(lons) > lon_max or max(lats) < lat_min or min(lats) > lat_max:
                    continue
                pts = []
                for lon, lat in ring:
                    nx = 0.04 + (((lon - lon_min) * cos_lat) / cw) * 0.92
                    ny = 0.04 + ((lat_max - lat) / ch) * 0.92
                    pts.append((nx, ny))
                if len(pts) >= 3:
                    polys.append(pts)
            if polys:
                largest = max(polys, key=lambda p: len(p))
                cx = sum(p[0] for p in largest) / len(largest)
                cy = sum(p[1] for p in largest) / len(largest)
                out[name] = {"polygons": polys, "centroid": (cx, cy)}
        _ARENA_CACHE[arena] = out
        return out

    # Default: Full World Robinson-like clean projection (no Antarctica)
    def proj_world(lon, lat):
        lat = max(-58.0, min(82.0, lat))
        lat_rad = math.radians(lat)
        scale_x = 0.8487 + 0.1513 * math.cos(lat_rad * 1.15)
        nx = 0.5 + (lon / 360.0) * scale_x * 0.96
        ny = (82.0 - lat) / (82.0 - (-58.0))
        return nx, ny

    out = {}
    for feat in data["features"]:
        props = feat["properties"]
        name = props.get("NAME") or props.get("ADMIN") or "Unknown"
        if name == "Antarctica":
            continue
        if arena == "americas" and props.get("CONTINENT") not in ("North America", "South America"):
            continue
        geom = feat["geometry"]
        raw_polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        polys = []
        for poly in raw_polys:
            ring = poly[0]
            lons = [pt[0] for pt in ring]
            if max(lons) - min(lons) > 180:
                continue
            pts = [proj_world(lon, lat) for lon, lat in ring]
            if len(pts) >= 3:
                polys.append(pts)
        if polys:
            largest = max(polys, key=lambda p: len(p))
            cx = sum(p[0] for p in largest) / len(largest)
            cy = sum(p[1] for p in largest) / len(largest)
            out[name] = {"polygons": polys, "centroid": (cx, cy)}

    # Re-normalize americas nicely to fill canvas
    if arena == "americas" and out:
        all_pts = [pt for v in out.values() for poly in v["polygons"] for pt in poly]
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        span = max(maxx - minx, maxy - miny, 0.01)
        ox = (1.0 - (maxx - minx) / span) * 0.5
        oy = (1.0 - (maxy - miny) / span) * 0.5
        for name, v in out.items():
            new_polys = []
            for poly in v["polygons"]:
                new_polys.append([(0.05 + (ox + (x - minx) / span) * 0.90, 0.05 + (oy + (y - miny) / span) * 0.90) for x, y in poly])
            largest = max(new_polys, key=lambda p: len(p))
            v["polygons"] = new_polys
            v["centroid"] = (sum(p[0] for p in largest) / len(largest), sum(p[1] for p in largest) / len(largest))

    _ARENA_CACHE[arena] = out
    return out


def transform_pt(nx, ny, box, zoom=1.0, focus=(0.5, 0.5)):
    x0, y0, w, h = box
    fx, fy = focus
    sx = (nx - fx) * zoom + 0.5
    sy = (ny - fy) * zoom + 0.5
    return (x0 + sx * w, y0 + sy * h)


def make_themed_bg(W, H, theme=None, seed=42):
    """Pre-render tactile broadcast cartography background tailored to one of 4 V22.3 visual themes."""
    th = theme or THEMES["saul_bass_paper"]
    style = th.get("bg_style", "paper")
    img = Image.new("RGB", (W, H), th["bg"])
    draw = ImageDraw.Draw(img, "RGBA")
    gcol = th["grid_rgba"]

    step = max(60, W // 18)
    for gx in range(0, W, step):
        draw.line([(gx, 0), (gx, H)], fill=gcol, width=1)
    for gy in range(0, H, step):
        draw.line([(0, gy), (W, gy)], fill=gcol, width=1)

    if style == "radar":
        # Subtle tactical command radar rings + compass crosshairs
        cx, cy = W // 2, int(H * 0.52)
        for mult in (0.18, 0.34, 0.50, 0.68):
            rr = int(min(W, H) * mult)
            draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(48, 206, 206, 22), width=2)
        draw.line([(cx, 0), (cx, H)], fill=(48, 206, 206, 18), width=1)
        draw.line([(0, cy), (W, cy)], fill=(48, 206, 206, 18), width=1)
    elif style == "blueprint":
        # Architectural major gridlines every 3 cells + subtle crosshair ticks
        major = step * 3
        mcol = (210, 236, 255, 42)
        for gx in range(0, W, major):
            draw.line([(gx, 0), (gx, H)], fill=mcol, width=2)
        for gy in range(0, H, major):
            draw.line([(0, gy), (W, gy)], fill=mcol, width=2)
    elif style == "thermal":
        # Subtle editorial horizon contour arcs for warm atlas texture
        for i in range(1, 5):
            yy = int(H * (i / 5.0))
            draw.line([(0, yy), (W, yy)], fill=(224, 162, 76, 26), width=2)

    rng = np.random.default_rng(seed)
    arr = np.array(img, dtype=np.int16)
    amp = 6 if not th.get("is_dark") else 4
    noise = rng.integers(-amp, amp + 1, size=(H, W, 1))
    arr = np.clip(arr + noise, 0, 255).astype(np.float32)

    Y, X = np.ogrid[:H, :W]
    dist = np.sqrt(((X - W * 0.5) / (W * 0.65)) ** 2 + ((Y - H * 0.5) / (H * 0.65)) ** 2)
    vig_str = 0.08 if not th.get("is_dark") else 0.22
    vig = np.clip(1.0 - vig_str * (dist ** 2.0), 0.72, 1.0)
    arr *= vig[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def make_saul_bass_paper_bg(W, H, seed=42):
    """Backwards-compatible wrapper for Theme 1 (Saul Bass Archival Cotton Paper)."""
    return make_themed_bg(W, H, THEMES["saul_bass_paper"], seed=seed)


def draw_text_crisp(draw, pos, text, font, fill, stroke_col=None, stroke_w=0, anchor="lt"):
    if stroke_col and stroke_w > 0:
        draw.text(pos, text, font=font, fill=fill, anchor=anchor, stroke_width=stroke_w, stroke_fill=stroke_col)
    else:
        draw.text(pos, text, font=font, fill=fill, anchor=anchor)
