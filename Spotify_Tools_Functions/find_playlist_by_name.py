from get_user_playlists import get_user_playlists

def find_playlist_by_name(access_token, playlist_name):
    """
    Find a playlist by name in the user's library
    
    Parameters:
    access_token (str): A valid Spotify access token
    playlist_name (str): The name of the playlist to search for
    
    Returns:
    dict: Playlist information including id, or None if not found
    """
    playlists = get_user_playlists(access_token)
    
    # Case-insensitive search
    search_name = playlist_name.lower()
    print(f"Searching for playlist with name: '{search_name}'")
    
    # First try exact match
    for playlist in playlists:
        playlist_name_lower = playlist.get("name", "").lower()
        if playlist_name_lower == search_name:
            print(f"Found exact match: {playlist.get('name')} (ID: {playlist.get('id')})")
            return playlist
    
    # Then try partial match
    for playlist in playlists:
        playlist_name_lower = playlist.get("name", "").lower()
        if search_name in playlist_name_lower or playlist_name_lower in search_name:
            print(f"Found partial match: {playlist.get('name')} (ID: {playlist.get('id')})")
            return playlist
    
    print(f"No matching playlist found for '{playlist_name}'")
    return None