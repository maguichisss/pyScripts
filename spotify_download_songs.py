"""
Descargador de Playlists de Spotify con METADATOS COMPLETOS
Uso: python script.py "URL_DE_LA_PLAYLIST"
Requiere: spotipy, yt-dlp, ffmpeg, mutagen, requests
"""

import os
import re
import time
import argparse
import yt_dlp
import spotipy
import requests
from io import BytesIO
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC, TCON, COMM, TPE2
from mutagen.mp3 import MP3

# ========== CONFIGURACIoN ==========
SPOTIFY_CLIENT_ID = "X"
SPOTIFY_CLIENT_SECRET = "Y"
DOWNLOAD_PATH = "~/descargas"  # Carpeta donde se guardaran los MP3
# ===================================

def sanitize_filename(filename):
    """Elimina caracteres no validos para nombres de archivo"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def get_album_artwork(album_data):
    """Obtiene la URL de la imagen del album (la de mayor resolucion)"""
    if album_data and 'images' in album_data and album_data['images']:
        return album_data['images'][0]['url']
    return None

def download_album_artwork(url, output_path):
    """Descarga la imagen de la caratula del album"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
    except Exception as e:
        print(f"    ⚠️ Error al descargar caratula: {e}")
    return None

def add_metadata_to_mp3(file_path, track_info, artwork_path=None):
    """
    Agrega metadatos completos a un archivo MP3 usando mutagen
    """
    try:
        # Cargar tags existentes o crear nuevos
        try:
            tags = ID3(file_path)
        except:
            tags = ID3()

        # Titulo de la cancion
        if track_info.get('title'):
            tags.add(TIT2(encoding=3, text=track_info['title']))

        # Artista principal
        if track_info.get('artist'):
            tags.add(TPE1(encoding=3, text=track_info['artist']))

        # Artista del album (si es diferente)
        if track_info.get('artist_album'):
            tags.add(TPE2(encoding=3, text=track_info['artist_album']))

        # album
        if track_info.get('album'):
            tags.add(TALB(encoding=3, text=track_info['album']))

        # Año de lanzamiento
        if track_info.get('year'):
            tags.add(TDRC(encoding=3, text=str(track_info['year'])))

        # Genero
        if track_info.get('genre'):
            tags.add(TCON(encoding=3, text=track_info['genre']))

        # Numero de pista (formato: "3/15")
        if track_info.get('track_number'):
            track_str = track_info['track_number']
            if track_info.get('total_tracks'):
                track_str = f"{track_info['track_number']}/{track_info['total_tracks']}"
            tags.add(TRCK(encoding=3, text=track_str))

        # Comentario
        if track_info.get('comment'):
            tags.add(COMM(encoding=3, lang='spa', desc='Comentario', text=track_info['comment']))

        # Caratula del album
        if artwork_path and os.path.exists(artwork_path):
            with open(artwork_path, 'rb') as f:
                tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # portada frontal
                    desc='Cover',
                    data=f.read()
                ))
            print(f"    🖼️  Caratula agregada")

        # Guardar los cambios
        tags.save(file_path, v2_version=3)
        print(f"    ✅ Metadatos agregados correctamente")
        return True

    except Exception as e:
        print(f"    ⚠️ Error al agregar metadatos: {e}")
        return False

def download_track(track_name, artist_name, output_dir, track_info=None, artwork_url=None):
    """Busca y descarga una cancion desde YouTube, luego agrega metadatos"""
    search_query = f"{artist_name} {track_name} letra"

    # Generar nombre de archivo seguro
    safe_filename = sanitize_filename(f"{artist_name} - {track_name}")
    temp_template = os.path.join(output_dir, f"{safe_filename}.%(ext)s")

    ydl_opts = {
        'format': 'best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': temp_template,
        'quiet': True,
        'no_warnings': True,
        'cookiesfrombrowser': ('firefox',),
        'ignoreerrors': True,  # Ignora errores y continúa
        'extract_flat': False,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            try:
                info = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                print(info)
                if 'entries' in info and info['entries']:
                    youtube_url = info['entries'][0].get('webpage_url')
            except Exception as e:
                print(f"  Error al obtener URL: {e}")
                youtube_url = ""

            ydl.download([f"ytsearch1:{search_query}"])

            # El archivo final tendra extension .mp3
            final_file = os.path.join(output_dir, f"{safe_filename}.mp3")

            # Descargar caratula si es necesario
            artwork_file = None
            if artwork_url:
                artwork_file = os.path.join(output_dir, f"{safe_filename}_cover.jpg")
                print(f"    🖼️  Descargando caratula...")
                download_album_artwork(artwork_url, artwork_file)

            # Agregar metadatos si estan disponibles
            if track_info and os.path.exists(final_file):
                print(f"    📝 Agregando metadatos...")
                track_info["comment"] += f"\nYoutube url: {youtube_url}"
                add_metadata_to_mp3(final_file, track_info, artwork_file)

            # Limpiar archivo temporal de caratula
            if artwork_file and os.path.exists(artwork_file):
                os.remove(artwork_file)

                return True
        except Exception as e:
            print(f"    ❌ Error al descargar: {e}")
            return False

def get_track_full_info(sp, track_id):
    """Obtiene informacion detallada de una cancion desde Spotify"""
    try:
        track = sp.track(track_id)
        album = sp.album(track['album']['id'])

        # Obtener generos del artista (si estan disponibles)
        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)
        genres = artist.get('genres', [])
        genre = genres[0] if genres else 'Pop'
        track_url = track["external_urls"]["spotify"]

        # Construir informacion completa
        track_info = {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'artist_album': ', '.join([a['name'] for a in album['artists']]),
            'album': album['name'],
            'year': album.get('release_date'),
            'genre': genre,
            'track_number': str(track.get('track_number', 0)),
            'total_tracks': str(album.get('total_tracks', 0)),
            'comment': f"Spotify ID: {track_url}",
        }

        # URL de la caratula
        artwork_url = None
        if album.get('images'):
            artwork_url = album['images'][0]['url']

        return track_info, artwork_url

    except Exception as e:
        print(f"    ⚠️ No se pudo obtener informacion completa: {e}")
        return None, None

