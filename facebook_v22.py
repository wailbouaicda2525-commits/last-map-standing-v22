"""
facebook_v22.py — 100% Direct Facebook Graph API v24.0 Publisher ($0/mo, ZERO Make.com ops!)
Supports ALL 4 Facebook Content Monetization formats natively from GitHub Actions:
  1) Facebook Reels (9:16 video -> /{page_id}/video_reels 3-phase rupload)
  2) Facebook Long-Form In-Stream Videos (16:9 video + custom thumb -> graph-video resumable upload)
  3) Facebook 3-Slide Photo Carousels (1080x1080 Saul Bass Map Data Cards -> /{page_id}/photos + /feed)
  4) Facebook Engagement Text Discussion Posts (/{page_id}/feed)
"""
import json
import os
import urllib.request
import requests
import numpy as np
from PIL import Image, ImageDraw

from map_geometry_v22 import (
    PALETTE,
    load_arena_geometry,
    make_themed_bg,
    get_theme_for_scenario,
    get_font,
    FONT_ANTON,
    FONT_BLACK,
    FONT_BOLD,
    FONT_MONO,
)
from renderer_v22_saul_bass import (
    draw_paper_cut_map_cv,
    draw_mechanic_overlay_cv,
    make_stamp_image,
    short_name,
)

GRAPH_VER = "v24.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VER}"
GRAPH_VIDEO_URL = f"https://graph-video.facebook.com/{GRAPH_VER}"


def _fb_creds():
    pid = os.environ.get("FB_PAGE_ID", "").strip()
    tok = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()
    return pid, tok


def fb_is_configured():
    pid, tok = _fb_creds()
    return bool(pid and tok)


def _check_fb_resp(resp, label):
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text[:400]}
    if resp.status_code >= 400 or "error" in data:
        raise RuntimeError(f"[FB {label} ERROR {resp.status_code}] {data}")
    return data


# =====================================================================
# 1) FACEBOOK REELS UPLOAD (9:16 MP4 -> 3-PHASE RUPLOAD)
# =====================================================================
def upload_fb_reel(mp4_path, description):
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB REEL] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not configured)")
        return None

    # Phase 1: Start session
    r1 = requests.post(
        f"{GRAPH_URL}/{pid}/video_reels",
        data={"upload_phase": "start", "access_token": tok},
        timeout=60,
    )
    d1 = _check_fb_resp(r1, "REEL_START")
    video_id = d1["video_id"]
    upload_url = d1.get("upload_url") or f"https://rupload.facebook.com/video-upload/{GRAPH_VER}/{video_id}"

    # Phase 2: Upload raw MP4 binary bytes
    fsize = os.path.getsize(mp4_path)
    with open(mp4_path, "rb") as fh:
        r2 = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {tok}",
                "offset": "0",
                "file_size": str(fsize),
            },
            data=fh,
            timeout=300,
        )
    _check_fb_resp(r2, "REEL_UPLOAD")

    # Phase 3: Finish & Publish
    r3 = requests.post(
        f"{GRAPH_URL}/{pid}/video_reels",
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description[:2100],
            "access_token": tok,
        },
        timeout=120,
    )
    d3 = _check_fb_resp(r3, "REEL_FINISH")
    print(f"[FB REEL LIVE!] video_id={video_id} resp={d3}")
    return video_id


