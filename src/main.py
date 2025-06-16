import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

from gemini_api import gemini_chat, gemini_search
import subprocess

def show_image_url(url):
    """Hiển thị ảnh trong terminal bằng kitty +kitten icat"""
    try:
        subprocess.run(['kitty', '+kitten', 'icat', url], check=True)
    except subprocess.CalledProcessError:
        print(f"[Không thể hiển thị ảnh: {url}]")

def render_ascii_art(url, width=60):
    """Render ảnh dạng ASCII art"""
    try:
        from PIL import Image
        import requests
        from io import BytesIO
        img_resp = requests.get(url, timeout=10)
        img = Image.open(BytesIO(img_resp.content)).convert("L")
        img = img.resize((width, int(img.height * width / img.width * 0.5)))
        chars = "@%#*+=-:. "
        ascii_art = ""
        for y in range(img.height):
            for x in range(img.width):
                pixel = img.getpixel((x, y))
                ascii_art += chars[int(pixel / 255 * (len(chars)-1))]
            ascii_art += "\n"
        return ascii_art
    except Exception as e:
        return f"[Image error: {e}]"

def main():
    config = load_config()
    print("=== Terminal-based AI Browser ===")
    print("Image mode:", config.get("image_mode", "auto"))
    print("Nhập truy vấn tìm kiếm (hoặc 'q' để thoát):")

    while True:
        query = input("> ").strip()
        if query.lower() == 'q':
            print("Thoát.")
            break
        if not query:
            continue

        if query.lower().startswith("/web "):
            link = query[5:].strip()
            print(f"Đang tải nội dung từ: {link}")
            try:
                # Tải và làm sạch HTML
                import requests
                from bs4 import BeautifulSoup
                resp = requests.get(link, timeout=20)
                resp.raise_for_status()
                html = resp.text
                body_idx = html.lower().find("<body")
                if body_idx != -1:
                    html = html[body_idx:]
                soup = BeautifulSoup(html, "html.parser")
                for tag in soup.find_all(True):
                    for attr in ["class", "style"]:
                        if attr in tag.attrs:
                            del tag.attrs[attr]
                clean_html = str(soup)

                # Chuyển sang markdown bằng AI
                from gemini_api import html_to_markdown_ai
                markdown = html_to_markdown_ai(clean_html, config["gemini_api_key"])

                # In text và xử lý ảnh
                import re
                mode = config.get("image_mode", "auto")
                text_parts = re.split(r'(!\[.*?\]\(.*?\))', markdown)
                
                from rich.console import Console
                from rich.markdown import Markdown
                console = Console()

                for part in text_parts:
                    if part.startswith("!["):
                        # Phần ảnh
                        match = re.match(r'!\[(.*?)\]\((.*?)\)', part)
                        if match:
                            url = match.group(2)
                            if mode == "protocol":
                                show_image_url(url)
                            elif mode == "ascii":
                                print(render_ascii_art(url))
                            else:
                                print(f"[Image: {url}]")
                    else:
                        # Phần text
                        if part.strip():
                            md = Markdown(part)
                            console.print(md)

            except Exception as e:
                print("Lỗi:", e)
            continue

        if query.lower().startswith("search:"):
            result = gemini_search(query[7:].strip(), config["gemini_api_key"])
            print("\n[Kết quả tìm kiếm với grounding]:")
            if isinstance(result, list):
                for idx, item in enumerate(result, 1):
                    print(f"{idx}. {item.get('title','')}\n   {item.get('link','')}\n")
                
                while True:
                    sel = input("Chọn số thứ tự link để đọc (hoặc 'b' để quay lại): ").strip()
                    if sel.lower() == 'b':
                        break
                    if not sel.isdigit() or not (1 <= int(sel) <= len(result)):
                        print("Lựa chọn không hợp lệ.")
                        continue
                    # Mở link bằng lệnh /web
                    idx = int(sel) - 1
                    link = result[idx].get('link','')
                    title = result[idx].get('title','')
                    main_loop = True
                    query = f"/web {link}"
                    break
            else:
                print(result)
            continue

        text = gemini_chat(query, config["gemini_api_key"])
        print("\n[Gemini chatbot]:")
        print(text)

if __name__ == "__main__":
    main()
