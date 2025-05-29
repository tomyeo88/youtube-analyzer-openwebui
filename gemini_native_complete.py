"""
title: Google AI Studio (Gemini) Native API Integration for OpenWebUI
author: CaptResolve
version: 2.0
license: MIT
requirements: pydantic>=2.0.0, aiohttp>=3.8.0
environment_variables:
    - GEMINI_API_KEY (required)
Supports:
- All Gemini models (2.0 and 1.5 series)
- Streaming responses
- Image/multimodal inputs
- Native Gemini API features
"""

import json
import logging
import base64
from typing import List, Dict, Union, AsyncIterator
from pydantic import BaseModel
from open_webui.utils.misc import pop_system_message
import aiohttp


class Pipe:
    # Using the native Gemini API endpoint
    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    class Valves(BaseModel):
        GEMINI_API_KEY: str = "Your API Key Here"

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.type = "manifold"
        self.id = "gemini_native"
        self.valves = self.Valves()

    def get_gemini_models(self) -> List[dict]:
        """Return all supported Gemini models"""
        models = [
            # Gemini 2.5 models (latest)
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
                "context_length": 1048576,  # 1M tokens
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
        return self.get_gemini_models()

    def _convert_role(self, role: str) -> str:
        """Convert OpenWebUI roles to Gemini roles"""
        role_mapping = {
            "user": "user",
            "assistant": "model",
            "system": "user"  # System messages are treated as user messages in Gemini
        }
        return role_mapping.get(role, "user")

    def _format_content_for_gemini(self, content, role: str):
        """Convert content to Gemini format"""
        if isinstance(content, str):
            return {"text": content}
        
        # Handle multimodal content
        parts = []
        
        for item in content:
            if item["type"] == "text":
                parts.append({"text": item["text"]})
            elif item["type"] == "image_url" and "url" in item["image_url"]:
                image_url = item["image_url"]["url"]
                if image_url.startswith("data:image"):
                    # Extract base64 data and mime type
                    header, data = image_url.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                    
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": data
                        }
                    })
                else:
                    # For URL images, we'd need to fetch and convert to base64
                    # For now, we'll add a text description
                    parts.append({"text": f"[Image URL: {image_url}]"})
        
        return parts if len(parts) > 1 else parts[0] if parts else {"text": ""}

    async def pipe(
        self, body: Dict, __event_emitter__=None
    ) -> Union[str, AsyncIterator[str]]:
        """Process a request to the native Gemini API."""
        if not self.valves.GEMINI_API_KEY or self.valves.GEMINI_API_KEY == "Your API Key Here":
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
                        "data": {"description": "Processing request...", "done": False},
                    }
                )

            system_message, messages = pop_system_message(body["messages"])
            model_name = body["model"].split("/")[-1]

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
                "temperature": body.get("temperature", 0.7),
                "topP": body.get("top_p", 0.95),
                "maxOutputTokens": body.get("max_tokens", 2048),
            }

            # Determine if streaming is requested
            is_streaming = body.get("stream", False)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Sending request to native Gemini API...",
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
            error_msg = f"Error: {str(e)}"
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

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, json=payload, params=params, timeout=60
                ) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        error_msg = f"Error: HTTP {response.status}: {response_text}"
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
                                    "description": "Request completed",
                                    "done": True,
                                },
                            }
                        )

                    return response_text
        except Exception as e:
            error_msg = f"Request error: {str(e)}"
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

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=headers, json=payload, params=params, timeout=60
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"Error: HTTP {response.status}: {error_text}"
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
                                    "description": "Stream completed",
                                    "done": True,
                                },
                            }
                        )
        except Exception as e:
            error_msg = f"Stream error: {str(e)}"
            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )
            yield error_msg