def download_spotify_playlist(playlist_url):
    """Descarga todas las canciones de una playlist con metadatos completos"""

    # Configurar cliente de Spotify
    client_credentials = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials)

    # Extraer ID de la playlist
    playlist_id = playlist_url.split("/playlist/")[1].split("?")[0]

    # Obtener informacion de la playlist
    playlist = sp.playlist(playlist_id)
    playlist_name = sanitize_filename(playlist["name"])

    # Crear carpeta de descarga
    output_dir = os.path.join(DOWNLOAD_PATH, playlist_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n📀 Playlist: {playlist['name']}")
    print(f"👤 Por: {playlist['owner']['display_name']}")
    print(f"🎵 Total canciones: {playlist['tracks']['total']}\n")

    # Obtener todas las canciones (manejando paginacion)
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results['items'])

    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    # Descargar cada cancion
    successful = 0
    for idx, item in enumerate(tracks, 1):
        track = item['track']
        if not track:
            continue

        track_name = track['name']
        artist_name = track['artists'][0]['name']
        track_id = track['id']

        print(f"\n[{idx}/{len(tracks)}] 🎤 {artist_name} - {track_name}")

        # Obtener informacion detallada desde Spotify
        print(f"    🔍 Obteniendo metadatos de Spotify...")
        track_info, artwork_url = get_track_full_info(sp, track_id)

        if track_info:
            print(f"    📀 album: {track_info['album']}")
            print(f"    📅 Año: {track_info['year']}")
            print(f"    🎸 Genero: {track_info['genre']}")
            print(f"    🎚️ Pista: {track_info['track_number']}/{track_info['total_tracks']}")

        if download_track(track_name, artist_name, output_dir, track_info, artwork_url):
            successful += 1
        else:
            print(f"    ❌ Fallo la descarga")

        #time.sleep(2)  # Pequeña pausa entre descargas

    print(f"\n✅ Completado! {successful}/{len(tracks)} canciones descargadas")
    print(f"📁 Ubicacion: {output_dir}")

if __name__ == "__main__":
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(
        description="Descargador de Playlists de Spotify con metadatos completos",
        epilog="Ejemplo: python script.py 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M'"
    )
    parser.add_argument(
        "playlist_url",
        help="URL de la playlist de Spotify (ej: https://open.spotify.com/playlist/...)",
        type=str
    )
    parser.add_argument(
        "--output", "-o",
        help="Carpeta de descarga (por defecto: ./descargas)",
        default=DOWNLOAD_PATH,
        type=str
    )
    parser.add_argument(
        "--quiet", "-q",
        help="Modo silencioso (menos output)",
        action="store_true"
    )

    args = parser.parse_args()

    # Actualizar la ruta de descarga si se proporciono
    if args.output:
        DOWNLOAD_PATH = args.output

    # Mostrar informacion inicial (si no esta en modo silencioso)
    if not args.quiet:
        print("🎵 Descargador de Playlists de Spotify con METADATOS COMPLETOS")
        print("=" * 55)
        print(f"📁 Carpeta de descarga: {DOWNLOAD_PATH}")
        print()

    # Ejecutar la descarga con la URL proporcionada
    download_spotify_playlist(args.playlist_url)




# descargar audio video youtube
#yt-dlp -x --audio-format mp3 https://www.youtube.com/watch?v=8DdHyaqIQko

# # Copiar solo metadatos (sin recodificar)
#ffmpeg -i origen_con_tags.mp3 -i destino_sin_tags.mp3 -map_metadata 0 -c copy destino_con_tags.mp3

# O sobreescribir los metadatos del destino
#ffmpeg -i origen_con_tags.mp3 -i destino_sin_tags.mp3 -map_metadata 0 -map_metadata:s:a 0 -c copy output.mp3

#ffmpeg -i $CONTAGS -i $SINTAGS -map_metadata 0 -map 1:a -c copy $LABUENA
#mv $LABUENA $SINTAGS
