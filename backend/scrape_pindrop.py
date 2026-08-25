import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = 'https://pindrop.host'
OUT_DIR = r'c:\Users\Admin\Documents\tech work\javis\new-project\jarvis\backend\templates\pindrop_kit'

def download_file(url, out_path):
    print(f'Downloading {url} to {out_path}')
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f'Failed to download {url}: {e}')

def scrape_page(url, current_path):
    print(f'Scraping {url}')
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f'Failed to fetch {url}: {e}')
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Download CSS
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            full_url = urljoin(url, href)
            parsed = urlparse(full_url)
            if parsed.netloc == urlparse(BASE_URL).netloc:
                local_path = os.path.join(OUT_DIR, parsed.path.lstrip('/'))
                download_file(full_url, local_path)
                link['href'] = parsed.path

    # Download JS
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            full_url = urljoin(url, src)
            parsed = urlparse(full_url)
            if parsed.netloc == urlparse(BASE_URL).netloc:
                local_path = os.path.join(OUT_DIR, parsed.path.lstrip('/'))
                download_file(full_url, local_path)
                script['src'] = parsed.path

    # Download images
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            full_url = urljoin(url, src)
            parsed = urlparse(full_url)
            if parsed.netloc == urlparse(BASE_URL).netloc:
                local_path = os.path.join(OUT_DIR, parsed.path.lstrip('/'))
                download_file(full_url, local_path)
                img['src'] = parsed.path

    # Save modified HTML
    out_file = os.path.join(OUT_DIR, current_path)
    if current_path == '' or current_path.endswith('/'):
        out_file = os.path.join(out_file, 'index.html')
    elif not current_path.endswith('.html'):
        out_file += '.html'
        
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f'Saved HTML to {out_file}')

if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    # Scrape homepage
    scrape_page(BASE_URL, '')
    # Scrape dashboard page
    scrape_page(f'{BASE_URL}/dashboard', 'dashboard')
