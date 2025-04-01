from Spotify_Tools_Functions.add_track_to_playlist import add_track_to_playlist
from Spotify_Tools_Functions.get_current_track import get_current_track
from Spotify_Tools_Functions.find_playlist_by_name import find_playlist_by_name
from Spotify_Tools_Functions.create_playlist import create_playlist
from Spotify_Tools_Functions.get_user_playlists import get_user_playlists
from Spotify_Authentication_functions.ensure_access_token import ensure_access_token

def call_spotify_function(tool_name, tool_args):
    """Execute the appropriate Spotify function based on the tool name and arguments"""
    # First, ensure we have a valid access token
    access_token = ensure_access_token()
    
    if tool_name == "get_current_track":
        return get_current_track(access_token)
    elif tool_name == "create_playlist":
        return create_playlist(
            access_token=access_token,
            playlist_name=tool_args.get("playlist_name", "New Playlist"),
            description=tool_args.get("description", ""),
            public=tool_args.get("public", False)
        )
    elif tool_name == "add_track_to_playlist":
        return add_track_to_playlist(
            access_token=access_token,
            playlist_id=tool_args.get("playlist_id"),
            track_uri=tool_args.get("track_uri"),
            position=tool_args.get("position")
        )
    elif tool_name == "find_playlist_by_name":
        return find_playlist_by_name(
            access_token=access_token,
            playlist_name=tool_args.get("playlist_name")
        )
    elif tool_name == "get_user_playlists":
        return get_user_playlists(
            access_token=access_token,
            limit=tool_args.get("limit", 50)
        )
    else:
        raise ValueError(f"Unknown tool: {tool_name}")