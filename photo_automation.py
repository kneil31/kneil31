import argparse
import os
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

PHOTO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".raw", ".heic")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

SSD_ROOT = Path("/Volumes/SSD CLIENT 2025")


def find_sd_cards(volumes_root: Path = Path("/Volumes")) -> list[Path]:
    """Return a list of mounted volumes that contain a DCIM folder."""
    cards = []
    for entry in volumes_root.iterdir():
        if (entry / "DCIM").is_dir():
            cards.append(entry)
    return cards


def copy_files(src_dir: Path, dest_dir: Path, extensions: tuple[str, ...]) -> None:
    """Recursively copy files matching extensions from src_dir to dest_dir."""
    for root, _, files in os.walk(src_dir):
        for fname in files:
            if fname.lower().endswith(extensions):
                src_path = Path(root) / fname
                relative = src_path.relative_to(src_dir)
                dest_path = dest_dir / relative
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)


def import_to_lightroom(folder: Path) -> None:
    """Open Lightroom to import photos from the given folder."""
    # Adjust this command for your Lightroom installation
    lightroom_cmd = ["open", "-a", "Adobe Lightroom Classic", str(folder)]
    try:
        subprocess.run(lightroom_cmd, check=True)
    except FileNotFoundError:
        print("Lightroom command not found. Please adjust lightroom_cmd in the script.")


def create_zip(folder: Path, zip_name: Path) -> Path:
    """Create a zip archive of the folder and return the path."""
    archive_path = shutil.make_archive(str(zip_name.with_suffix("")), "zip", root_dir=folder)
    return Path(archive_path)


def upload_to_wetransfer(zip_path: Path, api_key: str) -> None:
    """Upload the zip file to WeTransfer using their API."""
    # Placeholder implementation - requires WeTransfer API token
    # For a real implementation, use the official WeTransfer Python SDK or API
    print(f"Uploading {zip_path} to WeTransfer (not implemented).")
    # Example using requests (commented out):
    # import requests
    # with zip_path.open("rb") as f:
    #     response = requests.post(
    #         "https://dev.wetransfer.com/v2/transfers",
    #         headers={"Authorization": f"Bearer {api_key}"},
    #         files={"file": f},
    #     )
    # print(response.json())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect an SD card, copy media, zip the folder, and optionally upload to WeTransfer."
    )
    parser.add_argument("--api-key", type=str, default="", help="WeTransfer API key")
    args = parser.parse_args()

    cards = find_sd_cards()
    if not cards:
        print("No SD card found under /Volumes.")
        return
    card = cards[0]
    if len(cards) > 1:
        print("Select a memory card to import from:")
        for idx, c in enumerate(cards, start=1):
            print(f"{idx}: {c}")
        choice = input("Card [1]: ").strip() or "1"
        card = cards[int(choice) - 1]

    name = input("Event name: ").strip().replace(" ", "_")
    location = input("Location: ").strip().replace(" ", "_")
    today = date.today().strftime("%Y-%m-%d")
    date_str = input(f"Date [YYYY-MM-DD] (default {today}): ").strip() or today
    media_choice = input("Media to copy (photos/videos/both) [photos]: ").strip().lower() or "photos"

    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    dest_base = SSD_ROOT / str(date_obj.year) / f"{date_str}_{name}_{location}"
    photos_dest = dest_base / "Photos"
    videos_dest = dest_base / "Video"

    if media_choice in {"photos", "both"}:
        print(f"Copying photos from {card} to {photos_dest}")
        copy_files(card, photos_dest, PHOTO_EXTENSIONS)
    if media_choice in {"videos", "both"}:
        print(f"Copying videos from {card} to {videos_dest}")
        copy_files(card, videos_dest, VIDEO_EXTENSIONS)

    import_to_lightroom(dest_base)
    zip_path = create_zip(dest_base, dest_base)

    if args.api_key:
        upload_to_wetransfer(zip_path, args.api_key)
    else:
        print("Skipping WeTransfer upload (no API key provided).")

    delete_choice = input("Delete files from the memory card? [y/N]: ").strip().lower()
    if delete_choice == "y":
        shutil.rmtree(card)
        print("Memory card files deleted.")


if __name__ == "__main__":
    main()
