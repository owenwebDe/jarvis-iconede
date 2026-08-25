import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "templates" / "luxoria_kit"
CSS_DIR = OUT_DIR / "assets" / "css"
JS_DIR = OUT_DIR / "assets" / "js"
CSS_DIR.mkdir(parents=True, exist_ok=True)
JS_DIR.mkdir(parents=True, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}

home_html = (OUT_DIR / "home.html").read_text(encoding="utf-8", errors="ignore")

def download_file(url, target_path):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as res:
            data = res.read()
            target_path.write_bytes(data)
            return url, len(data), True
    except Exception as e:
        return url, str(e), False

# Extract all CSS
css_urls = set(re.findall(r'href=["\'](https?://[^"\']+\.css[^"\']*)["\']', home_html))
print(f"Total Unique CSS URLs found: {len(css_urls)}")

# Extract all JS
js_urls = set(re.findall(r'src=["\'](https?://[^"\']+\.js[^"\']*)["\']', home_html))
print(f"Total Unique JS URLs found: {len(js_urls)}")

with ThreadPoolExecutor(max_workers=16) as executor:
    futures = {}
    for c in css_urls:
        clean = c.split('?')[0]
        fname = clean.split('/')[-1]
        futures[executor.submit(download_file, c, CSS_DIR / fname)] = ('CSS', fname)

    for j in js_urls:
        clean = j.split('?')[0]
        fname = clean.split('/')[-1]
        futures[executor.submit(download_file, j, JS_DIR / fname)] = ('JS', fname)

    success = 0
    failed = 0
    for f in as_completed(futures):
        kind, fname = futures[f]
        url, res, ok = f.result()
        if ok:
            success += 1
            print(f" [OK] {kind}: {fname} ({res} bytes)")
        else:
            failed += 1
            print(f" [FAIL] {kind}: {fname} ({res})")

print(f"Fast Download Complete! {success} downloaded, {failed} failed.")
