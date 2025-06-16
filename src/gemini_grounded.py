import os
from google import genai
from google.genai import types

def search_with_grounding(query, api_key=None, model="gemini-2.5-flash-preview-05-20"):
    """
    Sử dụng Gemini với grounding (Google Search, UrlContext) để tìm kiếm.
    Trả về text kết quả (có thể parse link/title từ text).
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"Search: {query}, respond link and title website you've fetch. example: 1. (Title) [Full link]"),
            ],
        ),
    ]
    tools = [
        types.Tool(url_context=types.UrlContext()),
        types.Tool(google_search=types.GoogleSearch()),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        tools=tools,
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text="You are a search engine."),
        ],
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    # Trả về text kết quả
    return response.text if hasattr(response, "text") else str(response)
