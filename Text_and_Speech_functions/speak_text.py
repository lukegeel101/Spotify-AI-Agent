import pyttsx3

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