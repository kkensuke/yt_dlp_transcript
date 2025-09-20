import re
import json
import urllib.request
import yt_dlp
from utils import format_timestamp, vtt_time_to_seconds, detect_video_language, clean_japanese_text


def get_video_info_and_transcript(video_id):
    """Get video info and transcript using yt-dlp."""
    
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'cookiesfrombrowser': ('chrome',),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Extracting video information...")
            info = ydl.extract_info(video_id, download=False)
            
            title = info.get('title', 'Unknown Title')
            video_id = info.get('id', 'Unknown ID')
            duration = info.get('duration', 0)
            description = info.get('description', '')
            
            print(f"Title: {title}")
            print(f"Video ID: {video_id}")
            print(f"Duration: {format_timestamp(duration)}")
            
            # Detect video language
            detected_language = detect_video_language(title, description)
            print(f"Detected language: {detected_language}")
            
            # Look for subtitles
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            
            print(f"\nAvailable manual subtitles: {list(subtitles.keys())}")
            print(f"Available auto captions (first 10): {list(automatic_captions.keys())[:10]}...")
            
            # Choose language based on detection
            if detected_language == 'ja':
                preferred_languages = ['ja', 'ja-JP', 'en', 'en-US', 'en-GB']
            else:
                preferred_languages = ['en', 'en-US', 'en-GB', 'ja', 'ja-JP']
            
            transcript_data = None
            transcript_type = None
            
            # Try manual subtitles first
            for lang_code in preferred_languages:
                if lang_code in subtitles:
                    transcript_data = subtitles[lang_code]
                    transcript_type = f"Manual ({lang_code})"
                    break
            
            # Then try automatic captions
            if not transcript_data:
                for lang_code in preferred_languages:
                    if lang_code in automatic_captions:
                        transcript_data = automatic_captions[lang_code]
                        transcript_type = f"Auto-generated ({lang_code})"
                        break
            
            # If still no match, try any available language
            if not transcript_data:
                if subtitles:
                    lang_code = list(subtitles.keys())[0]
                    transcript_data = subtitles[lang_code]
                    transcript_type = f"Manual ({lang_code})"
                elif automatic_captions:
                    lang_code = list(automatic_captions.keys())[0]
                    transcript_data = automatic_captions[lang_code]
                    transcript_type = f"Auto-generated ({lang_code})"
            
            if transcript_data:
                print(f"Using transcript: {transcript_type}")
                return info, transcript_data
            else:
                print("No transcripts found")
                return info, None
                
    except Exception as e:
        print(f"Error extracting video info: {str(e)}")
        return None, None


def download_and_parse_transcript(transcript_data):
    """Download and parse the transcript file."""
    
    # Find the best format (prefer json, then vtt, then srt)
    best_format = None
    for item in transcript_data:
        ext = item.get('ext', '')
        if ext == 'json3':
            best_format = item
            break
        elif ext == 'vtt' and not best_format:
            best_format = item
        elif ext == 'srv1' and not best_format:
            best_format = item
    
    if not best_format:
        print("No suitable transcript format found")
        return None
    
    print(f"Downloading transcript in {best_format.get('ext')} format...")
    
    try:
        # Directly fetch the transcript URL
        transcript_url = best_format['url']
        print(f"Fetching from: {transcript_url}")
        
        # Download only the transcript file (small file)
        with urllib.request.urlopen(transcript_url) as response:
            content = response.read().decode('utf-8')
        
        print(f"Downloaded transcript ({len(content)} characters)")
        
        # Parse based on format
        if best_format.get('ext') == 'json3':
            return parse_json3_transcript(content)
        elif best_format.get('ext') == 'vtt':
            return parse_vtt_transcript(content)
        else:
            return parse_srv1_transcript(content)
                    
    except Exception as e:
        print(f"Error downloading transcript: {str(e)}")
        return None


