# ClipKing AI — free starter project

A mobile-friendly Streamlit web app that creates vertical clips from an uploaded video.
It ranks moments using audio energy (loud/exciting sections), then cuts MP4 clips with FFmpeg.

## Important limitations
- This is an MVP, not a full semantic AI editor. It detects high-energy audio, not game events.
- It accepts uploaded video files, **not YouTube URLs**. A YouTube link alone does not provide legal/technical access to the video file.
- Only upload videos you own or have permission to edit. Respect creator rights and platform terms.
- Free hosting has file-size, memory, and processing-time limits.

## Run locally
Requires Python 3.10+ and FFmpeg installed.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy free (Streamlit Community Cloud)
1. Create a GitHub account and a new public repository.
2. Upload `app.py`, `requirements.txt`, and `packages.txt`.
3. Open Streamlit Community Cloud and connect that repository.
4. Deploy `app.py`.
5. Open the app link on your phone and upload a video.

Deployment provider availability, limits, and free-tier terms can change.

## Files
- `app.py` — app
- `requirements.txt` — Python dependencies
- `packages.txt` — system package needed for FFmpeg
