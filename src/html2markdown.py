import html2text

def html_to_markdown(html):
    """
    Chuyển HTML đã làm sạch sang markdown.
    """
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0
    return h.handle(html)
