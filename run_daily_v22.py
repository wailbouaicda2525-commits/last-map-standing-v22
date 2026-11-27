"""
run_daily_v22.py — Unified 5+ Year Zero-Touch Orchestrator for Last Map Standing (V22 Saul Bass Atlas).
Usage:
  python3 run_daily_v22.py --mode short
  python3 run_daily_v22.py --mode longform
  python3 run_daily_v22.py --mode longform --dry-run --demo-fast
"""
import argparse
import datetime
import json
import os
import random
import subprocess
import tempfile
import time

import imageio_ffmpeg

from map_geometry_v22 import BASE_DIR, get_theme_for_scenario, get_layout_variant
from scenario_engine_v22 import pick_next_scenario, simulate_scenario, mark_published
from scriptwriter_v22 import (
    generate_short_script,
    generate_tiktok_65s_script,
    generate_longform_acts,
    compute_adaptive_minutes,
)
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
from tiktok_v22 import (
    buffer_is_configured,
    publish_tiktok_via_buffer,
    tiktok_is_configured,
    upload_tiktok_inbox_draft,
    build_tiktok_seo_caption,
)
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

    print(f"[SHORT] Rendering {total_dur:.1f}s V22.8 Themed Short + Subscribe CTA (1080x1920)...")
    render_short_9x16(
        sim,
        words,
        mixed_m4a,
        total_dur,
        out_mp4,
        fps=30,
        show_vs_showdown=False,
        cta_label="NEXT MAP TOMORROW  •  SUBSCRIBE",
    )
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


def generate_random_tiktok_delays(n_batch):
    """
    Generate 100% unpredictable, human-like random publish delays (in minutes from batch start)
    for TikTok PUBLIC autopilot (uses OS entropy via SystemRandom -> no two days ever repeat!).
    Example for n_batch=4:
      Start +42m -> gap +4h 35m -> gap +3h 10m -> gap +5h 08m -> (~10h 25m random overnight gap!)
    Single manual test (n_batch=1) posts immediately (0 min).
    """
    if n_batch <= 1:
        return [0]

    rng = random.SystemRandom()
    # Random start offset for Video #1 so even the first daily post never lands on the same minute
    first_delay = 0 if rng.random() < 0.20 else rng.randint(15, 135)

    if n_batch == 2:
        gaps = [rng.randint(240, 540)]  # 4h00m - 9h00m
        max_span = 720
    elif n_batch == 3:
        gaps = [rng.randint(185, 345), rng.randint(235, 455)]
        rng.shuffle(gaps)
        max_span = 960  # <= 16h span -> leaves ~8h-12h random overnight pause
    elif n_batch == 4:
        # Mirrors exact organic human rhythm: e.g. 4h35m, 3h10m, 5h08m + ~10h overnight!
        gaps = [
            rng.randint(160, 235),  # ~2h40m - 3h55m (e.g. 3h10m)
            rng.randint(220, 310),  # ~3h40m - 5h10m (e.g. 4h35m)
            rng.randint(255, 365),  # ~4h15m - 6h05m (e.g. 5h08m)
        ]
        rng.shuffle(gaps)
        max_span = 930  # <= 15h30m span -> leaves ~8h30m-11h30m random overnight rest!
    else:
        gaps = [rng.randint(150, 255) for _ in range(n_batch - 1)]
        rng.shuffle(gaps)
        max_span = 1020

    # Keep total daily window strictly under max_span so today's last post never collides with tomorrow
    if sum(gaps) > max_span:
        scale = max_span / float(sum(gaps))
        gaps = [max(135, int(round(g * scale))) for g in gaps]

    delays = [first_delay]
    for g in gaps:
        delays.append(delays[-1] + g)
    return delays


