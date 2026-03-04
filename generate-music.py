#!/usr/bin/env python3
"""Generate instrumental music locally using MusicGen on Apple Silicon.

Usage:
    python generate-music.py "epic cinematic orchestral trailer"
    python generate-music.py "lo-fi chill hip hop beat, jazzy piano" --duration 30
    python generate-music.py "dark minimal techno, pulsing bass" --model medium
"""

import argparse
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

OUTPUT_DIR = os.path.expanduser("~/Desktop/AI-Music")


def main():
    parser = argparse.ArgumentParser(description="Generate music with MusicGen")
    parser.add_argument("prompt", help="Text description of the music to generate")
    parser.add_argument("--duration", type=int, default=15, help="Duration in seconds (default: 15, max: 30)")
    parser.add_argument("--model", choices=["small", "medium", "large"], default="small",
                        help="Model size (default: small, best quality: large)")
    parser.add_argument("--output", help="Output filename (default: auto-generated)")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Loading MusicGen-{args.model}...")
    start = time.time()

    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    import scipy.io.wavfile

    # CPU is more stable on 16GB Apple Silicon — MPS can OOM with audio models
    device = "cpu"
    if args.model == "small" and torch.backends.mps.is_available():
        # Small model fits on MPS, but CPU is safer
        pass
    print(f"Device: {device}")

    model_id = f"facebook/musicgen-{args.model}"
    processor = AutoProcessor.from_pretrained(model_id)
    model = MusicgenForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=torch.float32
    )
    model = model.to(device)

    load_time = time.time() - start
    print(f"Model loaded in {load_time:.1f}s")
    print(f'Generating: "{args.prompt}" ({args.duration}s)')

    # Calculate max_new_tokens from duration (MusicGen generates at 50 tokens/sec)
    tokens_per_second = 50
    max_tokens = min(args.duration, 30) * tokens_per_second

    inputs = processor(text=[args.prompt], padding=True, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    gen_start = time.time()
    with torch.no_grad():
        audio_values = model.generate(**inputs, max_new_tokens=max_tokens)
    gen_time = time.time() - gen_start

    # Save
    if args.output:
        filename = args.output
    else:
        safe_prompt = args.prompt[:40].replace(" ", "-").replace("/", "-").lower()
        safe_prompt = "".join(c for c in safe_prompt if c.isalnum() or c == "-")
        filename = f"musicgen-{safe_prompt}-{args.duration}s.wav"

    output_path = os.path.join(OUTPUT_DIR, filename)
    sample_rate = model.config.audio_encoder.sampling_rate
    audio_data = audio_values[0, 0].cpu().numpy()
    scipy.io.wavfile.write(output_path, rate=sample_rate, data=audio_data)

    print(f"\nGenerated in {gen_time:.1f}s ({gen_time/args.duration:.1f}x real-time)")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
