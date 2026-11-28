#!/usr/bin/env python3
"""Bulletproof JSON union-merge + retry push for published_history.json.
Eliminates git push race failures when multiple workflows overlap.
"""
import json
import os
import shutil
import subprocess
import sys
import time


def run(cmd, check=True):
    r = subprocess.run(cmd, text=True, capture_output=True)
    if r.stdout:
        print(r.stdout.strip())
    if r.stderr:
        print(r.stderr.strip(), file=sys.stderr)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed ({r.returncode}): {' '.join(cmd)}")
    return r


def main():
    commit_msg = sys.argv[1] if len(sys.argv) > 1 else "chore: update published_history.json [skip ci]"
    hist_path = "published_history.json"
    tmp_path = "/tmp/local_published_history.json"

    if not os.path.exists(hist_path):
        print("No published_history.json present, skipping.")
        return

    shutil.copy2(hist_path, tmp_path)
    run(["git", "config", "user.name", "LastMapStanding Bot"])
    run(["git", "config", "user.email", "bot@lastmapstanding.local"])

    for attempt in range(1, 5):
        run(["git", "checkout", "--", hist_path], check=False)
        run(["git", "fetch", "origin", "main"])
        run(["git", "reset", "--hard", "origin/main"])

        with open(tmp_path, "r", encoding="utf-8") as f:
            loc = json.load(f)
        if os.path.exists(hist_path):
            with open(hist_path, "r", encoding="utf-8") as f:
                rem = json.load(f)
        else:
            rem = {"published_ids": [], "published_titles": [], "count": 0}

        merged_ids = list(rem.get("published_ids", []))
        for item in loc.get("published_ids", []):
            if item not in merged_ids:
                merged_ids.append(item)

        merged_titles = list(rem.get("published_titles", []))
        for title in loc.get("published_titles", []):
            if title not in merged_titles:
                merged_titles.append(title)

        rem["published_ids"] = merged_ids
        rem["published_titles"] = merged_titles
        rem["count"] = len(merged_ids)
        if loc.get("last_updated_utc"):
            rem["last_updated_utc"] = loc["last_updated_utc"]
        if loc.get("last_video_id"):
            rem["last_video_id"] = loc["last_video_id"]

        with open(hist_path, "w", encoding="utf-8") as f:
            json.dump(rem, f, indent=2)

        run(["git", "add", hist_path])
        diff = run(["git", "diff", "--staged", "--quiet"], check=False)
        if diff.returncode == 0:
            print("No new published_history.json changes to commit.")
            return

        run(["git", "commit", "-m", commit_msg])
        push = run(["git", "push", "origin", "main"], check=False)
        if push.returncode == 0:
            print(f"[OK] Pushed published_history.json cleanly on attempt {attempt}.")
            return

        print(f"[RETRY] Push race on attempt {attempt}, retrying in 3s...")
        time.sleep(3)

    raise SystemExit("ERROR: Failed to push published_history.json after 4 attempts.")


if __name__ == "__main__":
    main()