# =====================================================================
# 2) FACEBOOK LONG-FORM VIDEO UPLOAD (CHUNKED RESUMABLE + CUSTOM THUMB)
# =====================================================================
def upload_fb_long_video(mp4_path, title, description, thumb_path=None):
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB LONG VIDEO] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not configured)")
        return None

    fsize = os.path.getsize(mp4_path)
    endpoint = f"{GRAPH_VIDEO_URL}/{pid}/videos"

    # Phase 1: Start resumable session
    r1 = requests.post(
        endpoint,
        data={
            "upload_phase": "start",
            "file_size": str(fsize),
            "access_token": tok,
        },
        timeout=60,
    )
    d1 = _check_fb_resp(r1, "VIDEO_START")
    session_id = d1["upload_session_id"]
    video_id = d1["video_id"]
    start_off = int(d1.get("start_offset", 0))
    end_off = int(d1.get("end_offset", fsize))

    # Phase 2: Stream chunks cleanly
    with open(mp4_path, "rb") as fh:
        while start_off < fsize:
            chunk_len = max(1, min(end_off - start_off, 16 * 1024 * 1024))
            fh.seek(start_off)
            chunk = fh.read(chunk_len)
            r2 = requests.post(
                endpoint,
                data={
                    "upload_phase": "transfer",
                    "upload_session_id": session_id,
                    "start_offset": str(start_off),
                    "access_token": tok,
                },
                files={"video_file_chunk": ("chunk.mp4", chunk, "application/octet-stream")},
                timeout=300,
            )
            d2 = _check_fb_resp(r2, "VIDEO_TRANSFER")
            new_start = int(d2.get("start_offset", fsize))
            new_end = int(d2.get("end_offset", fsize))
            pct = int(min(100, (new_start / max(1, fsize)) * 100))
            print(f"  [FB VIDEO UPLOAD] {pct}%", flush=True)
            if new_start == start_off:
                break
            start_off, end_off = new_start, new_end

    # Phase 3: Finish + Publish (with custom 16:9 Saul Bass Thumbnail if provided!)
    finish_data = {
        "upload_phase": "finish",
        "upload_session_id": session_id,
        "title": title[:250],
        "description": description[:4900],
        "published": "true",
        "access_token": tok,
    }
    if thumb_path and os.path.exists(thumb_path):
        with open(thumb_path, "rb") as tfh:
            r3 = requests.post(
                endpoint,
                data=finish_data,
                files={"thumb": (os.path.basename(thumb_path), tfh, "image/jpeg")},
                timeout=120,
            )
    else:
        r3 = requests.post(endpoint, data=finish_data, timeout=120)

    d3 = _check_fb_resp(r3, "VIDEO_FINISH")
    print(f"[FB LONG VIDEO LIVE!] video_id={video_id} resp={d3}")
    return video_id


# =====================================================================
# 3) FACEBOOK MULTI-PHOTO CAROUSEL UPLOAD (3 SAUL BASS DATA CARDS)
# =====================================================================
def upload_fb_photo_carousel(image_paths, message):
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB CAROUSEL] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not configured)")
        return None

    media_ids = []
    for p in image_paths:
        with open(p, "rb") as fh:
            rp = requests.post(
                f"{GRAPH_URL}/{pid}/photos",
                data={"published": "false", "access_token": tok},
                files={"source": (os.path.basename(p), fh, "image/jpeg")},
                timeout=120,
            )
        dp = _check_fb_resp(rp, "PHOTO_STAGE")
        media_ids.append(dp["id"])

    payload = {"message": message[:4900], "access_token": tok}
    for idx, mid in enumerate(media_ids):
        payload[f"attached_media[{idx}]"] = json.dumps({"media_fbid": mid})

    rf = requests.post(f"{GRAPH_URL}/{pid}/feed", data=payload, timeout=120)
    df = _check_fb_resp(rf, "CAROUSEL_FEED")
    post_id = df.get("id", "")
    print(f"[FB PHOTO CAROUSEL LIVE!] post_id={post_id} ({len(media_ids)} slides)")
    return post_id


# =====================================================================
# 4) FACEBOOK ENGAGEMENT TEXT POST
# =====================================================================
def upload_fb_text_post(message):
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB TEXT POST] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not configured)")
        return None

    rf = requests.post(
        f"{GRAPH_URL}/{pid}/feed",
        data={"message": message[:4900], "access_token": tok},
        timeout=60,
    )
    df = _check_fb_resp(rf, "TEXT_FEED")
    post_id = df.get("id", "")
    print(f"[FB TEXT POST LIVE!] post_id={post_id}")
    return post_id


