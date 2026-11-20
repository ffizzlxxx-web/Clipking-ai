import streamlit as st
import subprocess, tempfile, os, json, math
from pathlib import Path
import numpy as np

st.set_page_config(page_title="ClipKing AI", page_icon="👑", layout="centered")

st.markdown("""
<style>
.block-container {max-width: 850px; padding-top: 2rem;}
.hero {padding: 1.4rem; border-radius: 18px; background: linear-gradient(120deg,#17172e,#38205d); color:white;}
.hero h1 {margin:0; font-size:2.2rem;}
.small {opacity:.85}
</style>
<div class="hero">
<h1>👑 ClipKing AI</h1>
<p class="small">Turn your gaming videos into short highlight clips.</p>
</div>
""", unsafe_allow_html=True)

st.info("MVP version: upload a video file you own or have permission to edit. The app finds high-energy audio moments and cuts short clips automatically.")

uploaded = st.file_uploader("Upload a video", type=["mp4", "mov", "mkv", "webm"])
c1, c2, c3 = st.columns(3)
with c1:
    clip_len = st.slider("Clip length (seconds)", 15, 60, 30, 5)
with c2:
    count = st.slider("Number of clips", 1, 10, 5)
with c3:
    gap = st.slider("Minimum gap (seconds)", 10, 120, 30, 5)

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-2500:])
    return p.stdout

def get_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    return float(out.strip())

def extract_energy(path, workdir):
    wav = Path(workdir) / "audio.wav"
    run(["ffmpeg", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "8000",
         "-acodec", "pcm_s16le", str(wav)])
    import wave
    with wave.open(str(wav), "rb") as wf:
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    step = rate * 2
    vals = []
    for i in range(0, len(audio), step):
        chunk = audio[i:i+step]
        vals.append(float(np.sqrt(np.mean(chunk * chunk))) if len(chunk) else 0.0)
    return np.array(vals), 2.0

def choose_moments(energy, step, duration, clip_len, count, gap):
    n = len(energy)
    if n == 0:
        return []
    # Smooth energy to avoid choosing a single noisy spike.
    kernel = np.ones(5) / 5
    smooth = np.convolve(energy, kernel, mode="same")
    candidates = np.argsort(smooth)[::-1]
    chosen = []
    half = clip_len / 2
    for idx in candidates:
        center = idx * step + step / 2
        start = max(0, min(duration - clip_len, center - half))
        end = start + clip_len
        if duration <= clip_len:
            start, end = 0, duration
        if all(end + gap <= s or start >= e + gap for s, e in chosen):
            chosen.append((start, end))
        if len(chosen) >= count:
            break
    return sorted(chosen)

if uploaded:
    st.video(uploaded)
    if st.button("✨ Find highlights & create clips", type="primary", use_container_width=True):
        with st.spinner("Analyzing audio and creating clips..."):
            try:
                with tempfile.TemporaryDirectory() as td:
                    source = Path(td) / uploaded.name
                    source.write_bytes(uploaded.getbuffer())
                    duration = get_duration(source)
                    energy, step = extract_energy(source, td)
                    moments = choose_moments(energy, step, duration, clip_len, count, gap)
                    if not moments:
                        st.warning("No suitable moments found. Try a longer video.")
                    else:
                        outdir = Path(td) / "clips"
                        outdir.mkdir()
                        results = []
                        progress = st.progress(0)
                        for i, (start, end) in enumerate(moments, 1):
                            out = outdir / f"ClipKing_clip_{i:02d}.mp4"
                            run(["ffmpeg", "-y", "-ss", f"{start:.2f}", "-i", str(source),
                                 "-t", f"{end-start:.2f}", "-vf",
                                 "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
                                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                                 "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)])
                            results.append((out.name, out.read_bytes(), start, end))
                            progress.progress(i / len(moments))
                        st.success(f"Created {len(results)} clips!")
                        for name, data, start, end in results:
                            with st.expander(f"{name} · {int(start)}s–{int(end)}s", expanded=True):
                                st.video(data)
                                st.download_button("⬇️ Download clip", data, file_name=name,
                                                   mime="video/mp4", key=name)
            except Exception as e:
                st.error("Something went wrong while processing this video.")
                st.code(str(e))

st.caption("Note: This first version detects loud/high-energy moments; it does not understand gameplay or guarantee viral moments. YouTube links are not imported in this version. Use your own video file or one you have permission to edit.")
