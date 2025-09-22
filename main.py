import os
import sys
import argparse

from url_extractor import extract_video_id
from gemini_api import call_gemini_api, create_summary_markdown
from transcript_processor import get_video_info_and_transcript, download_and_parse_transcript, transcript_to_markdown


# ===== CONFIGURATION =====
# Add your Gemini API key here
GEMINI_API_KEY = os.getenv("YOUR_GEMINI_API_KEY")
# GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

MAX_SUMMARY_LENGTH = 50000  # Max characters for summary input
# =========================


def main():
    parser = argparse.ArgumentParser(description='Extract YouTube transcript using yt-dlp')
    parser.add_argument('url', help='YouTube URL or video ID')
    parser.add_argument('-o', '--output', help='Output file (default: video_id_transcript.md)')
    parser.add_argument('--no-timestamps', action='store_true', help='Exclude timestamps from output')
    parser.add_argument('--no-summary', action='store_true', help='Skip summary generation')
    parser.add_argument('--summary-lang', choices=['auto', 'en', 'ja'], default='auto', 
                       help='Summary language: auto (same as original), en (English), ja (Japanese)')
    
    args = parser.parse_args()
    
    # Extract video ID for filename if needed
    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Could not extract a valid YouTube video ID from '{args.url}'")
        sys.exit(1)
    
    # Get video info and transcript
    video_info, transcript_data = get_video_info_and_transcript(video_id)
    
    if not video_info:
        print("Failed to get video information")
        sys.exit(1)
    
    if not transcript_data:
        print("No transcript data available")
        sys.exit(1)
    
    # Download and parse transcript
    transcript = download_and_parse_transcript(transcript_data)
    
    if not transcript:
        print("Failed to parse transcript")
        sys.exit(1)
    
    print(f"Successfully parsed {len(transcript)} transcript entries")
    
    # Convert to markdown
    include_timestamps = not args.no_timestamps
    markdown = transcript_to_markdown(transcript, video_info, include_timestamps)
    
    # Save original transcript to file
    output_file = args.output or f"{video_id}_transcript.md"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"Transcript saved to: {output_file}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        print("\n--- Transcript Content ---")
        print(markdown)
        return
    
    
    # Generate summary if API key is configured and not disabled
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY" and not args.no_summary:
        print("\nGenerating summary...")
        
        # Limit text length for API (Gemini has token limits)
        if len(markdown) > MAX_SUMMARY_LENGTH:
            markdown = markdown[:MAX_SUMMARY_LENGTH] + "... [transcript truncated for summarization]"
            print(f"Transcript truncated to {MAX_SUMMARY_LENGTH} characters for summarization")

        # Call Gemini API with language preference
        summary = call_gemini_api(markdown, GEMINI_API_KEY, args.summary_lang)

        if summary:
            # Create summary markdown
            summary_markdown = create_summary_markdown(video_info, summary)
            
            # Save summary to file
            summary_file = f"{video_id}_summarized.md"
            
            try:
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(summary_markdown)
                print(f"Summary saved to: {summary_file}")
            except Exception as e:
                print(f"Error saving summary file: {str(e)}")
                print("\n--- Summary Content ---")
                print(summary_markdown)
        else:
            print("Failed to generate summary")
    elif args.no_summary:
        print("Summary generation skipped (--no-summary flag used)")
    elif not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("No Gemini API key configured. Set GEMINI_API_KEY in the script to enable summarization.")
    else:
        print("Summarization disabled")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: python main.py <YouTube_URL_or_Video_ID>")
        print("Example: python main.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        print("\nOptions:")
        print("  --no-timestamps    Exclude timestamps from output")
        print("  --no-summary       Skip summary generation")
        print("  --summary-lang     Summary language: auto (default), en, ja")
        print("  -o FILE            Output filename")
        print("\nExamples:")
        print("  python main.py 'VIDEO_URL'")
        print("  python main.py 'VIDEO_URL' --summary-lang ja")
        print("  python main.py 'VIDEO_URL' --summary-lang en")
        sys.exit(1)
    
    main()