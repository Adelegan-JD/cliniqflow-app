"""Low-memory local ASR engine for CLINIQ-FLOW."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)
DEFAULT_MODEL_PATH = "/opt/models/yoruba-whisper-small-ct2"


@dataclass
class ModelManager:
    """One shared ASR model, loaded once during application startup."""

    model: WhisperModel | None = None
    device: str = "cpu"
    compute_type: str = "int8"
    model_loaded: bool = False
    diarization_enabled: bool = False


def model_path() -> str:
    """Return the deployed model path and fail clearly if the image is incomplete."""
    configured = os.environ.get("ASR_MODEL_PATH", DEFAULT_MODEL_PATH)
    if not Path(configured).is_dir():
        raise RuntimeError(
            "Offline ASR model is missing. Build the AI image with the converted "
            "Yoruba Whisper model or set ASR_MODEL_PATH to that model directory."
        )
    return configured


def load_model() -> ModelManager:
    """Load the quantized offline ASR model without PyTorch or network access."""
    manager = ModelManager(
        device=os.environ.get("ASR_DEVICE", "cpu"),
        compute_type=os.environ.get("ASR_COMPUTE_TYPE", "int8"),
    )
    path = model_path()
    logger.info("Loading offline Yoruba Whisper model from %s", path)
    manager.model = WhisperModel(path, device=manager.device, compute_type=manager.compute_type)
    manager.model_loaded = True
    logger.info("Offline Yoruba Whisper model loaded")
    return manager


def transcribe_file(audio_path: str, manager: ModelManager) -> list[dict]:
    """Transcribe a clinical recording with automatic Yoruba/English detection."""
    if not manager.model_loaded or manager.model is None:
        raise RuntimeError("ASR model is not loaded yet.")

    segments, _info = manager.model.transcribe(
        audio_path,
        task="transcribe",
        language=None,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    results: list[dict] = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            results.append({
                "speaker": "SPEAKER_00",
                "start": round(float(segment.start), 2),
                "end": round(float(segment.end), 2),
                "translation": text,
            })
    return results


def format_conversation(segments: list[dict]) -> str:
    return "\n".join(
        f"{item['speaker']} [{item['start']}s–{item['end']}s]: {item['translation']}"
        for item in segments
    )
