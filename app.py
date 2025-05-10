from flask import Flask, render_template, request, redirect, jsonify
from googlesearch import search
import requests as req
from bs4 import BeautifulSoup
import os
import yt_dlp
import json
import re

app = Flask(__name__)
requests_list = []
now_playing = "Nincs most játszott zene"
DOWNLOAD_DIR = "setlist"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def parse_duration(iso_duration):
    match = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return "ismeretlen"
    minutes = int(match.group(1)) if match.group(1) else 0
    seconds = int(match.group(2)) if match.group(2) else 0
    return f"{minutes}:{seconds:02d}"

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

                # Keresd meg az összes JSON-LD blokkot
                json_ld_blocks = soup.find_all("script", type="application/ld+json")
                duration = "ismeretlen"

                for block in json_ld_blocks:
                    try:
                        data = json.loads(block.string)
                        # Ha ez egy dict és tartalmaz duration-t
                        if isinstance(data, dict) and "duration" in data:
                            iso = data["duration"]
                            match = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', iso)
                            if match:
                                minutes = int(match.group(1)) if match.group(1) else 0
                                seconds = int(match.group(2)) if match.group(2) else 0
                                duration = f"{minutes}:{seconds:02d}"
                                break  # ha már találtunk érvényeset, elég
                    except Exception:
                        continue  # ha hibás JSON vagy nem releváns blokk, átugorjuk

                results.append({
                    'title': title,
                    'url': url,
                    'thumbnail': thumbnail,
                    'duration': duration
                })

            except Exception as e:
                print(f"Hiba feldolgozás közben: {e}")

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
    requests_list[index]['status'] = 'played'
    return ('', 204)

@app.route('/download', methods=['POST'])
def download():
    index = int(request.form['index'])
    request_item = requests_list[index]
    request_item['status'] = 'downloading'

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
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
        print(f"Hiba a letöltésnél: {e}")
        request_item['status'] = 'error'

    return ('', 204)

@app.route('/nowplaying')
def nowplaying():
    try:
        path = r"C:\Users\zambo\AppData\Local\VirtualDJ\History\tracklist.txt"
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Zenesorok kiszűrése
        track_lines = [line for line in lines if line.strip() and ':' in line and not line.startswith("VirtualDJ")]

        if not track_lines:
            return jsonify({'now_playing': 'Nincs zene a historyban'})

        last_track = track_lines[-1].strip()
        _, title = last_track.split(":", 1)
        return jsonify({'now_playing': title.strip()})

    except Exception as e:
        return jsonify({'now_playing': f"Hiba: {e}"})

if __name__ == '__main__':
    print("Flask indul...")
    app.run(debug=True, host='0.0.0.0')
