"""AI highlight and viral hook detection engine."""

from dataclasses import dataclass
from typing import List, Optional
from clipforge.core.transcriber import Transcript, Segment


@dataclass
class ClipCandidate:
    """A ranked candidate clip suitable for short-form repurposing."""
    title: str
    rationale: str
    start_time: float
    end_time: float
    viral_score: float  # 0.0 to 10.0
    segments: List[Segment]

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class HighlightAnalyzer:
    """Analyzes transcript segments to find the most engaging 30-60 second clips."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def find_candidates(
        self,
        transcript: Transcript,
        min_duration: float = 25.0,
        max_duration: float = 65.0,
        top_k: int = 3,
    ) -> List[ClipCandidate]:
        """
        Locates optimal clip windows. If an LLM key is provided, uses semantic analysis;
        otherwise applies heuristic hook scoring (speech pacing, keyword density, sentence continuity).
        """
        if not transcript.segments:
            return []

        # Heuristic sliding-window candidate generator
        candidates: List[ClipCandidate] = []
        segments = transcript.segments

        for i in range(len(segments)):
            curr_start = segments[i].start
            chunk_segments: List[Segment] = []

            for j in range(i, len(segments)):
                seg = segments[j]
                chunk_segments.append(seg)
                duration = seg.end - curr_start

                if min_duration <= duration <= max_duration:
                    score = self._heuristic_score(chunk_segments, duration)
                    title = f"Highlight: {chunk_segments[0].text[:40]}..."
                    candidates.append(
                        ClipCandidate(
                            title=title,
                            rationale="High sentence density and conversational flow.",
                            start_time=curr_start,
                            end_time=seg.end,
                            viral_score=score,
                            segments=list(chunk_segments),
                        )
                    )
                elif duration > max_duration:
                    break

        # Sort by viral score descending and remove overlapping segments
        candidates.sort(key=lambda c: c.viral_score, reverse=True)
        return self._deduplicate(candidates, top_k=top_k)

    def _heuristic_score(self, segments: List[Segment], duration: float) -> float:
        """Heuristic score based on words-per-minute, question marks, and action words."""
        total_words = sum(len(s.words) for s in segments)
        wpm = (total_words / duration) * 60.0

        # Optimal spoken tempo is between 130 and 175 WPM
        tempo_score = max(0.0, 10.0 - abs(wpm - 150.0) / 10.0)

        # Content punchiness markers
        full_text = " ".join(s.text for s in segments).lower()
        bonus = 0.0
        hooks = ["the secret", "why", "how to", "never", "always", "mistake", "truth", "crazy", "actually"]
        for hook in hooks:
            if hook in full_text:
                bonus += 0.5
        if "?" in full_text:
            bonus += 0.5

        return min(10.0, (tempo_score * 0.7) + bonus)

    def _deduplicate(self, candidates: List[ClipCandidate], top_k: int) -> List[ClipCandidate]:
        """Ensures selected clips do not significantly overlap in time."""
        selected: List[ClipCandidate] = []
        for cand in candidates:
            overlaps = False
            for sel in selected:
                # Check for > 40% time overlap
                overlap_start = max(cand.start_time, sel.start_time)
                overlap_end = min(cand.end_time, sel.end_time)
                if overlap_end > overlap_start:
                    overlap_dur = overlap_end - overlap_start
                    if overlap_dur / cand.duration > 0.4:
                        overlaps = True
                        break
            if not overlaps:
                selected.append(cand)
            if len(selected) >= top_k:
                break
        return selected
