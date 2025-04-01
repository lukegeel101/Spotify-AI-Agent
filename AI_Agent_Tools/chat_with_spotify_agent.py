import tools.json
import openai
import json
from call_spotify_function import call_spotify_function


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