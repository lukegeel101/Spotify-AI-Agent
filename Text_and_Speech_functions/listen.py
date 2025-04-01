import speech_recognition as sr

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