def parse_json3_transcript(content):
    """Parse JSON3 format transcript."""
    try:
        data = json.loads(content)
        transcript = []
        
        events = data.get('events', [])
        for event in events:
            if 'segs' in event:
                start_time = event.get('tStartMs', 0) / 1000.0
                text_parts = []
                for seg in event['segs']:
                    if 'utf8' in seg:
                        text_parts.append(seg['utf8'])
                
                text = ''.join(text_parts).strip()
                if text:
                    transcript.append({
                        'text': text,
                        'start': start_time,
                        'duration': event.get('dDurationMs', 0) / 1000.0
                    })
        
        return transcript
    except Exception as e:
        print(f"Error parsing JSON3 transcript: {str(e)}")
        return None


def parse_vtt_transcript(content):
    """Parse VTT format transcript."""
    try:
        transcript = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for timestamp lines
            if '-->' in line:
                time_parts = line.split(' --> ')
                start_time = vtt_time_to_seconds(time_parts[0])
                
                # Get the text (next non-empty lines)
                i += 1
                text_parts = []
                while i < len(lines) and lines[i].strip():
                    text_parts.append(lines[i].strip())
                    i += 1
                
                text = ' '.join(text_parts)
                # Remove VTT tags
                text = re.sub(r'<[^>]+>', '', text)
                
                if text:
                    transcript.append({
                        'text': text,
                        'start': start_time,
                        'duration': 0  # VTT doesn't always have duration
                    })
            
            i += 1
        
        return transcript
    except Exception as e:
        print(f"Error parsing VTT transcript: {str(e)}")
        return None


def parse_srv1_transcript(content):
    """Parse SRV1 (XML) format transcript."""
    try:
        import xml.etree.ElementTree as ET
        
        root = ET.fromstring(content)
        transcript = []
        
        for text_elem in root.findall('.//text'):
            start_time = float(text_elem.get('start', 0))
            duration = float(text_elem.get('dur', 0))
            text = text_elem.text or ''
            text = text.strip()
            
            if text:
                transcript.append({
                    'text': text,
                    'start': start_time,
                    'duration': duration
                })
        
        return transcript
    except Exception as e:
        print(f"Error parsing SRV1 transcript: {str(e)}")
        return None


def transcript_to_markdown(transcript, video_info, include_timestamps=True):
    """Convert transcript to markdown format."""
    title = video_info.get('title', 'Unknown Title')
    video_id = video_info.get('id', 'Unknown ID')
    
    # Detect if this is Japanese content
    is_japanese = detect_video_language(title) == 'ja'
    
    markdown = f"# {title}\n\n"
    markdown += f"**Video ID:** {video_id}  \n"
    markdown += f"**YouTube URL:** https://www.youtube.com/watch?v={video_id}\n\n"
    markdown += "---\n\n"
    
    if not transcript:
        markdown += "*No transcript available for this video.*\n"
        return markdown
    
    # Group transcript entries into paragraphs
    current_paragraph = ""
    current_start_time = None
    
    for entry in transcript:
        text = entry['text'].strip()
        
        if not text:
            continue
        
        # Clean Japanese text if needed
        if is_japanese:
            text = clean_japanese_text(text)
            if not text:  # Skip if text becomes empty after cleaning
                continue
            
        if current_start_time is None:
            current_start_time = entry['start']
        
        current_paragraph += text + " "
        
        # Start new paragraph if text ends with sentence punctuation
        if text.endswith(('.', '!', '?', '。', '！', '？')) or len(current_paragraph) > 500:
            if include_timestamps:
                timestamp = format_timestamp(current_start_time)
                final_text = current_paragraph.strip()
                if is_japanese:
                    final_text = clean_japanese_text(final_text)
                markdown += f"**[{timestamp}]** {final_text}\n\n"
            else:
                final_text = current_paragraph.strip()
                if is_japanese:
                    final_text = clean_japanese_text(final_text)
                markdown += f"{final_text}\n\n"
            
            current_paragraph = ""
            current_start_time = None
    
    # Add any remaining text
    if current_paragraph.strip():
        final_text = current_paragraph.strip()
        if is_japanese:
            final_text = clean_japanese_text(final_text)
        
        if final_text:  # Only add if text remains after cleaning
            if include_timestamps and current_start_time is not None:
                timestamp = format_timestamp(current_start_time)
                markdown += f"**[{timestamp}]** {final_text}\n\n"
            else:
                markdown += f"{final_text}\n\n"
    
    return markdown
