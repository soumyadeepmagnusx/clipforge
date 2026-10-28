"""ClipForge Interactive Web Studio powered by Streamlit."""

import os
from pathlib import Path
import tempfile
import time

try:
    import streamlit as st
except ImportError:
    print("Streamlit is not installed. Install with: pip install streamlit")
    exit(1)

from clipforge.core.media import MediaProcessor
from clipforge.core.transcriber import Transcriber
from clipforge.core.analyzer import HighlightAnalyzer
from clipforge.core.cropper import SmartCropper
from clipforge.core.subtitle import SubtitleGenerator


def main():
    st.set_page_config(
        page_title="ClipForge Studio",
        page_icon="🎬",
        layout="wide",
    )

    st.title("🎬 ClipForge Studio")
    st.caption("AI-Powered Video Repurposing & Kinetic Caption Generator")

    # Sidebar: Styling & Processing Parameters
    st.sidebar.header("⚙️ Settings")
    preset = st.sidebar.selectbox(
        "Subtitle Aesthetic Preset",
        options=["hormozi", "neon", "classic", "minimal"],
        index=0,
        help="Visual style and color theme for kinetic subtitles",
    )

    st.sidebar.markdown(
        f"**Style:** {'Neon Yellow & Green Active' if preset == 'hormozi' else 'Cyan & Magenta Active' if preset == 'neon' else 'Classic White & Yellow' if preset == 'classic' else 'Minimal Subtle'}"
    )

    min_dur, max_dur = st.sidebar.slider(
        "Clip Duration Window (seconds)",
        min_value=15,
        max_value=90,
        value=(20, 60),
    )

    top_k = st.sidebar.slider("Number of Shorts to Extract", min_value=1, max_value=5, value=2)
    burn_subs = st.sidebar.checkbox("Burn Kinetic Subtitles", value=True)

    # Main area: Video Input
    uploaded_file = st.file_uploader(
        "Upload a 16:9 Landscape Video (MP4 / MOV)",
        type=["mp4", "mov", "mkv"],
    )

    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📹 Source Video")
            st.video(uploaded_file)

        with col2:
            st.subheader("⚡ Output Studio")
            if st.button("🚀 Generate Viral Shorts", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Save temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
                    tmp_in.write(uploaded_file.read())
                    input_video_path = Path(tmp_in.name)

                output_dir = Path("./output_studio")
                output_dir.mkdir(parents=True, exist_ok=True)
                temp_dir = output_dir / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)

                media = MediaProcessor()

                try:
                    # Step 1: Probe
                    status_text.info("🔍 [1/5] Analyzing video resolution & framerate...")
                    progress_bar.progress(15)
                    meta = media.probe(input_video_path)

                    # Step 2: Extract audio
                    status_text.info("🎵 [2/5] Extracting audio track for speech recognition...")
                    progress_bar.progress(30)
                    audio_path = temp_dir / f"{input_video_path.stem}.wav"
                    media.extract_audio(input_video_path, audio_path)

                    # Step 3: Transcription
                    status_text.info("🎙️ [3/5] Transcribing speech with word-level timestamps...")
                    progress_bar.progress(55)
                    transcriber = Transcriber(model_size="base")
                    transcript = transcriber.transcribe(audio_path)

                    # Step 4: Highlight Detection
                    status_text.info("🧠 [4/5] Scoring transcript for viral hooks and punchlines...")
                    progress_bar.progress(75)
                    analyzer = HighlightAnalyzer()
                    candidates = analyzer.find_candidates(
                        transcript,
                        min_duration=float(min_dur),
                        max_duration=float(max_dur),
                        top_k=top_k,
                    )

                    if not candidates:
                        st.warning("No clips matched the specified duration window. Try loosening duration bounds.")
                        return

                    # Step 5: Render 9:16 Shorts
                    status_text.info(f"✂️ [5/5] Framing 9:16 vertical crop and burning '{preset}' captions...")
                    progress_bar.progress(90)

                    cropper = SmartCropper()
                    sub_gen = SubtitleGenerator.from_preset(preset)
                    generated_shorts = []

                    for idx, cand in enumerate(candidates, 1):
                        clip_name = f"short_{idx}_{int(time.time())}"
                        out_path = output_dir / f"{clip_name}.mp4"

                        crop = cropper.calculate_optimal_crop(input_video_path, cand.start_time, cand.end_time)

                        sub_file = None
                        if burn_subs:
                            sub_file = temp_dir / f"{clip_name}.ass"
                            sub_gen.generate_ass(cand.segments, cand.start_time, sub_file)

                        media.cut_and_crop_916(
                            video_path=input_video_path,
                            start_time=cand.start_time,
                            end_time=cand.end_time,
                            crop_x=crop.crop_x,
                            output_video=out_path,
                            subtitle_file=sub_file,
                        )
                        generated_shorts.append((cand, out_path))

                    progress_bar.progress(100)
                    status_text.success(f"🎉 Generated {len(generated_shorts)} viral short(s) successfully!")

                    for idx, (cand, short_path) in enumerate(generated_shorts, 1):
                        st.markdown(f"#### Short #{idx} (Score: {cand.viral_score:.1f}/10)")
                        st.video(str(short_path))
                        with open(short_path, "rb") as f:
                            st.download_button(
                                label=f"⬇️ Download Short #{idx}",
                                data=f,
                                file_name=f"clipforge_short_{idx}.mp4",
                                mime="video/mp4",
                                key=f"dl_{idx}",
                            )

                except Exception as e:
                    status_text.error(f"❌ Processing error: {e}")
                finally:
                    if input_video_path.exists():
                        try:
                            os.remove(input_video_path)
                        except OSError:
                            pass


if __name__ == "__main__":
    main()
