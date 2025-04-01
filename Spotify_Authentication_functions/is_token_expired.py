import time

def is_token_expired(token_info):
    """
    Check if the token is expired
    """
    if not token_info or 'expires_at' not in token_info:
        return True
        
    now = int(time.time())
    return token_info['expires_at'] - now < 60  # Consider expired if less than 60 seconds left