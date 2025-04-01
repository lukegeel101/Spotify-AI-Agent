import requests
import webbrowser
from urllib.parse import urlencode
from load_token_info import load_token_info
from is_token_expired import is_token_expired
from refresh_access_token import refresh_access_token
from save_token_info import save_token_info
from Text_and_Speech_functions.speak import speak



def get_access_token(client_id, client_secret, redirect_uri, scope):
    """Get Spotify access token using the Authorization Code Flow with token caching"""
    # First, try to load cached token
    token_info = load_token_info()
    
    # If we have a valid token, use it
    if token_info and not is_token_expired(token_info):
        print("Using cached access token")
        return token_info
        
    # If we have a refresh token, try to use it
    if token_info and 'refresh_token' in token_info:
        print("Refreshing access token...")
        try:
            new_token_info = refresh_access_token(client_id, client_secret, token_info['refresh_token'])
            save_token_info(new_token_info)
            return new_token_info
        except Exception as e:
            print(f"Error refreshing token: {e}")
            # If refresh fails, continue with the authorization flow
    
    # If we get here, we need to get a new token via browser auth
    print("Need to authorize via browser...")
    speak("I need authorization to access your Spotify account. Opening your browser now.")
    
    # Step 1: Get authorization code
    auth_url = "https://accounts.spotify.com/authorize"
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope
    }

    auth_redirect = f"{auth_url}?{urlencode(auth_params)}"
    print(f"Please open this URL in your browser: {auth_redirect}")
    speak("After authorizing in your browser, please copy the URL you were redirected to.")
    
    # Optional: automatically open the browser
    webbrowser.open(auth_redirect)
    
    redirect_response = input("Enter the full URL you were redirected to: ")
    
    # Extract the authorization code from the URL
    code = redirect_response.split("code=")[1].split("&")[0] if "code=" in redirect_response else None
    
    if not code:
        raise Exception("Authorization code not found in the redirect URL")
    
    # Step 2: Exchange code for access token
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    token_response = requests.post(token_url, data=token_data)
    token_info = token_response.json()
    
    if "access_token" not in token_info:
        raise Exception(f"Failed to get access token: {token_info}")
    
    # Save the token info for future use
    save_token_info(token_info)
    speak("Authorization successful.")
        
    return token_info