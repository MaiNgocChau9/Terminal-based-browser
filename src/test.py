import subprocess

def show_image_url(url):
    subprocess.run(['kitty', '+kitten', 'icat', url])

# Sử dụng
show_image_url('https://i0.wp.com/www.omgubuntu.co.uk/wp-content/uploads/2025/06/gradia-gradients.jpg?resize=768%2C403&ssl=1')