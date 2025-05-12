from flask import Flask, render_template, request, redirect, jsonify
from googlesearch import search
import requests as req
from bs4 import BeautifulSoup
import os
import yt_dlp
import json
import re

app = Flask(__name__)

# Load config at startup or use defaults
CONFIG_PATH = 'config.json'
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "vdj_enabled": False,
        "vdj_path": r"C:\\Users\\zambo\\AppData\\Local\\VirtualDJ\\History\\tracklist.txt",
        "download_dir": "setlist"
    }

config = load_config()
requests_list = []
now_playing = "Nincs most játszott zene"

os.makedirs(config['download_dir'], exist_ok=True)

# Parse ISO 8601 duration format (e.g. PT3M12S) to mm:ss string
def parse_duration(iso_duration):
    match = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return "ismeretlen"
    minutes = int(match.group(1)) if match.group(1) else 0
    seconds = int(match.group(2)) if match.group(2) else 0
    return f"{minutes}:{seconds:02d}"

# Perform a YouTube search using googlesearch and scrape video info
def search_youtube(query, limit=5):
    search_results = search(f"site:youtube.com {query}", num_results=limit)
    results = []
    for url in search_results:
        if "watch?v=" in url:
            try:
                page = req.get(url)
                soup = BeautifulSoup(page.content, 'html.parser')
                title = soup.find('title').text.replace(" - YouTube", "")
                video_id = url.split("watch?v=")[1].split("&")[0]
                thumbnail = f"https://img.youtube.com/vi/{video_id}/0.jpg"

                json_ld_blocks = soup.find_all("script", type="application/ld+json")
                duration = "ismeretlen"
                for block in json_ld_blocks:
                    try:
                        data = json.loads(block.string)
                        if isinstance(data, dict) and "duration" in data:
                            iso = data["duration"]
                            duration = parse_duration(iso)
                            break
                    except: continue

                results.append({
                    'title': title,
                    'url': url,
                    'thumbnail': thumbnail,
                    'duration': duration
                })
            except Exception as e:
                print(f"Error processing YouTube result: {e}")
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        query = request.form['query']
        results = search_youtube(query)
    return render_template('index.html', results=results)

@app.route('/request', methods=['POST'])
def add_request():
    title = request.form['title']
    url = request.form['url']
    requests_list.append({'title': title, 'url': url, 'status': 'pending'})
    return redirect('/')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/get_requests')
def get_requests():
    return jsonify(requests_list)

@app.route('/mark_played', methods=['POST'])
def mark_played():
    index = int(request.form['index'])
    if 0 <= index < len(requests_list):
        requests_list[index]['status'] = 'played'
    return ('', 204)

@app.route('/remove_request', methods=['POST'])
def remove_request():
    index = int(request.form['index'])
    if 0 <= index < len(requests_list):
        if requests_list[index]['status'] not in ['played', 'downloading']:
            del requests_list[index]
    return ('', 204)

@app.route('/download', methods=['POST'])
def download():
    index = int(request.form['index'])
    request_item = requests_list[index]
    request_item['status'] = 'downloading'

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(config['download_dir'], '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request_item['url']])
        request_item['status'] = 'done'
    except Exception as e:
        print(f"Download error: {e}")
        request_item['status'] = 'error'

    return ('', 204)

@app.route('/nowplaying')
def nowplaying():
    if not config.get("vdj_enabled"):
        return jsonify({'now_playing': '---'})
    try:
        path = config.get("vdj_path")
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        track_lines = [line for line in lines if line.strip() and ':' in line and not line.startswith("VirtualDJ")]
        if not track_lines:
            return jsonify({'now_playing': 'No track history found'})
        last_track = track_lines[-1].strip()
        _, title = last_track.split(":", 1)
        return jsonify({'now_playing': title.strip()})
    except Exception as e:
        return jsonify({'now_playing': f"Error: {e}"})

@app.route('/get_config')
def get_config():
    return jsonify(config)

@app.route('/save_config', methods=['POST'])
def save_config():
    global config
    config = request.get_json()
    os.makedirs(config['download_dir'], exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return ('', 204)

if __name__ == '__main__':
    print("Flask starting...")
    app.run(debug=False, host='0.0.0.0', port=5050)
