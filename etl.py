import sqlite3
import pandas as pd
import requests
import time
import json
from datetime import datetime

def init_db():
    # Ajout d'un timeout long pour éviter les erreurs "database is locked"
    conn = sqlite3.connect('opensound.db', timeout=20)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracks'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(tracks)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'id' in columns:
            print("Ancien schéma détecté, suppression des tables...")
            cursor.execute("DROP TABLE IF EXISTS tracks")
            cursor.execute("DROP TABLE IF EXISTS charts")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            track_key TEXT PRIMARY KEY,
            title TEXT,
            artist TEXT,
            genre TEXT,
            duration_ms INTEGER,
            release_date TEXT,
            artist_origin TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS charts (
            date TEXT,
            rank INTEGER,
            track_key TEXT,
            PRIMARY KEY (date, rank)
        )
    ''')
    conn.commit()
    return conn

def get_itunes_metadata(title, artist):
    search_term = f"{title} {artist}"
    url = f"https://itunes.apple.com/search?term={search_term}&entity=song&limit=1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                track = results[0]
                return {
                    'genre': track.get('primaryGenreName'),
                    'duration_ms': track.get('trackTimeMillis'),
                    'release_date': track.get('releaseDate', '')[:10]
                }
    except:
        pass
    return None

def get_artist_origin(artist_name):
    url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{artist_name}&fmt=json"
    headers = {'User-Agent': 'OpenSoundAnalytics/1.0 ( contact@example.com )'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            artists = response.json().get('artists', [])
            if artists:
                area = artists[0].get('area', {})
                return area.get('name', artists[0].get('country', 'Inconnu'))
    except:
        pass
    return "Inconnu"

def fetch_historical_data(progress_callback=None):
    if progress_callback:
        progress_callback(0, 100, "Initialisation de la base de données...")
    
    conn = init_db()
    cursor = conn.cursor()
    
    try:
        if progress_callback:
            progress_callback(0, 100, "Téléchargement du dataset Billboard complet (cela prend quelques secondes)...")
            
        print("Téléchargement du dataset Billboard historique...")
        billboard_url = "https://raw.githubusercontent.com/mhollingshead/billboard-hot-100/main/all.json"
        try:
            response = requests.get(billboard_url)
            all_charts = response.json()
        except Exception as e:
            print(f"Erreur lors du téléchargement : {e}")
            return

        filtered_charts = []
        seen_months = set()
        
        if progress_callback:
            progress_callback(0, 100, "Filtrage des données pour la période 2015-2025...")
            
        for chart in all_charts:
            date_str = chart['date']
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            if 2015 <= dt.year <= 2025:
                month_key = f"{dt.year}-{dt.month:02d}"
                if month_key not in seen_months:
                    filtered_charts.append(chart)
                    seen_months.add(month_key)
        
        total_months = len(filtered_charts)
        total_tracks_to_process = total_months * 100
        print(f"Traitement de {total_months} mois de données...")
        
        processed_tracks = {}
        current_track_idx = 0
        
        for chart in filtered_charts:
            chart_date = chart['date']
            top_100 = chart['data'][:100]
            
            for item in top_100:
                rank = item.get('this_week') or item.get('rank')
                title = item.get('song') or item.get('title')
                artist = item['artist']
                track_key = f"{title} | {artist}".lower()
                
                cursor.execute('INSERT OR REPLACE INTO charts (date, rank, track_key) VALUES (?, ?, ?)',
                             (chart_date, rank, track_key))
                
                if track_key not in processed_tracks:
                    cursor.execute('SELECT track_key FROM tracks WHERE track_key = ?', (track_key,))
                    if not cursor.fetchone():
                        metadata = get_itunes_metadata(title, artist)
                        genre = metadata['genre'] if metadata else "Pop"
                        duration = metadata['duration_ms'] if metadata else 210000
                        release = metadata['release_date'] if metadata else chart_date
                        
                        origin = "Inconnu"
                        if len(processed_tracks) % 10 == 0:
                             origin = get_artist_origin(artist)
                        
                        cursor.execute('''
                            INSERT INTO tracks (track_key, title, artist, genre, duration_ms, release_date, artist_origin)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (track_key, title, artist, genre, duration, release, origin))
                        
                    processed_tracks[track_key] = True
                
                current_track_idx += 1
                
                if progress_callback and current_track_idx % 25 == 0:
                    progress_callback(
                        current_track_idx, 
                        total_tracks_to_process, 
                        f"Mois : {chart_date[:7]} | Enrichissement du titre {current_track_idx}/{total_tracks_to_process}"
                    )
            
            conn.commit()
            time.sleep(0.1)

        if progress_callback:
            progress_callback(100, 100, "Extraction et enrichissement terminés avec succès !")
            
    finally:
        # On s'assure que la connexion est TOUJOURS fermée, même s'il y a une erreur
        conn.close()
        print("Connexion à la base de données fermée.")

if __name__ == "__main__":
    fetch_historical_data()
