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


def publish_tiktok_via_buffer(video_path, caption, delay_minutes=0, thumbnail_offset_ms=450):
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
    High-Search-Value English TikTok caption optimized for 2026 Creator Rewards RPM
    and Buffer's 5-hashtag TikTok rule.
    """
    sc = sim["scenario"]
    total = sim["total"]
    max_d = sc.get("max_day", 365)
    f1 = sim["first_out"][0]["name"].replace("United States of America", "the US")
    unit = "US states" if sc["arena"] == "us_states" else "countries"
    arena_tag = "#usstates" if sc["arena"] == "us_states" else "#worldmap"

    return (
        f"{sc['title_short']} 🗺️⚡\n\n"
        f"{f1} falls FIRST — and out of {total} {unit}, only ONE survives to Day {max_d}.\n"
        f"Did YOUR home survive? Drop your state or country below 👇\n\n"
        f"#mapsimulation #whatif #geography {arena_tag} #lastmapstanding"
    )
