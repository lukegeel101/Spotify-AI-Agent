import requests
from get_current_user_id import get_current_user_id

def get_user_playlists(access_token, limit=50):
    """
    Get a list of the user's playlists
    
    Parameters:
    access_token (str): A valid Spotify access token
    limit (int): Maximum number of playlists to return (max 50)
    
    Returns:
    list: A list of the user's playlists with name and ID
    """
    user_id = get_current_user_id(access_token)
    endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "limit": limit
    }
    
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        playlists_data = response.json()
        playlists = []
        
        for item in playlists_data.get("items", []):
            playlists.append({
                "name": item.get("name"),
                "id": item.get("id"),
                "total_tracks": item.get("tracks", {}).get("total", 0),
                "public": item.get("public", False)
            })
        
        print(f"Found {len(playlists)} playlists")
        return playlists
    else:
        raise Exception(f"Failed to get user playlists. Status code: {response.status_code}, Response: {response.text}")