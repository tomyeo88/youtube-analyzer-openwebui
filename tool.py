import os
import re
import base64
import requests
from datetime import datetime
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from openai import OpenAI
from PIL import Image
from io import BytesIO
import json

class Tools:
    def __init__(self):
        # Initialize OpenAI client for Gemini API
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
        )
        self.model = os.getenv("DEFAULT_MODELS", "gemini-2.5-flash-preview-05-20")

    def extract_youtube_video_id(self, url: str) -> str:
        """Extract YouTube video ID from various URL formats."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_youtube_transcript(self, video_id: str) -> str:
        """Get transcript for a YouTube video."""
        try:
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get the best available transcript
            transcript = None
            
            # First try English
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                # If no English, get any available transcript
                try:
                    # Get the first available transcript
                    for available_transcript in transcript_list:
                        transcript = available_transcript
                        break
                except:
                    pass
            
            if transcript is None:
                return "Error getting transcript: No transcripts available"
            
            # Fetch the actual transcript data
            transcript_data = transcript.fetch()
            
            # Extract text from transcript entries
            if isinstance(transcript_data, list):
                full_transcript = " ".join([
                    entry.get('text', '') if isinstance(entry, dict) else str(entry)
                    for entry in transcript_data
                ])
            else:
                full_transcript = str(transcript_data)
            
            return full_transcript
            
        except Exception as e:
            return f"Error getting transcript: {str(e)}"

    def get_youtube_metadata(self, url: str) -> dict:
        """Get YouTube video metadata including thumbnail."""
        video_id = self.extract_youtube_video_id(url)
        
        try:
            # Sometimes PyTube can have issues, so we'll add retry logic
            import time
            max_retries = 2  # Reduced retries to fail faster
            for attempt in range(max_retries):
                try:
                    yt = YouTube(url)
                    
                    metadata = {
                        'title': yt.title,
                        'description': yt.description,
                        'length': yt.length,
                        'views': yt.views,
                        'author': yt.author,
                        'publish_date': yt.publish_date.isoformat() if yt.publish_date else None,
                        'thumbnail_url': yt.thumbnail_url
                    }
                    
                    return metadata
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(0.5)  # Shorter wait
            
        except Exception as e:
            # If PyTube fails, return basic info with working thumbnail URL
            print(f"PyTube failed: {e}, using fallback method")
            return {
                'title': f'YouTube Video',
                'description': 'Video description unavailable (using fallback method)',
                'length': 0,
                'views': 'Unknown',
                'author': 'Unknown Channel',
                'publish_date': None,
                'thumbnail_url': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                'fallback_mode': True
            }

    def encode_image_from_url(self, image_url: str) -> str:
        """Download and encode image from URL to base64."""
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            # Convert to base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            return image_data
            
        except Exception as e:
            return None

    def analyze_video_with_gemini(self, youtube_url: str) -> str:
        """
        Analyze YouTube video directly using Gemini's video understanding capability.
        """
        try:
            # Prepare the analysis prompt for video understanding
            analysis_prompt = """
            Please analyze this YouTube video and provide a comprehensive summary. Include:

            1. A concise summary (2-3 sentences) of the main topic and content
            2. Key points covered in the video (bullet points)
            3. Target audience and content style assessment
            4. Main takeaways or conclusions
            5. Overall assessment of content quality and production value
            6. Any notable visual elements, graphics, or presentation style

            Focus on both the spoken content and visual elements of the video.
            """

            # Use Gemini's video understanding with the YouTube URL
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "video",
                            "video": {
                                "url": youtube_url
                            }
                        }
                    ]
                }
            ]
            
            # Call Gemini API with video understanding
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing video with Gemini: {str(e)}"

    def summarize_youtube_video(
        self,
        youtube_url: str = Field(
            ..., description="The YouTube video URL to analyze and summarize."
        ),
    ) -> str:
        """
        Analyze and summarize a YouTube video using Gemini's native video understanding.
        Falls back to transcript + thumbnail analysis if video understanding fails.
        """
        
        # Extract video ID
        video_id = self.extract_youtube_video_id(youtube_url)
        if not video_id:
            return "Error: Invalid YouTube URL format."
        
        # Get video metadata
        metadata = self.get_youtube_metadata(youtube_url)
        
        # Try Gemini's native video understanding first
        print("Attempting video analysis with Gemini's video understanding...")
        gemini_analysis = self.analyze_video_with_gemini(youtube_url)
        
        if not gemini_analysis.startswith("Error"):
            # Video understanding succeeded
            result = f"""
