from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os

# Import your existing functions
from url_extractor import extract_video_id
from transcript_processor import get_video_info_and_transcript, download_and_parse_transcript, transcript_to_markdown
from gemini_api import call_gemini_api, create_summary_markdown

app = FastAPI(title="YouTube Transcript Extractor")

# Store job status in memory (use Redis in production)
jobs = {}

class TranscriptRequest(BaseModel):
    url: str
    include_timestamps: bool = True
    generate_summary: bool = True
    summary_lang: str = "auto"

class JobStatus(BaseModel):
    status: str  # pending, processing, completed, error
    progress: str
    result: Optional[dict] = None
    error: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube Transcript Extractor</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github-dark.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
        <style>
            .markdown-preview {
                max-width: none;
            }
            .markdown-preview h1 { 
                font-size: 1.875rem;
                font-weight: bold;
                margin-top: 1.5rem;
                margin-bottom: 1rem;
            }
            .markdown-preview h2 { 
                font-size: 1.5rem;
                font-weight: bold;
                margin-top: 1.25rem;
                margin-bottom: 0.75rem;
            }
            .markdown-preview h3 { 
                font-size: 1.25rem;
                font-weight: 600;
                margin-top: 1rem;
                margin-bottom: 0.5rem;
            }
            .markdown-preview p { 
                margin-bottom: 1rem;
                line-height: 1.75;
            }
            .markdown-preview blockquote { 
                border-left: 4px solid #a855f7;
                padding-left: 1rem;
                font-style: italic;
                margin: 1rem 0;
                color: #4b5563;
            }
            .markdown-preview code { 
                background-color: #f3f4f6;
                padding: 0.125rem 0.25rem;
                border-radius: 0.25rem;
                font-size: 0.875rem;
                font-family: 'Courier New', monospace;
            }
            .markdown-preview pre { 
                background-color: #1f2937;
                color: #f3f4f6;
                padding: 1rem;
                border-radius: 0.5rem;
                overflow-x: auto;
                margin: 1rem 0;
            }
            .markdown-preview pre code {
                background-color: transparent;
                padding: 0;
                color: inherit;
            }
            .markdown-preview strong { 
                font-weight: bold;
                color: #111827;
            }
            .markdown-preview ul { 
                list-style-type: disc;
                margin-left: 1.5rem;
                margin-bottom: 1rem;
            }
            .markdown-preview ol { 
                list-style-type: decimal;
                margin-left: 1.5rem;
                margin-bottom: 1rem;
            }
            .markdown-preview li {
                margin-bottom: 0.5rem;
            }
            .markdown-preview a { 
                color: #9333ea;
                text-decoration: underline;
            }
            .markdown-preview a:hover { 
                color: #7e22ce;
            }
            .markdown-preview table {
                border-collapse: collapse;
                width: 100%;
                margin: 1rem 0;
            }
            .markdown-preview th, .markdown-preview td {
                border: 1px solid #e5e7eb;
                padding: 0.5rem;
                text-align: left;
            }
            .markdown-preview th {
                background-color: #f9fafb;
                font-weight: 600;
            }
            .tab-button {
                transition: all 0.3s ease;
            }
            .tab-button.active {
                border-bottom: 3px solid #9333ea;
                color: #9333ea;
                font-weight: 600;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
                animation: fadeIn 0.3s ease-out;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .animate-fade-in {
                animation: fadeIn 0.3s ease-out;
            }
        </style>
    </head>
    <body class="bg-gradient-to-br from-purple-50 to-blue-50 min-h-screen">
        <div class="container mx-auto px-4 py-12 max-w-4xl">
            <div class="bg-white rounded-2xl shadow-xl p-8">
                <div class="flex justify-between items-start mb-8">
                    <div>
                        <h1 class="text-4xl font-bold text-gray-800 mb-2">📝 YouTube Transcript Extractor</h1>
                        <p class="text-gray-600">Extract and summarize YouTube video transcripts instantly</p>
                    </div>
                </div>
                
                <div class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">YouTube URL or Video ID</label>
                        <input type="text" id="videoUrl" placeholder="https://youtube.com/watch?v=dQw4w9WgXcQ" 
                               class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition">
                    </div>
                    
                    <div class="flex flex-wrap gap-6">
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" id="timestamps" checked class="mr-2 w-4 h-4 text-purple-600 rounded cursor-pointer">
                            <span class="text-sm text-gray-700">Include timestamps</span>
                        </label>
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" id="summary" unchecked class="mr-2 w-4 h-4 text-purple-600 rounded cursor-pointer">
                            <span class="text-sm text-gray-700">Generate AI summary</span>
                        </label>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Summary Language</label>
                        <select id="summaryLang" class="px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-500 outline-none cursor-pointer">
                            <option value="auto">Auto-detect</option>
                            <option value="en">English</option>
                            <option value="ja">Japanese (日本語)</option>
                        </select>
                    </div>
                    
                    <button onclick="extractTranscript()" 
                            class="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all transform hover:scale-105">
                        Extract Transcript
                    </button>
                </div>
                
                <div id="progress" class="mt-6 hidden">
                    <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded animate-fade-in">
                        <p class="text-sm text-blue-700" id="progressText">Processing...</p>
                    </div>
                </div>
                
                <div id="result" class="mt-6 hidden animate-fade-in">
                    <h2 class="text-2xl font-bold mb-4">Results</h2>
                    
                    <!-- Tabs -->
                    <div class="border-b border-gray-200 mb-6">
                        <div class="flex space-x-8">
                            <button id="transcriptTab" onclick="switchTab('transcript')" 
                                    class="tab-button pb-3 text-gray-600 hover:text-purple-600 active">
                                📄 Transcript
                            </button>
                            <button id="summaryTab" onclick="switchTab('summary')" 
                                    class="tab-button pb-3 text-gray-600 hover:text-purple-600 hidden">
                                ✨ AI Summary
                            </button>
                        </div>
                    </div>
                    
                    <!-- Tab Contents -->
                    <div>
                        <!-- Transcript Tab -->
                        <div id="transcriptContent" class="tab-content active">
                            <div class="bg-white border-2 border-gray-200 rounded-xl p-6">
                                <div class="flex justify-between items-center mb-4">
                                    <div>
                                        <h3 class="font-bold text-lg">📄 Full Transcript</h3>
                                        <p class="text-sm text-gray-500" id="transcriptMeta"></p>
                                    </div>
                                    <div class="flex gap-2 flex-wrap">
                                        <button onclick="copyTranscript()" 
                                                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition text-sm">
                                            📋 Copy
                                        </button>
                                        <button onclick="downloadTranscript()" 
                                                class="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition text-sm">
                                            ⬇️ Download
                                        </button>
                                    </div>
                                </div>
                                <div id="transcriptDisplay" class="markdown-preview bg-gray-50 p-4 rounded-lg"></div>
                            </div>
                        </div>
                        
                        <!-- Summary Tab -->
                        <div id="summaryContent" class="tab-content">
                            <div class="bg-white border-2 border-gray-200 rounded-xl p-6">
                                <div class="flex justify-between items-center mb-4">
                                    <div>
                                        <h3 class="font-bold text-lg">✨ Full AI Summary</h3>
                                        <p class="text-sm text-gray-500">Generated with Gemini AI</p>
                                    </div>
                                    <div class="flex gap-2 flex-wrap">
                                        <button onclick="copySummary()" 
                                                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition text-sm">
                                            📋 Copy
                                        </button>
                                        <button onclick="downloadSummary()" 
                                                class="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition text-sm">
                                            ⬇️ Download
                                        </button>
                                    </div>
                                </div>
                                <div id="summaryDisplay" class="markdown-preview bg-gray-50 p-4 rounded-lg"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/common.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked-katex-extension@5.0.1/dist/index.umd.min.js"></script>
        
        <script>
            // Configure marked with extensions
            marked.use({
                gfm: true,
                breaks: true
            });
            
            // Add syntax highlighting
            marked.setOptions({
                highlight: function(code, lang) {
                    if (lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (e) {
                            console.error(e);
                        }
                    }
                    return hljs.highlightAuto(code).value;
                }
            });
            
            // Add KaTeX for math rendering
            if (typeof markedKatex !== 'undefined') {
                marked.use(markedKatex());
            }
            
            let currentJobId = null;
            let transcriptData = null;
            let summaryData = null;
            let videoId = null;
            
            function switchTab(tab) {
                // Update tab buttons
                document.getElementById('transcriptTab').classList.remove('active');
                document.getElementById('summaryTab').classList.remove('active');
                document.getElementById(tab + 'Tab').classList.add('active');
                
                // Update tab contents
                document.getElementById('transcriptContent').classList.remove('active');
                document.getElementById('summaryContent').classList.remove('active');
                document.getElementById(tab + 'Content').classList.add('active');
            }
            
            async function extractTranscript() {
                const url = document.getElementById('videoUrl').value.trim();
                const timestamps = document.getElementById('timestamps').checked;
                const summary = document.getElementById('summary').checked;
                const summaryLang = document.getElementById('summaryLang').value;
                
                if (!url) {
                    showToast('Please enter a YouTube URL or video ID', 'error');
                    return;
                }
                
                // Reset UI state
                document.getElementById('result').classList.add('hidden');
                document.getElementById('progress').classList.remove('hidden');
                document.getElementById('progressText').textContent = 'Starting...';
                
                // Clear previous data
                transcriptData = null;
                summaryData = null;
                videoId = null;
                currentJobId = null;
                
                // Reset tabs
                document.getElementById('summaryTab').classList.add('hidden');
                switchTab('transcript');
                
                try {
                    const response = await fetch('/api/extract', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            url, 
                            include_timestamps: timestamps,
                            generate_summary: summary,
                            summary_lang: summaryLang
                        })
                    });
                    
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.detail || 'Failed to start extraction');
                    }
                    
                    const data = await response.json();
                    currentJobId = data.job_id;
                    
                    // Poll for status
                    pollStatus();
                } catch (error) {
                    document.getElementById('progress').classList.add('hidden');
                    showToast('Error: ' + error.message, 'error');
                }
            }
            
            async function pollStatus() {
                try {
                    const response = await fetch(`/api/status/${currentJobId}`);
                    const data = await response.json();
                    
                    document.getElementById('progressText').textContent = data.progress;
                    
                    if (data.status === 'completed') {
                        document.getElementById('progress').classList.add('hidden');
                        document.getElementById('result').classList.remove('hidden');
                        
                        transcriptData = data.result.transcript;
                        videoId = data.result.video_id;
                        
                        // Show metadata
                        const wordCount = transcriptData.split(/\s+/).length;
                        document.getElementById('transcriptMeta').textContent = 
                            `${wordCount.toLocaleString()} words • ${Math.ceil(wordCount / 200)} min read`;
                        
                        // Render full transcript
                        document.getElementById('transcriptDisplay').innerHTML = marked.parse(transcriptData);
                        
                        // Switch to transcript tab by default
                        switchTab('transcript');
                        
                        if (data.result.summary) {
                            summaryData = data.result.summary;
                            document.getElementById('summaryTab').classList.remove('hidden');
                            document.getElementById('summaryDisplay').innerHTML = marked.parse(summaryData);
                        }
                        
                        showToast('Transcript extracted successfully!', 'success');
                    } else if (data.status === 'error') {
                        document.getElementById('progress').classList.add('hidden');
                        showToast('Error: ' + data.error, 'error');
                    } else {
                        setTimeout(pollStatus, 1000);
                    }
                } catch (error) {
                    document.getElementById('progress').classList.add('hidden');
                    showToast('Error: ' + error.message, 'error');
                }
            }
            
            // Copy functions
            async function copyTranscript() {
                if (!transcriptData) {
                    showToast('No transcript data available', 'error');
                    return;
                }
                try {
                    await navigator.clipboard.writeText(transcriptData);
                    showToast('Transcript copied to clipboard!', 'success');
                } catch (error) {
                    console.error('Copy failed:', error);
                    showToast('Failed to copy: ' + error.message, 'error');
                }
            }
            
            async function copySummary() {
                if (!summaryData) {
                    showToast('No summary data available', 'error');
                    return;
                }
                try {
                    await navigator.clipboard.writeText(summaryData);
                    showToast('Summary copied to clipboard!', 'success');
                } catch (error) {
                    console.error('Copy failed:', error);
                    showToast('Failed to copy: ' + error.message, 'error');
                }
            }
            
            // Toast notification
            function showToast(message, type = 'info') {
                const colors = {
                    success: 'bg-green-500',
                    error: 'bg-red-500',
                    info: 'bg-blue-500'
                };
                
                const toast = document.createElement('div');
                toast.className = `fixed bottom-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in`;
                toast.textContent = message;
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    toast.style.opacity = '0';
                    toast.style.transition = 'opacity 0.3s';
                    setTimeout(() => toast.remove(), 300);
                }, 3000);
            }
            
            // Download functions
            function downloadTranscript() {
                const filename = `${videoId}_transcript.md`;
                downloadFile(transcriptData, filename);
            }
            
            function downloadSummary() {
                const filename = `${videoId}_summary.md`;
                downloadFile(summaryData, filename);
            }
            
            function downloadFile(content, filename) {
                const blob = new Blob([content], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                showToast(`Downloaded ${filename}`, 'success');
            }
            
            // Allow Enter key to submit
            document.getElementById('videoUrl').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    extractTranscript();
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/api/extract")
async def extract_transcript(request: TranscriptRequest, background_tasks: BackgroundTasks):
    job_id = os.urandom(8).hex()
    jobs[job_id] = JobStatus(status="pending", progress="Starting...")
    
    background_tasks.add_task(process_transcript, job_id, request)
    
    return {"job_id": job_id}

async def process_transcript(job_id: str, request: TranscriptRequest):
    try:
        jobs[job_id].status = "processing"
        jobs[job_id].progress = "Extracting video ID..."
        
        video_id = extract_video_id(request.url)
        if not video_id:
            raise ValueError("Invalid YouTube URL or video ID")
        
        jobs[job_id].progress = "Fetching video information..."
        video_info, transcript_data = get_video_info_and_transcript(video_id)
        
        if not video_info:
            raise ValueError("Failed to get video information")
        
        if not transcript_data:
            raise ValueError("No transcript available for this video")
        
        jobs[job_id].progress = "Downloading transcript..."
        transcript = download_and_parse_transcript(transcript_data)
        
        if not transcript:
            raise ValueError("Failed to parse transcript")
        
        jobs[job_id].progress = "Converting to markdown..."
        markdown = transcript_to_markdown(transcript, video_info, request.include_timestamps)
        
        result = {
            "transcript": markdown,
            "video_id": video_id,
            "video_title": video_info.get('title', 'Unknown'),
            "video_info": video_info
        }
        
        if request.generate_summary:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and api_key != "YOUR_GEMINI_API_KEY":
                jobs[job_id].progress = "Generating AI summary..."
                
                text_to_summarize = markdown[:50000]
                summary = call_gemini_api(text_to_summarize, api_key, request.summary_lang)
                
                if summary:
                    result["summary"] = create_summary_markdown(video_info, summary)
                else:
                    jobs[job_id].progress = "Note: Summary generation failed, but transcript is ready"
        
        jobs[job_id].status = "completed"
        jobs[job_id].progress = "Complete! 🎉"
        jobs[job_id].result = result
        
    except Exception as e:
        jobs[job_id].status = "error"
        jobs[job_id].error = str(e)
        jobs[job_id].progress = f"Error: {str(e)}"

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("\n\n🚀 Starting YouTube Transcript Extractor...\n")
    print("🌐 Open in your browser: \n\n       ➡️ ➡️  http://localhost:8000\n\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)