# Offline ASR benchmark

Benchmark the exact same recordings through each model before selecting the
production default. Keep test audio and outputs outside Git; they may contain
patient-identifiable speech.

The runner automatically finds complete Hugging Face/Transformers Whisper
checkpoints under `models/`. It does not download anything and it reports an
error, rather than silently substituting another model, for unsupported formats
such as `.nemo` or CTranslate2 checkpoints.

```powershell
cd ai_engine
.\.venv\Scripts\python.exe .\scripts\benchmark_asr.py --list-models
.\.venv\Scripts\python.exe .\scripts\benchmark_asr.py `
  --audio ..\SESS-2026-02-23-F0Z39\doctor_SPK081.wav `
  --audio ..\SESS-2026-02-25-YDJ77\doctor_SPK001.wav
```

Docker alternative (uses the slim benchmark runtime and mounts models/audio
read-only):

```powershell
docker build -f .\Dockerfile.benchmark -t cliniqflow-asr-benchmark .
docker run --rm -v ..\models:/models:ro -v ..\SESS-2026-02-23-F0Z39:/audio:ro `
  -v ..\benchmark_results:/results cliniqflow-asr-benchmark `
  --models-root /models --audio /audio/doctor_SPK081.wav --output /results
```

For a meaningful accuracy score, create a manually verified UTF-8 reference
transcript for one clip and use it with one `--audio` file:

```powershell
.\.venv\Scripts\python.exe .\scripts\benchmark_asr.py `
  --audio ..\benchmark_audio\yoruba.wav `
  --reference ..\benchmark_audio\yoruba.reference.txt
```

Compare WER/CER separately for English, Yoruba, and genuine code-switched
speech. Also compare real-time factor, clinical-term accuracy, numbers, doses,
and negations. A model with the lowest global WER is not automatically safest
for clinical use.
