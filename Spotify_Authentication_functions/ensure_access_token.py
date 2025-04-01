from get_access_token import get_access_token

SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''
SPOTIFY_REDIRECT_URI = ''
SPOTIFY_SCOPE = ''

def ensure_access_token():
    """Ensure we have a valid access token, handling the entire auth flow if needed"""
    token_info = get_access_token(
        SPOTIFY_CLIENT_ID, 
        SPOTIFY_CLIENT_SECRET, 
        SPOTIFY_REDIRECT_URI, 
        SPOTIFY_SCOPE
    )
    return token_info["access_token"]