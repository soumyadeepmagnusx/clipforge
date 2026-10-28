"""ClipForge command-line interface."""

import argparse
from pathlib import Path
import sys
from clipforge.core.media import MediaProcessor
from clipforge.core.transcriber import Transcriber
from clipforge.core.analyzer import HighlightAnalyzer
from clipforge.core.cropper import SmartCropper
from clipforge.core.subtitle import SubtitleGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clipforge",
        description="ClipForge: AI Video Repurposing & Kinetic Caption Engine",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: process
    proc = subparsers.add_parser("process", help="Find highlights and render vertical 9:16 shorts")
    proc.add_argument("video_path", type=Path, help="Path to input 16:9 video file")
    proc.add_argument("--output-dir", type=Path, default=Path("./output"), help="Output directory")
    proc.add_argument("--min-duration", type=float, default=20.0, help="Minimum clip duration (seconds)")
    proc.add_argument("--max-duration", type=float, default=60.0, help="Maximum clip duration (seconds)")
    proc.add_argument("--top-k", type=int, default=3, help="Number of viral clips to extract")
    proc.add_argument("--no-subtitles", action="store_true", help="Disable burning kinetic subtitles")
    proc.add_argument(
        "--preset",
        type=str,
        default="classic",
        choices=["classic", "hormozi", "neon", "minimal"],
        help="Subtitle visual styling preset",
    )

    # Subcommand: probe
    subparsers.add_parser("probe", help="Inspect video properties and dimensions").add_argument(
        "video_path", type=Path, help="Path to video file"
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    media = MediaProcessor()

    if args.command == "probe":
        meta = media.probe(args.video_path)
        print(f"🎬 Video: {meta.path.name}")
        print(f"   Duration: {meta.duration:.2f}s | Resolution: {meta.width}x{meta.height} | FPS: {meta.fps:.1f}")
        print(f"   Has Audio: {meta.has_audio}")
        return

    if args.command == "process":
        video_path = args.video_path
        if not video_path.exists():
            print(f"❌ Error: File not found: {video_path}", file=sys.stderr)
            sys.exit(1)

        output_dir: Path = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        print(f"⚡ [1/5] Probing video media properties...")
        meta = media.probe(video_path)
        print(f"   Found {meta.width}x{meta.height} video ({meta.duration:.1f}s)")

        print(f"🎵 [2/5] Extracting audio for speech analysis...")
        audio_path = temp_dir / f"{video_path.stem}_audio.wav"
        media.extract_audio(video_path, audio_path)

        print(f"🎙️ [3/5] Transcribing speech with word-level timestamps...")
        transcriber = Transcriber(model_size="base")
        transcript = transcriber.transcribe(audio_path)
        print(f"   Transcribed {len(transcript.segments)} speech segments.")

        print(f"🧠 [4/5] Scoring transcript for viral hooks and highlights...")
        analyzer = HighlightAnalyzer()
        candidates = analyzer.find_candidates(
            transcript,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            top_k=args.top_k,
        )

        if not candidates:
            print("⚠️ No suitable clip candidates found within duration bounds.")
            return

        print(f"🎯 Found {len(candidates)} high-potential clip(s):")
        for idx, cand in enumerate(candidates, 1):
            print(f"   Clip #{idx}: {cand.start_time:.1f}s - {cand.end_time:.1f}s ({cand.duration:.1f}s) | Score: {cand.viral_score:.1f}/10")

        cropper = SmartCropper()
        sub_gen = SubtitleGenerator.from_preset(args.preset)

        print(f"✂️ [5/5] Framing vertical 9:16 clips & burning captions (preset: '{args.preset}')...")
        for idx, cand in enumerate(candidates, 1):
            clip_name = f"{video_path.stem}_clip_{idx}"
            out_clip = output_dir / f"{clip_name}.mp4"

            # 1. Calculate smart face crop
            crop = cropper.calculate_optimal_crop(video_path, cand.start_time, cand.end_time)

            # 2. Generate subtitles
            sub_file = None
            if not args.no_subtitles:
                sub_file = temp_dir / f"{clip_name}.ass"
                sub_gen.generate_ass(cand.segments, cand.start_time, sub_file)

            # 3. Cut, crop, and burn
            media.cut_and_crop_916(
                video_path=video_path,
                start_time=cand.start_time,
                end_time=cand.end_time,
                crop_x=crop.crop_x,
                output_video=out_clip,
                subtitle_file=sub_file,
            )
            print(f"   ✅ Exported: {out_clip.name}")

        print("\n🎉 All clips processed successfully! Check output directory:", output_dir.resolve())


if __name__ == "__main__":
    main()
