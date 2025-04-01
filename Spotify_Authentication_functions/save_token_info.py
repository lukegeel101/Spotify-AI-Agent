import json
import time

def save_token_info(token_info):
    """
    Save token information to a file
    """
    # Add expiration time
    token_info['expires_at'] = int(time.time()) + token_info['expires_in']
    
    with open('.spotify_token_cache.json', 'w') as f:
        json.dump(token_info, f)