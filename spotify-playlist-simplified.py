import json


def extract_playlist_songs(playlist_name, data):
    songs = []
    for item in data.get("playlists", []):
        if item.get("name") == playlist_name:
            for entry in item.get("tracks", []):
                track = entry.get("track", {})
                title = track.get("name", "Unknown Title")
                artists = [artist.get("name") for artist in track.get("artists", [])]
                album = track.get("album", {}).get("name", "Unknown Album")

                songs.append({"title": title, "artists": artists, "album": album})
            return songs
    print(f"❌ Playlist '{playlist_name}' not found.")
    return []


def write_songs_txt(filename, songs):
    with open(filename, "w", encoding="utf-8") as f:
        for song in songs:
            line = f"{song['title']} – {', '.join(song['artists'])} | Album: {song['album']}"
            f.write(line + "\n")
    print(f"✅ Saved {len(songs)} songs to '{filename}' (TXT)")


def write_songs_json(filename, songs):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(songs)} songs to '{filename}' (JSON)")


# Example usage
if __name__ == "__main__":
    with open("playlists.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    playlist_name = "Liked Songs"
    songs = extract_playlist_songs(playlist_name, data)

    write_songs_txt("songs.txt", songs)
    write_songs_json("songs.json", songs)
