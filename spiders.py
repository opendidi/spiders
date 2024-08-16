import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def ensure_dir(file_path):
    """确保文件路径中的目录存在"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_resource(resource_url, base_folder):
    """下载资源并保持原有的目录结构"""
    parsed_url = urlparse(resource_url)
    # 构建本地保存路径
    save_path = os.path.join(base_folder, parsed_url.netloc, parsed_url.path.lstrip('/'))
    ensure_dir(save_path)
    if not os.path.isfile(save_path):  # 如果文件尚未下载，则下载
        try:
            response = requests.get(resource_url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=128):
                        file.write(chunk)
                print(f"资源下载成功：{resource_url}")
            else:
                print(f"资源下载失败：{resource_url}")
        except Exception as e:
            print(f"下载异常：{e}")

def scrape_page(url, base_folder):
    """爬取单个页面并下载所有资源"""
    response = requests.get(url)
    if response.status_code != 200:
        print("网页加载失败")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    # 下载页面中的所有资源
    for resource_tag in soup.find_all(['img', 'link', 'script']):
        if resource_tag.name == 'link' and resource_tag.get('rel') == ['stylesheet']:
            resource_url = urljoin(url, resource_tag.get('href'))
            download_resource(resource_url, base_folder)
        elif resource_tag.name == 'script' and resource_tag.get('src'):
            resource_url = urljoin(url, resource_tag.get('src'))
            download_resource(resource_url, base_folder)
        elif resource_tag.name == 'img' and resource_tag.get('src'):
            resource_url = urljoin(url, resource_tag.get('src'))
            download_resource(resource_url, base_folder)

    # 保存页面本身
    parsed_url = urlparse(url)
    save_path = os.path.join(base_folder, parsed_url.netloc, parsed_url.path.lstrip('/'))
    if save_path.endswith('/') or save_path.endswith('\\'):  # 处理目录默认页面
        save_path = os.path.join(save_path, 'index.html')
    ensure_dir(save_path)  # 确保目录存在
    with open(save_path, 'wb') as file:
        file.write(response.content)

def scrape_site(start_url, base_folder='offline_site'):
    """爬取整个网站"""
    visited = set()
    to_visit = set([start_url])

    while to_visit:
        current_url = to_visit.pop()
        if current_url not in visited:
            visited.add(current_url)
            scrape_page(current_url, base_folder)

            # 获取当前页面上的所有链接，并加入待访问集合
            response = requests.get(current_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and not href.startswith('mailto:'):
                    full_url = urljoin(current_url, href)
                    if urlparse(full_url).netloc == urlparse(start_url).netloc:  # 仅访问相同域名下的链接
                        to_visit.add(full_url)

# 使用示例
target_url = 'http://localhost:8080'  # 你想要爬取的网页URL
scrape_site(target_url)