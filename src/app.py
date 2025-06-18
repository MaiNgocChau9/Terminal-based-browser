from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Input, Static, Button, ListView, ListItem, 
    RichLog, TabbedContent, TabPane, Label, Markdown
)
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.message import Message
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
import asyncio
import json
import os
import re
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# Import các module hiện có
from gemini_api import gemini_chat, gemini_search, html_to_markdown_ai
from html_cleaner import fetch_and_clean_html

class SearchResultItem(ListItem):
    def __init__(self, title: str, url: str, index: int):
        super().__init__()
        self.title = title
        self.url = url
        self.index = index
        
    def compose(self) -> ComposeResult:
        # Make title clickable
        yield Static(f"{self.index}. {self.title}", classes="search-title")
        # Store URL as data attribute
        self.url = self.url # Store URL for later use

class HelpScreen(ModalScreen):
    """Màn hình hiển thị hướng dẫn sử dụng"""
    
    BINDINGS = [
        ("escape", "dismiss", "Đóng"),
        ("q", "dismiss", "Thoát")
    ]
    
    def compose(self) -> ComposeResult:
        help_text = """
# 🚀 Terminal AI Browser - Hướng dẫn sử dụng

## Phím tắt chính (giống Neovim)

### Chế độ Normal
- `i` - Vào chế độ Insert (nhập tìm kiếm)
- `:` - Vào chế độ Command 
- `j/k` - Di chuyển lên/xuống trong danh sách
- `Enter` - Mở link được chọn
- `gg` - Về đầu danh sách
- `G` - Xuống cuối danh sách
- `ctrl+d` - Cuộn xuống nhanh
- `ctrl+u` - Cuộn lên nhanh

### Chế độ Insert
- `Escape` - Về chế độ Normal
- `Enter` - Thực hiện tìm kiếm
- `Tab` - Chuyển đổi giữa các tab

### Chế độ Command
- `/search <query>` - Tìm kiếm với từ khóa
- `/chat <message>` - Chat với AI
- `/open <url>` - Mở URL trực tiếp
- `/help` - Hiển thị trợ giúp
- `/quit` - Thoát ứng dụng

## Tính năng

### 🔍 Tìm kiếm thông minh
- Sử dụng Gemini AI để tìm kiếm
- Kết quả hiển thị dạng danh sách
- Hỗ trợ tìm kiếm realtime

### 📖 Đọc nội dung web
- Tự động làm sạch HTML
- Chuyển đổi sang Markdown
- Hiển thị ảnh (protocol/ASCII/off)

### 💬 Chat với AI
- Trò chuyện trực tiếp với Gemini
- Lịch sử chat được lưu trữ
- Hỗ trợ markdown trong chat

### ⚙️ Cấu hình
- Chế độ hiển thị ảnh
- API key Gemini
- Model AI có thể thay đổi

## Mẹo sử dụng
- Sử dụng `Ctrl+C` để copy text
- `Ctrl+V` để paste (trong chế độ Insert)
- Scroll bằng mouse wheel hoạt động
- Resize cửa sổ tự động điều chỉnh layout
        """
        
        yield Container(
            Markdown(help_text),
            classes="help-container"
        )