# YouTube Video Summary (Video Analysis)

**Video:** {metadata.get('title', 'N/A')}
**Channel:** {metadata.get('author', 'N/A')}
**Duration:** {metadata.get('length', 0)//60}:{metadata.get('length', 0)%60:02d}
**Views:** {metadata.get('views', 'Unknown')}

---

{gemini_analysis}

---
*Analysis completed using Gemini 2.5 Flash Video Understanding*
            """
            return result.strip()
        
        # Fallback to transcript + thumbnail analysis
        print("Video understanding failed, falling back to transcript + thumbnail analysis...")
        print(f"Video understanding error: {gemini_analysis}")
        
        # Get transcript
        transcript = self.get_youtube_transcript(video_id)
        if transcript.startswith("Error"):
            # If transcript fails, we can still provide thumbnail analysis
            transcript = "Transcript not available for this video. Analysis will be based on thumbnail and metadata only."
        
        # Get and encode thumbnail
        thumbnail_base64 = None
        if metadata.get('thumbnail_url'):
            thumbnail_base64 = self.encode_image_from_url(metadata['thumbnail_url'])
        
        # Prepare the analysis prompt
        analysis_prompt = f"""
        Please analyze this YouTube video and provide a comprehensive summary. Here's the information:

        **Video Metadata:**
        - Title: {metadata.get('title', 'N/A')}
        - Author: {metadata.get('author', 'N/A')}
        - Duration: {metadata.get('length', 0)} seconds
        - Views: {metadata.get('views', 'N/A')}
        - Published: {metadata.get('publish_date', 'N/A')}

        **Video Content:**
        {transcript[:3000]}  # Limit transcript to avoid token limits

        Please provide:
        1. A concise summary (2-3 sentences) of the main topic
        2. Key points covered in the video (bullet points)
        3. Target audience and content style
        4. Main takeaways or conclusions
        5. Overall assessment of content quality

        Focus on the actual content rather than just metadata.
        """

        try:
            # Start with text-only analysis
            messages = [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ]
            
            # Call Gemini API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content
            
            # Add thumbnail analysis if available
            thumbnail_analysis = ""
            if metadata.get('thumbnail_url') and not metadata.get('fallback_mode'):
                thumbnail_base64 = self.encode_image_from_url(metadata['thumbnail_url'])
                if thumbnail_base64:
                    print("Adding thumbnail analysis...")
                    thumbnail_messages = [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please analyze this YouTube video thumbnail and comment on its visual appeal, design quality, and how well it represents the content."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{thumbnail_base64}"
                                    }
                                }
                            ]
                        }
                    ]
                    
                    thumbnail_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=thumbnail_messages,
                        max_tokens=300,
                        temperature=0.7
                    )
                    
                    thumbnail_analysis = f"\n\n**Thumbnail Analysis:**\n{thumbnail_response.choices[0].message.content}"
            
            # Format the final response
            result = f"""
# YouTube Video Summary (Fallback Method)

**Video:** {metadata.get('title', 'N/A')}
**Channel:** {metadata.get('author', 'N/A')}
**Duration:** {metadata.get('length', 0)//60}:{metadata.get('length', 0)%60:02d}
**Views:** {metadata.get('views', 'Unknown')}

---

{summary}{thumbnail_analysis}

---
*Analysis completed using Gemini 2.5 Flash (Fallback: Transcript + Thumbnail)*
            """
            
            return result.strip()
            
        except Exception as e:
            return f"Error during analysis: {str(e)}"
	
    def get_user_name_and_email_and_id(self, __user__: dict = {}) -> str:
        """
        Get the user name, Email and ID from the user object.
        """
        # Do not include a descrption for __user__ as it should not be shown in the tool's specification
        # The session user object will be passed as a parameter when the function is called

        result = ""
        if "name" in __user__:
            result += f"User: {__user__['name']}"
        if "id" in __user__:
            result += f" (ID: {__user__['id']})"
        if "email" in __user__:
            result += f" (Email: {__user__['email']})"

        if result == "":
            result = "User: Unknown"

        return result

    def get_current_time(self) -> str:
        """
        Get the current time in a more human-readable format.
        """
        now = datetime.now()
        current_time = now.strftime("%I:%M:%S %p")
        current_date = now.strftime("%A, %B %d, %Y")
        return f"Current Date and Time = {current_date}, {current_time}"