def run_tiktok_65s(cfg, sim, out_dir, dry_run=False, batch_idx=1, batch_total=1, delay_minutes=0):
    """
    Generate & push a guaranteed 64-70s (>60s floor) TikTok Creator Rewards video for Last Map Standing!
    - Includes vertical FINAL 2 VS SHOWDOWN real-data comparison bars + Open-Loop Follow CTA.
    - Publishes PUBLIC automatically via Buffer Free GraphQL API ($0/mo unlimited, max 4/10 rolling slots)
      using truly randomized human-like spacing (no fixed posting clock!).
    """
    sc = sim["scenario"]
    th = get_theme_for_scenario(sc)
    ep_voice, ep_fallbacks = pick_episode_voice(cfg, sc)
    prefix = f"{batch_idx:02d}_" if batch_total > 1 else ""
    tag = f"[TIKTOK 65s {batch_idx}/{batch_total}]"
    print(f"{tag} Scenario: {sc['id']} | Theme: {th['name']} | Voice: {ep_voice} | {sc['title_short']}")

    script = generate_tiktok_65s_script(sim)
    print(f"{tag} Creator Rewards script ready ({len(script.split())} words)")

    voice_mp3 = os.path.join(out_dir, f"{prefix}tiktok_voice.mp3")
    sfx_wav = os.path.join(out_dir, f"{prefix}tiktok_sfx.wav")
    mixed_m4a = os.path.join(out_dir, f"{prefix}tiktok_mixed.m4a")
    out_mp4 = os.path.join(out_dir, f"{prefix}LMS_TIKTOK_65S_{sc['id']}.mp4")
    cover_jpg = os.path.join(out_dir, f"{prefix}LMS_TIKTOK_COVER_{sc['id']}.jpg")
    caption_txt = os.path.join(out_dir, f"{prefix}LMS_TIKTOK_CAPTION_{sc['id']}.txt")

    render_short_thumbnail_9x16(sim, cover_jpg)
    caption = build_tiktok_seo_caption(sim)
    with open(caption_txt, "w", encoding="utf-8") as cf:
        cf.write(caption + "\n")
    # Also append into a single ALL_CAPTIONS.txt for ultra-fast copy-paste across all 3 Drafts!
    all_caps = os.path.join(out_dir, "ALL_TIKTOK_CAPTIONS.txt")
    with open(all_caps, "a", encoding="utf-8") as af:
        af.write(f"================ DRAFT {batch_idx}/{batch_total}: {sc['id']} ================\n")
        af.write(caption + "\n\n")
    print(f"{tag} 9:16 Cover + SEO Caption saved ({cover_jpg})")

    # Slightly calmer +2% documentary pace -> precision 64-70s sweet spot for Creator Rewards (>60s rule!)
    words = synthesize_voice(
        script,
        voice_mp3,
        voice=ep_voice,
        fallbacks=ep_fallbacks,
        rate=cfg.get("voice_rate_tiktok", "+2%"),
        pitch=cfg.get("voice_pitch", "-2Hz"),
    )
    vdur = get_audio_duration(voice_mp3)
    # HARD CREATOR REWARDS FLOOR: guarantee >= 64.0s ALWAYS (just over 60s -> max Completion Rate + 100% paid!)
    total_dur = max(64.0, vdur + 1.8)
    print(f"{tag} Voice={vdur:.1f}s -> Final Duration={total_dur:.1f}s (Creator Rewards >=60s GUARANTEED)")

    t_win = max(12.0, total_dur - 5.4)
    elim_cues = [1.8 + i * ((t_win - 9.0) / 8.0) for i in range(8)]
    synthesize_saul_bass_soundscape(total_dur, elim_cues, [1.25, t_win - 7.8, t_win - 0.3], t_win, sfx_wav)
    mix_voice_and_sfx(voice_mp3, sfx_wav, mixed_m4a, total_dur)

    print(f"{tag} Rendering {total_dur:.1f}s V22.8 TikTok Video + FINAL 2 VS Showdown + Follow CTA (1080x1920 @ 30fps)...")
    render_short_9x16(
        sim,
        words,
        mixed_m4a,
        total_dur,
        out_mp4,
        fps=30,
        show_vs_showdown=True,
        cta_label="NEXT MAP TOMORROW  •  FOLLOW",
    )
    print(f"{tag} Render complete: {out_mp4} ({os.path.getsize(out_mp4) / 1e6:.2f} MB)")

    # Write convenient Copy-Paste Caption into GitHub Actions Step Summary when running in CI
    gh_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh_summary:
        try:
            with open(gh_summary, "a", encoding="utf-8") as sf:
                sf.write(f"## 🎵 Video {batch_idx}/{batch_total} — `{sc['id']}` (`{th['name']}`)\n")
                sf.write(f"- **Duration:** `{total_dur:.1f}s` ✅ (Creator Rewards >60s + FINAL 2 VS Showdown)\n")
                sf.write(f"- **File:** `{os.path.basename(out_mp4)}`\n\n")
                sf.write("```text\n" + caption + "\n```\n\n")
        except Exception:
            pass

    if dry_run:
        return out_mp4, None

    pub_id = ""
    if buffer_is_configured():
        # V22.8 Truly Randomized 24/7 Human-Like Spacing (generated fresh via OS entropy every day!)
        # Uses max 4 of 10 rolling Buffer Free queue slots -> 120+ PUBLIC TikToks/month for $0 FOREVER!
        delay_m = max(0, int(delay_minutes))
        pub_id = publish_tiktok_via_buffer(out_mp4, caption, delay_minutes=delay_m, thumbnail_offset_ms=450)
        hrs, mins = divmod(delay_m, 60)
        slot_note = "LIVE NOW!" if delay_m == 0 else f"RANDOM SCHEDULED PUBLIC (+{hrs}h {mins:02d}m)"
        send_telegram(
            f"🎵 <b>LAST MAP STANDING — TikTok {batch_idx}/{batch_total} ({total_dur:.0f}s) {slot_note}</b>\n"
            f"Buffer post_id={pub_id}\n\n{caption}"
        )
    elif tiktok_is_configured():
        pub_id = upload_tiktok_inbox_draft(out_mp4)
        send_telegram(
            f"🎵 <b>LAST MAP STANDING (TikTok Draft {batch_idx}/{batch_total} — {total_dur:.0f}s READY!)</b>\n"
            f"Open TikTok App → Inbox / Drafts & tap Post!\n\n{caption}"
        )
    else:
        print(f"{tag} Add BUFFER_API_KEY secret for 100% AUTOMATIC PUBLIC publishing ($0/mo unlimited via Buffer Free)!")

    mark_published(sc, mode="tiktok", video_id=pub_id or f"artifact_{sc['id']}")
    return out_mp4, pub_id


