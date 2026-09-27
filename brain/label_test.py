"""README step 1, the most important test: does Claude label dog frames the way we do?

  python label_test.py frames/                    classify every image in the folder
  python label_test.py clip.mp4                   save 1 frame every 30 s into clip_frames/, classify those
  python label_test.py frames/ --labels mine.csv  compare with our hand labels
  python label_test.py frames/ --dry-run          fake Claude, to check the script itself

Hand labels: a CSV with a header row "file,label", e.g.
  file,label
  frame_00030s.jpg,anxious
If the folder already has a labels.csv it is used automatically.
Labels: calm, anxious, lonely, sleeping, playing, not_visible.
Goal from the README: Claude agrees with us on 70% or more.
"""
import argparse
import csv
import sys
from pathlib import Path

import anthropic
import cv2

from classify import classify, fake_classify
from sense import to_jpeg

IMAGE_FILES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def video_to_frames(video, every_s):
    """Save one frame every every_s seconds into a folder next to the video."""
    folder = video.with_name(video.stem + "_frames")
    folder.mkdir(exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        sys.exit(f"Could not open video {video}")
    t = 0
    while True:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, image = cap.read()
        if not ok:
            break
        cv2.imwrite(str(folder / f"frame_{t:05d}s.jpg"), image)
        t += every_s
    cap.release()
    print(f"Saved {len(list(folder.glob('frame_*.jpg')))} frames to {folder}/ (label them there)")
    return folder


def read_labels(path):
    with open(path, newline="") as f:
        return {r["file"].strip(): r["label"].strip().lower().replace(" ", "_") for r in csv.DictReader(f)}


def main():
    parser = argparse.ArgumentParser(description="Compare Claude's labels with ours")
    parser.add_argument("path", type=Path, help="a folder of images, or a video file")
    parser.add_argument("--labels", type=Path, help="CSV with columns file,label")
    parser.add_argument("--every", type=int, default=30, help="seconds between video frames (default 30)")
    parser.add_argument("--dry-run", action="store_true", help="use a fake Claude")
    args = parser.parse_args()

    folder = args.path if args.path.is_dir() else video_to_frames(args.path, args.every)
    labels_path = args.labels or folder / "labels.csv"
    labels = read_labels(labels_path) if labels_path.exists() else {}
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_FILES)
    if not files:
        sys.exit(f"No images found in {folder}")

    checked = agreed = 0
    for file in files:
        image = cv2.imread(str(file))
        if image is None:
            print(f"{file.name}: could not read, skipped")
            continue
        try:
            result = (fake_classify if args.dry_run else classify)([to_jpeg(image)])
        except anthropic.AuthenticationError:
            sys.exit("Claude rejected the API key (401). Export a valid ANTHROPIC_API_KEY and retry.")
        ours = labels.get(file.name)
        verdict = ""
        if ours:
            checked += 1
            agreed += result["state"] == ours
            verdict = "OK  " if result["state"] == ours else "MISS"
        print(f"{verdict:4} {file.name:22} claude={result['state']:11} {result['confidence']:4.0%} "
              f"ours={ours or '-':11} {result['why']}")

    if checked:
        pct = 100 * agreed / checked
        print(f"\nAgreement: {agreed}/{checked} = {pct:.0f}%  "
              f"({'passes' if pct >= 70 else 'below'} the 70% goal)")
    else:
        print(f"\nNo hand labels found ({labels_path}). Add them to get an agreement score.")


if __name__ == "__main__":
    main()
