import requests

def get_current_track(access_token):
    """
    Get the currently playing track on the user's Spotify account
    
    Returns:
    dict: A dictionary containing the track name and artist name, or None if no track is playing
    """
    endpoint = "https://api.spotify.com/v1/me/player/currently-playing"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(endpoint, headers=headers)
    
    # If status code is 204, no track is currently playing
    if response.status_code == 204:
        return {"message": "No track is currently playing"}
    
    # If status code is 200, a track is currently playing
    elif response.status_code == 200:
        data = response.json()
        
        # Check if there's an item (track) in the response
        if data.get("item"):
            track_name = data["item"]["name"]
            track_uri = data["item"]["uri"]
            
            # Get the first artist's name (there can be multiple artists)
            artist_name = data["item"]["artists"][0]["name"]
            
            # If there are multiple artists, join their names
            if len(data["item"]["artists"]) > 1:
                all_artists = [artist["name"] for artist in data["item"]["artists"]]
                artist_name = ", ".join(all_artists)
            
            return {
                "track_name": track_name,
                "artist_name": artist_name,
                "is_playing": data["is_playing"],
                "track_uri": track_uri
            }
        else:
            return {"message": "No track information available"}
    else:
        raise Exception(f"Failed to get currently playing track. Status code: {response.status_code}, Response: {response.text}")