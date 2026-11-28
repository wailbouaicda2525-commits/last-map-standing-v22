"""
tiktok_v22.py — 100% Automatic PUBLIC TikTok Publisher for Last Map Standing (V22.7).

PRIMARY ENGINE (Recommended — $0/mo FOREVER, UNLIMITED 90–300+ PUBLIC videos/month, 1 Secret!):
  - Buffer Free Plan GraphQL API (`https://api.buffer.com`)
  - Buffer is an officially audited TikTok Direct-Post Partner!
  - Free plan allows 3 channels + 1 API key + 10 rolling queued posts at a time (NOT 10/month — slots
    free up the second each video goes live!). Publishing 3 videos/day (1 Share Now + 2 scheduled +4h/+8h)
    uses at most 2 of 10 slots -> UNLIMITED PUBLIC AUTO-PUBLISHING for $0/month, no credit card, no Drafts!
  - Video files are served cleanly via built-in GitHub Releases (`tiktok-media-buffer` tag, $0 unlimited)
    with automatic cleanup of assets older than 48 hours.

SECONDARY FALLBACK (Optional):
  - Official TikTok Content Posting API v2 Inbox Drafts (`video.upload` scope) if TIKTOK_REFRESH_TOKEN is set.
"""
import datetime
import json
import math
import os
import subprocess
import time
import requests

BUFFER_GRAPHQL_URL = "https://api.buffer.com"
RELEASE_TAG = "tiktok-media-buffer"

TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_INBOX_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
TIKTOK_STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

SINGLE_CHUNK_MAX = 64 * 1024 * 1024
MULTI_CHUNK_SIZE = 10 * 1024 * 1024


# =====================================================================
# 1) BUFFER FREE PLAN GRAPHQL API (UNLIMITED PUBLIC DIRECT AUTO-PUBLISH)
# =====================================================================
def buffer_is_configured():
    return bool(os.environ.get("BUFFER_API_KEY", "").strip())


