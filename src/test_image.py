import subprocess

def show_image_url(url):
    try:
        subprocess.run(['kitty', '+kitten', 'icat', url], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Lỗi: {e}")

print("Bắt đầu test hiển thị ảnh...")
# Test với ảnh mẫu
url = 'https://i0.wp.com/www.omgubuntu.co.uk/wp-content/uploads/2025/06/gradia-gradients.jpg?resize=768%2C403&ssl=1'
print(f"Đang hiển thị ảnh từ: {url}")
show_image_url(url)

# Test với một ảnh khác để kiểm tra
url2 = 'https://github.com/fluidicon.png'
print(f"\nĐang hiển thị ảnh từ: {url2}")
show_image_url(url2)
