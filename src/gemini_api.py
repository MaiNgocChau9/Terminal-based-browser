import os
from google import genai
from google.genai import types

def gemini_client(api_key=None):
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def gemini_chat(query, api_key=None, model="gemini-2.5-flash-preview-05-20"):
    client = gemini_client(api_key)
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)],
        ),
    ]
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="text/plain"
        ),
    )
    return response.text if hasattr(response, "text") else str(response)

def gemini_search(query, api_key=None, model="gemini-2.5-flash-preview-05-20"):
    client = gemini_client(api_key)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=(
                    f"Search: {query}\n"
                    "Hãy trả về kết quả dưới dạng một mảng JSON, mỗi phần tử có dạng:\n"
                    "{ \"title\": ..., \"link\": ... }\n"
                    "Chỉ trả về đúng block code JSON, không thêm giải thích, không thêm text ngoài block code."
                )),
            ],
        ),
    ]
    tools = [
        types.Tool(google_search=types.GoogleSearch()),
    ]
    generate_content_config = types.GenerateContentConfig(
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
    import re, json as _json
    text = response.text if hasattr(response, "text") else str(response)
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            arr = _json.loads(match.group(0))
            return arr
        except Exception:
            pass
    return text

def html_to_markdown_ai(html, api_key=None, model="gemini-2.5-flash-preview-05-20"):
    """
    Chuyển HTML sang markdown bằng Gemini AI.
    """
    client = gemini_client(api_key)
    prompt = (
        "Chuyển đổi HTML sau thành markdown để đọc trên terminal, chỉ giữ lại:\n"
        "- Tiêu đề bài viết (dùng # Title)\n"
        "- Nội dung chính (không sidebar, không quảng cáo, không menu, không footer)\n"
        "- Hình ảnh đúng định dạng markdown ![alt](url), không chuyển ảnh thành link, không giữ <a> ngoài markdown.\n"
        "- Không giữ lại class/style, không giải thích thêm, chỉ trả về markdown thuần.\n\n"
        "HTML:\n"
    )
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt + html)],
        ),
    ]
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="text/plain"
        ),
    )
    return response.text if hasattr(response, "text") else str(response)
