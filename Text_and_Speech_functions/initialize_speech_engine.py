import pyttsx3

def initialize_speech_engine():
    """Initialize the text-to-speech engine"""
    engine = pyttsx3.init()
    # Configure properties if needed (rate, voice, volume)
    engine.setProperty('rate', 175)  # Speed of speech
    # voices = engine.getProperty('voices')
    # engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female voice (depends on system)
    return engine