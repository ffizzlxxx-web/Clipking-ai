import streamlit as st
import subprocess
import tempfile
import os
import numpy as np
import wave
import zipfile
from pathlib import Path

st.set_page_config(
    page_title="ClipKing AI",
    page_icon="👑",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: #0e1117;
    color: white;
}
h1 {
    color: #a78bfa;
    text-align: center;
}
.stButton button {
    background: #8b5cf6;
    color: white;
    border-radius: 10px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

st.title("👑 ClipKing AI")
st.subheader("AI Gaming Shorts Generator")

st.info("Upload your video and automatically create highlight clips.")

uploaded = st.file_uploader(
    "🎮 Upload Gaming Video",
    type=["mp4", "mov", "mkv", "webm"]
)

st.markdown("### ⚙️ Advanced Settings")

clip_len = st.slider("Clip Length", 10, 60, 30)
count = st.slider("Number of Clips", 1, 10, 5)
gap = st.slider("Minimum Gap", 10, 120, 30)

vertical = st.checkbox("📱 Convert to 9:16 Shorts", True)

captions = st.checkbox("Enable Auto Captions (requires Whisper)", False)

def run(cmd):
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2000:])
    return p.stdout

def get_duration(path):
    out = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ])
    return float(out.strip())

def detect_moments(path, workdir, duration):
    audio = Path(workdir) / "audio.wav"

    run([
        "ffmpeg", "-y", "-i", str(path),
        "-vn", "-ac", "1",
        "-ar", "16000",
        str(audio)
    ])

    with wave.open(str(audio), "rb") as f:
        rate = f.getframerate()
        frames = f.readframes(f.getnframes())

    samples = np.frombuffer(frames, dtype=np.int16)
    samples = samples.astype(np.float32) / 32768

    step = rate // 2
    energy = []

    for i in range(0, len(samples), step):
        chunk = samples[i:i+step]
        energy.append(
            float(np.sqrt(np.mean(chunk ** 2)))
            if len(chunk) else 0
        )

    energy = np.array(energy)

    if len(energy) == 0:
        return []

    smooth = np.convolve(
        energy, np.ones(5)/5, mode="same"
    )

    candidates = np.argsort(smooth)[::-1]
    chosen = []
    half = clip_len / 2

    for idx in candidates:
        center = idx * 0.5
        start = max(0, min(duration-clip_len, center-half))
        end = start + clip_len

        if duration <= clip_len:
            start, end = 0, duration

        if all(
            end + gap <= s or start >= e + gap
            for s, e in chosen
        ):
            chosen.append((start, end))

        if len(chosen) >= count:
            break

    return sorted(chosen)

def make_clip(path, output, start, end):
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", str(path),
        "-t", str(end-start)
    ]

    if vertical:
        cmd += [
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        ]
    else:
        cmd += ["-vf", "scale=1280:-2"]

    cmd += [
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output)
    ]

    run(cmd)

if uploaded:
    st.success("Video uploaded successfully!")

    if st.button("🚀 Generate AI Clips"):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / uploaded.name
            source.write_bytes(uploaded.getvalue())

            try:
                duration = get_duration(source)

                if duration <= 0:
                    st.error("Invalid video duration.")
                    st.stop()

                with st.spinner("🤖 Detecting best moments..."):
                    moments = detect_moments(
                        source, temp, duration
                    )

                if not moments:
                    st.error("No highlight moments found.")
                    st.stop()

                clips = []

                progress = st.progress(0)

                for i, (start, end) in enumerate(moments):
                    output = Path(temp) / f"ClipKing_{i+1}.mp4"

                    with st.spinner(f"Creating clip {i+1}..."):
                        make_clip(source, output, start, end)

                    clips.append(output)
                    progress.progress((i+1)/len(moments))

                zip_path = Path(temp) / "ClipKing_Clips.zip"

                with zipfile.ZipFile(zip_path, "w") as z:
                    for clip in clips:
                        z.write(clip, clip.name)

                st.success(f"🎉 {len(clips)} clips created!")

                for clip in clips:
                    st.video(str(clip))

                st.download_button(
                    "📥 Download All Clips",
                    data=zip_path.read_bytes(),
                    file_name="ClipKing_AI_Clips.zip",
                    mime="application/zip"
                )

            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.caption("👑 ClipKing AI | Advanced Gaming Video Editor")