# =====================================================================
# VISUAL GENERATOR: 3-SLIDE SQUARE (1080x1080) SAUL BASS FB CAROUSEL
# =====================================================================
def _aspect_box(x, y, w, h, arena):
    ratio = 1.80 if arena == "world" else 1.55
    if (w / max(1.0, float(h))) > ratio:
        nw = int(h * ratio)
        return (x + (w - nw) // 2, y, nw, h)
    nh = int(w / ratio)
    return (x, y + (h - nh) // 2, w, nh)


def render_fb_carousel_slides(sim, out_dir):
    """Render 3 high-engagement 1080x1080 themed Facebook Carousel Cards (V22.3 Multi-Theme)."""
    os.makedirs(out_dir, exist_ok=True)
    W, H = 1080, 1080
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    geom = load_arena_geometry(sc["arena"])
    ents = sim["entities"]
    total = len(ents)
    win = sim["winner"]
    ru = sim["runner_up"]
    unit = "STATES" if sc["arena"] == "us_states" else "COUNTRIES"

    # ---------------- SLIDE 1: HOOK MAP CARD ("WHO FALLS FIRST?") ----------------
    bg1 = make_themed_bg(W, H, theme=th, seed=41)
    arr1 = np.array(bg1, dtype=np.uint8)
    st_map = {}
    for i, e in enumerate(ents):
        u = i / max(1, total - 1)
        if u > 0.86:
            st_map[e["name"]] = "alive"
        elif u > 0.72:
            st_map[e["name"]] = "warning"
        elif u > 0.60:
            st_map[e["name"]] = "just_fell"
        else:
            st_map[e["name"]] = "eliminated"

    mb1 = _aspect_box(36, 260, W - 72, 560, sc["arena"])
    draw_paper_cut_map_cv(arr1, geom, mb1, st_map, shadow_offset=(8, 10), border_w=3, theme=th)
    draw_mechanic_overlay_cv(arr1, sc, mb1, progress=0.68, theme=th)

    im1 = Image.fromarray(arr1, "RGB").convert("RGBA")
    d1 = ImageDraw.Draw(im1, "RGBA")
    d1.rectangle([0, 0, W, 220], fill=th["ink_black"] + (255,))
    d1.rectangle([0, 220, W, 234], fill=th["vermilion"] + (255,))
    d1.text((48, 52), "LAST MAP STANDING  //  SWIPE FOR DATA →", font=get_font(FONT_MONO, 24), fill=th["warning_ochre"] + (255,))

    top_t = sc.get("thumb_top", "ZERO POWER. 50 STATES.")
    f_t1 = get_font(FONT_ANTON, 82)
    while d1.textlength(top_t, font=f_t1) > W - 96:
        f_t1 = get_font(FONT_ANTON, f_t1.size - 4)
    d1.text((48, 146), top_t, font=f_t1, fill=th["header_text"] + (255,), anchor="lm")

    stamp1 = make_stamp_image(f"{total - 1} ELIMINATED", w=410, h=96, angle=8, paper_fill=True, theme=th)
    im1.alpha_composite(stamp1, (W - stamp1.width - 34, H - 190 - stamp1.height // 2))

    d1.rectangle([0, H - 122, W, H], fill=th["ink_black"] + (255,))
    d1.rectangle([0, H - 122, 18, H], fill=th["vermilion"] + (255,))
    d1.text((W // 2, H - 61), f"ONLY 1 OF {total} {unit} SURVIVES  •  SWIPE TO SEE WHY →",
            font=get_font(FONT_BOLD, 30), fill=th["header_text"] + (255,), anchor="mm")
    p1 = os.path.join(out_dir, f"fb_slide1_{sc['id']}.jpg")
    im1.convert("RGB").save(p1, quality=93)

    # ---------------- SLIDE 2: REAL DATA BAR CHART CARD ----------------
    bg2 = make_themed_bg(W, H, theme=th, seed=42)
    im2 = bg2.convert("RGBA")
    d2 = ImageDraw.Draw(im2, "RGBA")
    c1 = sim["chart1"]
    d2.rectangle([0, 0, W, 178], fill=th["ink_black"] + (255,))
    d2.rectangle([0, 178, W, 190], fill=th["vermilion"] + (255,))
    d2.text((48, 46), "SLIDE 2 / 3  //  REAL DATA BREAKDOWN", font=get_font(FONT_MONO, 24), fill=th["warning_ochre"] + (255,))
    f_c2 = get_font(FONT_ANTON, 64)
    while d2.textlength(c1["title"], font=f_c2) > W - 96:
        f_c2 = get_font(FONT_ANTON, f_c2.size - 4)
    d2.text((48, 124), c1["title"], font=f_c2, fill=th["header_text"] + (255,), anchor="lm")

    rows = c1["rows"][:6]
    max_v = max([r["value"] for r in rows] + [1.0])
    y0 = 248
    row_h = 114
    bx0 = 330
    bmax = W - 470
    for idx, row in enumerate(rows):
        ry = y0 + idx * row_h
        bw = max(18, int((row["value"] / max_v) * bmax))
        col = th["alive_blue"] if row["survived"] else th["vermilion"]
        tag = "SURVIVOR TIER" if row["survived"] else "EARLY COLLAPSE"
        d2.text((bx0 - 24, ry + 28), short_name(row["name"]).upper()[:15], font=get_font(FONT_BLACK, 27), fill=th["body_text"] + (255,), anchor="rm")
        d2.text((bx0 - 24, ry + 58), tag, font=get_font(FONT_MONO, 17), fill=col + (255,), anchor="rm")
        d2.rectangle([bx0 + 7, ry + 14, bx0 + bw + 7, ry + 70], fill=th["shadow_warm"] + (255,))
        d2.rectangle([bx0, ry + 8, bx0 + bw, ry + 64], fill=col + (255,), outline=th["ink_black"] + (255,), width=3)
        d2.text((bx0 + bw + 18, ry + 36), f"{row['value']:.1f}", font=get_font(FONT_ANTON, 40), fill=th["body_text"] + (255,), anchor="lm")

    d2.rectangle([0, H - 116, W, H], fill=th["ink_black"] + (255,))
    d2.rectangle([0, H - 116, 18, H], fill=th["vermilion"] + (255,))
    d2.text((W // 2, H - 58), "SWIPE FOR THE FINAL 2 HEAD-TO-HEAD SHOWDOWN →",
            font=get_font(FONT_BOLD, 30), fill=th["header_text"] + (255,), anchor="mm")
    p2 = os.path.join(out_dir, f"fb_slide2_{sc['id']}.jpg")
    im2.convert("RGB").save(p2, quality=93)

    # ---------------- SLIDE 3: FINAL 2 VS SHOWDOWN CLIFFHANGER ----------------
    bg3 = make_themed_bg(W, H, theme=th, seed=43)
    im3 = bg3.convert("RGBA")
    d3 = ImageDraw.Draw(im3, "RGBA")
    ru_n = short_name(ru["name"]).upper()
    win_n = short_name(win["name"]).upper()

    d3.rectangle([0, 0, W, 178], fill=th["ink_black"] + (255,))
    d3.rectangle([0, 178, W, 190], fill=th["vermilion"] + (255,))
    d3.text((W // 2, 46), "SLIDE 3 / 3  //  FINAL 2 SURVIVORS", font=get_font(FONT_MONO, 24), fill=th["warning_ochre"] + (255,), anchor="mm")
    vs_hdr = f"{ru_n}  VS  {win_n}"
    f_vs = get_font(FONT_ANTON, 68)
    while d3.textlength(vs_hdr, font=f_vs) > W - 80:
        f_vs = get_font(FONT_ANTON, f_vs.size - 4)
    d3.text((W // 2, 124), vs_hdr, font=f_vs, fill=th["header_text"] + (255,), anchor="mm")

    cx = W // 2
    d3.rectangle([42, 224, cx - 54, 342], fill=th["ink_black"] + (255,))
    d3.rectangle([42, 224, 60, 342], fill=th["warning_ochre"] + (255,))
    d3.text((80, 250), "FINALIST A", font=get_font(FONT_MONO, 20), fill=th["warning_ochre"] + (255,))
    d3.text((80, 278), ru_n[:13], font=get_font(FONT_ANTON, 46), fill=th["header_text"] + (255,))

    d3.rectangle([cx + 54, 224, W - 42, 342], fill=th["ink_black"] + (255,))
    d3.rectangle([W - 60, 224, W - 42, 342], fill=th["alive_blue"] + (255,))
    d3.text((W - 80, 250), "FINALIST B", font=get_font(FONT_MONO, 20), fill=th["stat_ok"] + (255,), anchor="ra")
    d3.text((W - 80, 278), win_n[:13], font=get_font(FONT_ANTON, 46), fill=th["header_text"] + (255,), anchor="ra")

    d3.ellipse([cx - 46, 237, cx + 46, 329], fill=th["vermilion"] + (255,), outline=th["ink_black"] + (255,), width=5)
    d3.text((cx, 283), "VS", font=get_font(FONT_ANTON, 52), fill=th["header_text"] + (255,), anchor="mm")

    vy0 = 398
    vgap = 136
    max_half = 395
    for idx, vm in enumerate(sim["vs_metrics"]):
        my = vy0 + idx * vgap
        d3.rectangle([cx - 145, my - 22, cx + 145, my + 12], fill=th["ink_black"] + (255,))
        d3.text((cx, my - 5), vm["label"], font=get_font(FONT_BLACK, 22), fill=th["header_text"] + (255,), anchor="mm")

        lw = max(14, int((vm["left_val"] / 100.0) * max_half))
        rw = max(14, int((vm["right_val"] / 100.0) * max_half))
        lx1 = cx - 18
        lx0 = lx1 - lw
        d3.rectangle([lx0, my + 22, lx1, my + 72], fill=th["warning_ochre"] + (255,), outline=th["ink_black"] + (255,), width=3)
        d3.text((lx0 - 14, my + 47), str(vm["left_val"]), font=get_font(FONT_ANTON, 38), fill=th["body_text"] + (255,), anchor="rm")

        rx0 = cx + 18
        rx1 = rx0 + rw
        d3.rectangle([rx0, my + 22, rx1, my + 72], fill=th["alive_blue"] + (255,), outline=th["ink_black"] + (255,), width=3)
        d3.text((rx1 + 14, my + 47), str(vm["right_val"]), font=get_font(FONT_ANTON, 38), fill=th["body_text"] + (255,), anchor="lm")

    d3.rectangle([0, H - 116, W, H], fill=th["vermilion"] + (255,))
    d3.text((W // 2, H - 58), f"WHO WINS? {ru_n} OR {win_n}? COMMENT BELOW!",
            font=get_font(FONT_ANTON, 44), fill=th["header_text"] + (255,), anchor="mm")
    p3 = os.path.join(out_dir, f"fb_slide3_{sc['id']}.jpg")
    im3.convert("RGB").save(p3, quality=93)

    return [p1, p2, p3]


# =====================================================================
# TEXT GENERATOR: HIGH-ENGAGEMENT US DEBATE POSTS FOR FB MONETIZATION
# =====================================================================
def generate_fb_text_discussion(sim):
    """Build a punchy, high-comment Facebook text discussion post backed by real simulation data."""
    sc = sim["scenario"]
    f3 = ", ".join(short_name(e["name"]) for e in sim["first_out"][:3])
    top3 = ", ".join(short_name(e["name"]) for e in sim["top5"][:3])
    ru = short_name(sim["runner_up"]["name"])
    win = short_name(sim["winner"]["name"])
    unit = "U.S. state" if sc["arena"] == "us_states" else "country"
    units = "50 U.S. states" if sc["arena"] == "us_states" else "177 countries"

    # Try Groq for ultra-natural US Facebook discussion phrasing, with instant offline fallback
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if groq_key:
        prompt = (
            f"Write a short, engaging, debate-sparking Facebook discussion post (90-130 words) for an adult U.S. geography & economics audience.\n"
            f"Topic: {sc['title_long']}\n"
            f"Premise: {sc['premise']}\n"
            f"First 3 eliminated in our data model: {f3}\n"
            f"Final 3 standing: {top3}\n"
            f"Final winner: {win} edging out {ru}.\n"
            f"Rules: Clean/factual tone, zero politics/wars, format cleanly with 3-4 short punchy paragraphs so people stop scrolling and debate in the comments. "
            f"End with an irresistible question asking readers if their home {unit} would survive. Output plain text only (no markdown asterisks)."
        )
        try:
            body = json.dumps({
                "model": "qwen/qwen3.8-27b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.72,
                "max_tokens": 350,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=body,
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json", "User-Agent": "LastMapStanding/22"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=40) as resp:
                txt = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
            if len(txt.split()) >= 55:
                return txt
        except Exception as e:
            print(f"[FB TEXT GROQ WARN] {e}")

    return (
        f"GEOGRAPHY STRESS TEST: {sc['title_long']}\n\n"
        f"{sc['premise']}\n\n"
        f"We ran all {units} through real-world energy, food surplus, freshwater, and self-reliance data:\n"
        f"• First 3 eliminated: {f3}\n"
        f"• Final 3 still standing: {top3}\n"
        f"• Last Map Standing: {win} (barely outlasting {ru}!)\n\n"
        f"Do you agree with the data—or would your home {unit} outlast {win}? Drop your pick below and tell us why."
    )