def _buffer_gql(query, variables=None):
    api_key = os.environ.get("BUFFER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("BUFFER_API_KEY is not set.")
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(
        BUFFER_GRAPHQL_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    data = resp.json() if resp.content else {}
    if not resp.ok or data.get("errors"):
        raise RuntimeError(f"Buffer GraphQL error ({resp.status_code}): {data}")
    return data.get("data") or {}


def get_buffer_tiktok_channel_id():
    """Auto-discover your connected TikTok channelId in Buffer (zero manual ID hunting!)."""
    override = os.environ.get("BUFFER_TIKTOK_CHANNEL_ID", "").strip()
    if override:
        return override

    org_data = _buffer_gql("query { account { organizations { id name } } }")
    orgs = ((org_data.get("account") or {}).get("organizations")) or []
    if not orgs:
        raise RuntimeError("No Buffer organizations found for this BUFFER_API_KEY.")

    for org in orgs:
        ch_data = _buffer_gql(
            """
            query GetChannels($orgId: OrganizationId!) {
              channels(input: { organizationId: $orgId }) {
                id
                name
                service
              }
            }
            """,
            {"orgId": org["id"]},
        )
        channels = ch_data.get("channels") or []
        for ch in channels:
            if str(ch.get("service", "")).lower() == "tiktok":
                print(f"[BUFFER] Auto-discovered TikTok channel: {ch.get('name')} (id={ch['id']})")
                return ch["id"]

    raise RuntimeError(
        "No connected TikTok channel found in Buffer! Open https://publish.buffer.com -> Connect Channel -> TikTok."
    )


def upload_video_to_github_release(video_path):
    """
    Upload rendered MP4 to a dedicated public GitHub Release (`tiktok-media-buffer`) using built-in GITHUB_TOKEN.
    Returns direct HTTPS download URL so Buffer can pull it cleanly ($0/mo, up to 2 GB/file).
    Automatically purges old assets > 48h to keep the repository spotless!
    """
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    gh_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo or not gh_token:
        raise RuntimeError(
            "GITHUB_REPOSITORY / GITHUB_TOKEN not set (these are automatic inside GitHub Actions!)."
        )

    env = dict(os.environ)
    env["GH_TOKEN"] = gh_token
    fname = os.path.basename(video_path)

    # Ensure release exists (idempotent)
    check = subprocess.run(
        ["gh", "release", "view", RELEASE_TAG, "--repo", repo],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if check.returncode != 0:
        subprocess.run(
            [
                "gh", "release", "create", RELEASE_TAG,
                "--repo", repo,
                "--title", "TikTok Media Staging (Auto-Cleaned)",
                "--notes", "Temporary public MP4 staging for Buffer GraphQL TikTok auto-publishing.",
            ],
            env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    # Prune old assets older than 48h (best-effort, non-blocking)
    try:
        out = subprocess.check_output(
            ["gh", "release", "view", RELEASE_TAG, "--repo", repo, "--json", "assets"],
            env=env, text=True,
        )
        assets = (json.loads(out) or {}).get("assets") or []
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=48)
        for a in assets:
            created = a.get("createdAt", "")
            if created:
                dt = datetime.datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt < cutoff:
                    subprocess.run(
                        ["gh", "release", "delete-asset", RELEASE_TAG, a["name"], "--repo", repo, "--yes"],
                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
    except Exception as e:
        print(f"[BUFFER STAGING] Cleanup note (non-blocking): {e}")

    # Upload fresh MP4 asset
    subprocess.run(
        ["gh", "release", "upload", RELEASE_TAG, video_path, "--repo", repo, "--clobber"],
        env=env, check=True,
    )

    public_url = f"https://github.com/{repo}/releases/download/{RELEASE_TAG}/{fname}"
    # Verify URL is reachable before handing to Buffer
    for attempt in range(1, 4):
        try:
            r = requests.head(public_url, allow_redirects=True, timeout=20)
            if r.status_code == 200:
                print(f"[BUFFER STAGING] Verified public MP4 URL ({r.headers.get('Content-Length', '?')} bytes): {public_url}")
                return public_url
        except Exception:
            pass
        time.sleep(2 * attempt)
    return public_url


def publish_tiktok_via_buffer(video_path, caption, delay_minutes=0, thumbnail_offset_ms=100):
    """
    Publish or schedule a 100% PUBLIC TikTok video via Buffer's official GraphQL API!
      - delay_minutes == 0 -> mode: shareNow (publishes PUBLICLY RIGHT NOW, 0 queue slots used!)
      - delay_minutes >  0 -> mode: customScheduled at UTC now + delay_minutes (organic human-like spacing!)
    """
    channel_id = get_buffer_tiktok_channel_id()
    public_url = upload_video_to_github_release(video_path)

    post_input = {
        "text": caption,
        "channelId": channel_id,
        "schedulingType": "automatic",
        "assets": [
            {
                "video": {
                    "url": public_url,
                    "metadata": {
                        "thumbnailOffset": int(thumbnail_offset_ms),
                    },
                }
            }
        ],
    }

    if delay_minutes <= 0:
        post_input["mode"] = "shareNow"
        sched_label = "SHARE NOW (LIVE IMMEDIATELY)"
    else:
        due = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=int(delay_minutes))
        due_iso = due.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        post_input["mode"] = "customScheduled"
        post_input["dueAt"] = due_iso
        hrs, mins = divmod(int(delay_minutes), 60)
        sched_label = f"SCHEDULED PUBLIC (+{hrs}h {mins:02d}m @ {due_iso})"

    mutation = """
    mutation CreateTikTokPost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            text
            dueAt
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """
    print(f"[BUFFER] Sending PUBLIC TikTok video ({sched_label})...")
    data = _buffer_gql(mutation, {"input": post_input})
    res = data.get("createPost") or {}
    if "message" in res and "post" not in res:
        raise RuntimeError(f"Buffer createPost rejected: {res['message']}")
    post = res.get("post") or {}
    post_id = post.get("id", "")
    if not post_id:
        raise RuntimeError(f"Buffer createPost unexpected response: {data}")
    print(f"[BUFFER] SUCCESS! TikTok post queued/live publicly (post_id={post_id}, dueAt={post.get('dueAt', 'now')})")
    return post_id


# =====================================================================
# 2) OPTIONAL FALLBACK: OFFICIAL TIKTOK INBOX / DRAFTS API
# =====================================================================
def tiktok_is_configured():
    if os.environ.get("TIKTOK_ACCESS_TOKEN", "").strip():
        return True
    return bool(
        os.environ.get("TIKTOK_CLIENT_KEY", "").strip()
        and os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
        and os.environ.get("TIKTOK_REFRESH_TOKEN", "").strip()
    )


def get_fresh_access_token():
    direct = os.environ.get("TIKTOK_ACCESS_TOKEN", "").strip()
    client_key = os.environ.get("TIKTOK_CLIENT_KEY", "").strip()
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("TIKTOK_REFRESH_TOKEN", "").strip()

    if client_key and client_secret and refresh_token:
        resp = requests.post(
            TIKTOK_TOKEN_URL,
            data={
                "client_key": client_key,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        data = resp.json() if resp.content else {}
        if not resp.ok or "access_token" not in data:
            err = data.get("error_description") or data.get("error") or resp.text[:300]
            raise RuntimeError(f"TikTok OAuth token refresh failed ({resp.status_code}): {err}")
        return data["access_token"]

    if direct:
        return direct
    raise RuntimeError("TikTok credentials not set.")


def upload_tiktok_inbox_draft(video_path):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"TikTok video not found: {video_path}")
    access_token = get_fresh_access_token()
    video_size = os.path.getsize(video_path)
    if video_size <= SINGLE_CHUNK_MAX:
        chunk_size, total_chunks = video_size, 1
    else:
        chunk_size = MULTI_CHUNK_SIZE
        total_chunks = int(math.ceil(video_size / float(chunk_size)))

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    r_init = requests.post(
        TIKTOK_INBOX_INIT_URL,
        headers=headers,
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunks,
            }
        },
        timeout=45,
    )
    body = r_init.json() if r_init.content else {}
    err_obj = body.get("error") or {}
    if not r_init.ok or (err_obj.get("code") and err_obj.get("code") != "ok"):
        raise RuntimeError(f"TikTok Inbox init failed ({r_init.status_code}): {body}")

    data = body.get("data") or {}
    publish_id, upload_url = data.get("publish_id"), data.get("upload_url")
    with open(video_path, "rb") as f:
        offset = 0
        for ci in range(total_chunks):
            chunk = f.read(chunk_size)
            if not chunk:
                break
            end = offset + len(chunk) - 1
            r_put = requests.put(
                upload_url,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {offset}-{end}/{video_size}",
                },
                data=chunk,
                timeout=180,
            )
            if r_put.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok chunk upload failed ({r_put.status_code}): {r_put.text[:300]}")
            offset = end + 1

    for _ in range(12):
        time.sleep(5)
        r_st = requests.post(TIKTOK_STATUS_URL, headers=headers, json={"publish_id": publish_id}, timeout=30)
        st = ((r_st.json() if r_st.content else {}).get("data") or {}).get("status", "UNKNOWN")
        if st in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return publish_id
        if st == "FAILED":
            raise RuntimeError(f"TikTok Inbox processing failed: {r_st.text[:300]}")
    return publish_id


# =====================================================================
# 3) HIGH-RPM TIKTOK CAPTION BUILDER (STRICTLY 5 HASHTAGS FOR BUFFER!)
# =====================================================================
def build_tiktok_seo_caption(sim):
    """
    Organic, anti-spam TikTok caption generator (zero copy-paste template fingerprint!).
    Rotates across 10 natural human hook/CTA styles and topic-matched 4-5 hashtag combinations
    strictly respecting Buffer's 5-hashtag TikTok limit.
    """
    import hashlib as _hl

    sc = sim["scenario"]
    total = sim["total"]
    max_d = sc.get("max_day", 365)
    f1 = sim["first_out"][0]["name"].replace("United States of America", "the US")
    winner = (sim.get("survivors") or sim.get("last_standing") or [{}])
    is_us = (sc.get("arena") == "us_states")
    unit = "US states" if is_us else "countries"
    place_word = "state" if is_us else "country"
    title = str(sc.get("title_short") or "Map Survival Simulation").strip()
    sid = str(sc.get("id") or title)
    seed = int(_hl.sha256(sid.encode("utf-8")).hexdigest()[:8], 16)

    openers = [
        f"{title}",
        f"Wait until you see who goes out first… {title}",
        f"I simulated this across all {total} {unit}: {title}",
        f"Most people guess wrong on this one — {title}",
        f"Day 1 to Day {max_d}: {title}",
        f"Could your {place_word} actually make it to Day {max_d}? {title}",
        f"Watch how fast {f1} collapses here — {title}",
        f"Nobody expected {f1} to fall first. {title}",
        f"Out of {total} {unit}, almost everyone gets eliminated before Day {max_d}.",
        f"This map simulation gets wild after Day 90: {title}",
    ]
    ctas = [
        f"How many days did your {place_word} last?",
        f"Did your {place_word} make the final 5 or fall early?",
        f"Comment your {place_word} — be honest, did you expect that?",
        f"Would you survive where you live right now?",
        f"Tell me which {place_word} surprised you the most.",
        f"Did {f1} deserve to go out first or was that harsh?",
        f"Drop your {place_word} below and check what day it fell.",
        f"Who did you think was winning before the final showdown?",
        f"What scenario should we run on the map next?",
        f"Be honest — did you think your {place_word} was winning this?",
    ]

    # Topic-matched rotating hashtags (strictly 4-5 tags total, no identical repeated block!)
    tl = title.lower()
    topic_tags = []
    if any(k in tl for k in ["money", "$", "salary", "rent", "rich", "economy", "tax", "inflation", "debt"]):
        topic_tags = ["#economics", "#personalfinance", "#moneyfacts"]
    elif any(k in tl for k in ["cold", "freeze", "heat", "rain", "water", "flood", "ice", "storm", "sun", "climate"]):
        topic_tags = ["#climate", "#sciencefacts", "#survival"]
    elif any(k in tl for k in ["power", "electric", "grid", "internet", "blackout", "oil", "fuel", "food"]):
        topic_tags = ["#survival", "#whatifscenario", "#infrastructure"]
    elif any(k in tl for k in ["border", "war", "island", "invasion", "empire", "zombie"]):
        topic_tags = ["#geopolitics", "#historyfacts", "#whatif"]
    else:
        topic_tags = ["#geographyfacts", "#worlddata", "#whatif"]

    core_pools = (
        [["#usgeography", "#50states", "#americamap"], ["#usstates", "#maptok", "#dataviz"], ["#unitedstates", "#geographytok", "#mapsimulation"]]
        if is_us else
        [["#worldmap", "#geographytok", "#maptok"], ["#worldgeography", "#dataviz", "#countries"], ["#mapsimulation", "#globaldata", "#geography"]]
    )
    pool = core_pools[seed % len(core_pools)]
    t_tag = topic_tags[(seed // 3) % len(topic_tags)]
    tags = []
    for tg in [pool[0], pool[1], t_tag, pool[2], "#lastmapstanding"]:
        if tg not in tags:
            tags.append(tg)
    tags = tags[:5]

    opener = openers[seed % len(openers)]
    cta = ctas[(seed // 7) % len(ctas)]
    return f"{opener}\n\n{cta}\n\n{' '.join(tags)}"
