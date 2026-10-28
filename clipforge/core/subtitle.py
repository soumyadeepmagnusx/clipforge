"""Kinetic animated karaoke subtitle generator in Advanced SubStation Alpha (.ass) format."""

from pathlib import Path
from typing import List
from clipforge.core.transcriber import Segment, WordTimestamp


class SubtitleGenerator:
    """Generates high-energy, word-highlighted karaoke subtitles for vertical video."""

    def __init__(
        self,
        font_name: str = "Arial",
        font_size: int = 70,
        primary_color: str = "&H00FFFFFF",    # White (&HAABBGGRR)
        highlight_color: str = "&H0000FFFF",  # Bright Yellow
        outline_color: str = "&H00000000",    # Black outline
        outline_width: int = 4,
    ):
        self.font_name = font_name
        self.font_size = font_size
        self.primary_color = primary_color
        self.highlight_color = highlight_color
        self.outline_color = outline_color
        self.outline_width = outline_width

    @classmethod
    def from_preset(cls, preset: str = "classic") -> "SubtitleGenerator":
        """Instantiate a subtitle generator with predefined aesthetic styles."""
        presets = {
            "classic": cls(
                font_name="Arial",
                font_size=70,
                primary_color="&H00FFFFFF",
                highlight_color="&H0000FFFF",  # Bright Yellow
                outline_color="&H00000000",
                outline_width=4,
            ),
            "hormozi": cls(
                font_name="Impact",
                font_size=82,
                primary_color="&H0000FFFF",    # Yellow base
                highlight_color="&H0000FF00",  # Neon Green active
                outline_color="&H00000000",
                outline_width=6,
            ),
            "neon": cls(
                font_name="Arial Black",
                font_size=74,
                primary_color="&H00FFFF00",    # Cyan base
                highlight_color="&H00FF00FF",  # Magenta active
                outline_color="&H00000000",
                outline_width=5,
            ),
            "minimal": cls(
                font_name="Helvetica",
                font_size=64,
                primary_color="&H00FFFFFF",
                highlight_color="&H00CCCCCC",
                outline_color="&H00000000",
                outline_width=2,
            ),
        }
        return presets.get(preset.lower(), presets["classic"])

    def generate_ass(
        self,
        segments: List[Segment],
        clip_start_time: float,
        output_path: Path,
        words_per_line: int = 4,
    ) -> Path:
        """
        Creates an ASS subtitle file where words appear in short, punchy 3-5 word groups
        and highlight individually as spoken (karaoke style).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kinetic,{self.font_name},{self.font_size},{self.primary_color},{self.highlight_color},{self.outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{self.outline_width},2,2,40,40,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events: List[str] = []

        # Collect all words relative to clip start time
        all_words: List[WordTimestamp] = []
        for s in segments:
            for w in s.words:
                rel_start = max(0.0, w.start - clip_start_time)
                rel_end = max(rel_start + 0.05, w.end - clip_start_time)
                all_words.append(WordTimestamp(word=w.word, start=rel_start, end=rel_end))

        # Chunk into short groups
        for i in range(0, len(all_words), words_per_line):
            group = all_words[i : i + words_per_line]
            if not group:
                continue

            group_start = group[0].start
            group_end = group[-1].end

            # Format start & end timestamps (H:MM:SS.cs)
            start_str = self._format_timestamp(group_start)
            end_str = self._format_timestamp(group_end)

            # Karaoke text assembly
            karaoke_parts = []
            for w in group:
                dur_cs = int((w.end - w.start) * 100)
                karaoke_parts.append(f"{{\\k{max(dur_cs, 1)}}}{w.word} ")

            line_text = "".join(karaoke_parts).strip()
            events.append(f"Dialogue: 0,{start_str},{end_str},Kinetic,,0,0,0,,{line_text}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(events))
            f.write("\n")

        return output_path

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Converts float seconds to ASS format: H:MM:SS.cc"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - int(seconds)) * 100))
        return f"{hrs:d}:{mins:02d}:{secs:02d}.{centis:02d}"
