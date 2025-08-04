import json
import argparse
import time
import logging
from ytmusicapi import YTMusic, OAuthCredentials
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

env = dotenv_values(".env")


def load_playlists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["playlists"]


def spotify_track_to_song(track):
    return {
        "title": track["name"],
        "artists": [artist["name"] for artist in track["artists"]]
    }


def search_song(ytmusic, song):
    query = f"{song['title']} {', '.join(song['artists'])}"
    results = ytmusic.search(query, filter="songs", limit=5)
    return results


def print_results(results):
    for i, r in enumerate(results):
        title = r.get("title")
        artists = ", ".join([a["name"] for a in r.get("artists", [])])
        album = r.get("album", {}).get("name", "Unknown Album")
        duration = r.get("duration", "Unknown")
        print(f"[{i}] {title} – {artists} | Album: {album} | Duration: {duration}")


def interactive_add_tracks(ytmusic, tracks):
    video_ids = []
    for i, item in enumerate(tracks):
        if item.get("is_local", False):
            print(f"⏭ Skipping local track: {item['track']['name']}")
            continue

        song = spotify_track_to_song(item["track"])
        print(f"\n🔍 [{i+1}/{len(tracks)}] Searching: {song['title']} – {', '.join(song['artists'])}")
        results = search_song(ytmusic, song)
        if not results:
            print("❌ No results found.")
            continue

        print_results(results)
        choice = input(
            "Select song number to add to playlist (or press Enter to skip): "
        ).strip()
        if choice.isdigit():
            index = int(choice)
            if 0 <= index < len(results):
                video_id = results[index].get("videoId")
                if video_id:
                    video_ids.append(video_id)
                    print(f"✅ Selected: {results[index]['title']}")
                else:
                    print("⚠️ No videoId found.")
            else:
                print("⚠️ Invalid choice.")
        else:
            print("⏭ Skipped.")
    return video_ids


def auto_add_tracks(ytmusic, tracks):
    video_ids = []
    for i, item in enumerate(tracks):
        if item.get("is_local", False):
            print(f"⏭ Skipping local track: {item['track']['name']}")
            continue

        song = spotify_track_to_song(item["track"])
        print(f"\n🔍 [{i+1}/{len(tracks)}] Searching: {song['title']} – {', '.join(song['artists'])}")
        results = search_song(ytmusic, song)
        if not results:
            print("❌ No results found.")
            continue

        first = results[0]
        video_id = first.get("videoId")
        if video_id:
            video_ids.append(video_id)
            title = first.get("title")
            artists = ", ".join([a["name"] for a in first.get("artists", [])])
            print(f"✅ Auto-selected: {title} – {artists}")
        else:
            print("⚠️ First result has no videoId.")
    return video_ids


def dry_run_tracks(ytmusic, tracks):
    for i, item in enumerate(tracks):
        if item.get("is_local", False):
            print(f"⏭ Skipping local track: {item['track']['name']}")
            continue

        song = spotify_track_to_song(item["track"])
        print(f"\n🔍 [{i+1}/{len(tracks)}] {song['title']} – {', '.join(song['artists'])}")
        results = search_song(ytmusic, song)
        if not results:
            print("❌ No results found.")
            continue
        print_results(results)


def create_yt_playlist(ytmusic, name, description, video_ids):
    playlist_name = f"{name} (from Spotify)"
    total_songs = len(video_ids)
    
    try:
        print("Creating empty playlist...")
        playlist_id = ytmusic.create_playlist(
            playlist_name, description, privacy_status="PRIVATE"
        )
        print(f"✅ Created empty playlist: {playlist_id}")
    except Exception as e:
        print(f"❌ Failed to create empty playlist: {e}")
        return None
    
    if not video_ids:
        print("⚠️ No songs to add to playlist")
        return playlist_id
    
    total_added = add_individual_songs(ytmusic, playlist_id, video_ids)
    
    print(f"Total songs added: {total_added}/{total_songs}")
    return playlist_id


def add_individual_songs(ytmusic, playlist_id, video_ids):
    added = 0
    for video_id in video_ids:
        success = False
        for attempt in range(1, 4):
            try:
                response = ytmusic.add_playlist_items(playlist_id, [video_id])
                
                if response and response[0]['status'] == 'STATUS_SUCCEEDED':
                    added += 1
                    success = True
                    print(f"✅ Added song: {video_id} (attempt {attempt})")
                    break
                else:
                    print(f"⚠️ Failed to add {video_id} (attempt {attempt}): {response}")
            except Exception as e:
                print(f"⚠️ Exception adding {video_id} (attempt {attempt}): {str(e)}")
            
            time.sleep(0.5)
        
        if not success:
            print(f"❌ Failed to add song after 3 attempts: {video_id}")
    
    print(f"Added {added}/{len(video_ids)} songs")
    return added


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Spotify playlists to YouTube Music.")
    parser.add_argument(
        "--add", action="store_true", help="Interactively create playlists with selected songs."
    )
    parser.add_argument(
        "--auto-add",
        action="store_true",
        help="Automatically create playlists using first search results.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only search and show results without creating playlists.",
    )
    parser.add_argument(
        "--file",
        default="playlists.json",
        help="JSON file with playlists (default: playlists.json)",
    )
    parser.add_argument(
        "--auth",
        default="headers_auth.json",
        help="Path to YTMusic auth headers (default: headers_auth.json)",
    )

    args = parser.parse_args()

    ytmusic = YTMusic(
        "browser.json"
    )
    playlists = load_playlists(args.file)

    if args.add or args.auto_add:
        for playlist in playlists:
            name = playlist["name"]
            description = playlist.get("description", "")
            tracks = playlist["tracks"]
            
            print(f"\n📝 Processing playlist: {name}")
            print(f"   Description: {description}")
            print(f"   Number of tracks: {len(tracks)}")
            
            if args.add:
                video_ids = interactive_add_tracks(ytmusic, tracks)
            else:
                video_ids = auto_add_tracks(ytmusic, tracks)
            
            if video_ids:
                print(f"\n📦 Creating playlist with {len(video_ids)} songs...")
                playlist_id = create_yt_playlist(ytmusic, name, description, video_ids)
                if playlist_id:
                    print(f"✅ Successfully created playlist '{name}'")
                    try:
                        playlist_details = ytmusic.get_playlist(playlist_id)
                        actual_count = playlist_details.get('trackCount', 'unknown')
                        print(f"🔍 Playlist verification: Expected {len(video_ids)} songs, actual: {actual_count}")
                    except Exception as e:
                        print(f"⚠️ Failed to verify playlist: {e}")
                else:
                    print(f"❌ Failed to create playlist '{name}'")
            else:
                print("⏭ No valid songs found, skipping playlist creation")

    elif args.dry_run:
        for playlist in playlists:
            name = playlist["name"]
            description = playlist.get("description", "")
            tracks = playlist["tracks"]
            
            print(f"\n📝 Simulating playlist: {name}")
            print(f"   Description: {description}")
            print(f"   Number of tracks: {len(tracks)}")
            
            dry_run_tracks(ytmusic, tracks)

    else:
        print("❌ Please specify --add, --auto-add, or --dry-run")