def main():
    parser = argparse.ArgumentParser(description="Last Map Standing V22 Autopilot (YouTube + Facebook + TikTok)")
    parser.add_argument("--mode", choices=["short", "longform", "fb_carousel", "fb_text", "tiktok"], default="short")
    parser.add_argument("--scenario-id", default=None)
    parser.add_argument("--count", type=int, default=1, help="Number of Drafts to generate in one batch (TikTok mode: 1-5, default 3 in CI)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--demo-fast", action="store_true")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    cfg = load_config()
    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)
        out_dir = args.out_dir
    else:
        out_dir = tempfile.mkdtemp(prefix="lms_v22_")

    if args.mode == "tiktok":
        n_batch = max(1, min(5, int(args.count or 1)))
        if n_batch > 1 and args.scenario_id:
            print("[TIKTOK] --scenario-id supplied -> using it for Video 1 and auto-picking fresh scenarios for the rest.")

        batch_start_ts = time.time()
        rand_delays = generate_random_tiktok_delays(n_batch)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        print(f"[TIKTOK] Generated 100% RANDOM daily schedule for {n_batch} videos:")
        sched_lines = []
        for idx_d, dm in enumerate(rand_delays):
            target_t = now_utc + datetime.timedelta(minutes=dm)
            gap_txt = "START" if idx_d == 0 else f"gap +{divmod(dm - rand_delays[idx_d - 1], 60)[0]}h {divmod(dm - rand_delays[idx_d - 1], 60)[1]:02d}m"
            line = f"  Video {idx_d + 1}/{n_batch}: +{dm // 60}h {dm % 60:02d}m ({target_t.strftime('%H:%M UTC')}) [{gap_txt}]"
            print(line)
            sched_lines.append(line)

        gh_summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if gh_summary:
            try:
                with open(gh_summary, "a", encoding="utf-8") as sf:
                    sf.write("## 🎲 Today's 100% Random TikTok Publish Schedule\n```text\n")
                    sf.write("\n".join(sched_lines) + "\n```\n\n")
            except Exception:
                pass

        dry_used = set()
        for bi in range(1, n_batch + 1):
            force = args.scenario_id if bi == 1 else None
            sc = pick_next_scenario(mode="tiktok", force_id=force)
            if args.dry_run and sc["id"] in dry_used:
                from scenario_engine_v22 import build_infinite_catalog
                for cand in build_infinite_catalog():
                    if cand["id"] not in dry_used:
                        sc = cand
                        break
            dry_used.add(sc["id"])
            sim = simulate_scenario(sc)
            # Subtract elapsed render minutes so actual publish gaps match the random schedule cleanly
            target_dm = rand_delays[bi - 1]
            elapsed_m = int((time.time() - batch_start_ts) // 60)
            eff_delay = 0 if target_dm == 0 else max(5, target_dm - elapsed_m)
            run_tiktok_65s(
                cfg,
                sim,
                out_dir,
                dry_run=args.dry_run,
                batch_idx=bi,
                batch_total=n_batch,
                delay_minutes=eff_delay,
            )
            if bi < n_batch and not args.dry_run and (buffer_is_configured() or tiktok_is_configured()):
                print("[TIKTOK] Cooling down 6s before next TikTok publish...")
                time.sleep(6)
        return

    sc = pick_next_scenario(mode=args.mode, force_id=args.scenario_id)
    sim = simulate_scenario(sc)

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
