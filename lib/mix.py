"""Audio mixing engine using ffmpeg filter_complex."""

import os
import subprocess
import tempfile

from .config import MIXED_DIR, OUTPUT_DIR
from .audio_utils import normalize_audio, get_duration


def mix_tracks(
    layers: list[dict],
    output: str | None = None,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    normalize: bool = True,
    target_lufs: float = -14.0,
) -> str:
    """
    Mix multiple audio layers into a single output file.

    Each layer dict:
        file: path to audio file
        volume: volume in dB (e.g., 0, -3, +2). Default 0.
        delay: start delay in seconds. Default 0.

    Returns path to mixed output file.
    """
    if len(layers) < 2:
        raise ValueError("Need at least 2 audio files to mix")

    os.makedirs(MIXED_DIR, exist_ok=True)

    output_path = output or os.path.join(MIXED_DIR, "mix-output.wav")

    # Build ffmpeg command
    inputs = []
    filter_parts = []

    for i, layer in enumerate(layers):
        inputs.extend(["-i", layer["file"]])
        vol = layer.get("volume", 0)
        delay = layer.get("delay", 0)

        filters = []
        if vol != 0:
            filters.append(f"volume={vol}dB")
        if delay > 0:
            filters.append(f"adelay={int(delay * 1000)}|{int(delay * 1000)}")

        if filters:
            filter_parts.append(f"[{i}:a]{','.join(filters)}[a{i}]")
        else:
            filter_parts.append(f"[{i}:a]anull[a{i}]")

    # Combine all streams
    mix_inputs = "".join(f"[a{i}]" for i in range(len(layers)))
    filter_parts.append(f"{mix_inputs}amix=inputs={len(layers)}:duration=longest:normalize=0[mixed]")

    # Apply fades
    last_label = "mixed"
    if fade_in > 0 or fade_out > 0:
        fade_filters = []
        if fade_in > 0:
            fade_filters.append(f"afade=t=in:d={fade_in}")
        if fade_out > 0:
            # Get duration from longest input for fade-out start
            max_dur = max(get_duration(l["file"]) for l in layers)
            start = max(0, max_dur - fade_out)
            fade_filters.append(f"afade=t=out:st={start:.2f}:d={fade_out}")
        filter_parts.append(f"[mixed]{','.join(fade_filters)}[faded]")
        last_label = "faded"

    filter_graph = ";".join(filter_parts)

    # If normalizing, mix to temp file first
    if normalize:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_graph,
            "-map", f"[{last_label}]",
            tmp_path,
        ]

        print(f"Mixing {len(layers)} tracks...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            os.unlink(tmp_path)
            raise RuntimeError(f"Mix failed: {result.stderr}")

        print(f"Normalizing to {target_lufs} LUFS...")
        normalize_audio(tmp_path, output_path, target_lufs)
        os.unlink(tmp_path)
    else:
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_graph,
            "-map", f"[{last_label}]",
            output_path,
        ]

        print(f"Mixing {len(layers)} tracks...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Mix failed: {result.stderr}")

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"Mixed: {output_path} ({size_mb:.1f} MB)")
    return output_path


def overlay_vocal(
    instrumental: str,
    vocal: str,
    output: str | None = None,
    vocal_volume: float = 0.0,
    instrumental_volume: float = 0.0,
) -> str:
    """Quick helper to overlay a vocal track on an instrumental."""
    return mix_tracks(
        layers=[
            {"file": instrumental, "volume": instrumental_volume},
            {"file": vocal, "volume": vocal_volume},
        ],
        output=output,
    )
