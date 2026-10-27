"""Audio transcription module providing word-level timestamps."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class WordTimestamp:
    """A single transcribed word with exact start and end times in seconds."""
    word: str
    start: float
    end: float
    probability: float = 1.0


@dataclass
class Segment:
    """A coherent phrase or sentence segment with word-level timestamps."""
    id: int
    text: str
    start: float
    end: float
    words: List[WordTimestamp] = field(default_factory=list)


@dataclass
class Transcript:
    """Full transcription of an audio file."""
    audio_path: Path
    language: str
    duration: float
    segments: List[Segment] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments)


class Transcriber:
    """Transcribes audio using Whisper or fallback models with word timestamps."""

    def __init__(self, model_size: str = "base", device: str = "auto"):
        self.model_size = model_size
        self.device = device
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_size, device=self.device, compute_type="auto")
            except ImportError:
                raise ImportError(
                    "faster-whisper is not installed. Install with: pip install faster-whisper"
                )

    def transcribe(self, audio_path: Path) -> Transcript:
        """Run transcription with word timestamps enabled."""
        self._load_model()
        segments_gen, info = self._model.transcribe(
            str(audio_path),
            word_timestamps=True,
            vad_filter=True,
        )

        segments: List[Segment] = []
        for idx, s in enumerate(segments_gen):
            words = [
                WordTimestamp(
                    word=w.word.strip(),
                    start=w.start,
                    end=w.end,
                    probability=w.probability,
                )
                for w in (s.words or [])
            ]
            segments.append(
                Segment(
                    id=idx,
                    text=s.text.strip(),
                    start=s.start,
                    end=s.end,
                    words=words,
                )
            )

        return Transcript(
            audio_path=audio_path,
            language=info.language,
            duration=info.duration,
            segments=segments,
        )
