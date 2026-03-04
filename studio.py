#!/usr/bin/env python3
"""AI Music Studio — unified CLI for local music production.

Generate, separate, convert, mix, and batch process music from the terminal.
"""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from lib.config import OUTPUT_DIR, STEMS_DIR, CONVERTED_DIR, MIXED_DIR, SUPPORTED_FORMATS

app = typer.Typer(
    name="studio",
    help="AI Music Studio — generate, separate, convert, mix, and batch process music.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Text description of the music to generate"),
    duration: int = typer.Option(15, "--duration", "-d", help="Duration in seconds (max 30)"),
    model: str = typer.Option("small", "--model", "-m", help="MusicGen model: small, medium, large"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename"),
):
    """Generate instrumental music from a text prompt using MusicGen."""
    from lib.generate import generate_music

    generate_music(prompt, duration, model, output)


@app.command()
def stems(
    input_file: str = typer.Argument(..., help="Input audio file (WAV, MP3, FLAC, etc.)"),
    model: str = typer.Option("htdemucs", "--model", "-m", help="htdemucs, htdemucs_ft, htdemucs_6s, mdx_extra"),
    two_stems: Optional[str] = typer.Option(None, "--two-stems", help="Isolate one stem: vocals, drums, bass, other"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Separate audio into stems (vocals, drums, bass, other) with Demucs."""
    from lib.stems import separate_stems

    separate_stems(input_file, model, two_stems, output)


@app.command()
def voice(
    input_file: str = typer.Argument(..., help="Input audio with vocals"),
    model: str = typer.Option(..., "--model", "-m", help="RVC model file (.pth)"),
    pitch: int = typer.Option(0, "--pitch", "-p", help="Pitch shift in semitones"),
    index: Optional[str] = typer.Option(None, "--index", help="RVC index file (.index)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Convert vocals to a target voice using RVC."""
    from lib.voice import convert_voice

    convert_voice(input_file, model, pitch, index, output)


@app.command()
def mix(
    files: list[str] = typer.Argument(..., help="Audio files to mix (2 or more)"),
    volumes: Optional[str] = typer.Option(None, "--volumes", "-v", help="Comma-separated dB values, e.g. '0,-3,-6'"),
    fade_in: float = typer.Option(0.0, "--fade-in", help="Fade in seconds"),
    fade_out: float = typer.Option(0.0, "--fade-out", help="Fade out seconds"),
    no_normalize: bool = typer.Option(False, "--no-normalize", help="Skip LUFS normalization"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Mix multiple audio files with volume control, fades, and normalization."""
    from lib.mix import mix_tracks

    # Parse volumes
    if volumes:
        vol_list = [float(v.strip().replace("dB", "")) for v in volumes.split(",")]
    else:
        vol_list = [0.0] * len(files)

    if len(vol_list) < len(files):
        vol_list.extend([0.0] * (len(files) - len(vol_list)))

    layers = [
        {"file": f, "volume": vol_list[i]}
        for i, f in enumerate(files)
    ]

    mix_tracks(
        layers=layers,
        output=output,
        fade_in=fade_in,
        fade_out=fade_out,
        normalize=not no_normalize,
    )


@app.command()
def batch(
    recipe: str = typer.Argument(..., help="YAML recipe file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without executing"),
):
    """Run a batch pipeline from a YAML recipe file."""
    from lib.batch import load_recipe, run_recipe

    r = load_recipe(recipe)
    results = run_recipe(r, dry_run=dry_run)

    table = Table(title="Batch Results")
    table.add_column("Track", style="cyan")
    table.add_column("Outputs", style="green")
    for r in results:
        outputs = ", ".join(r["outputs"].keys()) if r["outputs"] else "(dry run)"
        table.add_row(r["name"], outputs)
    console.print(table)


@app.command()
def info(
    file: str = typer.Argument(..., help="Audio file to inspect"),
):
    """Show audio file metadata (duration, sample rate, codec, size)."""
    from lib.audio_utils import get_audio_info

    if not os.path.exists(file):
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    data = get_audio_info(file)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    table = Table(title=os.path.basename(file))
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Duration", f"{float(fmt.get('duration', 0)):.2f}s")
    table.add_row("Format", fmt.get("format_long_name", "unknown"))
    table.add_row("Size", f"{int(fmt.get('size', 0)) / 1024 / 1024:.1f} MB")
    table.add_row("Bitrate", f"{int(fmt.get('bit_rate', 0)) / 1000:.0f} kbps")
    table.add_row("Sample Rate", f"{audio_stream.get('sample_rate', '?')} Hz")
    table.add_row("Channels", str(audio_stream.get('channels', '?')))
    table.add_row("Codec", audio_stream.get("codec_long_name", "unknown"))

    console.print(table)


@app.command(name="list")
def list_files(
    category: str = typer.Argument("all", help="Category: generated, stems, converted, mixed, all"),
):
    """List audio files in the output directory."""
    categories = {
        "generated": OUTPUT_DIR,
        "stems": STEMS_DIR,
        "converted": CONVERTED_DIR,
        "mixed": MIXED_DIR,
    }

    if category == "all":
        dirs = categories
    elif category in categories:
        dirs = {category: categories[category]}
    else:
        console.print(f"[red]Unknown category: {category}[/red]")
        console.print(f"Choose from: {', '.join(['all'] + list(categories.keys()))}")
        raise typer.Exit(1)

    for cat_name, dir_path in dirs.items():
        if not os.path.exists(dir_path):
            continue

        files = []
        for entry in os.scandir(dir_path):
            if entry.is_file() and Path(entry.name).suffix.lower() in SUPPORTED_FORMATS:
                size_mb = entry.stat().st_size / 1024 / 1024
                files.append((entry.name, size_mb))

        if not files:
            continue

        table = Table(title=f"{cat_name.upper()} ({dir_path})")
        table.add_column("File", style="cyan")
        table.add_column("Size", style="green", justify="right")
        for name, size in sorted(files):
            table.add_row(name, f"{size:.1f} MB")
        console.print(table)
        console.print()


if __name__ == "__main__":
    app()
