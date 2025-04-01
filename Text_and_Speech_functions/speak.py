import queue

tts_queue = queue.Queue()

def speak(text):
    """Add text to the speech queue"""
    print(f"\nAssistant: {text}")
    # Make sure we're actually adding to the queue
    try:
        tts_queue.put(text)
        print("Added response to speech queue.")
    except Exception as e:
        print(f"Error adding text to speech queue: {str(e)}")