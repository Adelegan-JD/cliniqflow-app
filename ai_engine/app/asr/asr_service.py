from app.asr.asr_engine import (
    ModelManager,
    format_conversation,
    transcribe_file,
)


class ASRService:
    def __init__(self, manager: ModelManager):
        """
        Args:
            manager: the ModelManager stored on app.state — passed in by the
                     endpoint so ASRService never touches global state itself.
        """
        self.manager = manager

    def is_ready(self) -> bool:
        """Return True once Whisper + pyannote are fully loaded."""
        return self.manager.model_loaded

    def transcribe(self, audio_path: str) -> list:
        """
        Run speaker diarization + Whisper translation on a numpy audio array.

        Args:
            audio: mono float32 numpy array at 16 kHz

        Returns:
            List of {speaker, start, end, translation} dicts.
        """
        if not self.is_ready():
            raise RuntimeError("Models are not loaded yet. Wait for server startup.")
        return transcribe_file(audio_path, self.manager)

    def format(self, segments: list) -> str:
        """
        Convert segment list into a readable conversation string.
        e.g. 'SPEAKER_00 [0.5s–8.2s]: Good morning...'
        """
        return format_conversation(segments)

    def transcribe_and_format(self, audio_path: str) -> dict:
        """
        Convenience method: transcribe and return both the raw segments
        and the formatted conversation string in one call.

        Returns:
            {
                "segments":     [...],
                "conversation": "SPEAKER_00 [0.5s–8.2s]: ..."
            }
        """
        segments = self.transcribe(audio_path)
        return {
            "segments":     segments,
            "conversation": self.format(segments),
        }
