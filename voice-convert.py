#!/usr/bin/env python3
"""Convert vocals to a target voice using RVC.

Usage:
    python voice-convert.py input_vocals.wav --model matthew.pth
    python voice-convert.py input.wav --model matthew.pth --pitch 0
    python voice-convert.py input.wav --model matthew.pth --output converted.wav

Prerequisites:
    - RVC model trained (run train-voice.py first)
    - Model file (.pth) in models/ directory
"""

import argparse
import os
import sys

RVC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai-music-rvc")
OUTPUT_DIR = os.path.expanduser("~/Desktop/AI-Music/converted")


def main():
    parser = argparse.ArgumentParser(description="Convert voice using RVC")
    parser.add_argument("input", help="Input audio file with vocals")
    parser.add_argument("--model", required=True, help="RVC model file (.pth)")
    parser.add_argument("--index", default=None, help="RVC index file (.index)")
    parser.add_argument("--pitch", type=int, default=0, help="Pitch shift in semitones (default: 0)")
    parser.add_argument("--output", default=None, help="Output file path")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Add RVC to path
    sys.path.insert(0, RVC_DIR)
    os.chdir(RVC_DIR)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = args.output or os.path.join(
        OUTPUT_DIR,
        f"converted-{os.path.basename(args.input)}"
    )

    print(f"Input: {args.input}")
    print(f"Model: {args.model}")
    print(f"Pitch: {args.pitch:+d} semitones")
    print(f"Output: {output_path}")
    print()

    try:
        from rvc.infer import infer_audio

        result = infer_audio(
            input_path=args.input,
            model_path=args.model,
            index_path=args.index,
            pitch=args.pitch,
            output_path=output_path,
        )
        print(f"\nConverted: {output_path}")

    except ImportError:
        print("RVC infer module not available. Falling back to CLI...")
        import subprocess
        cmd = [
            os.path.join(RVC_DIR, ".venv", "bin", "python"),
            os.path.join(RVC_DIR, "tools", "infer_cli.py"),
            "--model", args.model,
            "--input", args.input,
            "--output", output_path,
            "--pitch", str(args.pitch),
        ]
        if args.index:
            cmd.extend(["--index", args.index])
        subprocess.run(cmd)

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure RVC is set up correctly:")
        print(f"  cd {RVC_DIR}")
        print("  source .venv/bin/activate")
        print("  python web.py  (launches the WebUI)")
        sys.exit(1)


if __name__ == "__main__":
    main()
