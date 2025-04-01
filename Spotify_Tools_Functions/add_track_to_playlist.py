import requests
import json

def add_track_to_playlist(access_token, playlist_id, track_uri, position=None):
    """
    Add a track to a Spotify playlist
    
    Parameters:
    access_token (str): A valid Spotify access token
    playlist_id (str): The ID of the playlist
    track_uri (str): The Spotify URI of the track to add
    position (int, optional): Position to insert the track, zero-based index
    
    Returns:
    dict: Information about the result of the operation
    """
    endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Ensure track_uri is a string and not None
    if not track_uri or not isinstance(track_uri, str):
        raise ValueError(f"Invalid track URI: {track_uri}")
    
    # Prepare payload according to Spotify API docs
    payload = {
        "uris": [track_uri]
    }
    
    # Add position if specified
    if position is not None:
        payload["position"] = position
    
    print(f"Adding track {track_uri} to playlist {playlist_id}")
    print(f"Request payload: {json.dumps(payload)}")
    
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
    
    if response.status_code in [200, 201]:
        return {
            "success": True,
            "message": "Track successfully added to playlist",
            "snapshot_id": response.json().get("snapshot_id")
        }
    else:
        raise Exception(f"Failed to add track to playlist. Status code: {response.status_code}, Response: {response.text}")