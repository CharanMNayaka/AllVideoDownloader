from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import re
import tempfile
import os
import shutil
import yt_dlp
import asyncio
from typing import Dict
import uuid

# Initialize FastAPI
app = FastAPI(title="Video Downloader API 🚀")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store download progress
download_progress: Dict[str, dict] = {}

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

def progress_hook(d, download_id):
    """Hook to track download progress"""
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)
        
        percent = (downloaded / total * 100) if total > 0 else 0
        
        download_progress[download_id] = {
            'status': 'downloading',
            'percent': round(percent, 1),
            'downloaded': downloaded,
            'total': total,
            'speed': speed,
            'eta': eta
        }
    elif d['status'] == 'finished':
        download_progress[download_id] = {
            'status': 'processing',
            'percent': 100,
            'message': 'Processing video...'
        }

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the web interface"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Video Downloader Pro</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 { color: #333; margin-bottom: 10px; font-size: 32px; }
            .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
            .status-badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 20px;
            }
            .badge-success { background: #d4edda; color: #155724; }
            .badge-error { background: #f8d7da; color: #721c24; }
            .badge-checking { background: #fff3cd; color: #856404; animation: pulse 2s infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
            
            .supported-sites {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .supported-sites h3 {
                font-size: 14px;
                color: #555;
                margin-bottom: 10px;
            }
            .site-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            .site-tag {
                background: white;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 12px;
                color: #667eea;
                font-weight: 500;
            }
            
            .input-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #555; font-weight: 600; }
            input {
                width: 100%;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                transition: all 0.3s;
            }
            input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
            
            .button-group { display: flex; gap: 10px; margin-bottom: 20px; }
            button {
                flex: 1;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
            button:active { transform: translateY(0); }
            button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .btn-secondary { background: #f0f0f0; color: #333; }
            
            .video-preview {
                display: none;
                background: #f8f9fa;
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
                border: 2px solid #e0e0e0;
            }
            .video-preview.show { display: block; animation: slideIn 0.3s ease; }
            @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
            
            .preview-content { display: flex; gap: 20px; }
            .preview-thumbnail {
                flex-shrink: 0;
                width: 200px;
                height: 112px;
                border-radius: 10px;
                object-fit: cover;
                background: #e0e0e0;
            }
            .preview-info { flex: 1; }
            .preview-title {
                font-size: 18px;
                font-weight: 600;
                color: #333;
                margin-bottom: 10px;
                line-height: 1.4;
            }
            .preview-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                font-size: 13px;
                color: #666;
            }
            .meta-item {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .progress-container {
                display: none;
                margin-bottom: 20px;
            }
            .progress-container.show { display: block; animation: slideIn 0.3s ease; }
            .progress-bar-bg {
                width: 100%;
                height: 10px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin-bottom: 10px;
            }
            .progress-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                transition: width 0.3s ease;
                width: 0%;
            }
            .progress-info {
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                color: #666;
            }
            
            .status {
                padding: 15px;
                border-radius: 10px;
                margin-top: 15px;
                text-align: center;
                font-weight: 500;
                display: none;
            }
            .status.show { display: block; animation: slideIn 0.3s ease; }
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
                vertical-align: middle;
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            
            @media (max-width: 768px) {
                .container { padding: 20px; }
                h1 { font-size: 24px; }
                .preview-content { flex-direction: column; }
                .preview-thumbnail { width: 100%; height: 180px; }
                .button-group { flex-direction: column; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Video Downloader Pro</h1>
            <p class="subtitle">Download videos from multiple platforms</p>
            
            <div id="serverStatus" class="status-badge badge-checking">
                <span class="spinner" style="width: 12px; height: 12px; border-width: 2px; margin-right: 5px;"></span>
                Checking server status...
            </div>
            
            <div class="supported-sites">
                <h3>📺 Supported Sites</h3>
                <div class="site-tags">
                    <span class="site-tag">xHamster</span>
                    <span class="site-tag">Pornhub</span>
                    <span class="site-tag">XNXX</span>
                    <span class="site-tag">RedTube</span>
                    <span class="site-tag">YouPorn</span>
                    <span class="site-tag">YouTube</span>
                    <span class="site-tag">Vimeo</span>
                    <span class="site-tag">Dailymotion</span>
                    <span class="site-tag">+ 1000 more</span>
                </div>
            </div>
            
            <div class="input-group">
                <label for="videoUrl">Video URL</label>
                <input type="text" id="videoUrl" placeholder="Paste video URL here...">
            </div>
            
            <div class="button-group">
                <button class="btn-secondary" onclick="getInfo()" id="infoBtn">
                    📋 Get Info
                </button>
                <button class="btn-primary" onclick="downloadVideo()" id="downloadBtn">
                    ⬇️ Download
                </button>
            </div>
            
            <div id="videoPreview" class="video-preview"></div>
            
            <div id="progressContainer" class="progress-container">
                <div class="progress-bar-bg">
                    <div id="progressBar" class="progress-bar-fill"></div>
                </div>
                <div class="progress-info">
                    <span id="progressText">Preparing download...</span>
                    <span id="progressPercent">0%</span>
                </div>
            </div>
            
            <div id="status" class="status"></div>
        </div>

        <script>
            const API_URL = window.location.origin;
            let currentDownloadId = null;
            
            // Check server status on load
            async function checkServerStatus() {
                const statusEl = document.getElementById('serverStatus');
                try {
                    const response = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(5000) });
                    if (response.ok) {
                        statusEl.className = 'status-badge badge-success';
                        statusEl.innerHTML = '✅ Server Online';
                    } else {
                        statusEl.className = 'status-badge badge-error';
                        statusEl.innerHTML = '❌ Server Error';
                    }
                } catch (error) {
                    statusEl.className = 'status-badge badge-checking';
                    statusEl.innerHTML = '⏳ Server Starting (30s)...';
                    // Retry after 30 seconds
                    setTimeout(checkServerStatus, 30000);
                }
            }
            
            function showStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.className = `status ${type} show`;
                statusDiv.innerHTML = message;
            }
            
            function hideStatus() {
                const statusDiv = document.getElementById('status');
                statusDiv.className = 'status';
            }
            
            function showProgress() {
                document.getElementById('progressContainer').className = 'progress-container show';
            }
            
            function hideProgress() {
                document.getElementById('progressContainer').className = 'progress-container';
                document.getElementById('progressBar').style.width = '0%';
            }
            
            function updateProgress(percent, text) {
                document.getElementById('progressBar').style.width = percent + '%';
                document.getElementById('progressPercent').textContent = percent + '%';
                document.getElementById('progressText').textContent = text;
            }
            
            async function getInfo() {
                const url = document.getElementById('videoUrl').value.trim();
                if (!url) {
                    showStatus('⚠️ Please enter a video URL', 'error');
                    return;
                }
                
                const infoBtn = document.getElementById('infoBtn');
                infoBtn.disabled = true;
                infoBtn.innerHTML = '<span class="spinner"></span> Loading...';
                
                showStatus('<span class="spinner"></span> Fetching video information...', 'loading');
                
                try {
                    const response = await fetch(`${API_URL}/info?url=${encodeURIComponent(url)}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        const preview = document.getElementById('videoPreview');
                        preview.className = 'video-preview show';
                        
                        const thumbnail = data.thumbnail || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="112"><rect fill="%23e0e0e0" width="200" height="112"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="%23999" font-family="Arial" font-size="14">No Preview</text></svg>';
                        
                        preview.innerHTML = `
                            <div class="preview-content">
                                <img src="${thumbnail}" class="preview-thumbnail" alt="Thumbnail" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22112%22><rect fill=%22%23e0e0e0%22 width=%22200%22 height=%22112%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22 font-family=%22Arial%22 font-size=%2214%22>No Preview</text></svg>'">
                                <div class="preview-info">
                                    <div class="preview-title">${data.title}</div>
                                    <div class="preview-meta">
                                        ${data.duration ? `<div class="meta-item">⏱️ ${formatDuration(data.duration)}</div>` : ''}
                                        ${data.uploader ? `<div class="meta-item">👤 ${data.uploader}</div>` : ''}
                                        ${data.view_count ? `<div class="meta-item">👁️ ${formatNumber(data.view_count)} views</div>` : ''}
                                        ${data.filesize ? `<div class="meta-item">📦 ${formatBytes(data.filesize)}</div>` : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        showStatus('✅ Video information loaded successfully', 'success');
                    } else {
                        showStatus(`❌ Error: ${data.detail}`, 'error');
                    }
                } catch (error) {
                    showStatus(`❌ Error: ${error.message}`, 'error');
                } finally {
                    infoBtn.disabled = false;
                    infoBtn.innerHTML = '📋 Get Info';
                }
            }
            
            async function downloadVideo() {
                const url = document.getElementById('videoUrl').value.trim();
                if (!url) {
                    showStatus('⚠️ Please enter a video URL', 'error');
                    return;
                }
                
                const downloadBtn = document.getElementById('downloadBtn');
                downloadBtn.disabled = true;
                downloadBtn.innerHTML = '<span class="spinner"></span> Downloading...';
                
                hideStatus();
                showProgress();
                currentDownloadId = 'download_' + Date.now();
                
                try {
                    // Start monitoring progress
                    const progressInterval = setInterval(async () => {
                        try {
                            const response = await fetch(`${API_URL}/progress/${currentDownloadId}`);
                            if (response.ok) {
                                const data = await response.json();
                                if (data.percent !== undefined) {
                                    updateProgress(data.percent, data.message || 'Downloading...');
                                }
                                if (data.status === 'completed' || data.status === 'error') {
                                    clearInterval(progressInterval);
                                }
                            }
                        } catch (e) {}
                    }, 1000);
                    
                    // Create hidden iframe to trigger download
                    const downloadUrl = `${API_URL}/download?url=${encodeURIComponent(url)}&download_id=${currentDownloadId}`;
                    const iframe = document.createElement('iframe');
                    iframe.style.display = 'none';
                    iframe.src = downloadUrl;
                    document.body.appendChild(iframe);
                    
                    // Simulate progress for user feedback
                    updateProgress(10, 'Connecting to server...');
                    await sleep(1000);
                    updateProgress(30, 'Fetching video data...');
                    await sleep(2000);
                    updateProgress(50, 'Downloading video...');
                    
                    // Wait for download to complete
                    setTimeout(() => {
                        clearInterval(progressInterval);
                        updateProgress(100, 'Download complete!');
                        showStatus('✅ Download started! Check your downloads folder.', 'success');
                        setTimeout(() => {
                            hideProgress();
                            downloadBtn.disabled = false;
                            downloadBtn.innerHTML = '⬇️ Download';
                        }, 2000);
                    }, 10000);
                    
                } catch (error) {
                    hideProgress();
                    showStatus(`❌ Error: ${error.message}`, 'error');
                    downloadBtn.disabled = false;
                    downloadBtn.innerHTML = '⬇️ Download';
                }
            }
            
            function formatDuration(seconds) {
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = Math.floor(seconds % 60);
                if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
                return `${m}:${s.toString().padStart(2, '0')}`;
            }
            
            function formatNumber(num) {
                if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
                if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
                return num;
            }
            
            function formatBytes(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
            }
            
            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }
            
            // Enter key support
            document.getElementById('videoUrl').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') downloadVideo();
            });
            
            // Check server status on load
            checkServerStatus();
            setInterval(checkServerStatus, 60000); // Check every minute
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api")
def api_info():
    """API information endpoint"""
    ytdlp_status = "✅ Installed" if check_ytdlp() else "❌ Not installed"
    return {
        "message": "Video Downloader API",
        "status": "online",
        "ytdlp_status": ytdlp_status,
        "supported_sites": "1000+ sites including xHamster, Pornhub, YouTube, Vimeo, etc.",
        "endpoints": {
            "/": "Web interface",
            "/api": "API information",
            "/health": "Health check",
            "/info": "Get video information",
            "/download": "Download video",
            "/progress/{id}": "Get download progress"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint for uptime monitoring"""
    return {"status": "ok", "service": "running", "ytdlp": check_ytdlp()}

@app.head("/health")
def health_check_head():
    """HEAD request support for uptime monitors"""
    return {}

@app.get("/info")
def get_video_info(url: str = Query(..., description="Video URL")):
    """Get video information using yt-dlp"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                "title": info.get('title', 'Unknown'),
                "duration": info.get('duration'),
                "uploader": info.get('uploader') or info.get('channel'),
                "thumbnail": info.get('thumbnail'),
                "view_count": info.get('view_count'),
                "filesize": info.get('filesize') or info.get('filesize_approx'),
                "description": info.get('description', '')[:200] + '...' if info.get('description') else None,
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video info: {str(e)}")

@app.get("/progress/{download_id}")
def get_progress(download_id: str):
    """Get download progress"""
    if download_id in download_progress:
        return download_progress[download_id]
    return {"status": "unknown", "percent": 0}

@app.get("/download")
def download_video(
    url: str = Query(..., description="Video URL"),
    download_id: str = Query(None, description="Download ID for progress tracking")
):
    """Download video using yt-dlp"""
    
    if not check_ytdlp():
        raise HTTPException(
            status_code=500,
            detail="yt-dlp is not installed"
        )
    
    if not download_id:
        download_id = str(uuid.uuid4())
    
    try:
        # Initialize progress
        download_progress[download_id] = {
            'status': 'starting',
            'percent': 0,
            'message': 'Starting download...'
        }
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        print(f"[DEBUG] Downloading to: {temp_dir}")
        
        # yt-dlp options
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'nocheckcertificate': True,
            'progress_hooks': [lambda d: progress_hook(d, download_id)],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        }
        
        # Download video
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                
            download_progress[download_id] = {
                'status': 'completed',
                'percent': 100,
                'message': 'Download complete!'
            }
            
        except Exception as e:
            shutil.rmtree(temp_dir)
            download_progress[download_id] = {
                'status': 'error',
                'percent': 0,
                'message': str(e)
            }
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
        
        # Find downloaded file
        downloaded_files = []
        for file in os.listdir(temp_dir):
            if file.endswith(('.mp4', '.mkv', '.webm', '.flv', '.avi')):
                downloaded_files.append(file)
        
        if not downloaded_files:
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail="No video file found")
        
        file_path = os.path.join(temp_dir, downloaded_files[0])
        file_size = os.path.getsize(file_path)
        
        filename = sanitize_filename(title if 'title' in locals() else downloaded_files[0])
        
        # Stream file to user
        def iterfile():
            try:
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        yield chunk
            finally:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                # Clean up progress after some time
                import threading
                threading.Timer(300, lambda: download_progress.pop(download_id, None)).start()
        
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
        download_progress[download_id] = {
            'status': 'error',
            'percent': 0,
            'message': str(e)
        }
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
