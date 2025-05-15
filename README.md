#dj-booth

A simple web-based DJ request system built with Flask, YouTube scraping, and yt-dlp integration.  
Designed for house parties and events where guests can submit music requests in real-time.
Use index.html (base-url/) for guests, and admin.html (base-url/admin) for admin menu. 

---

## 🚀 Features

- 🔍 YouTube search interface for guests
- ✅ Admin panel with download and playback tracking
- 🎵 "Now Playing" display using VirtualDJ's history log
- 📥 Download requested tracks as MP3 via yt-dlp
- 🔁 Real-time request queue with status indicators
- 💻 Mobile-friendly UI
- 🎛️ Dark mode by default

Language is Hungarian, feel free to translate.

---

## 📸 Screenshots

- `assets/guest.png` – Guest view
- `assets/admin.png` – Admin panel

---

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- `ffmpeg` installed and available in PATH
- A `VirtualDJ` installation (Only for "Now Playing" - VDJ needs to be configured for 5-6s history tracking instead of default 45s) 
- `yt-dlp` installed via pip

```bash
pip install flask yt-dlp beautifulsoup4 googlesearch-python

☕ If you enjoy this project, consider [buying me a coffee](https://ko-fi.com/pradar123) – it helps a lot!
