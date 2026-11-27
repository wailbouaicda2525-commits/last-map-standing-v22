"""
map_geometry_v22.py — Real Natural Earth GeoJSON loader & Saul Bass Paper-Cut Atlas palette/utilities.
Supports 4 geographic arenas natively from local GeoJSON files ($0/mo, zero external API calls).
"""
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

# Official SAUL BASS PAPER-CUT ATLAS Palette (Style C — Locked Signature Identity)
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


def make_saul_bass_paper_bg(W, H, seed=42):
    """Pre-render tactile warm cotton archival paper sea with subtle architectural grid & organic grain."""
    img = Image.new("RGB", (W, H), PALETTE["sea_cream"])
    draw = ImageDraw.Draw(img, "RGBA")
    step = max(60, W // 18)
    for gx in range(0, W, step):
        draw.line([(gx, 0), (gx, H)], fill=(42, 36, 30, 18), width=1)
    for gy in range(0, H, step):
        draw.line([(0, gy), (W, gy)], fill=(42, 36, 30, 18), width=1)
    # Subtle warm vignette toward paper corners + organic cotton grain
    rng = np.random.default_rng(seed)
    arr = np.array(img, dtype=np.int16)
    noise = rng.integers(-6, 7, size=(H, W, 1))
    arr = np.clip(arr + noise, 0, 255).astype(np.float32)
    Y, X = np.ogrid[:H, :W]
    dist = np.sqrt(((X - W * 0.5) / (W * 0.65)) ** 2 + ((Y - H * 0.5) / (H * 0.65)) ** 2)
    vig = np.clip(1.0 - 0.08 * (dist ** 2.0), 0.88, 1.0)
    arr *= vig[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def draw_text_crisp(draw, pos, text, font, fill, stroke_col=None, stroke_w=0, anchor="lt"):
    if stroke_col and stroke_w > 0:
        draw.text(pos, text, font=font, fill=fill, anchor=anchor, stroke_width=stroke_w, stroke_fill=stroke_col)
    else:
        draw.text(pos, text, font=font, fill=fill, anchor=anchor)
