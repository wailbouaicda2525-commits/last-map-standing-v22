"""
run_daily_v22.py — Unified 5+ Year Zero-Touch Orchestrator for Last Map Standing (V22 Saul Bass Atlas).
Usage:
  python3 run_daily_v22.py --mode short
  python3 run_daily_v22.py --mode longform
  python3 run_daily_v22.py --mode longform --dry-run --demo-fast
"""
import argparse
import json
import os
import subprocess
import tempfile

import imageio_ffmpeg

from map_geometry_v22 import BASE_DIR, get_theme_for_scenario, get_layout_variant
from scenario_engine_v22 import pick_next_scenario, simulate_scenario, mark_published
from scriptwriter_v22 import generate_short_script, generate_longform_acts, compute_adaptive_minutes
from voice_sfx_v22 import (
    synthesize_voice,
    get_audio_duration,
    synthesize_saul_bass_soundscape,
    mix_voice_and_sfx,
)
from renderer_v22_saul_bass import (
    render_thumbnail_16x9,
    render_short_thumbnail_9x16,
    render_short_9x16,
    render_longform_16x9,
)
from uploader_v22 import upload_video_to_youtube, send_telegram
from facebook_v22 import (
    fb_is_configured,
    upload_fb_reel,
    upload_fb_long_video,
    upload_fb_photo_carousel,
    upload_fb_text_post,
    render_fb_carousel_slides,
    generate_fb_text_discussion,
)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def load_config():
    with open(os.path.join(BASE_DIR, "channel_config.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def pick_episode_voice(cfg, sc):
    """Rotate cleanly across 3 flagship US documentary narrators so episodes feel bespoke."""
    roster = cfg.get("voice_roster") or [cfg.get("voice", "en-US-AndrewNeural")]
    sid = sc.get("id", "lms")
    h = sum(ord(c) * (i + 5) for i, c in enumerate(sid))
    primary = roster[h % len(roster)]
    fallbacks = [v for v in (cfg.get("voice_fallbacks") or roster) if v != primary]
    return primary, fallbacks


def run_short(cfg, sim, out_dir, dry_run=False, privacy="public"):
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    ep_voice, ep_fallbacks = pick_episode_voice(cfg, sc)
    print(f"[SHORT] Scenario: {sc['id']} | Theme: {th['name']} | Voice: {ep_voice} | {sc['title_short']}")

    script = generate_short_script(sim)
    print(f"[SHORT] Script ready ({len(script.split())} words)")

    voice_mp3 = os.path.join(out_dir, "short_voice.mp3")
    sfx_wav = os.path.join(out_dir, "short_sfx.wav")
    mixed_m4a = os.path.join(out_dir, "short_mixed.m4a")
    out_mp4 = os.path.join(out_dir, f"LMS_SHORT_{sc['id']}.mp4")
    short_thumb_jpg = os.path.join(out_dir, f"LMS_SHORT_THUMB_{sc['id']}.jpg")

    # Generate matching 9:16 Custom Shorts & FB Reels Poster Miniature!
    render_short_thumbnail_9x16(sim, short_thumb_jpg)
    print(f"[SHORT] Custom 9:16 Thumbnail rendered: {short_thumb_jpg}")

    words = synthesize_voice(
        script,
        voice_mp3,
        voice=ep_voice,
        fallbacks=ep_fallbacks,
        rate=cfg.get("voice_rate_short", "+8%"),
        pitch=cfg.get("voice_pitch", "-2Hz"),
    )
    vdur = get_audio_duration(voice_mp3)
    total_dur = vdur + 1.4
    t_win = max(6.0, total_dur - 4.2)
    elim_cues = [2.2 + i * ((t_win - 3.2) / 6.0) for i in range(6)]
    synthesize_saul_bass_soundscape(total_dur, elim_cues, [1.8, t_win - 1.2], t_win, sfx_wav)
    mix_voice_and_sfx(voice_mp3, sfx_wav, mixed_m4a, total_dur)

    print(f"[SHORT] Rendering {total_dur:.1f}s V22.4 Themed Short (1080x1920)...")
    render_short_9x16(sim, words, mixed_m4a, total_dur, out_mp4, fps=30)
    print(f"[SHORT] Render complete: {out_mp4} ({os.path.getsize(out_mp4) / 1e6:.2f} MB)")

    if dry_run:
        return out_mp4, None

    title = sc["title_short"][:88] + " #Shorts"
    desc = f"{sc['title_short']}\n\n{sc['premise']}\n\n{cfg['description_footer']}\n\n{cfg['short_hashtags']}"
    vid_id = upload_video_to_youtube(
        out_mp4,
        title=title,
        description=desc,
        tags=cfg["default_tags"],
        privacy=privacy,
        thumbnail_path=short_thumb_jpg,
        category_id=cfg.get("category_id", "27"),
        wait_for_processing=True,
    )
    mark_published(sc, mode="short", video_id=vid_id)

    # Auto cross-post exact same 9:16 MP4 + custom 9:16 cover directly to Facebook Reels ($0/mo!)
    fb_note = ""
    if fb_is_configured():
        try:
            fb_desc = f"{sc['title_short']}\n\n{sc['premise']}\n\nWould your home survive? Tell us below! 👇\n\n#LastMapStanding #MapSimulation #Geography #USStates #WorldMap #DataVisualization"
            fb_vid = upload_fb_reel(out_mp4, fb_desc, thumb_path=short_thumb_jpg)
            if fb_vid:
                fb_note = f"\n📘 FB Reel LIVE (id={fb_vid})"
        except Exception as e:
            print(f"[FB REEL WARN — non-blocking]: {e}")

    send_telegram(f"🗺️ <b>LAST MAP STANDING (Short LIVE!)</b>\n{title}\nhttps://youtube.com/shorts/{vid_id}{fb_note}")
    return out_mp4, vid_id


def run_longform(cfg, sim, out_dir, dry_run=False, demo_fast=False, privacy="public"):
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    layout = get_layout_variant(sc)
    ep_voice, ep_fallbacks = pick_episode_voice(cfg, sc)
    print(f"[LONGFORM] Scenario: {sc['id']} | Theme: {th['name']} | Layout: {layout} | Voice: {ep_voice} | {sc['title_long']}")

    # 1) Generate V22.3 Multi-Theme Swiss Editorial Poster Thumbnail
    thumb_jpg = os.path.join(out_dir, f"LMS_THUMB_{sc['id']}.jpg")
    render_thumbnail_16x9(sim, thumb_jpg)
    print(f"[LONGFORM] Thumbnail rendered: {thumb_jpg}")

    # 2) Generate 6-act script (demo_fast produces compact ~36-second 6-act full showcase for local QA!)
    if demo_fast:
        ru_n = sim["runner_up"]["name"].replace("United States of America", "USA")
        win_n = sim["winner"]["name"].replace("United States of America", "USA")
        f1 = sim["first_out"][0]["name"].replace("United States of America", "USA")
        acts = [
            {"act_id": 0, "label": "ACT I — SIMULATION START", "scene_type": "map",
             "text": f"{sc['premise']} Only one survives to Day {sc['max_day']}."},
            {"act_id": 1, "label": "ACT II — FIRST COLLAPSE", "scene_type": "map",
             "text": f"Immediately, vulnerable territories like {f1} drop offline as early waves sweep across the map."},
            {"act_id": 2, "label": "ACT III — DATA BREAKDOWN", "scene_type": "chart1",
             "text": f"Look at the numbers behind {sim['chart1']['title'].lower()} separating top survivors from early casualties."},
            {"act_id": 3, "label": "ACT IV — HALFWAY COLLAPSE", "scene_type": "map_and_chart2",
             "text": "Past the halfway mark, secondary resource bottlenecks erase the middle tier across the board."},
            {"act_id": 4, "label": "ACT V — FINAL FIVE", "scene_type": "map",
             "text": f"Only five fortresses remain until two final contenders face off: {ru_n} versus {win_n}."},
            {"act_id": 5, "label": "ACT VI — FINAL VS SHOWDOWN", "scene_type": "vs_and_winner",
             "text": f"Side by side across all four survival pillars, {win_n} outlasts {ru_n} to become Last Map Standing."},
        ]
    else:
        adaptive_min = compute_adaptive_minutes(sim)
        print(f"[LONGFORM] Adaptive natural target runtime: {adaptive_min:.1f} min (arena={sc['arena']}, mechanic={sc['mechanic']})")
        acts = generate_longform_acts(sim, target_minutes=adaptive_min)

    # 3) Synthesize voice per act + concatenate seamlessly with exact act spans & word timings
    act_spans = []
    all_words = []
    act_mp3s = []
    cur_t = 0.0
    for act in acts:
        amp3 = os.path.join(out_dir, f"act_{act['act_id']}.mp3")
        awords = synthesize_voice(
            act["text"],
            amp3,
            voice=ep_voice,
            fallbacks=ep_fallbacks,
            rate=cfg.get("voice_rate_long", "+3%"),
            pitch=cfg.get("voice_pitch", "-2Hz"),
        )
        adur = get_audio_duration(amp3)
        for w in awords:
            all_words.append({"word": w["word"], "start": w["start"] + cur_t, "end": w["end"] + cur_t})
        act_spans.append({
            "act_id": act["act_id"],
            "label": act["label"],
            "scene_type": act["scene_type"],
            "start": cur_t,
            "end": cur_t + adur,
            "dur": adur,
        })
        act_mp3s.append(amp3)
        cur_t += adur

    concat_txt = os.path.join(out_dir, "acts_concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in act_mp3s:
            f.write(f"file '{os.path.abspath(p)}'\n")
    full_voice = os.path.join(out_dir, "long_voice.mp3")
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", full_voice],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    total_dur = cur_t + 1.8
    t_winner_rev = act_spans[-1]["start"] + act_spans[-1]["dur"] * 0.56
    act_cues = [sp["start"] for sp in act_spans[1:]]
    elim_cues = [act_spans[0]["start"] + 3.0 + i * ((act_spans[-1]["start"] - 4.0) / 14.0) for i in range(14)]

    sfx_wav = os.path.join(out_dir, "long_sfx.wav")
    mixed_m4a = os.path.join(out_dir, "long_mixed.m4a")
    synthesize_saul_bass_soundscape(total_dur, elim_cues, act_cues, t_winner_rev, sfx_wav)
    mix_voice_and_sfx(full_voice, sfx_wav, mixed_m4a, total_dur)

    out_mp4 = os.path.join(out_dir, f"LMS_LONG_{sc['id']}.mp4")
    print(f"[LONGFORM] Rendering {total_dur:.1f}s Saul Bass Documentary (1920x1080 @ 24fps)...")
    render_longform_16x9(sim, act_spans, all_words, mixed_m4a, total_dur, out_mp4, fps=24)
    print(f"[LONGFORM] Render complete: {out_mp4} ({os.path.getsize(out_mp4) / 1e6:.2f} MB)")

    if dry_run:
        return out_mp4, thumb_jpg

    # Auto-chapters for YouTube description
    chap_lines = ["0:00 Introduction"]
    for sp in act_spans[1:]:
        mm = int(sp["start"] // 60)
        ss = int(sp["start"] % 60)
        chap_lines.append(f"{mm}:{ss:02d} {sp['label']}")
    chapters_str = "\n".join(chap_lines)

    title = sc["title_long"][:98]
    desc = f"{sc['title_long']}\n\n{sc['premise']}\n\nCHAPTERS:\n{chapters_str}\n\n{cfg['description_footer']}\n\n{cfg['long_hashtags']}"
    vid_id = upload_video_to_youtube(
        out_mp4,
        title=title,
        description=desc,
        tags=cfg["default_tags"],
        privacy=privacy,
        thumbnail_path=thumb_jpg,
        category_id=cfg.get("category_id", "27"),
    )
    mark_published(sc, mode="longform", video_id=vid_id)

    # Auto cross-post exact same 16:9 Documentary + Thumbnail directly to Facebook In-Stream Video ($0/mo!)
    fb_note = ""
    if fb_is_configured():
        try:
            fb_desc = f"{sc['title_long']}\n\n{sc['premise']}\n\nCHAPTERS:\n{chapters_str}\n\nWhich territory surprised you most? Drop your take below! 👇\n\n#LastMapStanding #GeographyDocumentary #MapSimulation #DataVisualization"
            fb_vid = upload_fb_long_video(out_mp4, title=title, description=fb_desc, thumb_path=thumb_jpg)
            if fb_vid:
                fb_note = f"\n📘 FB Long Video LIVE (id={fb_vid})"
        except Exception as e:
            print(f"[FB LONG VIDEO WARN — non-blocking]: {e}")

    send_telegram(f"🗺️ <b>LAST MAP STANDING (Long-Form LIVE!)</b>\n{title}\nhttps://www.youtube.com/watch?v={vid_id}{fb_note}")
    return out_mp4, vid_id


def run_fb_carousel(cfg, sim, out_dir, dry_run=False):
    sc = sim["scenario"]
    print(f"[FB CAROUSEL] Scenario: {sc['id']} | {sc['title_short']}")
    slides = render_fb_carousel_slides(sim, out_dir)
    print(f"[FB CAROUSEL] Rendered 3 square Saul Bass slides: {slides}")
    win = sim["winner"]["name"].replace("United States of America", "USA")
    ru = sim["runner_up"]["name"].replace("United States of America", "USA")
    f1 = sim["first_out"][0]["name"].replace("United States of America", "USA")
    msg = (
        f"🗺️ {sc['title_long']}\n\n"
        f"{sc['premise']}\n\n"
        f"Swipe through all 3 slides to see why {f1} falls first — and who survives the final {ru} vs {win} showdown!\n\n"
        f"Would YOUR home survive? Comment below 👇\n\n"
        f"#LastMapStanding #Geography #MapSimulation #DataVisualization #USStates #WorldMap"
    )
    if dry_run:
        return slides, msg
    if not fb_is_configured():
        print("[FB CAROUSEL] Skipped upload (set FB_PAGE_ID & FB_PAGE_ACCESS_TOKEN in GitHub Secrets)")
        return slides, None
    post_id = upload_fb_photo_carousel(slides, msg)
    mark_published(sc, mode="fb_carousel", video_id=post_id or "")
    send_telegram(f"📘 <b>LAST MAP STANDING (FB 3-Slide Photo Carousel LIVE!)</b>\n{sc['title_short']}\npost_id={post_id}")
    return slides, post_id


def run_fb_text(cfg, sim, dry_run=False):
    sc = sim["scenario"]
    print(f"[FB TEXT] Scenario: {sc['id']} | {sc['title_short']}")
    msg = generate_fb_text_discussion(sim)
    print("[FB TEXT] Preview:\n" + msg)
    if dry_run:
        return msg, None
    if not fb_is_configured():
        print("[FB TEXT] Skipped upload (set FB_PAGE_ID & FB_PAGE_ACCESS_TOKEN in GitHub Secrets)")
        return msg, None
    post_id = upload_fb_text_post(msg)
    mark_published(sc, mode="fb_text", video_id=post_id or "")
    send_telegram(f"💬 <b>LAST MAP STANDING (FB Text Debate Post LIVE!)</b>\n{sc['title_short']}\npost_id={post_id}")
    return msg, post_id


def main():
    parser = argparse.ArgumentParser(description="Last Map Standing V22 Autopilot (YouTube + Facebook Graph API)")
    parser.add_argument("--mode", choices=["short", "longform", "fb_carousel", "fb_text"], default="short")
    parser.add_argument("--scenario-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--demo-fast", action="store_true")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    cfg = load_config()
    sc = pick_next_scenario(mode=args.mode, force_id=args.scenario_id)
    sim = simulate_scenario(sc)

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
        out_dir = args.out_dir
    else:
        out_dir = tempfile.mkdtemp(prefix="lms_v22_")

    if args.mode == "short":
        run_short(cfg, sim, out_dir, dry_run=args.dry_run, privacy=args.privacy)
    elif args.mode == "longform":
        run_longform(cfg, sim, out_dir, dry_run=args.dry_run, demo_fast=args.demo_fast, privacy=args.privacy)
    elif args.mode == "fb_carousel":
        run_fb_carousel(cfg, sim, out_dir, dry_run=args.dry_run)
    else:
        run_fb_text(cfg, sim, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
