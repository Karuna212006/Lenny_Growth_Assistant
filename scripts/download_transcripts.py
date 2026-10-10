"""
Transcripts Downloader Script.

Downloads Lenny's Podcast transcripts from the open archive:
https://github.com/ChatPRD/lennys-podcast-transcripts

Usage:
    python scripts/download_transcripts.py --sample 5   # Download only 5 sample episodes
    python scripts/download_transcripts.py --all        # Download all 300+ episodes
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/ChatPRD/lennys-podcast-transcripts.git"
ROOT_DIR = Path(__file__).resolve().parent.parent
TARGET_DIR = ROOT_DIR / "data" / "transcripts"


def download_transcripts(sample_size: int | None = None) -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = ROOT_DIR / "temp_transcripts_download"

    print(f"Fetching transcript archive from {REPO_URL}...")
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        # Shallow clone to minimize network transfer
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        episodes_dir = temp_dir / "episodes"
        if not episodes_dir.exists():
            print("Error: 'episodes' directory not found in cloned repository.", file=sys.stderr)
            sys.exit(1)

        episode_folders = sorted([f for f in episodes_dir.iterdir() if f.is_dir()])
        total_available = len(episode_folders)
        print(f"Discovered {total_available} episodes.")

        if sample_size and sample_size > 0:
            episode_folders = episode_folders[:sample_size]
            print(f"Selecting {len(episode_folders)} sample episodes.")

        copied_count = 0
        for ep_folder in episode_folders:
            dest_folder = TARGET_DIR / ep_folder.name
            if dest_folder.exists():
                shutil.rmtree(dest_folder)
            shutil.copytree(ep_folder, dest_folder)
            copied_count += 1

        print(f"Successfully downloaded {copied_count} episode transcripts to {TARGET_DIR}.")

    except subprocess.CalledProcessError as err:
        print(f"Failed to clone repository: {err.stderr or err}", file=sys.stderr)
        sys.exit(1)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download transcripts from ChatPRD repository")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sample", type=int, default=None, help="Number of sample episodes to download")
    group.add_argument("--all", action="store_true", help="Download all available episodes")

    args = parser.parse_args()

    # Default to sample 10 if neither is specified
    if not args.all and args.sample is None:
        sample = 10
    else:
        sample = args.sample

    download_transcripts(sample_size=sample)


if __name__ == "__main__":
    main()
