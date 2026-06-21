#!/usr/bin/env python3
"""
fetch_transcripts.py

Fetch YouTube transcripts for the AI-SEO research project via the Supadata API
(https://supadata.ai) and save them as Markdown files under
research/youtube-transcripts/, organized by author.

Why Supadata: the youtube-transcript-api library scrapes YouTube's InnerTube
endpoint from the local machine, and YouTube IP-blocks those requests
(RequestBlocked) from this network. Supadata fetches server-side, so the local
IP block does not apply.

Usage:
    # Put your key in a gitignored .env file at the repo root:
    #   SUPADATA_API_KEY=sd_xxx
    # ...or export it in the environment, then:
    python scripts/fetch_transcripts.py

Reads the list of videos from scripts/channels.json. Each entry:
    {
      "author": "Mike King",
      "video_id": "XXXXXXXXXXX",
      "title": "How AI Mode Actually Works",
      "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
      "date": "2025-04-10"
    }

Videos with no available transcript (HTTP 206/404/403) are skipped and logged to
research/youtube-transcripts/_skipped.log instead of crashing the run. Videos
longer than ~20 minutes are returned asynchronously (HTTP 202 + jobId); the
script polls the job endpoint until it completes.
"""

import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.supadata.ai/v1/transcript"

# Supadata sits behind Cloudflare, which blocks the default "Python-urllib"
# User-Agent with a 1010 error. Send a browser-like UA so requests get through.
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "scripts" / "channels.json"
OUT_DIR = ROOT / "research" / "youtube-transcripts"
SKIP_LOG = OUT_DIR / "_skipped.log"

POLL_INTERVAL = 2     # seconds between job polls
POLL_TIMEOUT = 180    # max seconds to wait for an async job


def load_dotenv() -> None:
    """Minimal .env loader (no dependency). Does not overwrite existing vars."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def slugify(text: str) -> str:
    # Fold accented characters to ASCII (e.g. "Gübür" -> "gubur") so folder and
    # file names are consistent and portable.
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:80]


def api_get(url: str, api_key: str):
    """GET a Supadata URL. Returns (status_code, parsed_json|None)."""
    req = urllib.request.Request(
        url, headers={"x-api-key": api_key, "User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        # 206/404/403 etc. carry a JSON body describing the problem.
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"error": raw[:200]}
    body = json.loads(raw) if raw else {}
    return status, body


def fetch_transcript_text(entry: dict, api_key: str):
    """Return the transcript text for a video, or raise a Skip with a reason."""
    query = urllib.parse.urlencode(
        {"url": entry["url"], "text": "true", "lang": "en"}
    )
    status, body = api_get(f"{API_BASE}?{query}", api_key)

    if status == 200:
        return body.get("content", "")

    if status == 202:  # async job for long videos
        job_id = body.get("jobId")
        if not job_id:
            raise Skip("async-no-jobId")
        return poll_job(job_id, api_key)

    # 206 transcript unavailable, 404 not found, 403 restricted, etc.
    reason = body.get("error") or body.get("message") or f"http-{status}"
    raise Skip(f"{status}:{reason}")


def poll_job(job_id: str, api_key: str) -> str:
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        status, body = api_get(f"{API_BASE}/{job_id}", api_key)
        job_status = body.get("status")
        if job_status == "completed":
            return body.get("content", "")
        if job_status == "failed":
            raise Skip("job-failed")
        time.sleep(POLL_INTERVAL)
    raise Skip("job-timeout")


class Skip(Exception):
    """Raised when a transcript cannot be retrieved; logged and skipped."""


def fetch_one(entry: dict, api_key: str) -> bool:
    """Fetch and save a single transcript. Returns True on success."""
    author = entry["author"]
    video_id = entry["video_id"]
    title = entry.get("title", video_id)

    author_dir = OUT_DIR / slugify(author)
    author_dir.mkdir(parents=True, exist_ok=True)
    out_path = author_dir / f"{slugify(title)}.md"

    try:
        text = fetch_transcript_text(entry, api_key)
    except Skip as e:
        log_skip(entry, str(e))
        return False
    except Exception as e:  # network / unexpected
        log_skip(entry, f"error:{e}")
        return False

    if not text or not text.strip():
        log_skip(entry, "empty-transcript")
        return False

    header = (
        f"# {title}\n\n"
        f"- **Author:** {author}\n"
        f"- **URL:** {entry.get('url', '')}\n"
        f"- **Date:** {entry.get('date', 'unknown')}\n"
        f"- **Video ID:** {video_id}\n"
        f"- **Source:** Supadata transcript API\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + text.strip() + "\n", encoding="utf-8")
    print(f"  saved: {out_path.relative_to(ROOT)}")
    return True


def log_skip(entry: dict, reason: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with SKIP_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{entry.get('author')}\t{entry.get('video_id')}\t{reason}\n")
    print(f"  skipped {entry.get('video_id')} ({reason})")


def main() -> None:
    load_dotenv()
    api_key = os.environ.get("SUPADATA_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing SUPADATA_API_KEY. Set it in the environment or a .env file "
            "at the repo root (SUPADATA_API_KEY=sd_...)."
        )

    if not SOURCES.exists():
        raise SystemExit(f"Missing {SOURCES}. Create it first (see README).")

    entries = json.loads(SOURCES.read_text(encoding="utf-8"))
    print(f"Fetching {len(entries)} transcripts via Supadata...")

    ok = 0
    for entry in entries:
        print(f"- {entry['author']}: {entry.get('title', entry['video_id'])}")
        if fetch_one(entry, api_key):
            ok += 1

    print(f"\nDone. {ok}/{len(entries)} transcripts saved.")
    if SKIP_LOG.exists():
        print(f"Skipped videos logged to {SKIP_LOG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
