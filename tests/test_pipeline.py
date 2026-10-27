"""Unit tests for ClipForge core modules using standard unittest."""

import os
from pathlib import Path
import tempfile
import unittest

# Ensure clipforge module is importable from scratch directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from clipforge.core.transcriber import Segment, WordTimestamp, Transcript
from clipforge.core.analyzer import HighlightAnalyzer
from clipforge.core.subtitle import SubtitleGenerator
from clipforge.core.cropper import CropWindow


class TestClipForge(unittest.TestCase):
    def test_subtitle_timestamp_format(self):
        """Verify ASS timestamp formatting (H:MM:SS.cs)."""
        self.assertEqual(SubtitleGenerator._format_timestamp(0.0), "0:00:00.00")
        self.assertEqual(SubtitleGenerator._format_timestamp(65.25), "0:01:05.25")
        self.assertEqual(SubtitleGenerator._format_timestamp(3600.0), "1:00:00.00")

    def test_subtitle_generation(self):
        """Verify ASS file generation with kinetic tags."""
        generator = SubtitleGenerator()
        segments = [
            Segment(
                id=0,
                text="Welcome to ClipForge",
                start=1.0,
                end=3.0,
                words=[
                    WordTimestamp(word="Welcome", start=1.0, end=1.5),
                    WordTimestamp(word="to", start=1.5, end=2.0),
                    WordTimestamp(word="ClipForge", start=2.0, end=3.0),
                ],
            )
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "test.ass"
            generator.generate_ass(segments, clip_start_time=1.0, output_path=out_file)

            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("[Script Info]", content)
            self.assertIn("PlayResX: 1080", content)
            self.assertIn("PlayResY: 1920", content)
            self.assertIn("Dialogue: 0,0:00:00.00", content)
            self.assertIn("ClipForge", content)

    def test_highlight_analyzer_heuristic(self):
        """Verify heuristic scoring and deduplication."""
        analyzer = HighlightAnalyzer()
        segments = [
            Segment(
                id=i,
                text=f"This is segment number {i} talking about something interesting.",
                start=float(i * 5),
                end=float((i + 1) * 5),
                words=[WordTimestamp(word="word", start=float(i * 5), end=float((i + 1) * 5))],
            )
            for i in range(15)
        ]
        transcript = Transcript(
            audio_path=Path("dummy.wav"),
            language="en",
            duration=75.0,
            segments=segments,
        )

        candidates = analyzer.find_candidates(
            transcript,
            min_duration=20.0,
            max_duration=40.0,
            top_k=2,
        )

        self.assertLessEqual(len(candidates), 2)
        for c in candidates:
            self.assertGreaterEqual(c.duration, 20.0)
            self.assertLessEqual(c.duration, 40.0)
            self.assertGreaterEqual(c.viral_score, 0.0)

    def test_crop_window_dataclass(self):
        """Verify CropWindow attributes."""
        crop = CropWindow(crop_x=420, crop_width=608, crop_height=1080)
        self.assertEqual(crop.crop_x, 420)
        self.assertEqual(crop.crop_width, 608)
        self.assertEqual(crop.crop_height, 1080)


if __name__ == "__main__":
    unittest.main()
