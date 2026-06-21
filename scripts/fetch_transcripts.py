#!/usr/bin/env python3
"""
fetch_transcripts.py

Programmatically fetch YouTube transcripts for the AI-SEO research project
and save them as Markdown files under research/youtube-transcripts/, organized
by author.

Usage:
    pip install youtube-transcript-api
    python scripts/fetch_transcripts.py

Reads the list of videos from scripts/channels.json. Each entry:
    {
      "author": "Mike King",
      "video_id": "XXXXXXXXXXX",
      "title": "How AI Mode Actually Works",
      "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
      "date": "2025-04-10"
    }

Videos with disabled/unavailable transcripts are skipped and logged to
research/youtube-transcripts/_skipped.log instead of crashing the run.
"""

import json
import os
import re
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        CouldNotRetrieveTranscript,
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
except ImportError:
    raise SystemExit(
        "Missing dependency. Run: pip install youtube-transcript-api"
    )

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "scripts" / "channels.json"
OUT_DIR = ROOT / "research" / "youtube-transcripts"
SKIP_LOG = OUT_DIR / "_skipped.log"


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:80]


def fetch_one(entry: dict) -> bool:
    """Fetch and save a single transcript. Returns True on success."""
    author = entry["author"]
    video_id = entry["video_id"]
    title = entry.get("title", video_id)

    author_dir = OUT_DIR / slugify(author)
    author_dir.mkdir(parents=True, exist_ok=True)
    out_path = author_dir / f"{slugify(title)}.md"

    try:
        # youtube-transcript-api >= 1.0 uses an instance-based API.
        segments = YouTubeTranscriptApi().fetch(video_id).to_raw_data()
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        log_skip(entry, type(e).__name__)
        return False
    except CouldNotRetrieveTranscript as e:  # IP block, request blocked, etc.
        log_skip(entry, type(e).__name__)
        return False
    except Exception as e:  # network / unexpected
        log_skip(entry, f"error:{e}")
        return False

    body = "\n".join(seg["text"] for seg in segments)
    header = (
        f"# {title}\n\n"
        f"- **Author:** {author}\n"
        f"- **URL:** {entry.get('url', '')}\n"
        f"- **Date:** {entry.get('date', 'unknown')}\n"
        f"- **Video ID:** {video_id}\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + body, encoding="utf-8")
    print(f"  saved: {out_path.relative_to(ROOT)}")
    return True


def log_skip(entry: dict, reason: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with SKIP_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{entry.get('author')}\t{entry.get('video_id')}\t{reason}\n")
    print(f"  skipped {entry.get('video_id')} ({reason})")


def main() -> None:
    if not SOURCES.exists():
        raise SystemExit(f"Missing {SOURCES}. Create it first (see README).")

    entries = json.loads(SOURCES.read_text(encoding="utf-8"))
    print(f"Fetching {len(entries)} transcripts...")

    ok = 0
    for entry in entries:
        print(f"- {entry['author']}: {entry.get('title', entry['video_id'])}")
        if fetch_one(entry):
            ok += 1

    print(f"\nDone. {ok}/{len(entries)} transcripts saved.")
    if SKIP_LOG.exists():
        print(f"Skipped videos logged to {SKIP_LOG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
