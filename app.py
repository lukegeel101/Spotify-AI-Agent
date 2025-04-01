#The entire code compressed into a single file
import os
import json
import time
import requests
from urllib.parse import urlencode
import webbrowser
import openai
import speech_recognition as sr
import pyttsx3
import threading
import queue
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI') #I'm pretty sure you can just use 'http://000.00.00.000/5000' or something like that
SPOTIFY_SCOPE = "playlist-modify-public playlist-modify-private user-read-private user-read-email user-read-currently-playing"

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

# Create a queue for speech synthesis
tts_queue = queue.Queue()

# ===== Speech Recognition and Text-to-Speech Functions =====

def initialize_speech_engine():
    """Initialize the text-to-speech engine"""
    engine = pyttsx3.init()
    # Configure properties if needed (rate, voice, volume)
    engine.setProperty('rate', 175)  # Speed of speech
    # voices = engine.getProperty('voices')
    # engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female voice (depends on system)
    return engine

def speak_text(engine, text):
    """Use the speech engine to say the text directly"""
    print(f"\nAssistant: {text}")
    print("Speaking response...")
    try:
        engine.say(text)
        engine.runAndWait()
        print("Finished speaking.")
    except Exception as e:
        print(f"Error in speech synthesis: {str(e)}")
        # Try reinitializing the engine
        try:
            new_engine = pyttsx3.init()
            new_engine.setProperty('rate', 175)
            new_engine.say(text)
            new_engine.runAndWait()
            print("Reinitialized engine and finished speaking.")
            return new_engine
        except Exception as e2:
            print(f"Failed even after reinitializing: {str(e2)}")
    return engine

def speak(text):
    """Add text to the speech queue"""
    print(f"\nAssistant: {text}")
    # Make sure we're actually adding to the queue
    try:
        tts_queue.put(text)
        print("Added response to speech queue.")
    except Exception as e:
        print(f"Error adding text to speech queue: {str(e)}")

