import requests

def get_current_user_id(access_token):
    """Get the current user's Spotify user ID"""
    endpoint = "https://api.spotify.com/v1/me"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        user_profile = response.json()
        return user_profile["id"]
    else:
        raise Exception(f"Failed to get user profile. Status code: {response.status_code}, Response: {response.text}")