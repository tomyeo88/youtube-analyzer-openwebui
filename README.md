# YouTube Analyzer with Gemini Native API for OpenWebUI

A comprehensive YouTube video analysis tool with native Google Gemini API integration for OpenWebUI. This setup provides direct video understanding capabilities, enhanced performance, and access to the latest Gemini models.

## 🎯 Features

### YouTube Analysis Tool
- **Video Summarizer**: Analyzes YouTube videos using both transcript and thumbnail image
- **Content Understanding**: Direct video processing with Gemini 2.5 Flash Preview
- **Thumbnail Analysis**: Evaluates visual appeal and design quality
- **Comprehensive Summaries**: Structured summaries with key points and takeaways

### Gemini Native API Integration
- **Direct API Access**: Native connection to Google's Gemini API (no OpenAI compatibility layer)
- **Video Understanding**: Native YouTube URL processing and analysis
- **Auto-Detection**: Automatically detects and processes YouTube URLs in messages
- **All Gemini Models**: Support for Gemini 2.5, 2.0, and 1.5 series
- **Enhanced Performance**: Better latency and feature access
- **Streaming Support**: Real-time streaming responses
- **Multimodal Input**: Text, image, and video support

## 🚀 Quick Start

### Prerequisites
1. **Google AI Studio API Key**: Get your free key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Supabase Account**: For OpenWebUI database (optional for local setup)
3. **Python 3.10+** or **Docker**

### Option 1: Codespaces (Recommended)

1. **Open in Codespaces**
2. **Set Environment Variables** in Codespace settings:
   ```
   DATABASE_URL=your_supabase_connection_string
   PGVECTOR_DB_URL=your_supabase_connection_string
   OPENAI_API_KEY=your_gemini_api_key
   ```
3. **Run OpenWebUI**:
   ```bash
   dotenv run open-webui serve
   ```

### Option 2: Local Python Environment

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd youtube-analyzer-openwebui
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run OpenWebUI**:
   ```bash
   dotenv run open-webui serve
   ```

