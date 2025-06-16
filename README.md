# Terminal-based AI Browser

Trình duyệt tìm kiếm và đọc nội dung web ngay trong terminal, sử dụng Gemini API.

## Tính năng
- Tìm kiếm thông tin qua Gemini API, trả về kết quả dạng Google.
- Chọn link để đọc nội dung, tự động loại bỏ phần thừa và chuyển sang markdown.
- Hiển thị hình ảnh dạng protocol (nếu terminal hỗ trợ), ASCII art, hoặc tắt hoàn toàn.
- Tối ưu CPU/RAM, cấu hình linh hoạt.

## Cấu hình
Chỉnh sửa file `config/config.json` để chọn chế độ hiển thị ảnh và nhập API key.

## Khởi động
```bash
python src/main.py
