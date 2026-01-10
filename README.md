# 🎬 Video Downloader Pro

A powerful, modern web application for downloading videos from 1000+ websites including xHamster, Pornhub, YouTube, Vimeo, and many more.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

## ✨ Features

- 🌐 **1000+ Supported Sites** - Works with xHamster, Pornhub, XNXX, YouTube, Vimeo, Dailymotion, and more
- 📊 **Real-time Progress** - Visual progress bar with download statistics
- 🖼️ **Video Preview** - Shows thumbnail, title, duration, and metadata before downloading
- 📱 **Mobile Optimized** - Beautiful responsive design that works on all devices
- ⚡ **Fast & Reliable** - Powered by yt-dlp for robust video extraction
- 🎯 **No Ads** - Clean, ad-free interface
- 🔒 **Privacy First** - No data collection, all processing happens server-side
- 🆓 **Free & Open Source** - MIT licensed

## 🚀 Live Demo

Try it now: [Your Demo URL Here]

## 📸 Screenshots

<div align="center">
  <img src="https://via.placeholder.com/800x450/667eea/ffffff?text=Main+Interface" alt="Main Interface" width="45%">
  <img src="https://via.placeholder.com/800x450/764ba2/ffffff?text=Video+Preview" alt="Video Preview" width="45%">
</div>

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Video Extraction:** yt-dlp
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Deployment:** Render (Free tier)
- **Monitoring:** UptimeRobot

## 📋 Supported Platforms

### Adult Content
- xHamster
- Pornhub
- XNXX
- RedTube
- YouPorn
- XVideos
- Beeg
- And many more...

### General Content
- YouTube
- Vimeo
- Dailymotion
- Facebook
- Twitter/X
- Instagram
- TikTok
- Twitch

[See full list of 1000+ supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/video-downloader-pro.git
   cd video-downloader-pro
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open your browser**
   ```
   http://localhost:8000
   ```

## 🌐 Deployment

### Deploy on Render (Recommended)

1. Fork this repository
2. Sign up at [Render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Render will auto-detect `render.yaml` and deploy!

### Deploy on Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### Deploy on Fly.io

```bash
flyctl launch
flyctl deploy
```

## 📁 Project Structure

```
video-downloader-pro/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── render.yaml         # Render deployment config
├── README.md           # This file
├── LICENSE             # MIT license
└── .gitignore         # Git ignore rules
```

## 🔧 Configuration

### Environment Variables

No environment variables required! The app works out of the box.

### Customization

You can customize the UI by editing the HTML/CSS in `main.py` (line ~100):

```python
html_content = """
    <!-- Your custom HTML here -->
"""
```

## 📖 API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api` | GET | API information |
| `/health` | GET | Health check |
| `/info` | GET | Get video metadata |
| `/download` | GET | Download video |
| `/progress/{id}` | GET | Get download progress |

### Example API Usage

**Get video info:**
```bash
curl "http://localhost:8000/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Download video:**
```bash
curl "http://localhost:8000/download?url=VIDEO_URL" -o video.mp4
```

## 🤝 Contributing

We love contributions! Whether it's bug fixes, new features, or documentation improvements, we welcome them all.

### How to Contribute

1. **Fork the repository**
   
   Click the "Fork" button at the top right of this page.

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/video-downloader-pro.git
   cd video-downloader-pro
   ```

3. **Create a new branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

4. **Make your changes**
   
   Write your code, add tests if applicable.

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**
   
   Go to the original repository and click "New Pull Request"

### Contribution Ideas

Here are some ways you can contribute:

#### 🐛 Bug Fixes
- Fix download issues with specific sites
- Improve error handling
- Fix mobile responsiveness issues

#### ✨ New Features
- [ ] Add download history
- [ ] Support for playlists/channels
- [ ] Quality selector (720p, 1080p, etc.)
- [ ] Audio-only download option
- [ ] Batch download support
- [ ] Dark mode toggle
- [ ] Multi-language support
- [ ] Browser extension
- [ ] Desktop app (Electron)
- [ ] Download scheduler
- [ ] Subtitles download
- [ ] Format conversion (MP4, WebM, etc.)

#### 📚 Documentation
- Improve README
- Add API examples
- Create video tutorials
- Translate documentation
- Write deployment guides

#### 🎨 UI/UX Improvements
- Better mobile experience
- Accessibility improvements
- New themes/skins
- Better error messages
- Loading animations

#### 🧪 Testing
- Write unit tests
- Add integration tests
- Test on different platforms
- Performance testing

### Development Guidelines

- **Code Style:** Follow PEP 8 for Python code
- **Commits:** Use clear, descriptive commit messages
- **Documentation:** Update README if you add features
- **Testing:** Test your changes thoroughly
- **Issues:** Reference issue numbers in commits/PRs

### Good First Issues

Look for issues labeled `good first issue` or `beginner-friendly` to get started!

## 🐛 Bug Reports

Found a bug? Please open an issue with:

- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Your environment (OS, Python version, etc.)

## 💡 Feature Requests

Have an idea? Open an issue with:

- Clear description of the feature
- Use cases / why it's useful
- Possible implementation approach (optional)

## 📝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone.

### Expected Behavior

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy toward others

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Powerful video extraction tool
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Render](https://render.com/) - Easy deployment platform
- All our amazing contributors!

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/video-downloader-pro?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/video-downloader-pro?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/video-downloader-pro)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/video-downloader-pro)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/video-downloader-pro&type=Date)](https://star-history.com/#yourusername/video-downloader-pro&Date)

## 📞 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/video-downloader-pro/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/video-downloader-pro/discussions)
- **Email:** your.email@example.com
- **Twitter:** [@yourhandle](https://twitter.com/yourhandle)

## 🚀 Roadmap

### Version 2.0 (Q1 2025)
- [ ] Playlist support
- [ ] Download history
- [ ] User accounts (optional)
- [ ] API rate limiting

### Version 2.1 (Q2 2025)
- [ ] Browser extension (Chrome, Firefox)
- [ ] Mobile apps (Android, iOS)
- [ ] Batch downloads

### Version 3.0 (Q3 2025)
- [ ] Desktop app (Windows, Mac, Linux)
- [ ] Advanced video editing
- [ ] Cloud storage integration

## 🎉 Contributors

Thanks to all contributors!

<a href="https://github.com/yourusername/video-downloader-pro/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=yourusername/video-downloader-pro" />
</a>

---

<div align="center">

**Made with ❤️ by the community**

[⭐ Star us on GitHub](https://github.com/yourusername/video-downloader-pro) • [🐛 Report Bug](https://github.com/yourusername/video-downloader-pro/issues) • [✨ Request Feature](https://github.com/yourusername/video-downloader-pro/issues)

</div>
