"""Importable wrapper for Demucs stem separation."""

import os
import subprocess
import sys

from .config import STEMS_DIR


def separate_stems(
    input_file: str,
    model: str = "htdemucs",
    two_stems: str | None = None,
    output_dir: str | None = None,
) -> str:
    """Separate audio into stems. Returns path to stems directory."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")

    out = output_dir or STEMS_DIR
    os.makedirs(out, exist_ok=True)

    cmd = [sys.executable, "-m", "demucs", "-n", model, "-o", out, input_file]
    if two_stems:
        cmd.extend(["--two-stems", two_stems])

    print(f"Separating: {os.path.basename(input_file)}")
    print(f"Model: {model}")
    print(f"Output: {out}")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError("Stem separation failed")

    basename = os.path.splitext(os.path.basename(input_file))[0]
    stem_dir = os.path.join(out, model, basename)

    if os.path.exists(stem_dir):
        print(f"\nStems saved to: {stem_dir}")
        for f in sorted(os.listdir(stem_dir)):
            filepath = os.path.join(stem_dir, f)
            size_mb = os.path.getsize(filepath) / 1024 / 1024
            print(f"  {f} ({size_mb:.1f} MB)")

    return stem_dir
