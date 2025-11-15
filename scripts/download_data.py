import json
import shutil
import subprocess
from pathlib import Path

from datasets import load_dataset


DATA_DIR = Path("data")
MISED_REPO = "https://github.com/google-research-datasets/MISeD.git"
PUBLIC_MEETINGS_REPO = "https://github.com/pltrdy/public_meetings.git"


def clone_repo(url: str, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    subprocess.run(["git", "clone", url, str(target)], check=True)
    print(f"Cloned {url} -> {target}")


def download_mised() -> None:
    clone_repo(MISED_REPO, DATA_DIR / "mised")


def download_public_meetings() -> None:
    clone_repo(PUBLIC_MEETINGS_REPO, DATA_DIR / "public_meetings")


def download_meetingbank() -> None:
    target_dir = DATA_DIR / "meetingbank"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    dataset = load_dataset("lytang/MeetingBank-transcript")
    for split, split_ds in dataset.items():
        split_path = target_dir / f"{split}.jsonl"
        with split_path.open("w", encoding="utf-8") as fp:
            for record in split_ds:
                fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"Saved MeetingBank split '{split}' with {len(split_ds)} rows -> {split_path}")


def create_sample_images() -> None:
    from PIL import Image, ImageDraw

    images_dir = DATA_DIR / "sample_images"
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True)

    specs = [
        ("project_update.png", "Q4 Launch\nRoadmap"),
        ("retro_notes.png", "Retrospective\nNext Steps"),
    ]

    for filename, text in specs:
        img = Image.new("RGB", (1200, 675), color="#1f2933")
        draw = ImageDraw.Draw(img)
        draw.text((80, 120), text, fill="#f8fafc")
        path = images_dir / filename
        img.save(path)
        print(f"Created sample image -> {path}")


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    download_mised()
    download_public_meetings()
    download_meetingbank()
    create_sample_images()


if __name__ == "__main__":
    main()
