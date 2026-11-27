# LAST MAP STANDING — V22.0 SAUL BASS PAPER-CUT ATLAS ENGINE ($0/month • 5+ Years Infinite Autopilot)

## 1) Quick GitHub Setup (Windows — No `git` Required)
1. Create a new **Public** GitHub repository named: `last-map-standing-v22`
2. Unzip `LastMapStanding-V22-SAUL-BASS-ENGINE.zip` on your PC.
3. Click **Add file -> Upload files** on GitHub and drag-and-drop all files and folders (`*.py`, `channel_config.json`, `published_history.json`, `requirements.txt`, `maps/`, `fonts/`).
4. **IMPORTANT (GitHub Web UI hides `.github` folders on drag-and-drop!):**
   - Click **Add file -> Create new file**
   - Type: `.github/workflows/short_autopilot.yml` and paste the contents from `workflows_copy/short_autopilot.yml` -> Commit.
   - Click **Add file -> Create new file**
   - Type: `.github/workflows/longform_autopilot.yml` and paste the contents from `workflows_copy/longform_autopilot.yml` -> Commit.

## 2) Add GitHub Secrets (`Settings -> Secrets and variables -> Actions`)
- `YOUTUBE_CLIENT_ID` — From Google Cloud Console (set OAuth Publishing Status to **In Production** so your refresh token NEVER expires!)
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN` — Generated for your `@LastMapStanding` YouTube channel
- `GROQ_API_KEY` — Free Groq key (optional: engine still runs 100% offline with built-in documentary scriptwriter!)
- `GEMINI_API_KEY` — Free Gemini backup key (optional)
- `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID` — Optional live upload alerts

## 3) Automatic 5+ Year Publishing Schedule ($0/month)
- **3 Vertical Shorts / day** (`19 11,16,21 * * *` UTC — off-peak odd minutes, zero queue lag)
- **1 Full 10-14 Minute Documentary / 2 days** (`47 17 1-31/2 * *` UTC — with custom Saul Bass Poster Thumbnail + Auto-Chapters)
- **Auto-commits `published_history.json`** after every upload so GitHub Actions NEVER disables cron workflows even after 5+ years!
