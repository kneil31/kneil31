#!/usr/bin/env python3

"""Automate importing photos/videos from an SD card to an SSD.

This script detects mounted SD cards (looking for ``/Volumes/*/DCIM``) and
interactively copies photos and/or videos to a target SSD folder. After copying
the files it optionally launches Lightroom, creates a zip archive of the shoot
folder and can upload that archive to WeTransfer.

Example usage::

    python photo_automation.py --api-key YOUR_API_KEY

The script will prompt for all required information.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".raw", ".dng"}
VIDEO_EXTS = {".mov", ".mp4", ".avi", ".mkv"}


def detect_sd_cards() -> list[Path]:
    """Return a list of SD card mount points under ``/Volumes``."""
    cards = []
    for dcim in glob.glob("/Volumes/*/DCIM"):
        path = Path(dcim).parent
        if path.is_dir():
            cards.append(path)
    return cards


def choose_sd_card(cards: list[Path]) -> Path:
    """Prompt the user to choose one of the detected SD cards."""
    if not cards:
        print("No SD card with DCIM folder found under /Volumes.")
        sys.exit(1)
    if len(cards) == 1:
        return cards[0]

    print("Select SD card to import from:")
    for idx, card in enumerate(cards, 1):
        print(f"  {idx}: {card}")
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(cards):
            return cards[int(choice) - 1]
        print("Invalid selection. Try again.")


def prompt_metadata() -> tuple[str, str, str, str]:
    """Ask for event name, location, date and import type."""
    event = input("Event name: ").strip() or "Untitled"
    location = input("Location: ").strip() or "Unknown"
    today = date.today().strftime("%Y-%m-%d")
    date_str = input(f"Date [default {today}]: ").strip() or today

    print("Import content:")
    print("  p: Photos")
    print("  v: Videos")
    print("  b: Both")
    mode = input("Choose [b]: ").strip().lower() or "b"
    if mode not in {"p", "v", "b"}:
        mode = "b"
    return event, location, date_str, mode


def build_dest_folder(ssd_root: Path, date_str: str, event: str, location: str) -> Path:
    """Return the destination folder for the shoot."""
    folder_name = f"{date_str}_{event}_{location}".replace(" ", "_")
    return ssd_root / folder_name


def copy_media(src: Path, dest: Path, mode: str) -> None:
    """Copy photos/videos from ``src`` to ``dest`` based on ``mode``."""
    include_photos = mode in {"p", "b"}
    include_videos = mode in {"v", "b"}

    for root, _, files in os.walk(src):
        for fname in files:
            ext = Path(fname).suffix.lower()
            is_photo = ext in PHOTO_EXTS
            is_video = ext in VIDEO_EXTS

            if (is_photo and include_photos) or (is_video and include_videos):
                src_path = Path(root) / fname
                rel = src_path.relative_to(src)
                subfolder = "Photos" if is_photo else "Video"
                dest_path = dest / subfolder / rel
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                print(f"Copied {src_path} -> {dest_path}")


def import_to_lightroom(folder: Path) -> None:
    """Open Lightroom Classic pointed at the given folder."""
    cmd = ["open", "-a", "Adobe Lightroom Classic", str(folder)]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("Lightroom command not found. Please adjust the script if needed.")


def create_zip(folder: Path) -> Path:
    """Create a zip archive of ``folder`` and return the archive path."""
    archive_path = shutil.make_archive(str(folder), "zip", root_dir=folder)
    print(f"Created archive {archive_path}")
    return Path(archive_path)


def upload_to_wetransfer(zip_path: Path, api_key: str) -> None:
    """Upload ``zip_path`` to WeTransfer using ``api_key``.

    This function provides only a minimal example. For a full integration,
    consult the official WeTransfer API documentation.
    """

    print(f"Uploading {zip_path} to WeTransfer...")
    try:
        import requests

        # Create transfer
        resp = requests.post(
            "https://dev.wetransfer.com/v2/transfers",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"name": zip_path.name},
        )
        resp.raise_for_status()
        transfer = resp.json()
        upload_url = transfer["upload_url"]

        # Upload file
        with zip_path.open("rb") as f:
            up = requests.put(upload_url, data=f)
            up.raise_for_status()

        print("Upload completed.")
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to upload: {exc}")


def confirm_delete(src: Path) -> None:
    ans = input("Delete files from SD card? [y/N]: ").strip().lower()
    if ans == "y":
        print("Removing files from SD card...")
        for item in src.glob("**/*"):
            if item.is_file():
                item.unlink()
        print("Files deleted.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automate photo import workflow")
    parser.add_argument("--ssd", type=Path, default=Path("/Volumes/SSD CLIENT 2025"),
                        help="Root folder of the SSD")
    parser.add_argument("--api-key", type=str, default="", help="WeTransfer API key")
    args = parser.parse_args()

    sd_card = choose_sd_card(detect_sd_cards())
    print(f"Using SD card: {sd_card}")

    event, location, date_str, mode = prompt_metadata()

    dest_root = build_dest_folder(args.ssd, date_str, event, location)
    (dest_root / "Photos").mkdir(parents=True, exist_ok=True)
    (dest_root / "Video").mkdir(parents=True, exist_ok=True)

    print("Copying media files...")
    copy_media(sd_card, dest_root, mode)

    try:
        import_to_lightroom(dest_root)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to open Lightroom: {exc}")

    zip_path = create_zip(dest_root)
    if args.api_key:
        upload_to_wetransfer(zip_path, args.api_key)
    else:
        print("Skipping upload (no API key provided)")

    confirm_delete(sd_card)
    print("Done.")


if __name__ == "__main__":
    main()

