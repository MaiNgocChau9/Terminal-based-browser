import requests
from bs4 import BeautifulSoup

def fetch_and_clean_html(url):
    """
    Tải HTML từ url, loại bỏ <style>, <script>, class, header, footer.
    Trả về HTML đã làm sạch.
    """
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Xóa style, script
        for tag in soup(["style", "script", "noscript"]):
            tag.decompose()

        # Xóa header, footer
        for tag in soup.find_all(["header", "footer"]):
            tag.decompose()

        # Xóa thuộc tính class/id/style khỏi tất cả tag
        for tag in soup.find_all(True):
            for attr in ["class", "id", "style"]:
                if attr in tag.attrs:
                    del tag.attrs[attr]

        # Trả về nội dung body nếu có, ngược lại trả về toàn bộ
        if soup.body:
            return str(soup.body)
        return str(soup)
    except Exception as e:
        print("Lỗi khi tải/làm sạch HTML:", e)
        return ""
