import json
import urllib.request
import urllib.error
from utils import format_timestamp


def call_gemini_api(text, api_key, language='auto'):
    """Call Gemini API to summarize the transcript."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # Detect language if auto
    if language == 'auto':
        # Simple detection based on Japanese characters
        japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF')
        total_chars = len([char for char in text if char.isalpha() or '\u3040' <= char <= '\u9FAF'])
        
        if total_chars > 0 and japanese_chars / total_chars > 0.3:  # If >30% Japanese characters
            language = 'ja'
        else:
            language = 'en'
    
    # Prepare language-specific prompts
    if language == 'ja':
        # PROMPT FOR JAPANESE
        prompt = f"""
        あなたは熟練したテクニカルライター兼アナリストです。あなたのタスクは、提供された動画の文字起こしを、読みやすく構造化され、かつ学術的に正確なマークダウン形式の要約ドキュメントに変換することです。。
        
        【前処理ルール】
        - 文字起こしに同音異義語などの誤字・ASR誤認識があれば文脈で修正・削除して自然な日本語にしてください。ただし、**不確かな解釈箇所は[不確か]タグ**を付けて示してください。
        - 専門用語は原語（英語）が存在する場合は原語を括弧で併記してください（例：経験的リスク（empirical risk））。
        - 数式・アルゴリズムは可能な限りLaTeX形式で示してください（`$$...$$`）。
        
        **必ず以下の構成とマークダウン指定に厳密に従って、応答全体を作成してください：**
        
        ## 📝 要約
        動画の主題、目的、そして主要な発見についての簡潔な1段落の概要。
        
        ## 🔑 主要な概念とキーワード（原語も括弧で加える）
        - **用語A:** 簡潔な説明、重要度（高/中/低）。
        - **用語B:** ...
        
        ## ✨ 重要ポイント (箇条書き)
        動画から得られる重要なポイントや発見をいくつかリストアップしてください。簡潔で読みやすい箇条書きで、各項目は完全な文章にしてください。
        
        ## 📄 詳細な分析
        動画で提示された主要なアイデアを論理的・構造的に結びつけ、「背景」「仕組み（how）」「理由（why）」「関連する例または直感的な説明」を分かりやすく高校生にもわかるように解説してください。分量は説明の難易度に応じて調整してください。
        - 必要なら短い擬似コード、図式的の説明、または数式（LaTeX）を入れてください。
        - 長くなる場合は小見出し（###）で区切る。
        
        ## 💬 注目すべき引用
        中心的なアイデアを捉えている、最も重要または影響力のある引用を2〜3個、文字起こしから抽出してください。マークダウンの引用符（>）を使用してフォーマットしてください。
        > "影響力のある引用1..."
        > "影響力のある引用2..."
        
        ### 🧐 Critical Evaluation（批判的評価）
        動画の議論における **不足点、見落とされた視点、弱い論点、明らかな誤り** を指摘してください。また、説明を強化するためにどのような要素が含まれるべきだったかを提案してください。
        
        ## 🚀 実用的な学びと結論
        主要な学びで締めくくってください。この動画を視聴した後、視聴者は何をすべきか、何を記憶すべきか、または何を考慮すべきか。短い段落または最後のいくつかの箇条書きで記述できます。
        
        ---
        要約する文字起こしは以下の通りです：
        {text}
        """
    else:  # Default to English
        # PROMPT FOR ENGLISH
        prompt = f"""
        You are a skilled technical writer and analyst. Your task is to transform the provided video transcript into a well-structured, readable, and academically accurate summary document in Markdown format.
        
        ### Preprocessing Rules
        * If there are typos, homophones, or ASR misrecognitions in the transcript, correct or remove them based on context to produce natural language. However, for **uncertain interpretations, mark them with the [Uncertain] tag**.
        * Represent mathematical formulas or algorithms in LaTeX format whenever possible (`$$...$$`).
        
        **Strictly follow the structure and Markdown specifications below for your entire response:**
        
        ## 📝 Summary
        A concise one-paragraph overview of the video's topic, purpose, and key findings.
        
        ## 🔑 Key Concepts and Keywords
        * **Term A:** brief explanation, importance (high/medium/low).
        * **Term B:** ...
        
        ## ✨ Key Points (Bulleted List)
        List several key takeaways or findings from the video in concise, easy-to-read bullet points. Each item should be a complete sentence.
        
        ## 📄 Detailed Analysis
        Logically and structurally connect the main ideas presented in the video, and explain them in a way that even high school students can understand by covering "background", "how", "why", and "examples or intuitive explanations". Adjust the length according to the complexity of the explanation.
        * Include short pseudocode, schematic explanations, or formulas (LaTeX) where necessary.
        * If the section becomes long, divide it with subheadings (###).
        
        ## 💬 Notable Quotes
        Extract 2–3 of the most important or impactful quotes from the transcript that capture central ideas. Format them using Markdown blockquotes:
        > "Impactful Quote 1..."
        > "Impactful Quote 2..."
        
        ## 🧐 Critical Evaluation
        Point out any gaps, overlooked perspectives, weak arguments, or clear errors in the video's discussion. Also, suggest what could have been included to strengthen the explanation.
        
        ## 🚀 Practical Lessons and Conclusion
        Conclude with the key lessons learned. What should the viewer do, remember, or consider after watching this video? This can be expressed in a short paragraph or as a final set of bullet points.
        
        ---
        
        The transcript to summarize is as follows:
        {text}
        """
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    try:
        # Prepare the request
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data)
        req.add_header('Content-Type', 'application/json')
        
        print(f"Calling Gemini API for summarization (language: {language})...")
        
        # Make the request
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        # Extract the generated text
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                summary = candidate['content']['parts'][0]['text']
                print("Successfully generated summary")
                return summary
            else:
                print("Unexpected API response structure")
                return None
        else:
            print("No candidates in API response")
            return None
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return None


def create_summary_markdown(video_info, summary):
    """Create a markdown file with the Gemini-generated summary."""
    title = video_info.get('title', 'Unknown Title')
    video_id = video_info.get('id', 'Unknown ID')
    duration = video_info.get('duration', 0)
    
    markdown = f"# {title} - Summary\n\n"
    markdown += f"**Video ID:** {video_id}  \n"
    markdown += f"**YouTube URL:** https://www.youtube.com/watch?v={video_id}  \n"
    markdown += f"**Duration:** {format_timestamp(duration)}\n\n"
    markdown += "---\n\n"
    
    if summary:
        markdown += summary
    else:
        markdown += "*Failed to generate summary.*\n"
    
    markdown += "\n\n---\n\n"
    markdown += "*Summary generated using Gemini AI*\n"
    
    return markdown