def listen():
    """Listen for voice input and convert to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...")
        # Adjust the recognizer sensitivity to ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=1)
        # Increase timeout and phrase_time_limit for longer sentences
        try:
            print("Speak now - I'm waiting for your full request...")
            # Increased timeout to 20 seconds (waiting for speech to start)
            # Increased phrase_time_limit to 15 seconds (maximum length of phrase)
            audio = recognizer.listen(source, timeout=20, phrase_time_limit=15)
            print("Processing speech...")
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Sorry, I didn't catch that. Could you repeat it?")
                return None
            except sr.RequestError:
                print("Sorry, I'm having trouble connecting to the speech recognition service.")
                return None
        except sr.WaitTimeoutError:
            print("I didn't hear anything. Please try again when you're ready to speak.")
            return None

# ===== Spotify Authentication Functions =====
        
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

def save_token_info(token_info):
    """
    Save token information to a file
    """
    # Add expiration time
    token_info['expires_at'] = int(time.time()) + token_info['expires_in']
    
    with open('.spotify_token_cache.json', 'w') as f:
        json.dump(token_info, f)
    
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
    
def is_token_expired(token_info):
    """
    Check if the token is expired
    """
    if not token_info or 'expires_at' not in token_info:
        return True
        
    now = int(time.time())
    return token_info['expires_at'] - now < 60  # Consider expired if less than 60 seconds left

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

def ensure_access_token():
    """Ensure we have a valid access token, handling the entire auth flow if needed"""
    token_info = get_access_token(
        SPOTIFY_CLIENT_ID, 
        SPOTIFY_CLIENT_SECRET, 
        SPOTIFY_REDIRECT_URI, 
        SPOTIFY_SCOPE
    )
    return token_info["access_token"]

# ===== Spotify Tools/Interactions Functions =====

def get_current_user_profile(access_token):
    """
    Get the current user's Spotify profile to retrieve the user ID
    """
    endpoint = "https://api.spotify.com/v1/me"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        user_profile = response.json()
        return user_profile
    else:
        print(f"Failed to get user profile. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

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

def create_playlist(access_token, playlist_name, description="", public=False):
    """
    Create a new Spotify playlist with the specified name
    
    Parameters:
    access_token (str): A valid Spotify access token
    playlist_name (str): The name for the new playlist
    description (str): Optional description for the playlist
    public (bool): Whether the playlist should be public (True) or private (False)
    
    Returns:
    dict: Information about the created playlist
    """
    user_id = get_current_user_id(access_token)
    endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": playlist_name,
        "description": description,
        "public": public
    }
    
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        playlist_info = response.json()
        return {
            "playlist_id": playlist_info['id'],
            "playlist_name": playlist_info['name'],
            "playlist_url": playlist_info['external_urls']['spotify']
        }
    else:
        raise Exception(f"Failed to create playlist. Status code: {response.status_code}, Response: {response.text}")

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

def add_track_to_playlist(access_token, playlist_id, track_uri, position=None):
    """
    Add a track to a Spotify playlist
    
    Parameters:
    access_token (str): A valid Spotify access token
    playlist_id (str): The ID of the playlist
    track_uri (str): The Spotify URI of the track to add
    position (int, optional): Position to insert the track, zero-based index
    
    Returns:
    dict: Information about the result of the operation
    """
    endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Ensure track_uri is a string and not None
    if not track_uri or not isinstance(track_uri, str):
        raise ValueError(f"Invalid track URI: {track_uri}")
    
    # Prepare payload according to Spotify API docs
    payload = {
        "uris": [track_uri]
    }
    
    # Add position if specified
    if position is not None:
        payload["position"] = position
    
    print(f"Adding track {track_uri} to playlist {playlist_id}")
    print(f"Request payload: {json.dumps(payload)}")
    
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.text}")
    
    if response.status_code in [200, 201]:
        return {
            "success": True,
            "message": "Track successfully added to playlist",
            "snapshot_id": response.json().get("snapshot_id")
        }
    else:
        raise Exception(f"Failed to add track to playlist. Status code: {response.status_code}, Response: {response.text}")

def get_user_playlists(access_token, limit=50):
    """
    Get a list of the user's playlists
    
    Parameters:
    access_token (str): A valid Spotify access token
    limit (int): Maximum number of playlists to return (max 50)
    
    Returns:
    list: A list of the user's playlists with name and ID
    """
    user_id = get_current_user_id(access_token)
    endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "limit": limit
    }
    
    response = requests.get(endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        playlists_data = response.json()
        playlists = []
        
        for item in playlists_data.get("items", []):
            playlists.append({
                "name": item.get("name"),
                "id": item.get("id"),
                "total_tracks": item.get("tracks", {}).get("total", 0),
                "public": item.get("public", False)
            })
        
        print(f"Found {len(playlists)} playlists")
        return playlists
    else:
        raise Exception(f"Failed to get user playlists. Status code: {response.status_code}, Response: {response.text}")

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

# Define the tools for the AI agent
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_track",
            "description": "Get information about the track currently playing on the user's Spotify account",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_playlist",
            "description": "Create a new Spotify playlist with the specified name",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_name": {
                        "type": "string",
                        "description": "The name for the new playlist"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the playlist"
                    },
                    "public": {
                        "type": "boolean",
                        "description": "Whether the playlist should be public (True) or private (False). Default is False."
                    }
                },
                "required": ["playlist_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_track_to_playlist",
            "description": "Add the currently playing track to a playlist",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "The ID of the playlist to add the track to"
                    },
                    "track_uri": {
                        "type": "string",
                        "description": "The Spotify URI of the track to add"
                    },
                    "position": {
                        "type": "integer",
                        "description": "Optional position to insert the track (zero-based index)"
                    }
                },
                "required": ["playlist_id", "track_uri"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_playlist_by_name",
            "description": "Find a playlist by name in the user's library",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_name": {
                        "type": "string",
                        "description": "The name of the playlist to search for"
                    }
                },
                "required": ["playlist_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_playlists",
            "description": "Get a list of the user's playlists",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of playlists to return (max 50)"
                    }
                },
                "required": []
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "add_current_track_to_playlist",
        "description": "Add the currently playing track to a playlist by name",
        "parameters": {
            "type": "object",
            "properties": {
                "playlist_name": {
                    "type": "string",
                    "description": "The name of the playlist to add the track to"
                }
            },
            "required": ["playlist_name"]
        }
    }
}
]

def add_current_track_to_playlist(access_token, playlist_name):
    # Step 1: Get current track
    track_info = get_current_track(access_token)
    
    # Step 2: Find playlist
    playlist = find_playlist_by_name(access_token, playlist_name)
    
    # Step 3: Add track to playlist
    if track_info and "track_uri" in track_info and playlist and "id" in playlist:
        result = add_track_to_playlist(
            access_token=access_token,
            playlist_id=playlist["id"],
            track_uri=track_info["track_uri"]
        )
        return {
            "success": True,
            "track_name": track_info["track_name"],
            "artist_name": track_info["artist_name"],
            "playlist_name": playlist["name"],
            "message": f"Added {track_info['track_name']} by {track_info['artist_name']} to playlist {playlist['name']}"
        }
    else:
        return {
            "success": False,
            "message": "Failed to add track to playlist - missing information"
        }

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
    
def chat_with_spotify_agent(user_message):
    """Process a user message through the AI agent with Spotify tools"""
    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant with access to Spotify. You can:
            1. Check what's currently playing
            2. Create playlists
            3. Add currently playing tracks to playlists
            4. Find playlists by name
            5. List user's playlists
            
            When a user asks to "add the current song to [playlist name]", you MUST follow these exact steps in order:
            Step 1: Call get_current_track to get the currently playing track
            Step 2: Call find_playlist_by_name to find the playlist ID
            Step 3: Call add_track_to_playlist with the playlist ID and track URI
            
            Always complete ALL THREE steps in sequence. Never stop after step 1 or step 2.
            
            Keep your responses concise and conversational since they will be spoken aloud."""
        },
        {"role": "user", "content": user_message}
    ]
    
    # Variables to track our workflow
    current_track = None
    current_playlist = None
    
    # First API call
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=1000
    )
    
    response_message = response.choices[0].message
    
    # Process first response
    if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
        # Convert message to dictionary for our messages array
        messages.append({
            "role": "assistant",
            "content": response_message.content if hasattr(response_message, 'content') else None,
            "tool_calls": [t.model_dump() for t in response_message.tool_calls] if hasattr(response_message, 'tool_calls') else None
        })
        
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"Executing function: {function_name}")
            print(f"With arguments: {json.dumps(function_args, indent=2)}")
            
            try:
                function_response = call_spotify_function(function_name, function_args)
                
                # Store track info if this is get_current_track
                if function_name == "get_current_track" and "track_uri" in function_response:
                    current_track = function_response
                
                # Store playlist info if this is a playlist function
                if function_name == "create_playlist" and "playlist_id" in function_response:
                    current_playlist = {"id": function_response["playlist_id"], "name": function_response["playlist_name"]}
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(function_response)
                })
            except Exception as e:
                print(f"Error in function {function_name}: {str(e)}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps({"error": str(e)})
                })
        
        # Second API call
        second_response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1000
        )
        
        second_message = second_response.choices[0].message
        
        # Check for function calls in second response
        if hasattr(second_message, 'tool_calls') and second_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": second_message.content if hasattr(second_message, 'content') else None,
                "tool_calls": [t.model_dump() for t in second_message.tool_calls] if hasattr(second_message, 'tool_calls') else None
            })
            
            for tool_call in second_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"Executing additional function: {function_name}")
                print(f"With arguments: {json.dumps(function_args, indent=2)}")
                
                try:
                    function_response = call_spotify_function(function_name, function_args)
                    
                    # Store track info if this is get_current_track
                    if function_name == "get_current_track" and "track_uri" in function_response:
                        current_track = function_response
                    
                    # Store playlist info if this is find_playlist_by_name
                    if function_name == "find_playlist_by_name" and function_response:
                        current_playlist = function_response
                    
                    # Store playlist info if this is create_playlist
                    if function_name == "create_playlist" and "playlist_id" in function_response:
                        current_playlist = {"id": function_response["playlist_id"], "name": function_response["playlist_name"]}
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_response)
                    })
                except Exception as e:
                    print(f"Error in function {function_name}: {str(e)}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps({"error": str(e)})
                    })
            
            # Check if we have both track and playlist but no add_track_to_playlist call yet
            if current_track and current_playlist:
                # Check if add_track_to_playlist has been called
                add_track_called = False
                for msg in messages:
                    if msg.get("role") == "tool" and msg.get("name") == "add_track_to_playlist":
                        add_track_called = True
                        break
                
                if not add_track_called:
                    print("SAFETY NET: We have track and playlist info but no add_track_to_playlist call yet")
                    print(f"Track: {current_track['track_name']} ({current_track['track_uri']})")
                    print(f"Playlist: {current_playlist['name']} ({current_playlist['id']})")
                    
                    # Add a message from the assistant indicating the intention to add the track
                    messages.append({
                        "role": "assistant",
                        "content": f"Now I'll add {current_track['track_name']} by {current_track['artist_name']} to the {current_playlist['name']} playlist."
                    })
                    
                    # Explicitly force a third function call
                    third_response = openai.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=messages,
                        tools=tools,
                        tool_choice={"type": "function", "function": {"name": "add_track_to_playlist"}},
                        max_tokens=1000
                    )
                    
                    third_message = third_response.choices[0].message
                    
                    if hasattr(third_message, 'tool_calls') and third_message.tool_calls:
                        messages.append(third_message)
                        
                        for tool_call in third_message.tool_calls:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)
                            
                            print(f"Executing final function: {function_name}")
                            print(f"With arguments: {json.dumps(function_args, indent=2)}")
                            
                            try:
                                function_response = call_spotify_function(function_name, function_args)
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": json.dumps(function_response)
                                })
                            except Exception as e:
                                print(f"Error in function {function_name}: {str(e)}")
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": json.dumps({"error": str(e)})
                                })
                    else:
                        # Ultimate safety net - model didn't make the call even when forced
                        print("ULTIMATE SAFETY NET: Model did not make add_track_to_playlist call even when forced")
                        try:
                            add_result = call_spotify_function("add_track_to_playlist", {
                                "playlist_id": current_playlist["id"],
                                "track_uri": current_track["track_uri"]
                            })
                            
                            print(f"Manual add result: {json.dumps(add_result, indent=2)}")
                            
                            # Create a safety net message
                            safety_tool_id = "safety_net_add_track_call"
                            messages.append({
                                "role": "assistant",
                                "content": f"I'm adding {current_track['track_name']} to the {current_playlist['name']} playlist."
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": safety_tool_id,
                                "name": "add_track_to_playlist",
                                "content": json.dumps(add_result)
                            })
                        except Exception as e:
                            print(f"Error in manual add: {str(e)}")
            
            # Get final response
            final_response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                max_tokens=1000
            )
            
            return final_response.choices[0].message.content
        
        # If second message doesn't have tool calls but we have track and playlist info
        if current_track and current_playlist:
            # Check if add_track_to_playlist has been called
            add_track_called = False
            for msg in messages:
                if isinstance(msg, dict) and msg.get("role") == "tool" and msg.get("name") == "add_track_to_playlist":
                    add_track_called = True
                    break
            
            if not add_track_called:
                print("SAFETY NET: We have track and playlist info but second message has no tool calls")
                try:
                    add_result = call_spotify_function("add_track_to_playlist", {
                        "playlist_id": current_playlist["id"],
                        "track_uri": current_track["track_uri"]
                    })
                    
                    print(f"Safety net add result: {json.dumps(add_result, indent=2)}")
                    
                    # Add safety net messages
                    safety_tool_id = "safety_net_add_track_call"
                    messages.append({
                        "role": "assistant",
                        "content": f"I'm adding {current_track['track_name']} to the {current_playlist['name']} playlist."
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": safety_tool_id,
                        "name": "add_track_to_playlist",
                        "content": json.dumps(add_result)
                    })
                    
                    # Get final response
                    final_response = openai.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=messages,
                        max_tokens=1000
                    )
                    
                    return final_response.choices[0].message.content
                except Exception as e:
                    print(f"Error in safety net add: {str(e)}")
        
        return second_message.content
    
    return response_message.content

