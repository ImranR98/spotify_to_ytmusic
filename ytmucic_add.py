import json
import argparse
from ytmusicapi import YTMusic, OAuthCredentials
from dotenv import dotenv_values

env = dotenv_values(".env")


def load_songs(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


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


def interactive_add(ytmusic, songs):
    for song in songs:
        print(f"\n🔍 Searching: {song['title']} – {', '.join(song['artists'])}")
        results = search_song(ytmusic, song)
        if not results:
            print("❌ No results found.")
            continue

        print_results(results)
        choice = input(
            "Select song number to add to 'Liked Music' (or press Enter to skip): "
        ).strip()
        if choice.isdigit():
            index = int(choice)
            if 0 <= index < len(results):
                video_id = results[index].get("videoId")
                if video_id:
                    ytmusic.rate_song(video_id, "LIKE")
                    print(f"✅ Added: {results[index]['title']}")
                else:
                    print("⚠️ No videoId found.")
            else:
                print("⚠️ Invalid choice.")
        else:
            print("⏭ Skipped.")


def auto_add(ytmusic, songs):
    for song in songs:
        print(f"\n🔍 Searching: {song['title']} – {', '.join(song['artists'])}")
        results = search_song(ytmusic, song)
        if not results:
            print("❌ No results found.")
            continue

        first = results[0]
        video_id = first.get("videoId")
        if video_id:
            ytmusic.rate_song(video_id, "LIKE")
            title = first.get("title")
            artists = ", ".join([a["name"] for a in first.get("artists", [])])
            print(f"✅ Auto-added: {title} – {artists}")
        else:
            print("⚠️ First result has no videoId.")


def dry_run(ytmusic, songs):
    for song in songs:
        print(f"\n🔍 {song['title']} – {', '.join(song['artists'])}")
        results = search_song(ytmusic, song)
        if not results:
            print("❌ No results found.")
            continue
        print_results(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Spotify songs to YouTube Music.")
    parser.add_argument(
        "--add", action="store_true", help="Interactively add songs to Liked Music."
    )
    parser.add_argument(
        "--auto-add",
        action="store_true",
        help="Automatically add first result to Liked Music.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only search and show results without adding.",
    )
    parser.add_argument(
        "--file",
        default="songs.json",
        help="JSON file with songs (default: songs.json)",
    )
    parser.add_argument(
        "--auth",
        default="headers_auth.json",
        help="Path to YTMusic auth headers (default: headers_auth.json)",
    )

    args = parser.parse_args()

    ytmusic = YTMusic(
        "oauth.json",
        oauth_credentials=OAuthCredentials(
            client_id=env["YOUTUBE_CLIENT_ID"],
            client_secret=env["YOUTUBE_CLIENT_SECRET"],
        ),
    )
    songs = load_songs(args.file)

    if args.add:
        interactive_add(ytmusic, songs)
    elif args.auto_add:
        auto_add(ytmusic, songs)
    elif args.dry_run:
        dry_run(ytmusic, songs)
    else:
        print("❌ Please specify --add, --auto-add, or --dry-run")
