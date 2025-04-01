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