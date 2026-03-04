# AI Music Studio

Local AI music production from the command line. Generate instrumentals, separate stems, convert voices, mix tracks, and run batch pipelines — all on Apple Silicon, no cloud APIs required.

## What It Does

| Command | Engine | Description |
|---|---|---|
| `studio generate` | [MusicGen](https://github.com/facebookresearch/audiocraft) | Text-to-instrumental generation (small/medium/large models) |
| `studio stems` | [Demucs](https://github.com/facebookresearch/demucs) | Separate audio into vocals, drums, bass, other |
| `studio voice` | [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) | Voice conversion with trained .pth models |
| `studio mix` | ffmpeg | Mix multiple tracks with per-channel volume, fades, LUFS normalization |
| `studio batch` | All of the above | Run multi-track pipelines from YAML recipe files |
| `studio info` | ffprobe | Display audio metadata (duration, sample rate, codec, bitrate) |
| `studio list` | — | Browse generated files by category |

## Quick Start

```bash
# Clone
git clone https://github.com/ExpertVagabond/ai-music-studio.git
cd ai-music-studio

# Set up Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Generate a beat
python studio.py generate "dark trap beat with heavy 808s" --duration 30

# Separate into stems
python studio.py stems ~/Desktop/AI-Music/musicgen-dark-trap-beat-30s.wav

# Mix stems with custom levels
python studio.py mix drums.wav bass.wav other.wav --volumes "0,-3,-6" --fade-in 2 --fade-out 3

# Inspect any audio file
python studio.py info track.wav

# Run a batch pipeline
python studio.py batch examples/basic-recipe.yaml
```

## Batch Recipes

Define multi-track pipelines in YAML:

```yaml
output_dir: ~/Desktop/AI-Music/batch

jobs:
  - name: dark-trap
    prompt: "dark minimal trap beat, heavy 808s, distorted bass"
    duration: 30
    model: small
    stems: true

  - name: cinematic
    prompt: "epic orchestral trailer, brass and strings"
    duration: 15
    stems: true
    mix:
      layers:
        - stem: drums
          volume: 0dB
        - stem: bass
          volume: -2dB
        - stem: other
          volume: -4dB
      fade_in: 2
      fade_out: 3
      normalize: true
```

Run with `studio batch recipe.yaml` or preview with `--dry-run`.

## Mixing Engine

The `mix` command uses ffmpeg's `filter_complex` for low-memory, hardware-accelerated mixing:

- **Per-track volume** — adjust each input in dB (`--volumes "0,-3,-6,+2"`)
- **Fade in/out** — smooth transitions (`--fade-in 2 --fade-out 3`)
- **LUFS normalization** — two-pass loudnorm to -14 LUFS (streaming standard)
- **Any format** — WAV, MP3, FLAC, M4A, OGG input/output

## Requirements

- **Python 3.11+** with PyTorch, Transformers, Demucs
- **ffmpeg** (for mixing, normalization, format conversion, metadata)
- **Apple Silicon Mac** recommended (CPU inference, ~10x real-time for MusicGen-small)
- **RVC** (optional, for voice conversion — requires separate [RVC WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) installation)

## Architecture

```
studio.py              → Typer CLI (lazy imports per command)
lib/
  config.py            → Shared paths and constants
  audio_utils.py       → ffprobe/ffmpeg wrappers
  generate.py          → MusicGen wrapper
  stems.py             → Demucs wrapper
  voice.py             → RVC wrapper
  mix.py               → ffmpeg mixing engine
  batch.py             → YAML pipeline processor
```

Standalone scripts (`generate-music.py`, `separate-stems.py`, `voice-convert.py`) are preserved for direct use.

## Output

All files go to `~/Desktop/AI-Music/` organized by type:

```
~/Desktop/AI-Music/
  ├── *.wav, *.mp3        (generated tracks)
  ├── stems/              (Demucs separations)
  ├── converted/          (RVC voice conversions)
  ├── mixed/              (mix outputs)
  └── batch/              (batch pipeline outputs)
```

## License

MIT
