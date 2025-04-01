import json

def load_token_info():
    """
    Load token information from a file if it exists
    """
    try:
        with open('.spotify_token_cache.json', 'r') as f:
            token_info = json.load(f)
            return token_info
    except FileNotFoundError:
        return None