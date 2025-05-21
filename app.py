from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp as youtube_dl
import os
import threading
import random
import requests

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
completed_downloads = {}

# Dictionary of country-specific music genres
COUNTRY_GENRES = {
    'ZW': {  # Zimbabwe
        'genres': [
            'Zimdancehall',
            'Chimurenga',
            'Jit',
            'Sungura',
            'Afro Jazz',
            'Gospel',
            'Urban Grooves',
            'Traditional',
            'Mbira',
            'Rhumba'
        ],
        'trending_terms': ['Zimbabwe music', 'Zim music', 'Harare music']
    },
    'ZA': {  # South Africa
        'genres': [
            'Amapiano',
            'Gqom',
            'Kwaito',
            'Afro House',
            'Maskandi',
            'Gospel',
            'Afro Pop',
            'Traditional',
            'Jazz',
            'Hip Hop'
        ],
        'trending_terms': ['South African music', 'SA music', 'Johannesburg music']
    },
    'NG': {  # Nigeria
        'genres': [
            'Afrobeats',
            'Highlife',
            'Juju',
            'Fuji',
            'Gospel',
            'Afro Pop',
            'Traditional',
            'Hip Hop',
            'R&B',
            'Reggae'
        ],
        'trending_terms': ['Nigerian music', 'Naija music', 'Lagos music']
    },
    'KE': {  # Kenya
        'genres': [
            'Benga',
            'Gospel',
            'Afro Pop',
            'Traditional',
            'Hip Hop',
            'R&B',
            'Reggae',
            'Taarab',
            'Kapuka',
            'Genge'
        ],
        'trending_terms': ['Kenyan music', 'Nairobi music', 'East African music']
    },
    'GH': {  # Ghana
        'genres': [
            'Highlife',
            'Hiplife',
            'Gospel',
            'Afro Pop',
            'Traditional',
            'Hip Hop',
            'R&B',
            'Reggae',
            'Azonto',
            'Ghanaian Jazz'
        ],
        'trending_terms': ['Ghanaian music', 'Accra music', 'West African music']
    }
}

# Global trending terms for worldwide content
GLOBAL_TRENDING_TERMS = [
    'global music hits',
    'worldwide trending music',
    'international music charts',
    'top music videos',
    'viral music',
    'popular music',
    'music trends',
    'global hits',
    'international hits',
    'world music'
]

# Default genres if country not found
DEFAULT_GENRES = {
    'genres': [
        'Pop',
        'Rock',
        'Hip Hop',
        'Electronic',
        'Classical',
        'Jazz',
        'Country',
        'R&B',
        'Metal',
        'Folk'
    ],
    'trending_terms': ['music', 'trending music', 'popular music']
}

def get_user_country():
    try:
        # Get IP address from request
        ip = request.remote_addr
        if ip == '127.0.0.1':  # For local development
            return 'ZW'  # Default to Zimbabwe for testing
        
        # Use ipinfo.io to get country code
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            country_code = data.get('country', 'ZW')
            # Verify if we have genres for this country
            if country_code in COUNTRY_GENRES:
                return country_code
    except:
        pass
    return 'ZW'  # Default to Zimbabwe if detection fails

@app.route('/')
def index():
    country_code = get_user_country()
    country_genres = COUNTRY_GENRES.get(country_code, DEFAULT_GENRES)
    return render_template('index.html', 
                         genres=country_genres['genres'],
                         country_code=country_code)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    language = request.form.get('language', 'en')
    genre = request.form.get('genre', 'all')
    country_code = get_user_country()
    country_genres = COUNTRY_GENRES.get(country_code, DEFAULT_GENRES)

    if not query:
        return jsonify({"status": "error", "message": "No query provided!"}), 400

    # Map language codes to YouTube's language codes
    language_map = {
        'en': 'en',
        'sn': 'sn'  # Shona
    }
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'extract_flat': 'in_playlist',
        'lang': language_map.get(language, 'en')
    }

    try:
        # Add language and genre to search query if specified
        search_query = query
        if genre != 'all':
            search_query = f"{query} {genre} music"
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch50:{search_query}", download=False)['entries']
            videos = [{
                'title': v.get('title'),
                'url': f"https://www.youtube.com/watch?v={v.get('id')}",
                'thumbnail': f"https://i.ytimg.com/vi/{v.get('id')}/hqdefault.jpg",
                'id': v.get('id')
            } for v in results]

        return jsonify({"status": "success", "results": videos})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/trending')
def trending():
    try:
        genre = request.args.get('genre', 'all')
        language = request.args.get('language', 'en')
        country_code = get_user_country()
        country_genres = COUNTRY_GENRES.get(country_code, DEFAULT_GENRES)
        
        # Map language codes to YouTube's language codes
        language_map = {
            'en': 'en',
            'sn': 'sn'  # Shona
        }
        
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'noplaylist': True,
            'extract_flat': 'in_playlist',
            'lang': language_map.get(language, 'en')
        }

        trending_videos = []
        
        if genre == 'all':
            # Use global trending terms for worldwide content
            search_terms = GLOBAL_TRENDING_TERMS
        else:
            # Use the selected genre with global context
            search_terms = [f"{genre} music global", f"{genre} music worldwide", f"{genre} music international"]

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            for term in search_terms:
                try:
                    results = ydl.extract_info(f"ytsearch10:{term}", download=False)['entries']
                    for v in results:
                        trending_videos.append({
                            'title': v.get('title'),
                            'url': f"https://www.youtube.com/watch?v={v.get('id')}",
                            'thumbnail': f"https://i.ytimg.com/vi/{v.get('id')}/hqdefault.jpg",
                            'genre': genre.split()[0].title() if genre != 'all' else 'Global'
                        })
                except Exception as e:
                    print(f"Error fetching results for term {term}: {str(e)}")
                    continue

        # Shuffle and limit to 12 videos
        random.shuffle(trending_videos)
        trending_videos = trending_videos[:12]

        return jsonify({
            "status": "success", 
            "results": trending_videos,
            "country_code": country_code
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    format_type = request.form.get('format', 'video')

    if not url:
        return jsonify({"status": "error", "message": "No URL provided!"}), 400

    def thread_callback(data):
        if data['status'] == 'finished':
            completed_downloads['last'] = data

    threading.Thread(target=download_video, args=(url, format_type, thread_callback), daemon=True).start()
    return jsonify({"status": "success", "message": "Download started!"})

def download_video(url, format_type, callback):
    try:
        if format_type == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [callback],
            }
        else:
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'progress_hooks': [callback],
            }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            callback({'status': 'finished', 'video_title': info_dict['title'], 'video_filename': os.path.basename(filename)})

    except Exception as e:
        callback({'status': 'error', 'message': str(e)})

@app.route('/check-completed')
def check_completed():
    last_download = completed_downloads.get('last')
    if last_download:
        return jsonify({
            "status": "finished",
            "filename": last_download['video_filename'],
            "path": f"/download/{last_download['video_filename']}"
        })
    else:
        return jsonify({"status": "pending"})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=False)

