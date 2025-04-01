from clean_text_for_speech import clean_text_for_speech
from Spotify_Tools_Functions import chat_with_spotify_agent
from Text_and_Speech_functions import initialize_speech_engine
from Text_and_Speech_functions import listen
from Text_and_Speech_functions import speak_text

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