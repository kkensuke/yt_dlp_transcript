import re
from datetime import timedelta


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format."""
    return str(timedelta(seconds=int(seconds)))


def vtt_time_to_seconds(time_str):
    """Convert VTT timestamp to seconds."""
    try:
        # Remove milliseconds part if present
        time_str = time_str.split('.')[0]
        parts = time_str.split(':')
        
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return int(parts[0])
    except:
        return 0


def detect_video_language(title, description=""):
    """Simple language detection based on title and description."""
    text = (title + " " + description).lower()
    
    # Japanese detection - look for hiragana, katakana, or common Japanese words
    japanese_indicators = ['を', 'は', 'が', 'に', 'で', 'と', 'の', 'です', 'ます', 'した', 'する', 'ある', 'いる']
    if any(indicator in text for indicator in japanese_indicators):
        return 'ja'
    
    # Could add more language detection here
    return 'en'  # Default to English


def clean_japanese_text(text):
    """Clean Japanese transcript text by removing music tags and unnecessary spaces."""
    # Remove common Japanese music/sound tags
    music_tags = ['[音楽]', '♪', '♫', '♬', '♩', '[拍手]', '[笑い]', '[笑]', '[音響効果]', '[効果音]']
    for tag in music_tags:
        text = text.replace(tag, '')
    
    # Remove spaces between Japanese characters
    # This regex matches spaces that are between Japanese characters (hiragana, katakana, kanji)
    # Unicode ranges: Hiragana (3040-309F), Katakana (30A0-30FF), CJK Unified Ideographs (4E00-9FAF)
    japanese_char_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]'
    
    # Remove spaces between Japanese characters
    text = re.sub(f'({japanese_char_pattern})\\s+({japanese_char_pattern})', r'\1\2', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing spaces
    text = text.strip()
    
    return text
