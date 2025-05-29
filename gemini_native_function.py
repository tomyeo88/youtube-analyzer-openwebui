"""
title: Gemini Native API Pipe
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 2.0
requirements: pydantic>=2.0.0, aiohttp>=3.8.0
description: Direct connection to Google's Gemini API without OpenAI compatibility layer
"""

import json
import logging
import re
from typing import List, Dict, Union, AsyncIterator, Optional
from pydantic import BaseModel, Field
from open_webui.utils.misc import pop_system_message
import aiohttp


class Pipe:
    """Native Gemini API Pipe for OpenWebUI"""
    
    # Using the native Gemini API endpoint
    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    class Valves(BaseModel):
        """Configuration valves for the Gemini API pipe"""
        GEMINI_API_KEY: str = Field(
            default="",
            description="Your Google AI Studio (Gemini) API key. Get it from https://aistudio.google.com/"
        )
        DEFAULT_MODEL: str = Field(
            default="gemini-1.5-flash",
            description="Default Gemini model to use"
        )
        MAX_TOKENS: int = Field(
            default=2048,
            description="Maximum number of tokens to generate"
        )
        TEMPERATURE: float = Field(
            default=0.7,
            description="Temperature for response generation (0.0 - 1.0)"
        )
        ENABLE_VISION: bool = Field(
            default=True,
            description="Enable vision/multimodal capabilities including video understanding"
        )
        AUTO_DETECT_YOUTUBE: bool = Field(
            default=True,
            description="Automatically detect and process YouTube URLs in text messages"
        )
        DEFAULT_VIDEO_FPS: float = Field(
            default=1.0,
            description="Default frames per second for video processing (1.0 = 1 frame per second)"
        )

    def __init__(self):
        """Initialize the Gemini Native API Pipe"""
        logging.basicConfig(level=logging.INFO)
        self.type = "manifold"
        self.id = "gemini_native"
        self.name = "Gemini Native API"
        self.valves = self.Valves()

    def get_gemini_models(self) -> List[dict]:
        """Return all supported Gemini models"""
        models = [
            # Gemini 2.5 models (latest from your .env)
            {
                "id": "gemini/gemini-2.5-flash-preview-05-20",
                "name": "gemini-2.5-flash-preview-05-20",
                "context_length": 1048576,  # 1M tokens
                "supports_vision": True,
                "description": "Latest Gemini 2.5 preview model with enhanced capabilities",
            },
            # Gemini 2.0 models
            {
                "id": "gemini/gemini-2.0-flash-exp",
                "name": "gemini-2.0-flash-exp",
                "context_length": 1048576,
                "supports_vision": True,
                "description": "Latest experimental version with enhanced capabilities",
            },
            {
                "id": "gemini/gemini-2.0-flash-thinking-exp",
                "name": "gemini-2.0-flash-thinking-exp",
                "context_length": 1048576,
                "supports_vision": True,
                "description": "Experimental model with enhanced reasoning capabilities",
            },
            # Gemini 1.5 models
            {
                "id": "gemini/gemini-1.5-flash",
                "name": "gemini-1.5-flash",
                "context_length": 1048576,
                "supports_vision": True,
                "description": "Fast and versatile performance for diverse tasks",
            },
            {
                "id": "gemini/gemini-1.5-flash-8b",
                "name": "gemini-1.5-flash-8b",
                "context_length": 1048576,
                "supports_vision": True,
                "description": "8B parameter model for high volume tasks",
            },
            {
                "id": "gemini/gemini-1.5-pro",
                "name": "gemini-1.5-pro",
                "context_length": 1048576,
                "supports_vision": True,
                "description": "Complex reasoning tasks requiring more intelligence",
            },
        ]
        return models

    def pipes(self) -> List[dict]:
        """Return available model pipes"""
        return self.get_gemini_models()

    def _convert_role(self, role: str) -> str:
        """Convert OpenWebUI roles to Gemini roles"""
        role_mapping = {
            "user": "user",
            "assistant": "model",
            "system": "user"  # System messages are treated as user messages in Gemini
        }
        return role_mapping.get(role, "user")

    def _detect_youtube_urls(self, text: str) -> List[str]:
        """Extract YouTube URLs from text"""
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/v/[\w-]+'
        ]
        
        urls = []
        for pattern in youtube_patterns:
            urls.extend(re.findall(pattern, text))
        return urls

    def _format_content_for_gemini(self, content, role: str):
        """Convert content to Gemini format"""
        if isinstance(content, str):
            # Check if the text contains YouTube URLs
            youtube_urls = self._detect_youtube_urls(content)
            if youtube_urls and self.valves.ENABLE_VISION and self.valves.AUTO_DETECT_YOUTUBE:
                parts = []
                remaining_text = content
                
                # Add each YouTube URL as a separate part
                for url in youtube_urls:
                    video_part = {
                        "file_data": {
                            "file_uri": url
                        }
                    }
                    
                    # Add default video metadata if FPS is not 1.0
                    if self.valves.DEFAULT_VIDEO_FPS != 1.0:
                        video_part["video_metadata"] = {
                            "fps": self.valves.DEFAULT_VIDEO_FPS
                        }
                    
                    parts.append(video_part)
                    logging.info(f"Auto-detected YouTube video: {url}")
                    # Remove the URL from the text to avoid duplication
                    remaining_text = remaining_text.replace(url, "").strip()
                
                # Add remaining text if any
                if remaining_text:
                    parts.append({"text": remaining_text})
                
                return parts if len(parts) > 1 else parts[0] if parts else {"text": content}
            else:
                return {"text": content}
        
        # Handle multimodal content
        parts = []
        
        if not self.valves.ENABLE_VISION:
            # If vision is disabled, convert everything to text
            for item in content:
                if item["type"] == "text":
                    parts.append({"text": item["text"]})
                elif item["type"] == "image_url":
                    parts.append({"text": "[Image content not processed - vision disabled]"})
                elif item["type"] == "video_url":
                    parts.append({"text": "[Video content not processed - vision disabled]"})
            return parts if len(parts) > 1 else parts[0] if parts else {"text": ""}
        
        for item in content:
            if item["type"] == "text":
                text_content = item["text"]
                # Check for YouTube URLs in text
                youtube_urls = self._detect_youtube_urls(text_content)
                if youtube_urls and self.valves.AUTO_DETECT_YOUTUBE:
                    remaining_text = text_content
                    
                    # Add each YouTube URL as a separate part
                    for url in youtube_urls:
                        video_part = {
                            "file_data": {
                                "file_uri": url
                            }
                        }
                        
                        # Add default video metadata if FPS is not 1.0
                        if self.valves.DEFAULT_VIDEO_FPS != 1.0:
                            video_part["video_metadata"] = {
                                "fps": self.valves.DEFAULT_VIDEO_FPS
                            }
                        
                        parts.append(video_part)
                        logging.info(f"Auto-detected YouTube video: {url}")
                        # Remove the URL from the text to avoid duplication
                        remaining_text = remaining_text.replace(url, "").strip()
                    
                    # Add remaining text if any
                    if remaining_text:
                        parts.append({"text": remaining_text})
                else:
                    parts.append({"text": text_content})
            elif item["type"] == "image_url" and "url" in item["image_url"]:
                image_url = item["image_url"]["url"]
                if image_url.startswith("data:image"):
                    # Extract base64 data and mime type
                    try:
                        header, data = image_url.split(",", 1)
                        mime_type = header.split(";")[0].split(":")[1]
                        
                        parts.append({
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": data
                            }
                        })
                    except Exception as e:
                        logging.error(f"Error processing image: {e}")
                        parts.append({"text": "[Error processing image]"})
                else:
                    # For URL images, we'd need to fetch and convert to base64
                    # For now, we'll add a text description
                    parts.append({"text": f"[Image URL: {image_url}]"})
            elif item["type"] == "video_url" and "url" in item["video_url"]:
                video_url = item["video_url"]["url"]
                
                # Handle YouTube URLs
                if "youtube.com/watch" in video_url or "youtu.be/" in video_url:
                    video_part = {
                        "file_data": {
                            "file_uri": video_url
                        }
                    }
                    
                    # Add video metadata if provided
                    if "video_metadata" in item["video_url"]:
                        video_part["video_metadata"] = item["video_url"]["video_metadata"]
                    
                    parts.append(video_part)
                    logging.info(f"Added YouTube video: {video_url}")
                elif video_url.startswith("data:video"):
                    # Handle inline video data
                    try:
                        header, data = video_url.split(",", 1)
                        mime_type = header.split(";")[0].split(":")[1]
                        
                        video_part = {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": data
                            }
                        }
                        
                        # Add video metadata if provided
                        if "video_metadata" in item["video_url"]:
                            video_part["video_metadata"] = item["video_url"]["video_metadata"]
                        
                        parts.append(video_part)
                        logging.info(f"Added inline video data")
                    except Exception as e:
                        logging.error(f"Error processing video: {e}")
                        parts.append({"text": "[Error processing video]"})
                else:
                    # For other video URLs, add as text description
                    parts.append({"text": f"[Video URL: {video_url}]"})
        
        return parts if len(parts) > 1 else parts[0] if parts else {"text": ""}

    async def pipe(
        self, body: Dict, __user__: Optional[dict] = None, __event_emitter__=None
    ) -> Union[str, AsyncIterator[str]]:
        """Process a request to the native Gemini API."""
        
        # Validate API key
        if not self.valves.GEMINI_API_KEY or self.valves.GEMINI_API_KEY.strip() == "":
            error_msg = "Error: GEMINI_API_KEY is required. Please set your Gemini API key in the function settings."
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            return error_msg

        try:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "Processing request with native Gemini API...", "done": False},
                    }
                )

            # Extract system message and regular messages
            system_message, messages = pop_system_message(body["messages"])
            model_name = body["model"].split("/")[-1] if "/" in body["model"] else body["model"]

            # Log the request for debugging
            logging.info(f"Processing request for model: {model_name}")
            if __user__:
                logging.info(f"User: {__user__.get('name', 'Unknown')}")

            # Format messages for Gemini
            gemini_contents = []
            
            # Add system message as the first user message if present
            if system_message:
                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": f"System: {system_message}"}]
                })

            # Process other messages
            for message in messages:
                role = self._convert_role(message["role"])
                content = self._format_content_for_gemini(message["content"], role)
                
                # Ensure content is in parts format
                if isinstance(content, dict) and "text" in content:
                    parts = [content]
                elif isinstance(content, list):
                    parts = content
                else:
                    parts = [{"text": str(content)}]
                
                gemini_contents.append({
                    "role": role,
                    "parts": parts
                })

            # Create the payload for native Gemini API
            generation_config = {
                "temperature": body.get("temperature", self.valves.TEMPERATURE),
                "topP": body.get("top_p", 0.95),
                "maxOutputTokens": body.get("max_tokens", self.valves.MAX_TOKENS),
            }

            # Determine if streaming is requested
            is_streaming = body.get("stream", False)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Sending request to Gemini {model_name}...",
                            "done": False,
                        },
                    }
                )

            # Handle streaming vs non-streaming
            if is_streaming:
                return self._handle_streaming(
                    model_name, gemini_contents, generation_config, __event_emitter__
                )
            else:
                return await self._handle_normal(
                    model_name, gemini_contents, generation_config, __event_emitter__
                )

        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logging.error(error_msg)
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            return error_msg

    async def _handle_normal(self, model_name, contents, generation_config, __event_emitter__):
        """Handle non-streaming request using native Gemini API"""
        try:
            url = f"{self.API_BASE_URL}/{model_name}:generateContent"
            
            payload = {
                "contents": contents,
                "generationConfig": generation_config
            }

            headers = {
                "Content-Type": "application/json",
            }

            params = {
                "key": self.valves.GEMINI_API_KEY
            }

            logging.info(f"Making request to: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, json=payload, params=params, timeout=60
                ) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        error_msg = f"Gemini API Error: HTTP {response.status}: {response_text}"
                        logging.error(error_msg)
                        if __event_emitter__:
                            await __event_emitter__(
                                {
                                    "type": "status",
                                    "data": {"description": error_msg, "done": True},
                                }
                            )
                        return error_msg

                    data = json.loads(response_text)

                    # Extract response text from Gemini format
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            response_text = ""
                            for part in parts:
                                if "text" in part:
                                    response_text += part["text"]
                        else:
                            response_text = "No response generated"
                    else:
                        response_text = "No response generated"

                    if __event_emitter__:
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": "Request completed successfully",
                                    "done": True,
                                },
                            }
                        )

                    return response_text
        except Exception as e:
            error_msg = f"Request error: {str(e)}"
            logging.error(error_msg)
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            return error_msg

    async def _handle_streaming(self, model_name, contents, generation_config, __event_emitter__):
        """Handle streaming request using native Gemini API"""
        try:
            url = f"{self.API_BASE_URL}/{model_name}:streamGenerateContent"
            
            payload = {
                "contents": contents,
                "generationConfig": generation_config
            }

            headers = {
                "Content-Type": "application/json",
            }

            params = {
                "key": self.valves.GEMINI_API_KEY,
                "alt": "sse"
            }

            logging.info(f"Making streaming request to: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, json=payload, params=params, timeout=60
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"Gemini API Streaming Error: HTTP {response.status}: {error_text}"
                        logging.error(error_msg)
                        if __event_emitter__:
                            await __event_emitter__(
                                {
                                    "type": "status",
                                    "data": {"description": error_msg, "done": True},
                                }
                            )
                        yield error_msg
                        return

                    buffer = b""
                    async for chunk in response.content.iter_chunked(1024):
                        buffer += chunk
                        if b"\n" in buffer:
                            lines = buffer.split(b"\n")
                            buffer = lines.pop()

                            for line in lines:
                                line_text = line.decode("utf-8").strip()
                                if not line_text:
                                    continue

                                if line_text.startswith("data: "):
                                    line_text = line_text[6:]  # Remove "data: " prefix

                                try:
                                    data = json.loads(line_text)
                                    
                                    # Extract from Gemini streaming format
                                    if "candidates" in data and len(data["candidates"]) > 0:
                                        candidate = data["candidates"][0]
                                        if "content" in candidate and "parts" in candidate["content"]:
                                            parts = candidate["content"]["parts"]
                                            for part in parts:
                                                if "text" in part:
                                                    yield part["text"]
                                except json.JSONDecodeError:
                                    continue

                    # Process any remaining data in buffer
                    if buffer:
                        try:
                            line_text = buffer.decode("utf-8").strip()
                            if line_text.startswith("data: "):
                                line_text = line_text[6:]
                            
                            data = json.loads(line_text)
                            if "candidates" in data and len(data["candidates"]) > 0:
                                candidate = data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    parts = candidate["content"]["parts"]
                                    for part in parts:
                                        if "text" in part:
                                            yield part["text"]
                        except:
                            pass

                    if __event_emitter__:
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": "Streaming completed successfully",
                                    "done": True,
                                },
                            }
                        )
        except Exception as e:
            error_msg = f"Stream error: {str(e)}"
            logging.error(error_msg)
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            yield error_msg
