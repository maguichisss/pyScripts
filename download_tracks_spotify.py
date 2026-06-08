#!/usr/bin/env python3
"""
Descargador de Playlists de Spotify con METADATOS COMPLETOS y exportación CSV (pandas)
Uso: python script.py "URL_DE_LA_PLAYLIST"
Requiere: spotipy, yt-dlp, ffmpeg, mutagen, requests, pandas
"""

import os
import re
import time
import argparse
import sqlite3
import yt_dlp
import spotipy
import requests
from unidecode import unidecode
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC, TCON, COMM, TPE2
from mutagen.mp3 import MP3

# ========== CONFIGURACIÓN ==========
SPOTIFY_CLIENT_ID = "X"
SPOTIFY_CLIENT_SECRET = "X"
DOWNLOAD_PATH = "~/descargas"  # Carpeta base
REDIRECT_URI = "http://127.0.0.1:8080"
# Los scopes definen los permisos que le pides al usuario:
SCOPE = "user-library-read"  # Solo lectura de tus canciones guardadas
# ===================================
ARTISTS = {}


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            #id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_name TEXT,
            artist_id TEXT,
            artist TEXT,
            track_id TEXT PRIMARY KEY,
            track_name TEXT,
            album_id TEXT,
            album TEXT,
            release_date TEXT,
            genres TEXT,
            track_number TEXT,
            total_tracks TEXT,
            url_spotify TEXT,
            artwork_url TEXT,
            artwork_path TEXT,
            youtube_search_query TEXT,
            is_downloaded INTEGER DEFAULT 0,
            downloaded_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def download_album_artwork(url, output_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
    except Exception as e:
        print(f"    ⚠️ Error al descargar carátula: {e}")
    return None

def download_track(track_name, artist_name, output_dir, track_info=None, artwork_url=None):
    """
    Descarga la caratula, retorna (success, search_query, cover_path)
    """
    search_query = f"{artist_name} {track_name} letra"
    safe_filename = sanitize_filename(f"{artist_name} - {track_name}")
    cover_path = None

    # Descargar caratula (archivo permanente)
    if artwork_url:
        cover_path = os.path.join(output_dir, f"{safe_filename}_cover.jpg")
        print(f"    🖼️  Guardando carátula permanente...")
        download_album_artwork(artwork_url, cover_path)

        return True, search_query, cover_path

    return False, search_query, ''

def get_track_full_info(sp, track):
    try:
        album = track['album']
        artist_id = track['artists'][0]['id']
        try:
            artist = ARTISTS[artist_id]
        except Exception as e:
            artist = sp.artist(artist_id)
            ARTISTS[artist_id] = artist
        genres = "|".join(artist.get('genres', []))
        track_url = track["external_urls"]["spotify"]

        track_info = {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'artist_album': ', '.join([a['name'] for a in album['artists']]),
            'album': album['name'],
            'release_date': album.get('release_date'),
            'genres': genres,
            'track_number': str(track.get('track_number', 0)),
            'total_tracks': str(album.get('total_tracks', 0)),
            'comment': f"Spotify URL: {track_url}",
        }
        artwork_url = album['images'][0]['url'] if album.get('images') else None
        return track_info, artwork_url
    except Exception as e:
        print(f"    ⚠️ No se pudo obtener información completa: {e}")
        return None, None

def download_spotify_playlist(playlist_url):

    if playlist_url:
        client_credentials = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials)
        playlist_id = playlist_url.split("/playlist/")[1].split("?")[0]
        playlist = sp.playlist(playlist_id)
        playlist_name = sanitize_filename(playlist["name"])
        output_dir = os.path.join(DOWNLOAD_PATH, playlist_name)

        print(f"\n📀 Playlist: {playlist['name']}")
        print(f"👤 Por: {playlist['owner']['display_name']}")
        print(f"🎵 Total canciones: {playlist['tracks']['total']}\n")
    else:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            cache_path=".spotify_token_cache" # Opcional: archivo para guardar el token
        ))
        playlist_name = "me_gusta"
        output_dir = os.path.join(DOWNLOAD_PATH, playlist_name)

    os.makedirs(output_dir, exist_ok=True)


    # Obtener todas las canciones
    tracks = []
    if playlist_url:
        results = sp.playlist_tracks(playlist_id)
    else:
        print("🔄 Obteniendo TODAS tus canciones guardadas... Puede tomar unos segundos.")
        #results = sp.current_user_saved_tracks(offset=300+110)
        results = sp.current_user_saved_tracks(offset=0)

    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Lista para acumular datos del CSV
    data_rows = []

    successful = 0
    for idx, item in enumerate(tracks, 1):
        track = item['track']
        if not track:
            continue

        track_name = track['name']
        artist_name = track['artists'][0]['name']
        track_id = track['id']

        print(f"\n[{idx}/{len(tracks)}] 🎤 {artist_name} - {track_name}")
        print(f"    🔍 Obteniendo metadatos de Spotify...")
        track_info, artwork_url = get_track_full_info(sp, track)

        if track_info:
            print(f"    📀 Álbum: {track_info['album']}")
            print(f"    📅 Año: {track_info['year']}")
            print(f"    🎸 Género: {track_info['genres']}")
            print(f"    🎚️ Pista: {track_info['track_number']}/{track_info['total_tracks']}")

        success, search_query, cover_path = download_track(
            track_name, artist_name, output_dir, track_info, artwork_url
        )

        # Crear registro para la DB/CSV
        row = {
            'playlist_name': playlist_name,
            'artist_id': track['artists'][0]["id"],
            'artist': artist_name,
            'track_id': track_id,
            'track_name': track_name,
            'album_id': track['album']["id"],
            'album': track_info.get('album') if track_info else '',
            'release_date': track_info.get('release_date') if track_info else '',
            'genres': track_info.get('genres') if track_info else '',
            'track_number': track_info.get('track_number') if track_info else '',
            'total_tracks': track_info.get('total_tracks') if track_info else '',
            'url_spotify': track_info.get('comment', '').split('\n')[0] if track_info else '',
            'artwork_url': artwork_url if artwork_url else '',
            'artwork_path': cover_path if cover_path else '',
            'youtube_search_query': search_query if search_query else '',
            'is_downloaded': False,
        }
        data_rows.append(row)

        if success:
            successful += 1
        else:
            print(f"    ❌ Falló la descarga")

        # Pequeña pausa opcional (descomentar si se desea)
        # time.sleep(2)

    # Guardar metadatos
    if args.csv:
        import pandas as pd
        df = pd.DataFrame(data_rows)
        csv_path = os.path.join(output_dir, "playlist_metadata.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"📊 Metadatos guardados en: {csv_path}")
    else:
        db_path = os.path.join(output_dir, "playlist_metadata.db")
        conn = init_db(db_path)
        conn.executemany("""
            INSERT OR IGNORE INTO tracks (
                playlist_name, artist_id, artist, track_id, track_name, album_id,
                album, release_date, genres, track_number, total_tracks, url_spotify,
                artwork_url, artwork_path, youtube_search_query, is_downloaded
            ) VALUES (
                :playlist_name, :artist_id, :artist, :track_id, :track_name, :album_id,
                :album, :release_date, :genres, :track_number, :total_tracks, :url_spotify,
                :artwork_url, :artwork_path, :youtube_search_query, :is_downloaded
            )
        """, data_rows)
        conn.commit()
        conn.close()
        print(f"📊 Metadatos guardados en: {db_path}")

    print(f"\n✅ Completado! {successful}/{len(tracks)} canciones descargadas")
    print(f"📁 Ubicación: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descargador de Playlists de Spotify con metadatos completos (SQLite por defecto, CSV con --csv)"
    )
    parser.add_argument("--playlist", "-p", help="URL de la playlist de Spotify", default=None)
    parser.add_argument("--output", "-o", help="Carpeta de descarga", default=DOWNLOAD_PATH)
    parser.add_argument("--csv", action="store_true", help="Exportar a CSV en lugar de SQLite")
    args = parser.parse_args()

    if args.output:
        DOWNLOAD_PATH = args.output

    print("🎵 Descargador de Playlists de Spotify con METADATOS COMPLETOS")
    print("=" * 60)
    print(f"📁 Carpeta de descarga: {DOWNLOAD_PATH}\n")

    download_spotify_playlist(args.playlist)



# descargar audio video youtube
#yt-dlp -x --audio-format mp3 https://www.youtube.com/watch?v=8DdHyaqIQko

# # Copiar solo metadatos (sin recodificar)
#ffmpeg -i origen_con_tags.mp3 -i destino_sin_tags.mp3 -map_metadata 0 -c copy destino_con_tags.mp3

# O sobreescribir los metadatos del destino
#ffmpeg -i origen_con_tags.mp3 -i destino_sin_tags.mp3 -map_metadata 0 -map_metadata:s:a 0 -c copy output.mp3

#ffmpeg -i $CONTAGS -i $SINTAGS -map_metadata 0 -map 1:a -c copy $LABUENA
#mv $LABUENA $SINTAGS
