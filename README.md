# Spotify to Youtube Music

This is a semi automatic way to migrate Spotify playlist to Youtube music.
Inspired by https://github.com/linsomniac/spotify_to_ytmusic but it has Youtube authentication problems (as in how it uses ytmusicapi package). In summary, loading Liked Songs playlist didn't work as ytmusicapi reported authentication issue.
Also, this version allows to pick which song from the found results to pick (although not very useful), allows to see the playlist in a human readable form etc.

This is purely for my own use and is only tested on a couple of playlists.

## How to use

Install requirements:
```
pip install -r requirements.txt
```

Authenticate yourself in google youtube. This should create you a browser.json file (cookie).

```
ytmusicapi browser
```


Authenticate and download/backup your spotify playlist. Authentication will be performed in the browser by the script:

```
python spotify-backup.py playlists.json --dump=liked,playlists --format=json

```

Output should be in playlists.json file.

Test if it finds songs:

```
python ytmusic_add.py --dry-run 
```


Interactively add each song (select which result to add):

```
python ytmusic_add.py --add
```


Always add the first found song:

```
python ytmusic_add.py --auto-add 
```

