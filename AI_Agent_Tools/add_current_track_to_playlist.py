from Spotify_Tools_Functions.get_current_track import get_current_track
from Spotify_Tools_Functions.find_playlist_by_name import find_playlist_by_name
from Spotify_Tools_Functions.add_track_to_playlist import add_track_to_playlist


def add_current_track_to_playlist(access_token, playlist_name):
    # Step 1: Get current track
    track_info = get_current_track(access_token)
    
    # Step 2: Find playlist
    playlist = find_playlist_by_name(access_token, playlist_name)
    
    # Step 3: Add track to playlist
    if track_info and "track_uri" in track_info and playlist and "id" in playlist:
        result = add_track_to_playlist(
            access_token=access_token,
            playlist_id=playlist["id"],
            track_uri=track_info["track_uri"]
        )
        return {
            "success": True,
            "track_name": track_info["track_name"],
            "artist_name": track_info["artist_name"],
            "playlist_name": playlist["name"],
            "message": f"Added {track_info['track_name']} by {track_info['artist_name']} to playlist {playlist['name']}"
        }
    else:
        return {
            "success": False,
            "message": "Failed to add track to playlist - missing information"
        }