4. **Access**: Open [http://localhost:8080](http://localhost:8080)

## 🔧 Setup Native Gemini API

### 1. Install the Gemini Native Function

1. **Access OpenWebUI Admin**:
   - Go to your OpenWebUI instance
   - Click your profile → **Admin Panel** → **Functions**

2. **Install Function**:
   - Click **Create New Function**
   - Copy the entire content from `gemini_native_function.py`
   - Paste and **Save**

### 2. Configure API Key

1. **Function Settings**:
   - Find "Gemini Native API" in functions list
   - Click the settings (gear) icon
   - Set **GEMINI_API_KEY** to your Google AI Studio API key
   - Ensure **ENABLE_VISION**: `true`
   - Ensure **AUTO_DETECT_YOUTUBE**: `true`
   - **Save**

### 3. Available Models

The native function provides access to:

#### Gemini 2.5 Series (Latest)
- `gemini-2.5-flash-preview-05-20` - Latest with enhanced video capabilities

#### Gemini 2.0 Series  
- `gemini-2.0-flash-exp` - Latest experimental version
- `gemini-2.0-flash-thinking-exp` - Enhanced reasoning capabilities

#### Gemini 1.5 Series
- `gemini-1.5-flash` - Fast and versatile
- `gemini-1.5-flash-8b` - High volume tasks  
- `gemini-1.5-pro` - Complex reasoning (2M tokens)

## 🎥 Video Understanding Usage

### Basic Video Analysis
```
Analyze this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ
What are the main topics discussed?
```

### Multiple Videos
```
Compare these two videos:
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
```

### With Timestamps
```
What happens at 2:30 in this video?
https://www.youtube.com/watch?v=example
```

### Using the YouTube Analyzer Tool
```python
from tool import Tools

tools = Tools()
result = tools.summarize_youtube_video("https://www.youtube.com/watch?v=VIDEO_ID")
print(result)
```

## 🔄 Configuration Options

### Environment Variables (.env)
```properties
# Database (for OpenWebUI)
DATABASE_URL=your_supabase_connection_string
PGVECTOR_DB_URL=your_supabase_connection_string

# API Configuration
OPENAI_API_KEY=your_gemini_api_key
OPENAI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
DEFAULT_MODELS=gemini-2.5-flash-preview-05-20

# Embedding Configuration
RAG_EMBEDDING_ENGINE=openai
RAG_EMBEDDING_MODEL=text-embedding-004
```

### Native Function Settings
- **GEMINI_API_KEY**: Your Google AI Studio API key
- **ENABLE_VISION**: Enable video/image processing (default: true)
- **AUTO_DETECT_YOUTUBE**: Auto-detect YouTube URLs (default: true)
- **DEFAULT_VIDEO_FPS**: Video sampling rate (default: 1.0)
- **MAX_TOKENS**: Maximum response tokens (default: 2048)
- **TEMPERATURE**: Response creativity (default: 0.7)

## 🏗️ Architecture

### Native API vs OpenAI-Compatible

| Feature | OpenAI-Compatible | Native API |
|---------|------------------|------------|
| **Latency** | Higher (translation layer) | ✅ Lower (direct) |
| **Models** | Limited selection | ✅ All latest models |
| **Streaming** | Emulated | ✅ True SSE streaming |
| **Video Support** | Basic | ✅ Full YouTube processing |
| **Error Handling** | Generic | ✅ Gemini-specific |
| **Features** | OpenAI subset | ✅ Full Gemini capabilities |

### Technical Components
- **YouTube Transcript API**: Video transcript extraction
- **PyTube**: Video metadata extraction  
- **Gemini Native API**: Direct AI processing
- **Auto URL Detection**: Regex-based YouTube URL recognition
- **Multimodal Processing**: Text, image, and video content

## 🧪 Testing

### Test Native Function
```bash
python test_video_support.py
```

### Test YouTube Tool
```bash
python test_tool.py
```

### Expected Results
- **Before**: "I can see the URL but cannot analyze the video"
- **After**: Detailed video content analysis, transcription, visual descriptions

## 🔧 Troubleshooting

### Video Not Processing
1. **Check Settings**:
   - Ensure `ENABLE_VISION` = `true`
   - Ensure `AUTO_DETECT_YOUTUBE` = `true`
   - Verify Gemini API key is valid

2. **Video Requirements**:
   - Must be public YouTube video
   - Video should have available transcript
   - Try different video URL if issues persist

3. **Check Logs**:
   - Look for "Auto-detected YouTube video" messages
   - Verify no API quota errors

### Performance Issues
- Use `gemini-2.5-flash-preview-05-20` for best video support
- Lower `DEFAULT_VIDEO_FPS` for very long videos
- Process one video at a time for reliability
- Free tier: 8 hours of video per day limit

### Database Reset (if needed)
```sql
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS "' || rec.tablename || '" CASCADE;';
    END LOOP;
END $$;
```

⚠️ **CAUTION**: This deletes ALL database tables. Backup important data first.

## 📚 Additional Setup

### OpenWebUI Configuration
1. **Models**: Go to Settings → Models → Default Models
   - Select `gemini-2.5-flash-preview` or similar
2. **Embeddings**: Settings → Documents → Embedding
   - Engine: `https://generativelanguage.googleapis.com/v1beta/openai`
   - API Key: Your Google API key
   - Model: `text-embedding-004`

### Development Setup
- **Dependencies**: `pydantic>=2.0.0`, `aiohttp>=3.8.0`
- **Python**: 3.10+ required
- **Testing**: Run test files to verify functionality

## 🎯 Usage Limitations

- **YouTube**: Public videos only (no private/unlisted)
- **Transcripts**: Must be available (auto-generated OK)
- **API Limits**: Based on Google AI Studio quotas
- **File Size**: Videos <20MB for inline processing
- **Multiple Videos**: Up to 10 per request (Gemini 2.5+)

## 🔐 Security

- Keep API keys secure and never commit to version control
- Use environment variables for sensitive configuration
- Regular key rotation recommended
- Monitor API usage and costs

---

**Status**: ✅ Production Ready - Full video understanding capabilities matching Google AI Studio