class ConfigScreen(ModalScreen):
    """Màn hình cấu hình"""
    
    BINDINGS = [
        ("escape", "dismiss", "Đóng"),
        ("ctrl+s", "save_config", "Lưu")
    ]
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("⚙️ Cấu hình", classes="config-title"),
            Vertical(
                Label("API Key:"),
                Input(placeholder="Nhập Gemini API Key", id="api_key"),
                Label("Chế độ hiển thị ảnh:"),
                Input(placeholder="protocol/ascii/off", id="image_mode"),
                Label("Search Model:"),
                Input(placeholder="gemini-2.5-flash-preview-05-20", id="search_model"),
                Label("Markdown Model:"),
                Input(placeholder="gemini-2.0-flash-lite", id="markdown_model"),
                Horizontal(
                    Button("💾 Lưu", variant="primary", id="save"),
                    Button("❌ Hủy", variant="default", id="cancel"),
                    classes="config-buttons"
                ),
                classes="config-form"
            ),
            classes="config-container"
        )
    
    def on_mount(self):
        """Load cấu hình hiện tại"""
        try:
            with open('config/config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.query_one("#api_key", Input).value = config.get("gemini_api_key", "")
            self.query_one("#image_mode", Input).value = config.get("image_mode", "protocol")
            self.query_one("#search_model", Input).value = config.get("search_model", "gemini-2.5-flash-preview-05-20")
            self.query_one("#markdown_model", Input).value = config.get("markdown_model", "gemini-2.0-flash-lite")
        except Exception as e:
            self.app.notify(f"Không thể load cấu hình: {e}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save":
            self.action_save_config()
        elif event.button.id == "cancel":
            self.dismiss()
    
    def action_save_config(self):
        """Lưu cấu hình"""
        try:
            config = {
                "gemini_api_key": self.query_one("#api_key", Input).value,
                "image_mode": self.query_one("#image_mode", Input).value,
                "search_model": self.query_one("#search_model", Input).value,
                "markdown_model": self.query_one("#markdown_model", Input).value
            }
            
            os.makedirs('config', exist_ok=True)
            with open('config/config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.app.notify("✅ Đã lưu cấu hình!", severity="information")
            self.dismiss()
        except Exception as e:
            self.app.notify(f"❌ Lỗi lưu cấu hình: {e}", severity="error")

class TerminalAIBrowser(App):
    """Terminal AI Browser với giao diện Textual"""
    
    CSS_PATH = "browser.tcss"
    
    TITLE = "🌐 Terminal AI Browser"
    SUB_TITLE = "Powered by Gemini AI"
    
    BINDINGS = [
        # Vim-like bindings
        ("i", "insert_mode", "Insert"),
        ("colon", "command_mode", "Command"),
        ("j", "cursor_down", "Xuống"),
        ("k", "cursor_up", "Lên"),
        ("g,g", "goto_top", "Đầu trang"),
        ("shift+g", "goto_bottom", "Cuối trang"),
        ("ctrl+d", "page_down", "Page Down"),
        ("ctrl+u", "page_up", "Page Up"),
        ("enter", "open_selected", "Mở"),
        
        # App controls
        ("f1", "help", "Trợ giúp"),
        ("f2", "config", "Cấu hình"),
        ("ctrl+c", "quit", "Thoát"),
        ("escape", "normal_mode", "Normal"),
    ]
    
    def __init__(self):
        super().__init__()
        self.mode = "normal"  # normal, insert, command
        self.search_results = []
        self.selected_index = 0
        self.config = self.load_config()
    
    def load_config(self):
        """Load cấu hình từ file"""
        try:
            # Sử dụng đường dẫn tuyệt đối để đảm bảo luôn tìm thấy file config
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Đặt API key vào environment variable để Gemini API có thể sử dụng
                os.environ["GEMINI_API_KEY"] = config.get("gemini_api_key", "")
                return config
        except Exception as e:
            print(f"Lỗi load config: {e}")
            return {
                "gemini_api_key": "",
                "image_mode": "protocol",
                "search_model": "gemini-2.5-flash-lite-preview-06-17",
                "markdown_model": "gemini-2.5-flash-lite-preview-06-17"
            }
    
    def compose(self) -> ComposeResult:
        """Tạo layout chính"""
        yield Header()
        
        with TabbedContent(initial="search"):
            with TabPane("🔍 Tìm kiếm", id="search"):
                yield Container(
                    # Search input
                    Input(
                        placeholder="Nhập từ khóa tìm kiếm... (Enter để tìm, Esc về Normal mode)",
                        id="search_input"
                    ),
                    # Search results
                    ScrollableContainer(
                        ListView(id="search_results"),
                        id="results_container"
                    ),
                    classes="search-tab"
                )
            
            with TabPane("📖 Nội dung", id="content"):
                yield ScrollableContainer(
                    RichLog(id="content_display", auto_scroll=False),
                    id="content_container"
                )
            
            with TabPane("💬 Chat", id="chat"):
                yield Container(
                    ScrollableContainer(
                        RichLog(id="chat_history", auto_scroll=True),
                        id="chat_container"
                    ),
                    Input(
                        placeholder="Nhập tin nhắn... (Enter để gửi)",
                        id="chat_input"
                    ),
                    classes="chat-tab"
                )
        
        # Status bar
        yield Container(
            Static(f"Mode: {self.mode.upper()}", id="mode_status"),
            Static("Ready", id="main_status"),
            classes="status-bar"
        )
        
        yield Footer()
    
    def on_mount(self):
        """Khởi tạo sau khi mount"""
        self.update_mode_display()
        self.query_one("#search_input", Input).focus()
    
    def update_mode_display(self):
        """Cập nhật hiển thị mode"""
        mode_colors = {
            "normal": "blue",
            "insert": "green",
            "command": "yellow"
        }
        
        mode_status = self.query_one("#mode_status", Static)
        mode_status.update(f"Mode: {self.mode.upper()}")
        mode_status.styles.color = mode_colors.get(self.mode, "white")
    
    def action_insert_mode(self):
        """Chuyển sang chế độ Insert"""
        self.mode = "insert"
        self.update_mode_display()
        
        # Focus vào input của tab hiện tại
        tabs = self.query_one(TabbedContent)
        if tabs.active == "search":
            self.query_one("#search_input", Input).focus()
        elif tabs.active == "chat":
            self.query_one("#chat_input", Input).focus()
    
    def action_command_mode(self):
        """Chuyển sang chế độ Command"""
        self.mode = "command"
        self.update_mode_display()
        # Tạo command input tạm thời
        self.show_command_input()
    
    def action_normal_mode(self):
        """Chuyển về chế độ Normal"""
        self.mode = "normal"
        self.update_mode_display()
        
        # Unfocus các input
        try:
            self.query_one("#search_input", Input).blur()
            self.query_one("#chat_input", Input).blur()
        except:
            pass
    
    def show_command_input(self):
        """Hiển thị command input"""
        async def handle_command():
            command = await self.app.prompt("Command:", password=False)
            if command:
                await self.execute_command(command)
            self.action_normal_mode()
        
        asyncio.create_task(handle_command())
    
    async def execute_command(self, command: str):
        """Thực thi command"""
        parts = command.strip().split(None, 1)
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        try:
            if cmd == "search":
                await self.perform_search(args)
            elif cmd == "chat":
                await self.send_chat_message(args)
            elif cmd == "open":
                await self.open_url(args)
            elif cmd == "help":
                self.action_help()
            elif cmd == "config":
                self.action_config()
            elif cmd == "quit" or cmd == "q":
                self.exit()
            else:
                self.notify(f"❌ Lệnh không xác định: {cmd}", severity="error")
        except Exception as e:
            self.notify(f"❌ Lỗi thực thi lệnh: {e}", severity="error")
    
    async def perform_search(self, query: str):
        """Thực hiện tìm kiếm"""
        if not query:
            self.notify("❌ Vui lòng nhập từ khóa tìm kiếm", severity="error")
            return
        
        self.notify("🔍 Đang tìm kiếm...", severity="information")
        
        try:
            # Chuyển sang tab search
            tabs = self.query_one(TabbedContent)
            tabs.active = "search"
            
            # Thực hiện tìm kiếm
            results = gemini_search(query, self.config["gemini_api_key"], self.config["search_model"])
            
            if isinstance(results, list):
                self.search_results = results
                await self.display_search_results()
                self.notify(f"✅ Tìm thấy {len(results)} kết quả", severity="information")
            else:
                self.notify("❌ Không có kết quả tìm kiếm", severity="error")
        
        except Exception as e:
            self.notify(f"❌ Lỗi tìm kiếm: {e}", severity="error")
    
    async def display_search_results(self):
        """Hiển thị kết quả tìm kiếm"""
        results_list = self.query_one("#search_results", ListView)
        results_list.clear()
        
        for i, result in enumerate(self.search_results):
            title = result.get('title', 'No title')
            url = result.get('url', result.get('link', ''))
            
            item = SearchResultItem(title, url, i + 1)
            results_list.append(item)
    
    async def open_url(self, url: str):
        """Mở và hiển thị nội dung URL"""
        if not url:
            self.notify("❌ Vui lòng cung cấp URL", severity="error")
            return
        
        self.notify("📥 Đang tải nội dung...", severity="information")
        
        try:
            # Chuyển sang tab content
            tabs = self.query_one(TabbedContent)
            tabs.active = "content"
            
            # Fetch và clean HTML
            clean_html = fetch_and_clean_html(url)
            if not clean_html:
                self.notify("❌ Không thể tải nội dung", severity="error")
                return
            
            # Chuyển đổi sang markdown
            markdown_content = html_to_markdown_ai(
                clean_html, 
                self.config["gemini_api_key"],
                self.config["markdown_model"]
            )
            
            # Hiển thị nội dung
            content_display = self.query_one("#content_display", RichLog)
            content_display.clear()
            
            # Process images based on config
            await self.display_markdown_content(markdown_content, content_display)
            
            self.notify("✅ Đã tải nội dung thành công", severity="information")
        
        except Exception as e:
            self.notify(f"❌ Lỗi tải nội dung: {e}", severity="error")
    
    async def display_markdown_content(self, markdown: str, display_widget):
        """Hiển thị nội dung markdown với xử lý ảnh"""
        image_mode = self.config.get("image_mode", "protocol")
        
        # Split content by images
        parts = re.split(r'(!\[.*?\]\(.*?\))', markdown)
        
        for part in parts:
            if part.startswith("!["):
                # Image part
                match = re.match(r'!\[(.*?)\]\((.*?)\)', part)
                if match:
                    alt_text, url = match.groups()
                    
                    if image_mode == "off":
                        display_widget.write(f"[Image: {alt_text or url}]")
                    elif image_mode == "ascii":
                        ascii_art = self.render_ascii_art(url)
                        display_widget.write(ascii_art)
                    else:  # protocol mode
                        if not self.show_protocol_image(url):
                            # Fallback to ASCII art if protocol fails
                            ascii_art = self.render_ascii_art(url)
                            display_widget.write(ascii_art)
                        display_widget.write(f"🖼️  {alt_text or 'Image'}\n")
            else:
                # Text part
                if part.strip():
                    # Render as markdown
                    from rich.markdown import Markdown
                    md = Markdown(part)
                    display_widget.write(md)
    
    def render_ascii_art(self, url: str, width: int = 60) -> str:
        """Render ảnh thành ASCII art"""
        try:
            img_resp = requests.get(url, timeout=10)
            img = Image.open(BytesIO(img_resp.content)).convert("L")
            img = img.resize((width, int(img.height * width / img.width * 0.5)))
            chars = "@%#*+=-:. "
            ascii_art = "\n"  # Start with newline
            for y in range(img.height):
                for x in range(img.width):
                    pixel = img.getpixel((x, y))
                    ascii_art += chars[int(pixel / 255 * (len(chars)-1))]
                ascii_art += "\n"
            return ascii_art
        except Exception as e:
            return f"[Image error: {e}]"
    
    async def send_chat_message(self, message: str):
        """Gửi tin nhắn chat"""
        if not message:
            return
        
        try:
            # Chuyển sang tab chat
            tabs = self.query_one(TabbedContent)
            tabs.active = "chat"
            
            chat_history = self.query_one("#chat_history", RichLog)
            
            # Hiển thị tin nhắn của user 
            timestamp = datetime.now().strftime("%H:%M:%S")
            chat_history.write(f"[{timestamp}] 👤 Bạn: {message}")
            
            # Gửi tin nhắn đến AI
            self.notify("🤖 AI đang trả lời...", severity="information")
            
            response = gemini_chat(message, self.config["gemini_api_key"], self.config["search_model"])
            
            # Hiển thị phản hồi của AI
            from rich.markdown import Markdown
            chat_history.write(f"[{timestamp}] 🤖 AI:")
            chat_history.write(Markdown(response))
            
            self.notify("✅ Đã nhận phản hồi từ AI", severity="information")
        
        except Exception as e:
            self.notify(f"❌ Lỗi chat: {e}", severity="error")
    
    # Event handlers
    async def on_input_submitted(self, event: Input.Submitted):
        """Xử lý khi nhấn Enter trong input"""
        if event.input.id == "search_input":
            query = event.value.strip()
            if query:
                await self.perform_search(query)
        elif event.input.id == "chat_input":
            message = event.value.strip()
            if message:
                await self.send_chat_message(message)
                event.input.value = ""  # Clear input
    
    async def on_list_view_selected(self, event: ListView.Selected):
        """Xử lý khi chọn item trong danh sách"""
        if event.list_view.id == "search_results":
            if self.search_results and event.item:
                # Get selected result
                selected_item = event.item
                if hasattr(selected_item, 'url'):
                    await self.open_url(selected_item.url)
    
    def on_key(self, event: events.Key):
        """Xử lý phím nhấn"""
        if self.mode == "normal":
            # Chỉ xử lý trong normal mode
            return
        elif self.mode == "insert":
            if event.key == "escape":
                self.action_normal_mode()
                event.prevent_default()
    
    # Action handlers
    def action_help(self):
        """Hiển thị trợ giúp"""
        self.push_screen(HelpScreen())
    
    def action_config(self):
        """Hiển thị cấu hình"""
        self.push_screen(ConfigScreen())
    
    def action_cursor_down(self):
        """Di chuyển cursor xuống"""
        if self.mode == "normal":
            try:
                results_list = self.query_one("#search_results", ListView)
                if results_list.children:
                    current = results_list.index or 0
                    if current < len(results_list.children) - 1:
                        results_list.index = current + 1
            except:
                pass
    
    def action_cursor_up(self):
        """Di chuyển cursor lên"""
        if self.mode == "normal":
            try:
                results_list = self.query_one("#search_results", ListView)
                if results_list.children:
                    current = results_list.index or 0
                    if current > 0:
                        results_list.index = current - 1
            except:
                pass
    
    def action_goto_top(self):
        """Về đầu danh sách"""
        if self.mode == "normal":
            try:
                results_list = self.query_one("#search_results", ListView)
                if results_list.children:
                    results_list.index = 0
            except:
                pass
    
    def action_goto_bottom(self):
        """Về cuối danh sách"""
        if self.mode == "normal":
            try:
                results_list = self.query_one("#search_results", ListView)
                if results_list.children:
                    results_list.index = len(results_list.children) - 1
            except:
                pass
    
    async def action_open_selected(self):
        """Mở item được chọn"""
        if self.mode == "normal":
            try:
                results_list = self.query_one("#search_results", ListView)
                if results_list.highlighted_child:
                    selected_item = results_list.highlighted_child
                    if hasattr(selected_item, 'url'):
                        await self.open_url(selected_item.url)
            except:
                pass

    def show_protocol_image(self, url: str) -> bool:
        """Hiển thị ảnh bằng kitty protocol"""
        try:
            import subprocess
            subprocess.run(['kitty', '+kitten', 'icat', url], check=True)
            return True
        except:
            return False

def main():
    """Chạy ứng dụng"""
    app = TerminalAIBrowser()
    app.run()

if __name__ == "__main__":
    main()