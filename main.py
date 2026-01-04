from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
import subprocess
import tempfile
import os
import shutil
import yt_dlp

# Initialize FastAPI
app = FastAPI(title="xHamster Downloader API 🚀")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sanitize_filename(name: str) -> str:
    """Sanitize video title for safe filenames"""
    safe_name = re.sub(r'[^\w\s-]', '', name)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    safe_name = safe_name.strip()[:100]
    return safe_name + ".mp4"

def check_ytdlp():
    """Check if yt-dlp is available"""
    try:
        import yt_dlp
        return True
    except ImportError:
        return False

@app.get("/", response_class=HTMLResponse)
def root():
    # Serve the web interface as default page
    ytdlp_status = "✅ Installed" if check_ytdlp() else "❌ Not installed"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Downloader</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{ color: #333; margin-bottom: 10px; font-size: 28px; }}
            .subtitle {{ color: #666; margin-bottom: 30px; font-size: 14px; }}
            .status-badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 20px;
            }}
            .badge-success {{ background: #d4edda; color: #155724; }}
            .badge-error {{ background: #f8d7da; color: #721c24; }}
            .input-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 8px; color: #555; font-weight: 500; }}
            input {{
                width: 100%;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                transition: border 0.3s;
            }}
            input:focus {{ outline: none; border-color: #667eea; }}
            .button-group {{ display: flex; gap: 10px; margin-bottom: 20px; }}
            button {{
                flex: 1;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, opacity 0.2s;
            }}
            button:active {{ transform: scale(0.98); }}
            button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            .btn-primary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .btn-secondary {{ background: #f0f0f0; color: #333; }}
            .info-box {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
                display: none;
            }}
            .info-box.show {{ display: block; }}
            .info-item {{
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
            }}
            .info-label {{ color: #666; font-weight: 500; }}
            .info-value {{ color: #333; font-weight: 600; }}
            .status {{
                padding: 10px;
                border-radius: 8px;
                margin-top: 15px;
                text-align: center;
                font-weight: 500;
            }}
            .status.loading {{ background: #fff3cd; color: #856404; }}
            .status.success {{ background: #d4edda; color: #155724; }}
            .status.error {{ background: #f8d7da; color: #721c24; }}
            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 10px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            @media (max-width: 480px) {{
                .container {{ padding: 20px; }}
                h1 {{ font-size: 24px; }}
                .button-group {{ flex-direction: column; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Video Downloader</h1>
            <p class="subtitle">Download videos easily to your device</p>
            <div class="status-badge {'badge-success' if ytdlp_status == '✅ Installed' else 'badge-error'}">
                yt-dlp: {ytdlp_status}
            </div>
            
            <div class="input-group">
                <label for="videoUrl">Video URL</label>
                <input type="text" id="videoUrl" placeholder="Paste video URL here...">
            </div>
            
            <div class="button-group">
                <button class="btn-secondary" onclick="getInfo()">Get Info</button>
                <button class="btn-primary" onclick="downloadVideo()">Download</button>
            </div>
            
            <div id="infoBox" class="info-box"></div>
            <div id="status"></div>
        </div>

        <script>
            const API_URL = window.location.origin;
            
            function showStatus(message, type) {{
                const statusDiv = document.getElementById('status');
                statusDiv.className = `status ${{type}}`;
                statusDiv.innerHTML = message;
            }}
            
            async function getInfo() {{
                const url = document.getElementById('videoUrl').value.trim();
                if (!url) {{ showStatus('Please enter a video URL', 'error'); return; }}
                
                showStatus('<div class="spinner"></div> Fetching video info...', 'loading');
                
                try {{
                    const response = await fetch(`${{API_URL}}/info?url=${{encodeURIComponent(url)}}`);
                    const data = await response.json();
                    
                    if (response.ok) {{
                        const infoBox = document.getElementById('infoBox');
                        infoBox.className = 'info-box show';
                        infoBox.innerHTML = `
                            <div class="info-item">
                                <span class="info-label">Title:</span>
                                <span class="info-value">${{data.title}}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Method:</span>
                                <span class="info-value">${{data.method || 'yt-dlp'}}</span>
                            </div>
                        `;
                        showStatus('✅ Video info loaded successfully', 'success');
                    }} else {{
                        showStatus(`❌ Error: ${{data.detail}}`, 'error');
                    }}
                }} catch (error) {{
                    showStatus(`❌ Error: ${{error.message}}`, 'error');
                }}
            }}
            
            function downloadVideo() {{
                const url = document.getElementById('videoUrl').value.trim();
                if (!url) {{ showStatus('Please enter a video URL', 'error'); return; }}
                
                showStatus('<div class="spinner"></div> Starting download (may take 1-2 minutes)...', 'loading');
                
                const downloadUrl = `${{API_URL}}/download?url=${{encodeURIComponent(url)}}`;
                window.open(downloadUrl, '_blank');
                
                setTimeout(() => {{
                    showStatus('✅ Download started! This may take 1-2 minutes for the video to process.', 'success');
                }}, 1000);
            }}
            
            document.getElementById('videoUrl').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') downloadVideo();
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api")
def api_info():
    ytdlp_status = "✅ Installed" if check_ytdlp() else "❌ Not installed"
    return {
        "message": "xHamster Downloader API",
        "ytdlp_status": ytdlp_status,
        "method": "yt-dlp (bypasses anti-bot protection)",
        "endpoints": {
            "/": "Web interface",
            "/api": "API information",
            "/info": "Get video information",
            "/download": "Download video"
        }
    }

@app.get("/info")
def get_video_info(url: str = Query(..., description="xHamster video URL")):
    """Get video information using yt-dlp"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                "title": info.get('title', 'Unknown'),
                "duration": info.get('duration', 'Unknown'),
                "uploader": info.get('uploader', 'Unknown'),
                "method": "yt-dlp",
                "formats_available": len(info.get('formats', []))
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video info: {str(e)}")

@app.get("/download")
def download_video(url: str = Query(..., description="xHamster video URL")):
    """
    Download video using yt-dlp (bypasses anti-bot protection).
    yt-dlp acts like a real browser and handles cookies/tokens automatically.
    """
    
    if not check_ytdlp():
        raise HTTPException(
            status_code=500,
            detail="yt-dlp is not installed. Please install: pip install yt-dlp"
        )
    
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        print(f"[DEBUG] Downloading to: {temp_dir}")
        
        # yt-dlp options
        ydl_opts = {
            'format': 'best',  # Best quality
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'nocheckcertificate': True,
            # Add headers to mimic browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://xhamster.com/',
            }
        }
        
        # Download video
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                ext = info.get('ext', 'mp4')
                
            print(f"[DEBUG] Download completed: {title}")
            
        except Exception as e:
            shutil.rmtree(temp_dir)
            print(f"[ERROR] yt-dlp download failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Download failed: {str(e)}. The video may be private or geo-blocked."
            )
        
        # Find downloaded file
        downloaded_files = []
        for file in os.listdir(temp_dir):
            if file.endswith(('.mp4', '.mkv', '.webm', '.flv')):
                downloaded_files.append(file)
        
        if not downloaded_files:
            shutil.rmtree(temp_dir)
            raise HTTPException(
                status_code=500,
                detail="Download completed but no video file found."
            )
        
        file_path = os.path.join(temp_dir, downloaded_files[0])
        file_size = os.path.getsize(file_path)
        
        print(f"[DEBUG] File: {downloaded_files[0]} ({file_size / (1024*1024):.2f} MB)")
        
        # Get safe filename
        filename = sanitize_filename(title if 'title' in locals() else downloaded_files[0])
        
        # Stream file to user
        def iterfile():
            try:
                with open(file_path, 'rb') as f:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            finally:
                try:
                    shutil.rmtree(temp_dir)
                    print(f"[DEBUG] Cleaned up temp directory")
                except Exception as e:
                    print(f"[ERROR] Cleanup failed: {e}")
        
        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
