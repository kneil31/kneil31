import argparse
import os
import shutil
import subprocess
from pathlib import Path


def copy_photos(src_dir: Path, dest_dir: Path) -> None:
    """Recursively copy photos from src_dir to dest_dir."""
    for root, _, files in os.walk(src_dir):
        for fname in files:
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".raw")):
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
    parser = argparse.ArgumentParser(description="Import photos, zip them, and upload to WeTransfer.")
    parser.add_argument("src", type=Path, help="Source directory with photos")
    parser.add_argument("dest", type=Path, help="Destination directory on SSD")
    parser.add_argument("--api-key", type=str, help="WeTransfer API key", default="")
    args = parser.parse_args()

    copy_photos(args.src, args.dest)
    import_to_lightroom(args.dest)
    zip_path = create_zip(args.dest, args.dest.name)
    if args.api_key:
        upload_to_wetransfer(zip_path, args.api_key)
    else:
        print("Skipping WeTransfer upload (no API key provided).")


if __name__ == "__main__":
    main()
