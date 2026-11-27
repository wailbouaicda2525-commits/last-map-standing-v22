"""
uploader_v22.py — Zero-Touch YouTube Data API v3 Uploader + Thumbnail Setter + Telegram Alert.
Uses identical GitHub Secret names as V20 (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN).
"""
import os
import urllib.parse
import urllib.request


def send_telegram(text):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    cid = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not tok or not cid:
        return
    try:
        url = f"https://api.telegram.org/bot{tok}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": cid, "text": text, "parse_mode": "HTML"}).encode("utf-8")
        urllib.request.urlopen(urllib.request.Request(url, data=data, method="POST"), timeout=15)
    except Exception as e:
        print(f"[TELEGRAM WARN] {e}")


def get_google_creds(scopes):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    refresh_token = (os.environ.get("YOUTUBE_REFRESH_TOKEN") or os.environ.get("GOOGLE_REFRESH_TOKEN") or "").strip()
    client_id = (os.environ.get("YOUTUBE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (os.environ.get("YOUTUBE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    if not (refresh_token and client_id and client_secret):
        raise RuntimeError("Missing YouTube OAuth secrets: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN")
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    creds.refresh(Request())
    return creds


def get_youtube_service():
    from googleapiclient.discovery import build
    creds = get_google_creds([
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video_to_youtube(mp4_path, title, description, tags, privacy="public", thumbnail_path=None, category_id="27"):
    from googleapiclient.http import MediaFileUpload

    yt = get_youtube_service()
    body = {
        "snippet": {
            "title": title[:98],
            "description": description[:4900],
            "tags": tags[:20],
            "categoryId": str(category_id),
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(mp4_path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  [YT UPLOAD] {int(status.progress() * 100)}%", flush=True)
    vid_id = resp["id"]
    print(f"[YOUTUBE LIVE!] https://www.youtube.com/watch?v={vid_id} (privacy={privacy})")

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            yt.thumbnails().set(
                videoId=vid_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
            ).execute()
            print("[THUMBNAIL UPLOADED OK!]")
        except Exception as e:
            print(f"[THUMBNAIL SKIPPED — verify channel phone at youtube.com/verify]: {e}")

    return vid_id
