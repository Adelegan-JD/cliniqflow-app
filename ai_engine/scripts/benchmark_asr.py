"""Offline, repeatable benchmark for local Hugging Face Whisper checkpoints.

This tool never downloads models. Add a verified transcript later to calculate
WER/CER; until then it records speed and each model's transcript for blinded
clinical review. Benchmark outputs may contain patient speech and are ignored
by Git by design.
"""

from __future__ import annotations

import argparse
import gc
import json
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import soundfile as sf
import torch
import torch.nn.functional as functional
from transformers import WhisperForConditionalGeneration, WhisperProcessor


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_ROOT = PROJECT_ROOT / "models"
REQUIRED_FILES = {"config.json", "model.safetensors", "tokenizer.json"}


@dataclass
class Result:
    model: str
    model_path: str
    audio: str
    duration_seconds: float
    elapsed_seconds: float
    realtime_factor: float
    transcript: str
    word_error_rate: float | None
    character_error_rate: float | None
    error: str | None = None


def discover_models(root: Path) -> list[Path]:
    """Find complete local Transformers Whisper model folders, never caches."""
    if not root.exists():
        return []
    return sorted(
        path for path in root.iterdir()
        if path.is_dir() and REQUIRED_FILES.issubset({child.name for child in path.iterdir()})
    )


def normalize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[^\w\s']", " ", text, flags=re.UNICODE)
    return [item for item in text.split() if item]


def edit_distance(expected: list[str], actual: list[str]) -> int:
    previous = list(range(len(actual) + 1))
    for i, left in enumerate(expected, start=1):
        current = [i]
        for j, right in enumerate(actual, start=1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


def error_rate(expected: Iterable[str], actual: Iterable[str]) -> float | None:
    expected_list, actual_list = list(expected), list(actual)
    if not expected_list:
        return None
    return round(edit_distance(expected_list, actual_list) / len(expected_list), 4)


def transcribe(model_path: Path, audio_path: Path, device: str, reference: str | None) -> Result:
    audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if sample_rate != 16_000:
        tensor = torch.from_numpy(np.ascontiguousarray(audio)).reshape(1, 1, -1)
        audio = functional.interpolate(
            tensor, size=16_000 * round(len(audio) / sample_rate), mode="linear", align_corners=False
        ).reshape(-1).numpy()
        sample_rate = 16_000
    duration = len(audio) / sample_rate
    started = time.perf_counter()
    processor = WhisperProcessor.from_pretrained(model_path, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(model_path, local_files_only=True).to(device)
    model.eval()
    features = processor.feature_extractor(audio, sampling_rate=sample_rate, return_tensors="pt").input_features.to(device)
    with torch.inference_mode():
        ids = model.generate(features, task="transcribe", max_new_tokens=448)
    transcript = processor.tokenizer.batch_decode(ids, skip_special_tokens=True)[0].strip()
    elapsed = time.perf_counter() - started
    words = normalize(reference) if reference else []
    result = Result(
        model=model_path.name, model_path=str(model_path), audio=str(audio_path),
        duration_seconds=round(duration, 3), elapsed_seconds=round(elapsed, 3),
        realtime_factor=round(elapsed / duration, 3) if duration else 0.0,
        transcript=transcript,
        word_error_rate=error_rate(words, normalize(transcript)) if reference else None,
        character_error_rate=error_rate(list("".join(words)), list("".join(normalize(transcript)))) if reference else None,
    )
    del model, processor, features
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline local Whisper benchmark")
    parser.add_argument("--audio", type=Path, action="append", help="WAV/MP3/etc. recording; repeat for each test clip")
    parser.add_argument("--model", type=Path, action="append", help="Model directory; repeat to select candidates")
    parser.add_argument("--models-root", type=Path, default=DEFAULT_MODELS_ROOT)
    parser.add_argument("--reference", type=Path, help="UTF-8 transcript when benchmarking one audio clip")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "benchmark_results")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--list-models", action="store_true")
    args = parser.parse_args()

    models = args.model or discover_models(args.models_root)
    if args.list_models:
        for model in models:
            print(model)
        return
    if not args.audio:
        parser.error("--audio is required unless --list-models is used")
    if args.reference and len(args.audio) != 1:
        parser.error("--reference can only be used with exactly one --audio clip")
    if not models:
        parser.error("No complete local Transformers Whisper checkpoints found")

    reference = args.reference.read_text(encoding="utf-8").strip() if args.reference else None
    results: list[Result] = []
    for audio in args.audio:
        for model in models:
            try:
                results.append(transcribe(model, audio, args.device, reference))
                print(f"completed: {model.name} / {audio.name}")
            except Exception as exc:  # Preserve a failed candidate in the report.
                results.append(Result(model.name, str(model), str(audio), 0, 0, 0, "", None, None, str(exc)))
                print(f"failed: {model.name} / {audio.name}: {exc}")

    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / f"asr-benchmark-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    destination.write_text(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"results written to {destination}")


if __name__ == "__main__":
    main()
