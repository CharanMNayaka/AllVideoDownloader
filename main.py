from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from xhamster_api import Client
import requests
import re
import subprocess
import tempfile
import os
import shutil

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

# Initialize xHamster client
client = Client()

def sanitize_filename(name: str) -> str:
    """Sanitize video title for safe filenames"""
    safe_name = re.sub(r'[^\w\s-]', '', name)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    safe_name = safe_name.strip()[:100]
    return safe_name + ".mp4"

def get_ffmpeg_command():
    """Get the ffmpeg command to use"""
    # Try PATH first
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return 'ffmpeg'
    except:
        pass
    
    # Try current directory
    local_ffmpeg = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    # Try common paths
    common_paths = [
        r'D:\ffmpeg-2025-12-31-git-38e89fe502-full_build\bin\ffmpeg.exe',
        r'C:\ffmpeg\bin\ffmpeg.exe',
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return 'ffmpeg'  # Fallback

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    # Check in PATH
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check in current directory
    local_ffmpeg = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        try:
            subprocess.run([local_ffmpeg, '-version'], capture_output=True, check=True)
            return True
        except:
            pass
    
    # Check in common installation paths
    common_paths = [
        r'D:\ffmpeg-2025-12-31-git-38e89fe502-full_build\bin\ffmpeg.exe',
        r'C:\ffmpeg\bin\ffmpeg.exe',
    ]
    for path in common_paths:
        if os.path.exists(path):
            try:
                subprocess.run([path, '-version'], capture_output=True, check=True)
                return True
            except:
                pass
    
    return False

def get_best_quality_m3u8(base_url: str) -> str:
    """Get the best quality M3U8 URL from base URL"""
    # The base URL template has _TPL_ which needs to be replaced
    # Try different qualities in order
    qualities = ['2160p', '1080p', '720p', '480p', '240p', '144p']
    
    for quality in qualities:
        m3u8_url = base_url.replace('_TPL_', quality)
        try:
            response = requests.head(m3u8_url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                print(f"[DEBUG] Found working quality: {quality}")
                return m3u8_url
        except:
            continue
    
    # If none work, try 720p as default
    return base_url.replace('_TPL_', '720p')

@app.get("/", response_class=HTMLResponse)
def root():
    # Serve the web interface as default page
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Downloader</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 { color: #333; margin-bottom: 10px; font-size: 28px; }
            .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
            .input-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
            input {
                width: 100%;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                transition: border 0.3s;
            }
            input:focus { outline: none; border-color: #667eea; }
            .button-group { display: flex; gap: 10px; margin-bottom: 20px; }
            button {
                flex: 1;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, opacity 0.2s;
            }
            button:active { transform: scale(0.98); }
            button:disabled { opacity: 0.5; cursor: not-allowed; }
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .btn-secondary { background: #f0f0f0; color: #333; }
            .info-box {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
                display: none;
            }
            .info-box.show { display: block; }
            .info-item {
                margin-bottom: 10px;
                display: flex;
                justify-content: space-between;
            }
            .info-label { color: #666; font-weight: 500; }
            .info-value { color: #333; font-weight: 600; }
            .status {
                padding: 10px;
                border-radius: 8px;
                margin-top: 15px;
                text-align: center;
                font-weight: 500;
            }
            .status.loading { background: #fff3cd; color: #856404; }
            .status.success { background: #d4edda; color: #155724; }
            .status.error { background: #f8d7da; color: #721c24; }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @media (max-width: 480px) {
                .container { padding: 20px; }
                h1 { font-size: 24px; }
                .button-group { flex-direction: column; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Video Downloader</h1>
            <p class="subtitle">Download videos easily to your device</p>
            
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
            
            function showStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.className = `status ${type}`;
                statusDiv.innerHTML = message;
            }
            
            async function getInfo() {
                const url = document.getElementById('videoUrl').value.trim();
                if (!url) { showStatus('Please enter a video URL', 'error'); return; }
                
                showStatus('<div class="spinner"></div> Fetching video info...', 'loading');
                
                try {
                    const response = await fetch(`${API_URL}/info?url=${encodeURIComponent(url)}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        const infoBox = document.getElementById('infoBox');
                        infoBox.className = 'info-box show';
                        infoBox.innerHTML = `
                            <div class="info-item">
                                <span class="info-label">Title:</span>
                                <span class="info-value">${data.title}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Format:</span>
                                <span class="info-value">${data.format || 'M3U8/HLS'}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Stars:</span>
                                <span class="info-value">${data.pornstars || 'Unknown'}</span>
                            </div>
                        `;
                        showStatus('✅ Video info loaded successfully', 'success');
                    } else {
                        showStatus(`❌ Error: ${data.detail}`, 'error');
                    }
                } catch (error) {
                    showStatus(`❌ Error: ${error.message}`, 'error');
                }
            }
            
            function downloadVideo() {
                const url = document.getElementById('videoUrl').value.trim();
                if (!url) { showStatus('Please enter a video URL', 'error'); return; }
                
                showStatus('<div class="spinner"></div> Starting download...', 'loading');
                
                const downloadUrl = `${API_URL}/download?url=${encodeURIComponent(url)}`;
                window.open(downloadUrl, '_blank');
                
                setTimeout(() => {
                    showStatus('✅ Download started! Check your downloads folder.', 'success');
                }, 1000);
            }
            
            document.getElementById('videoUrl').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') downloadVideo();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api")
def api_info():
    ffmpeg_status = "✅ Installed" if check_ffmpeg() else "❌ Not installed"
    return {
        "message": "xHamster Downloader API",
        "ffmpeg_status": ffmpeg_status,
        "endpoints": {
            "/": "Web interface",
            "/api": "API information (this page)",
            "/info": "Get video information",
            "/debug": "Debug video sources",
            "/m3u8-url": "Get M3U8 stream URL",
            "/download": "Download video"
        }
    }

@app.get("/info")
def get_video_info(url: str = Query(..., description="xHamster video URL")):
    """Get video information"""
    try:
        video = client.get_video(url)
        return {
            "title": video.title,
            "thumbnail": getattr(video, 'thumbnail', 'Unknown'),
            "pornstars": getattr(video, 'pornstars', 'Unknown'),
            "has_m3u8": hasattr(video, 'm3u8_base_url'),
            "format": "M3U8/HLS" if hasattr(video, 'm3u8_base_url') else "Unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video info: {str(e)}")

@app.get("/debug")
def debug_video(url: str = Query(..., description="xHamster video URL")):
    """Debug endpoint to see video data"""
    try:
        video = client.get_video(url)
        
        debug_info = {
            "title": video.title,
            "has_m3u8_base_url": hasattr(video, 'm3u8_base_url'),
            "has_download_method": hasattr(video, 'download'),
        }
        
        if hasattr(video, 'm3u8_base_url'):
            base_url = video.m3u8_base_url
            debug_info['m3u8_base_url'] = base_url
            debug_info['m3u8_note'] = "This is M3U8/HLS format. _TPL_ will be replaced with quality (720p, 1080p, etc.)"
            
            # Test which qualities are available
            qualities = ['2160p', '1080p', '720p', '480p', '240p', '144p']
            available = []
            for quality in qualities:
                test_url = base_url.replace('_TPL_', quality)
                try:
                    r = requests.head(test_url, timeout=3)
                    if r.status_code == 200:
                        available.append(quality)
                except:
                    pass
            debug_info['available_qualities'] = available
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/m3u8-url")
def get_m3u8_url(
    url: str = Query(..., description="xHamster video URL"),
    quality: str = Query("720p", description="Quality: 2160p, 1080p, 720p, 480p, 240p, 144p")
):
    """
    Get the M3U8 stream URL.
    You can use this URL with video players like VLC, mpv, or online players.
    """
    try:
        video = client.get_video(url)
        
        if not hasattr(video, 'm3u8_base_url'):
            raise HTTPException(status_code=404, detail="No M3U8 URL found for this video")
        
        base_url = video.m3u8_base_url
        m3u8_url = base_url.replace('_TPL_', quality)
        
        # Verify URL works
        try:
            response = requests.head(m3u8_url, timeout=5)
            if response.status_code != 200:
                # Try to find a working quality
                m3u8_url = get_best_quality_m3u8(base_url)
        except:
            m3u8_url = get_best_quality_m3u8(base_url)
        
        return {
            "title": video.title,
            "m3u8_url": m3u8_url,
            "quality": quality,
            "how_to_use": {
                "vlc": f"vlc {m3u8_url}",
                "mpv": f"mpv {m3u8_url}",
                "ffmpeg_download": f'ffmpeg -i "{m3u8_url}" -c copy output.mp4',
                "browser": "Paste URL in video player extensions"
            },
            "note": "M3U8 URLs may expire after some time"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

@app.get("/download")
def download_video(
    url: str = Query(..., description="xHamster video URL"),
    quality: str = Query("720p", description="Quality: 2160p, 1080p, 720p, 480p, 240p, 144p")
):
    """
    Download M3U8 video using ffmpeg.
    Requires ffmpeg to be installed on the system.
    """
    
    # Check if ffmpeg is available
    if not check_ffmpeg():
        raise HTTPException(
            status_code=500,
            detail="ffmpeg is not installed. Please install ffmpeg first. See / endpoint for instructions."
        )
    
    try:
        video = client.get_video(url)
        
        if not hasattr(video, 'm3u8_base_url'):
            raise HTTPException(status_code=404, detail="No video stream found")
        
        # Get M3U8 URL
        base_url = video.m3u8_base_url
        m3u8_url = get_best_quality_m3u8(base_url)
        
        print(f"[DEBUG] Downloading from: {m3u8_url}")
        
        # Create temp file
        temp_dir = tempfile.mkdtemp()
        filename = sanitize_filename(video.title)
        output_path = os.path.join(temp_dir, filename)
        
        print(f"[DEBUG] Saving to: {output_path}")
        
        # Download using ffmpeg
        ffmpeg_cmd = get_ffmpeg_command()
        print(f"[DEBUG] Using ffmpeg: {ffmpeg_cmd}")
        
        try:
            subprocess.run([
                ffmpeg_cmd,
                '-i', m3u8_url,
                '-c', 'copy',  # Copy without re-encoding (faster)
                '-bsf:a', 'aac_adtstoasc',  # Fix audio
                output_path
            ], check=True, capture_output=True, timeout=300)  # 5 min timeout
            
            print(f"[DEBUG] Download complete")
            
        except subprocess.TimeoutExpired:
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=504, detail="Download timeout (>5 minutes)")
        except subprocess.CalledProcessError as e:
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail=f"ffmpeg error: {e.stderr.decode()}")
        
        # Stream file back to user
        def iterfile():
            try:
                with open(output_path, 'rb') as f:
                    while chunk := f.read(1024*1024):  # 1MB chunks
                        yield chunk
            finally:
                # Cleanup
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/download-simple")
def download_simple(url: str = Query(..., description="xHamster video URL")):
    """
    Try to download using the library's built-in download method.
    May or may not work depending on the video.
    """
    try:
        video = client.get_video(url)
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Try using the library's download method
            video.download(downloader="threaded", quality="best", path=temp_dir)
            
            # Find downloaded file
            files = [f for f in os.listdir(temp_dir) if f.endswith('.mp4')]
            
            if not files:
                shutil.rmtree(temp_dir)
                raise HTTPException(status_code=500, detail="Download completed but no MP4 file found")
            
            file_path = os.path.join(temp_dir, files[0])
            filename = sanitize_filename(video.title)
            
            # Stream file
            def iterfile():
                try:
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(1024*1024):
                            yield chunk
                finally:
                    shutil.rmtree(temp_dir)
            
            return StreamingResponse(
                iterfile(),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'}
            )
            
        except Exception as e:
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail=f"Library download failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)