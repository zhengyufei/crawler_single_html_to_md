import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
from unidecode import unidecode
import html2text


def get_md(url):
    # 向URL发送GET请求
    response = requests.get(url)

    # 使用BeautifulSoup解析响应的内容
    soup = BeautifulSoup(response.content, 'html.parser')

    # 删除footer部分
    for footer in soup.find_all('footer'):
        footer.decompose()

    # 获取文章标题
    title = soup.find('title').string.strip()

    # 删除head部分
    for head in soup.find_all('head'):
        head.decompose()

    # 将标题中不合法的文件名字符替换为下划线
    valid_title = re.sub(r'[\\/:"*?<>|]', '_', title)

    # 你想保存内容的路径
    save_path = os.path.join(".", "save", valid_title.strip())

    # 你想保存图片的目录
    image_dir = os.path.join(save_path, "images")
    os.makedirs(image_dir, exist_ok=True)

    # 找到所有的<img>标签
    img_tags = soup.find_all('img')

    # 用于存储图片的本地路径和原始URL的映射关系
    img_map = {}

    # 遍历所有的<img>标签
    for img in img_tags:
        # 获取图片的URL
        img_url = img.get('src')
        if img_url:
            # 如果URL是相对路径，需要转换为绝对路径
            img_url = urljoin(url, img_url)

            # 如果图片已经被下载过了，就跳过
            if img_url in img_map:
                continue

            try:
                # 下载图片并保存到本地
                img_response = requests.get(img_url, stream=True)
                img_response.raise_for_status()

                # 使用图片URL的最后一部分作为文件名
                img_name = os.path.split(urlparse(img_url).path)[-1]  # 使用urlparse来移除查询参数
                img_path = os.path.join(image_dir, img_name)
                with open(img_path, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # 将图片的本地路径和原始URL添加到映射关系中
                img_map[img_url] = f"images/{img_name}"  # 这里图片的路径包括了 'images/' 文件夹
            except requests.exceptions.RequestException as e:
                # 请求失败，打印错误信息，但不结束程序
                print(f"Error occurred: {e}")

    # 将HTML转换为字符串
    body = str(soup)

    # 使用html2text转换HTML为Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False  # 需要保留图片的链接
    h.body_width = 0
    markdown = h.handle(body)

    # 在Markdown文本中，使用正则表达式替换所有的图片链接为本地路径
    for img_url, img_path in img_map.items():
        # 从绝对路径中提取出相对路径
        parsed_url = urlparse(img_url)
        relative_img_url = parsed_url.path

        # 使用正则表达式替换图片的绝对路径和相对路径
        markdown = re.sub(re.escape(img_url) + '|' + re.escape(relative_img_url), img_path, markdown)

    # 从第一个"h1"标签开始
    markdown_split = markdown.split("\n# ")
    if len(markdown_split) > 1:
        markdown = "\n# " + "\n# ".join(markdown_split[1:])

    # 将 Markdown 内容拆分成行
    lines = markdown.split('\n')

    # 创建一个空列表来存储唯一的行
    unique_lines = []

    for line in lines:
        # 如果行是空的，我们直接添加到 unique_lines 中
        if line == '':
            unique_lines.append(line)
        # 如果行不是空的，并且还没有在列表中，我们将其添加到列表中
        elif line not in unique_lines:
            unique_lines.append(line)

    # 将唯一的行重新组合成单个字符串
    markdown_unique = '\n'.join(unique_lines)

    # 保证标题和正文之间有空行
    markdown_unique = re.sub(r'(#+)([^\n]+)\n([^\n])', r'\1\2\n\n\3', markdown_unique)

    # 删除多余的空行
    markdown_unique = re.sub(r'\n{3,}', '\n\n', markdown_unique)

    # 保证列表的格式
    markdown_unique = re.sub(r'(\n *)-\s', r'\1  - ', markdown_unique)

    # 将内容保存到Markdown文件
    with open(os.path.join(save_path, f'{valid_title}.md'), 'w', encoding='utf-8') as f:
        f.write(markdown_unique)


if __name__ == '__main__':
    print('Starting')

    # 你想下载和保存的URL
    url = "https://gradient.ai/blog/rag-101-for-enterprise"
    get_md(url)

    print('End')
