import requests

def refresh_access_token(client_id, client_secret, refresh_token):
    """
    Use a refresh token to get a new access token
    """
    token_url = "https://accounts.spotify.com/api/token"
    
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    token_response = requests.post(token_url, data=token_data)
    new_token_info = token_response.json()
    
    if "access_token" not in new_token_info:
        raise Exception(f"Failed to refresh access token: {new_token_info}")
    
    # Refresh token is not always returned, so keep the old one if not present
    if "refresh_token" not in new_token_info:
        new_token_info["refresh_token"] = refresh_token
        
    return new_token_info