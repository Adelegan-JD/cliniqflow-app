
import torchaudio
import soundfile as _sf

# Patch 1 — AudioMetaData (dropped in newer torchaudio, still used by pyannote)
if not hasattr(torchaudio, 'AudioMetaData'):
    from dataclasses import dataclass
    @dataclass
    class _AudioMetaData:
        sample_rate:     int = 0
        num_channels:    int = 0
        num_frames:      int = 0
        bits_per_sample: int = 0
        encoding:        str = ""
    torchaudio.AudioMetaData = _AudioMetaData

# Patch 2 — torchaudio.info  (uses soundfile instead of ffmpeg/sox)
if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ["soundfile"]
if not hasattr(torchaudio, 'set_audio_backend'):
    torchaudio.set_audio_backend = lambda x: None

def _info(filepath, *args, **kwargs):
    info = _sf.info(filepath)
    return torchaudio.AudioMetaData(
        sample_rate=info.samplerate,
        num_channels=info.channels,
        num_frames=info.frames,
        bits_per_sample=16,
        encoding="PCM_S",
    )
torchaudio.info = _info

# Patch 3 — torchaudio.load  (uses soundfile instead of ffmpeg/sox)
import torch as _torch
def _load(filepath, *args, **kwargs):
    kwargs.pop('backend', None)
    kwargs.pop('normalize', None)
    data, sr = _sf.read(filepath, dtype='float32', always_2d=True)
    return _torch.from_numpy(data.T), sr
torchaudio.load = _load

# Patch 4 — torch.load weights_only  (pyannote checkpoints need full pickle)
import torch
import lightning_fabric.utilities.cloud_io as _lf_io
import pytorch_lightning.core.saving as _pl_saving

def _safe_load(path, map_location=None, **kwargs):
    kwargs.pop('weights_only', None)
    with open(path, 'rb') as f:
        return torch.load(f, map_location=map_location, weights_only=False)

_lf_io._load       = _safe_load
_pl_saving.pl_load = _safe_load

_orig_torch_load = torch.load
def _patched_torch_load(f, *args, **kwargs):
    kwargs['weights_only'] = False
    return _orig_torch_load(f, *args, **kwargs)
torch.load = _patched_torch_load


import logging
import os
import numpy as np
import torch as torch
from pyannote.audio import Pipeline as DiarizationPipeline
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from huggingface_hub import snapshot_download

logger = logging.getLogger(__name__)

SAMPLE_RATE    = 16000
MIN_DURATION_S = 0
HF_TOKEN       = os.environ.get("HF_TOKEN")
MODEL_ID       = "openai/whisper-small"
CACHE_DIR      = os.environ.get("CACHE_DIR", "./model_cache")


# ── ModelManager ───────────────────────────────────────────────────────────────

class ModelManager:
    """
    Holds Whisper + pyannote in memory.
    One instance is created at startup in main.py and stored on app.state
    so every router can access it via request.app.state.model_manager.
    """
    processor:    WhisperProcessor                = None
    model:        WhisperForConditionalGeneration = None
    diarizer:     DiarizationPipeline             = None
    device:       str                             = None
    model_loaded: bool                            = False


# Model download helper 

def download_model_if_needed() -> str:
    """Returns local cache path. Downloads from HuggingFace only on first run."""
    config_path = os.path.join(CACHE_DIR, "config.json")
    if os.path.exists(config_path):
        logger.info(f"Whisper model found in cache at {CACHE_DIR} — skipping download")
        return CACHE_DIR
    logger.info(f"Downloading Whisper model: {MODEL_ID} (first run only)...")
    os.makedirs(CACHE_DIR, exist_ok=True)
    snapshot_download(repo_id=MODEL_ID, local_dir=CACHE_DIR, token=HF_TOKEN)
    logger.info(f"Download complete — saved to {CACHE_DIR}")
    return CACHE_DIR



def diarize_and_transcribe(audio: np.ndarray, manager: ModelManager) -> list:
    """
    Run pyannote diarization then Whisper translation on each speaker segment.

    Args:
        audio:   mono float32 numpy array at 16 kHz
        manager: ModelManager instance (passed in — no global state)

    Returns:
        List of {speaker, start, end, translation} dicts sorted by start time.
    """
    logger.info("Running pyannote speaker diarization...")

    waveform = torch.from_numpy(audio.astype(np.float32))
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    waveform = waveform.to(manager.device)
    audio_input = {"waveform": waveform, "sample_rate": SAMPLE_RATE}

    diarization_output = manager.diarizer(audio_input)

    if hasattr(diarization_output, "speaker_diarization"):
        annotation = diarization_output.speaker_diarization
    else:
        annotation = diarization_output

    segments = []
    for segment, _, speaker in annotation.itertracks(yield_label=True):
        start_sample  = int(segment.start * SAMPLE_RATE)
        end_sample    = int(segment.end   * SAMPLE_RATE)
        speaker_audio = audio[start_sample:end_sample]

        if len(speaker_audio) < SAMPLE_RATE * MIN_DURATION_S:
            continue

        segments.append({
            "speaker": speaker,
            "start":   round(segment.start, 2),
            "end":     round(segment.end,   2),
            "audio":   speaker_audio,
        })

    logger.info(f"Diarization found {len(segments)} speaker segments")

    # Fallback: no segments detected → treat full audio as one speaker
    if not segments:
        logger.info("No speaker segments — transcribing full audio as single block")
        if len(audio) >= int(SAMPLE_RATE * 0.5):
            segments = [{
                "speaker": "SPEAKER_00",
                "start":   0.0,
                "end":     round(len(audio) / SAMPLE_RATE, 2),
                "audio":   audio,
            }]

    results = []
    for seg in segments:
        input_features = manager.processor.feature_extractor(
            seg["audio"],
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
        ).input_features.to(
            device=manager.device,
            dtype=torch.float16 if manager.device == "cuda" else torch.float32,
        )

        with torch.no_grad():
            predicted_ids = manager.model.generate(
                input_features,
                task="translate",
                language=None,
                max_new_tokens=256,
            )

        translation = manager.processor.tokenizer.batch_decode(
            predicted_ids, skip_special_tokens=True
        )[0].strip()

        results.append({
            "speaker":     seg["speaker"],
            "start":       seg["start"],
            "end":         seg["end"],
            "translation": translation,
        })

    results.sort(key=lambda x: x["start"])
    return results


def format_conversation(segments: list) -> str:
    """
    Convert segment list into a readable labelled transcript string.
    e.g. 'SPEAKER_00 [0.5s–8.2s]: Good morning, how are you feeling?'
    """
    return "\n".join(
        f"{s['speaker']} [{s['start']}s\u2013{s['end']}s]: {s['translation']}"
        for s in segments
    )
