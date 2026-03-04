"""Importable wrapper for MusicGen generation."""

import os
import time
import warnings

from .config import OUTPUT_DIR

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"


def generate_music(prompt: str, duration: int = 15, model: str = "small", output: str | None = None) -> str:
    """Generate instrumental music with MusicGen. Returns output file path."""
    import torch
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    import scipy.io.wavfile

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    device = "cpu"
    print(f"Loading MusicGen-{model} on {device}...")
    start = time.time()

    model_id = f"facebook/musicgen-{model}"
    processor = AutoProcessor.from_pretrained(model_id)
    gen_model = MusicgenForConditionalGeneration.from_pretrained(
        model_id, torch_dtype=torch.float32
    )
    gen_model = gen_model.to(device)

    load_time = time.time() - start
    print(f"Model loaded in {load_time:.1f}s")
    print(f'Generating: "{prompt}" ({duration}s)')

    tokens_per_second = 50
    max_tokens = min(duration, 30) * tokens_per_second

    inputs = processor(text=[prompt], padding=True, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    gen_start = time.time()
    with torch.no_grad():
        audio_values = gen_model.generate(**inputs, max_new_tokens=max_tokens)
    gen_time = time.time() - gen_start

    if output:
        filename = output
    else:
        safe_prompt = prompt[:40].replace(" ", "-").replace("/", "-").lower()
        safe_prompt = "".join(c for c in safe_prompt if c.isalnum() or c == "-")
        filename = f"musicgen-{safe_prompt}-{duration}s.wav"

    output_path = os.path.join(OUTPUT_DIR, filename)
    sample_rate = gen_model.config.audio_encoder.sampling_rate
    audio_data = audio_values[0, 0].cpu().numpy()
    scipy.io.wavfile.write(output_path, rate=sample_rate, data=audio_data)

    print(f"Generated in {gen_time:.1f}s ({gen_time/duration:.1f}x real-time)")
    print(f"Saved: {output_path}")

    # Free memory
    del gen_model, processor, audio_values
    import gc
    gc.collect()

    return output_path
