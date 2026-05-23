from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import yt_dlp
import tempfile
import os
import shutil
import re
import uuid
from typing import Dict

app = FastAPI(title="Video Downloader API")

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PROGRESS STORAGE
# =========================

download_progress: Dict[str, dict] = {}

# =========================
# HELPERS
# =========================

def sanitize_filename(name: str) -> str:
    safe_name = re.sub(r'[^\w\s-]', '', name)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    safe_name = safe_name.strip()[:100]
    return safe_name + ".mp4"


def progress_hook(d, download_id):
    if d['status'] == 'downloading':

        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)

        percent = (downloaded / total * 100) if total else 0

        download_progress[download_id] = {
            "status": "downloading",
            "percent": round(percent, 1)
        }

    elif d['status'] == 'finished':

        download_progress[download_id] = {
            "status": "processing",
            "percent": 100
        }


def get_ydl_opts(temp_dir=None, download=False, download_id=None):

    opts = {
        "quiet": True,
        "no_warnings": True,

        # CLOUDLFARE FIX
        "extractor_args": {
            "generic": {
                "impersonate": ["chrome"]
            }
        },

        # BETTER HEADERS
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },

        # EXTRA FIXES
        "geo_bypass": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "nocheckcertificate": True,
    }

    if download:

        opts.update({
            "format": "best",
            "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
            "progress_hooks": [
                lambda d: progress_hook(d, download_id)
            ]
        })

    return opts


# =========================
# ROUTES
# =========================

@app.get("/")
def root():
    return {
        "message": "Video Downloader API Running 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/info")
def get_info(url: str = Query(...)):

    try:

        ydl_opts = get_ydl_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
            }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch video info: {str(e)}"
        )


@app.get("/progress/{download_id}")
def progress(download_id: str):

    return download_progress.get(
        download_id,
        {
            "status": "unknown",
            "percent": 0
        }
    )


@app.get("/download")
def download_video(
    url: str = Query(...),
    download_id: str = Query(None)
):

    if not download_id:
        download_id = str(uuid.uuid4())

    temp_dir = tempfile.mkdtemp()

    try:

        download_progress[download_id] = {
            "status": "starting",
            "percent": 0
        }

        ydl_opts = get_ydl_opts(
            temp_dir=temp_dir,
            download=True,
            download_id=download_id
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            title = info.get("title", "video")

        # FIND FILE
        downloaded_files = []

        for file in os.listdir(temp_dir):

            if file.endswith((
                ".mp4",
                ".mkv",
                ".webm",
                ".avi",
                ".flv"
            )):
                downloaded_files.append(file)

        if not downloaded_files:

            raise HTTPException(
                status_code=500,
                detail="No downloaded file found"
            )

        file_path = os.path.join(
            temp_dir,
            downloaded_files[0]
        )

        file_size = os.path.getsize(file_path)

        filename = sanitize_filename(title)

        def iterfile():

            try:

                with open(file_path, "rb") as f:

                    while chunk := f.read(1024 * 1024):
                        yield chunk

            finally:

                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{filename}"',
                "Content-Length": str(file_size)
            }
        )

    except Exception as e:

        try:
            shutil.rmtree(temp_dir)
        except:
            pass

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# RUN
# =========================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
