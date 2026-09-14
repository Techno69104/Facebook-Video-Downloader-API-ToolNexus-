from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import yt_dlp
import re

app = FastAPI(title="FBFetch API", version="1.0")

# Allow your tool to call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_fb_url(url: str):
    return "facebook.com" in url or "fb.watch" in url

@app.get("/")
def home():
    return {"status": "FBFetch API is running", "endpoints": ["/api/info", "/api/download"]}

@app.get("/api/info")
def get_info(url: str = Query(..., description="Facebook Video URL")):
    if not is_fb_url(url):
        raise HTTPException(status_code=400, detail="Invalid Facebook URL")

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec')!= 'none':
                    formats.append({
                        "quality": f.get('format_note') or f.get('height'),
                        "ext": f.get('ext'),
                        "url": f.get('url'),
                        "height": f.get('height')
                    })
            # Sort by quality
            formats = sorted(formats, key=lambda x: x.get('height') or 0, reverse=True)

            return {
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "uploader": info.get('uploader'),
                "formats": formats[:5], # top 5 qualities
                "original_url": url
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download")
def download(url: str, quality: str = "best"):
    if not is_fb_url(url):
        raise HTTPException(status_code=400, detail="Invalid Facebook URL")

    ydl_opts = {
        'quiet': True,
        'format': f'best[height<={quality}]' if quality.isdigit() else 'best',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Get best URL
            download_url = info.get('url')
            if not download_url and info.get('formats'):
                download_url = sorted(info['formats'], key=lambda x: x.get('height') or 0, reverse=True)[0]['url']

            # Redirect to direct video URL for download
            return RedirectResponse(url=download_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