# ===== Main Application =====

def clean_text_for_speech(text):
    """Remove markdown formatting and other characters that don't work well in speech"""
    # Handle None value case
    if text is None:
        return "I've completed the operation."
    
    # Replace markdown links with just the text
    text = text.replace('[here]', 'here')
    # Remove markdown formatting characters
    text = text.replace('**', '')
    text = text.replace('*', '')
    text = text.replace('`', '')
    text = text.replace('```', '')
    text = text.replace('#', '')
    # Replace URLs with a simple mention
    import re
    text = re.sub(r'https?://\S+', 'at this link', text)
    # Replace any markdown links [text](url) with just text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    return text

def main():
    print("🎵 Spotify Voice Assistant 🎵")
    print("Say 'exit', 'quit', or 'bye' to end the conversation")
    
    # Initialize speech engine
    engine = initialize_speech_engine()
    
    print("Voice recognition settings:")
    print("- Listening timeout: 20 seconds (time to start speaking)")
    print("- Maximum phrase time: 15 seconds (time to complete your request)")
    print("Say your request clearly after 'Listening...' appears")
    
    # Initial greeting
    engine = speak_text(engine, "Hello! I'm your Spotify voice assistant. How can I help you today?")
    
    while True:
        user_input = listen()
        if not user_input:
            continue
            
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            speak_text(engine, "Goodbye! Have a great day.")
            break
        
        try:
            response = chat_with_spotify_agent(user_input)
            # Clean the text for speech before speaking it
            speech_text = clean_text_for_speech(response)
            engine = speak_text(engine, speech_text)
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            print(error_msg)
            engine = speak_text(engine, error_msg)

if __name__ == "__main__":
    main()