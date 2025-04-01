import json
import requests
from get_current_user_id import get_current_user_id


def create_playlist(access_token, playlist_name, description="", public=False):
    """
    Create a new Spotify playlist with the specified name
    
    Parameters:
    access_token (str): A valid Spotify access token
    playlist_name (str): The name for the new playlist
    description (str): Optional description for the playlist
    public (bool): Whether the playlist should be public (True) or private (False)
    
    Returns:
    dict: Information about the created playlist
    """
    user_id = get_current_user_id(access_token)
    endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": playlist_name,
        "description": description,
        "public": public
    }
    
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        playlist_info = response.json()
        return {
            "playlist_id": playlist_info['id'],
            "playlist_name": playlist_info['name'],
            "playlist_url": playlist_info['external_urls']['spotify']
        }
    else:
        raise Exception(f"Failed to create playlist. Status code: {response.status_code}, Response: {response.text}")