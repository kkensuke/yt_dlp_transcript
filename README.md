# YouTube Transcript to Markdown Converter

A Python script that extracts transcripts from YouTube videos using `yt-dlp` and converts them to clean, readable Markdown format. Includes optional AI-powered summarization using Google's Gemini API.

## Features

- 🎥 **Reliable transcript extraction** using yt-dlp
- 📝 **Clean Markdown output** with optional timestamps
- 🤖 **AI summarization** powered by Gemini API
- 🌐 **Multi-language support** (optimized for English and Japanese)
- 🎯 **Smart language detection** and text cleaning
- 📊 **Multiple transcript formats** (JSON3, VTT, SRV1)
- 🔧 **Flexible output options**

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install yt-dlp
   ```

2. **Download the script:**
   ```bash
   # Clone or download yt_dlp_transcript.py
   ```

3. **Optional - Set up Gemini API (for summaries):**
   - Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/)
   - Set the environment variable:
     ```bash
     export GEMINI_API_KEY="your_api_key_here"
     ```
   - Or edit the script and add your key to `GEMINI_API_KEY`

## Usage

### Basic Usage

```bash
# Extract transcript from YouTube URL
python yt_dlp_transcript.py 'https://www.youtube.com/watch?v=VIDEO_ID'

# Or use just the video ID
python yt_dlp_transcript.py 'VIDEO_ID'
```

### Advanced Options

```bash
# Remove timestamps from output
python yt_dlp_transcript.py 'VIDEO_URL' --no-timestamps

# Skip AI summary generation
python yt_dlp_transcript.py 'VIDEO_URL' --no-summary

# Specify summary language
python yt_dlp_transcript.py 'VIDEO_URL' --summary-lang ja  # Japanese
python yt_dlp_transcript.py 'VIDEO_URL' --summary-lang en  # English

# Custom output filename
python yt_dlp_transcript.py 'VIDEO_URL' -o my_transcript.md
```

## Output Files

The script generates up to two files:

1. **`{video_id}_transcript.md`** - Full transcript with timestamps
2. **`{video_id}_summarized.md`** - AI-generated summary (if Gemini API is configured)

### Sample Output Structure

```markdown
# Video Title

**Video ID:** ABC123  
**YouTube URL:** https://www.youtube.com/watch?v=ABC123

---

**[00:00:15]** Welcome to this tutorial about Python programming...

**[00:01:30]** In this section, we'll cover the basics of variables...
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `url` | YouTube URL or video ID (required) |
| `-o, --output` | Custom output filename |
| `--no-timestamps` | Exclude timestamps from transcript |
| `--no-summary` | Skip AI summary generation |
| `--summary-lang` | Summary language: `auto`, `en`, `ja` |

## Configuration

### Environment Variables

- `GEMINI_API_KEY` - Your Gemini API key for summarization

### Supported Video Sources

- YouTube videos with available transcripts
- Videos with manual subtitles (preferred)
- Videos with auto-generated captions
- Multiple language support

## Language Support

The script automatically detects video language and:

- **Japanese videos**: Removes music tags, cleans spacing between characters
- **English videos**: Standard text cleaning and formatting
- **Auto-detection**: Based on title and description content
- **Summary language**: Can be forced to specific language regardless of video language

## Examples

### Extract English video transcript:
```bash
python yt_dlp_transcript.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
```

### Extract Japanese video with English summary:
```bash
python yt_dlp_transcript.py 'https://www.youtube.com/watch?v=JAPANESE_VIDEO_ID' --summary-lang en
```

### Clean transcript without timestamps:
```bash
python yt_dlp_transcript.py 'VIDEO_ID' --no-timestamps -o clean_transcript.md
```

## Troubleshooting

### Common Issues

1. **"No transcripts found"**
   - Video may not have subtitles/captions available
   - Try videos from educational channels or popular creators

2. **Gemini API errors**
   - Check your API key is valid
   - Ensure you have quota remaining
   - Very long videos may hit token limits

3. **yt-dlp extraction fails**
   - Update yt-dlp: `pip install -U yt-dlp`
   - Some videos may be region-restricted

### Browser Cookies

The script uses Chrome browser cookies for better access. Ensure Chrome is installed for optimal results.

## Requirements

- Python 3.6+
- yt-dlp
- Internet connection
- Chrome browser (for cookie support)
- Gemini API key (optional, for summaries)

## License

This script is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues and enhancement requests!