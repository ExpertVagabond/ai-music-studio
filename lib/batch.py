"""Batch pipeline processor — run multiple music generation jobs from a YAML recipe."""

import os
import gc

import yaml

from .config import OUTPUT_DIR, BATCH_DIR


def load_recipe(recipe_path: str) -> dict:
    """Load and validate a YAML batch recipe."""
    with open(recipe_path) as f:
        recipe = yaml.safe_load(f)

    if not recipe or "jobs" not in recipe:
        raise ValueError("Recipe must have a 'jobs' list")

    for i, job in enumerate(recipe["jobs"]):
        if "prompt" not in job:
            raise ValueError(f"Job {i} missing 'prompt'")

    return recipe


def run_recipe(recipe: dict, dry_run: bool = False) -> list[dict]:
    """
    Execute a batch recipe. For each job:
    1. Generate instrumental (if prompt present)
    2. Separate stems (if stems: true)
    3. Voice convert (if voice config present)
    4. Mix (if mix config present)

    Returns list of result dicts with output paths.
    """
    output_dir = recipe.get("output_dir", BATCH_DIR)
    output_dir = os.path.expanduser(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    results = []

    for i, job in enumerate(recipe["jobs"]):
        name = job.get("name", f"track-{i+1}")
        print(f"\n{'='*60}")
        print(f"Job {i+1}/{len(recipe['jobs'])}: {name}")
        print(f"{'='*60}")

        result = {"name": name, "outputs": {}}

        if dry_run:
            print(f"  [DRY RUN] Would generate: \"{job['prompt']}\" ({job.get('duration', 15)}s)")
            if job.get("stems"):
                print("  [DRY RUN] Would separate stems")
            if job.get("voice"):
                print(f"  [DRY RUN] Would convert voice: {job['voice']}")
            if job.get("mix"):
                print("  [DRY RUN] Would mix tracks")
            results.append(result)
            continue

        # Step 1: Generate
        from .generate import generate_music

        gen_output = os.path.join(output_dir, f"{name}.wav")
        generated = generate_music(
            prompt=job["prompt"],
            duration=job.get("duration", 15),
            model=job.get("model", "small"),
            output=gen_output,
        )
        result["outputs"]["generated"] = generated

        # Free model memory between jobs
        gc.collect()

        # Step 2: Stems
        if job.get("stems"):
            from .stems import separate_stems

            stem_dir = separate_stems(
                input_file=generated,
                model=job.get("stems_model", "htdemucs"),
                output_dir=os.path.join(output_dir, "stems"),
            )
            result["outputs"]["stems"] = stem_dir

        # Step 3: Voice convert
        voice_cfg = job.get("voice")
        if voice_cfg and result["outputs"].get("stems"):
            from .voice import convert_voice

            model_name = voice_cfg if isinstance(voice_cfg, str) else voice_cfg.get("model", "matthew-voice.pth")
            pitch = voice_cfg.get("pitch", 0) if isinstance(voice_cfg, dict) else 0
            stem = voice_cfg.get("stem", "vocals") if isinstance(voice_cfg, dict) else "vocals"

            vocal_path = os.path.join(result["outputs"]["stems"], f"{stem}.wav")
            if os.path.exists(vocal_path):
                converted = convert_voice(
                    input_file=vocal_path,
                    model=model_name,
                    pitch=pitch,
                    output=os.path.join(output_dir, f"{name}-converted-{stem}.wav"),
                )
                result["outputs"]["converted"] = converted

        # Step 4: Mix
        mix_cfg = job.get("mix")
        if mix_cfg and result["outputs"].get("stems"):
            from .mix import mix_tracks

            layers_cfg = mix_cfg.get("layers", [])
            layers = []
            stem_dir = result["outputs"]["stems"]

            for lc in layers_cfg:
                if "stem" in lc:
                    filepath = os.path.join(stem_dir, f"{lc['stem']}.wav")
                elif "source" in lc and lc["source"] == "voice" and result["outputs"].get("converted"):
                    filepath = result["outputs"]["converted"]
                else:
                    continue

                if os.path.exists(filepath):
                    vol_str = lc.get("volume", "0dB").replace("dB", "")
                    layers.append({"file": filepath, "volume": float(vol_str)})

            if len(layers) >= 2:
                mixed = mix_tracks(
                    layers=layers,
                    output=os.path.join(output_dir, f"{name}-mixed.wav"),
                    fade_in=mix_cfg.get("fade_in", 0),
                    fade_out=mix_cfg.get("fade_out", 0),
                    normalize=mix_cfg.get("normalize", True),
                )
                result["outputs"]["mixed"] = mixed

        results.append(result)
        print(f"  Outputs: {list(result['outputs'].keys())}")

    print(f"\n{'='*60}")
    print(f"Batch complete: {len(results)} jobs processed")
    return results
