#!/usr/bin/env python3
"""Separate audio into stems (vocals, drums, bass, other) using Demucs.

Usage:
    python separate-stems.py song.mp3
    python separate-stems.py song.wav --model htdemucs_ft
    python separate-stems.py song.mp3 --output ~/Desktop/stems/
"""

import argparse
import os
import sys
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Separate audio into stems with Demucs")
    parser.add_argument("input", help="Input audio file (MP3, WAV, FLAC, etc.)")
    parser.add_argument("--model", default="htdemucs",
                        choices=["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx_extra"],
                        help="Demucs model (default: htdemucs, best: htdemucs_ft)")
    parser.add_argument("--output", default=None, help="Output directory (default: ~/Desktop/AI-Music/stems/)")
    parser.add_argument("--two-stems", choices=["vocals", "drums", "bass", "other"],
                        help="Only separate into two stems (e.g., vocals + everything else)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    output_dir = args.output or os.path.expanduser("~/Desktop/AI-Music/stems")
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        sys.executable, "-m", "demucs",
        "-n", args.model,
        "-o", output_dir,
        args.input
    ]

    if args.two_stems:
        cmd.extend(["--two-stems", args.two_stems])

    print(f"Separating: {os.path.basename(args.input)}")
    print(f"Model: {args.model}")
    print(f"Output: {output_dir}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        # Find output files
        basename = os.path.splitext(os.path.basename(args.input))[0]
        stem_dir = os.path.join(output_dir, args.model, basename)
        if os.path.exists(stem_dir):
            print(f"\nStems saved to: {stem_dir}")
            for f in sorted(os.listdir(stem_dir)):
                filepath = os.path.join(stem_dir, f)
                size_mb = os.path.getsize(filepath) / 1024 / 1024
                print(f"  {f} ({size_mb:.1f} MB)")
    else:
        print("\nSeparation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
