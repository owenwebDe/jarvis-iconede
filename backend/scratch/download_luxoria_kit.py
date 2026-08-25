import os
import re
import urllib.request
from pathlib import Path

BASE_URL = "https://templates.sparklethings.com/luxoria/template-kit"
OUT_DIR = Path(__file__).resolve().parent.parent / "templates" / "luxoria_kit"
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "assets" / "css").mkdir(parents=True, exist_ok=True)
(OUT_DIR / "assets" / "js").mkdir(parents=True, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_binary(url):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read()
    except Exception as e:
        return None

# 1. Fetch Home
print("Fetching Home page...")
home_html = fetch_url(f"{BASE_URL}/home/")
if home_html:
    (OUT_DIR / "home.html").write_text(home_html, encoding="utf-8")
    print(f"Saved home.html ({len(home_html)} bytes)")

# 2. Discover links
links = re.findall(r'href=["\'](https://templates\.sparklethings\.com/luxoria/template-kit/[^"\'#]+)["\']', home_html or "")
unique_pages = set()
for l in links:
    cleaned = l.rstrip('/')
    slug = cleaned.split('/')[-1]
    if slug and slug != 'template-kit':
        unique_pages.add((slug, cleaned + '/'))

print("Discovered Pages:", unique_pages)

for slug, p_url in unique_pages:
    print(f"Fetching {slug} ({p_url})...")
    p_html = fetch_url(p_url)
    if p_html:
        (OUT_DIR / f"{slug}.html").write_text(p_html, encoding="utf-8")
        print(f"Saved {slug}.html ({len(p_html)} bytes)")

# 3. Extract and Download CSS
css_links = re.findall(r'href=["\'](https?://[^"\']+\.css[^"\']*)["\']', home_html or "")
print(f"Found {len(css_links)} CSS files.")
css_count = 0
for c in set(css_links):
    clean_c = c.split('?')[0]
    filename = clean_c.split('/')[-1]
    data = fetch_binary(c)
    if data:
        (OUT_DIR / "assets" / "css" / filename).write_bytes(data)
        css_count += 1

print(f"Downloaded {css_count} CSS files.")

# 4. Extract and Download JS
js_links = re.findall(r'src=["\'](https?://[^"\']+\.js[^"\']*)["\']', home_html or "")
print(f"Found {len(js_links)} JS files.")
js_count = 0
for j in set(js_links):
    clean_j = j.split('?')[0]
    filename = clean_j.split('/')[-1]
    data = fetch_binary(j)
    if data:
        (OUT_DIR / "assets" / "js" / filename).write_bytes(data)
        js_count += 1

print(f"Downloaded {js_count} JS files.")
print("Luxoria Kit Download Complete!")
