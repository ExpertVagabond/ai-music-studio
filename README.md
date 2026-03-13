# AI Music Studio

**Local AI music production from the command line. Generate instrumentals, separate stems, convert voices, mix tracks, and run batch pipelines — all on Apple Silicon, no cloud APIs required.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-Optimized-000000?logo=apple&logoColor=white)](https://support.apple.com/en-us/116943)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MusicGen](https://img.shields.io/badge/Meta-MusicGen-0467DF?logo=meta&logoColor=white)](https://github.com/facebookresearch/audiocraft)

## Commands

| Command | Engine | What It Does |
|---------|--------|--------------|
| `studio generate` | MusicGen | Text-to-music generation (small/medium/large) |
| `studio stems` | Demucs | Separate audio into vocals, drums, bass, other |
| `studio voice` | RVC | Voice conversion with trained .pth models |
| `studio mix` | ffmpeg | Mix tracks with per-channel volume, fades, LUFS normalization |
| `studio batch` | All | Multi-track pipelines from YAML recipe files |
| `studio info` | ffprobe | Audio metadata (duration, sample rate, codec, bitrate) |
| `studio list` | — | Browse generated files by category |

## Quick Start

```bash
git clone https://github.com/ExpertVagabond/ai-music-studio.git
cd ai-music-studio
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
brew install ffmpeg
```

## Usage

```bash
# Generate instrumental from text prompt
python studio.py generate "dark trap beat with heavy 808s" --duration 30

# Separate stems
python studio.py stems song.mp3

# Voice conversion
python studio.py voice vocals.wav --model matthew.pth --pitch 0

# Mix tracks with volume control
python studio.py mix drums.wav bass.wav other.wav --volumes "0,-3,-6"

# Batch pipeline from YAML
python studio.py batch examples/basic-recipe.yaml
```

## Batch Pipelines

Define multi-step workflows in YAML:

```yaml
output_dir: ~/Desktop/AI-Music/batch
jobs:
  - name: dark-trap
    prompt: "dark minimal trap beat, heavy 808s"
    duration: 30
    stems: true
    mix:
      layers:
        - stem: drums
          volume: 0dB
        - stem: bass
          volume: -2dB
```

## Mixing Engine

- Per-track volume adjustment in dB
- Fade in/out with smooth transitions
- LUFS normalization targeting -14 LUFS (streaming standard)
- Any format: WAV, MP3, FLAC, M4A, OGG

## Architecture

```
studio.py                  Typer CLI with lazy imports
lib/
  generate.py              MusicGen text-to-music wrapper
  stems.py                 Demucs stem separation
  voice.py                 RVC voice conversion
  mix.py                   ffmpeg filter_complex mixing engine
  batch.py                 YAML recipe pipeline
  audio_utils.py           ffprobe/ffmpeg utilities
  config.py                Shared paths and constants
examples/
  basic-recipe.yaml        Example batch recipe
```

## Requirements

- Python 3.11+ with PyTorch, Transformers, Demucs
- ffmpeg for mixing, normalization, format conversion
- Apple Silicon Mac recommended (~10x real-time for MusicGen-small)
- RVC optional (requires separate installation)

## License

[MIT](LICENSE)

## Author

Built by [Purple Squirrel Media](https://purplesquirrelmedia.io)
