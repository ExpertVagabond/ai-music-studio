"""Importable wrapper for RVC voice conversion."""

import os
import sys

from .config import RVC_DIR, CONVERTED_DIR


def convert_voice(
    input_file: str,
    model: str,
    pitch: int = 0,
    index: str | None = None,
    output: str | None = None,
) -> str:
    """Convert vocals using RVC. Returns output file path."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    os.makedirs(CONVERTED_DIR, exist_ok=True)

    output_path = output or os.path.join(
        CONVERTED_DIR,
        f"converted-{os.path.basename(input_file)}",
    )

    print(f"Input: {input_file}")
    print(f"Model: {model}")
    print(f"Pitch: {pitch:+d} semitones")
    print(f"Output: {output_path}")

    try:
        sys.path.insert(0, RVC_DIR)
        saved_cwd = os.getcwd()
        os.chdir(RVC_DIR)

        from rvc.infer import infer_audio

        infer_audio(
            input_path=input_file,
            model_path=model,
            index_path=index,
            pitch=pitch,
            output_path=output_path,
        )
        os.chdir(saved_cwd)
        print(f"\nConverted: {output_path}")

    except ImportError:
        os.chdir(saved_cwd if "saved_cwd" in dir() else os.path.dirname(__file__))
        print("RVC infer module not available. Falling back to CLI...")
        import subprocess

        cmd = [
            os.path.join(RVC_DIR, ".venv", "bin", "python"),
            os.path.join(RVC_DIR, "tools", "cmd", "infer_cli.py"),
            "--model_name", model,
            "--input_path", input_file,
            "--opt_path", output_path,
            "--f0up_key", str(pitch),
        ]
        if index:
            cmd.extend(["--index_path", index])
        subprocess.run(cmd)

    return output_path
