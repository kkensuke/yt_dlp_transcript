import re
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    """
    Extracts the YouTube video ID from a variety of URL formats.
    Handles standard, shortened, embed, shorts, live, and music URLs,
    as well as regional domains and mobile versions.
    """
    if not url:
        return None

    # Handle the case where the input is just the 11-character video ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    # Prepend 'http://' if no scheme is present to help urlparse
    if not re.match(r'http(s)?://', url):
        url = 'http://' + url

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname

    # A regex to match youtube.com, youtu.be, and regional/mobile variations
    # e.g., www.youtube.com, m.youtube.co.uk, music.youtube.com, youtu.be
    if not hostname or not re.match(r'(?:www\.|m\.|music\.)?youtube\.co(m|\.uk|\.jp|\.de|.\w{2})|youtu\.be', hostname):
        return None

    # Case 1: Standard /watch url (e.g., youtube.com/watch?v=VIDEO_ID)
    if parsed_url.path == '/watch':
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v', [None])[0]

    # Case 2: Shortened URL (e.g., youtu.be/VIDEO_ID)
    if hostname == 'youtu.be':
        # The ID is the first part of the path, ignore query params
        return parsed_url.path.split('/')[1].split('?')[0]

    # Case 3: Embed, Shorts, Live, or old /v/ urls
    # (e.g., /embed/VIDEO_ID, /shorts/VIDEO_ID, /live/VIDEO_ID, /v/VIDEO_ID)
    path_parts = parsed_url.path.split('/')
    if len(path_parts) > 2 and path_parts[1] in ['embed', 'shorts', 'live', 'v']:
        # The ID is the second part of the path, ignore query params
        return path_parts[2].split('?')[0]

    return None

# --- Example Usage ---
urls_to_test = [
    # Standard
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    # Watch list
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=WL&index=1',
    # Just the ID
    'dQw4w9WgXcQ',
    # Shortened
    'https://youtu.be/dQw4w9WgXcQ',
    # Shortened with tracking
    'https://youtu.be/dQw4w9WgXcQ?si=abcde12345',
    # Embed
    'https://www.youtube.com/embed/dQw4w9WgXcQ',
    # Music
    'https://music.youtube.com/watch?v=dQw4w9WgXcQ&list=...',
    # Mobile
    'https://m.youtube.com/watch?v=dQw4w9WgXcQ',
    # International
    'https://www.youtube.co.uk/watch?v=dQw4w9WgXcQ',
    # No scheme
    'youtube.com/watch?v=dQw4w9WgXcQ',
    # Old embed format
    'https://www.youtube.com/v/dQw4w9WgXcQ',
    # Shorts
    'https://www.youtube.com/shorts/o-YBDTqX_ZU',
    # Live
    'https://www.youtube.com/live/some_live_id?feature=share',
    # Invalid URLs
    'https://www.google.com',
    'not a url',
    'https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw',
]

for url in urls_to_test:
    video_id = extract_video_id(url)
    print(f"URL: {url:<65} -> ID: {video_id}")
