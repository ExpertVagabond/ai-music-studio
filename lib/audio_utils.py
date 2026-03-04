"""FFmpeg/FFprobe utility wrappers for audio info, normalization, and processing."""

import json
import subprocess
from pathlib import Path


def get_audio_info(file_path: str) -> dict:
    """Get audio metadata via ffprobe. Returns dict with format and stream info."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(file_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return json.loads(result.stdout)


def get_duration(file_path: str) -> float:
    """Get audio duration in seconds."""
    info = get_audio_info(file_path)
    return float(info["format"]["duration"])


def normalize_audio(input_path: str, output_path: str, target_lufs: float = -14.0) -> str:
    """Two-pass loudnorm normalization via ffmpeg."""
    # Pass 1: measure
    measure_cmd = [
        "ffmpeg", "-y", "-i", input_path, "-af",
        f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-",
    ]
    result = subprocess.run(measure_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Loudnorm measure failed: {result.stderr}")

    # Extract JSON from stderr (ffmpeg outputs loudnorm stats there)
    stderr = result.stderr
    json_start = stderr.rfind("{")
    json_end = stderr.rfind("}") + 1
    if json_start < 0:
        raise RuntimeError("Could not parse loudnorm measurement output")
    stats = json.loads(stderr[json_start:json_end])

    # Pass 2: apply with measured values
    apply_cmd = [
        "ffmpeg", "-y", "-i", input_path, "-af",
        (
            f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11"
            f":measured_I={stats['input_i']}"
            f":measured_LRA={stats['input_lra']}"
            f":measured_TP={stats['input_tp']}"
            f":measured_thresh={stats['input_thresh']}"
            f":offset={stats['target_offset']}"
            f":linear=true"
        ),
        output_path,
    ]
    result = subprocess.run(apply_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Loudnorm apply failed: {result.stderr}")
    return output_path


def apply_fade(input_path: str, output_path: str, fade_in: float = 0, fade_out: float = 0) -> str:
    """Apply fade in/out using ffmpeg afade filter."""
    filters = []
    if fade_in > 0:
        filters.append(f"afade=t=in:d={fade_in}")
    if fade_out > 0:
        duration = get_duration(input_path)
        start = max(0, duration - fade_out)
        filters.append(f"afade=t=out:st={start:.2f}:d={fade_out}")

    if not filters:
        # No fades, just copy
        subprocess.run(["cp", input_path, output_path])
        return output_path

    cmd = ["ffmpeg", "-y", "-i", input_path, "-af", ",".join(filters), output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Fade failed: {result.stderr}")
    return output_path


def convert_format(input_path: str, output_path: str, bitrate: str = "320k") -> str:
    """Convert audio to another format (determined by output extension)."""
    cmd = ["ffmpeg", "-y", "-i", input_path, "-b:a", bitrate, output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Convert failed: {result.stderr}")
    return output_path
