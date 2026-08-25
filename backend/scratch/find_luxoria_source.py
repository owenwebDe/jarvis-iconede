import subprocess
import re
import os

url = 'https://preview.themeforest.net/item/luxoria-luxury-real-estate-elementor-template-kit/full_screen_preview/62499928'
headers = [
    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    '-H', 'Accept-Language: en-US,en;q=0.9',
    '-H', 'Sec-Fetch-Dest: document',
    '-H', 'Sec-Fetch-Mode: navigate',
    '-H', 'Sec-Fetch-Site: none',
    '-H', 'Sec-Fetch-User: ?1',
    '-H', 'Upgrade-Insecure-Requests: 1',
]

res = subprocess.run(['curl.exe', '-s', '-L'] + headers + [url], capture_output=True, text=True, timeout=15)
print('--- REMAINDER OF STDOUT ---')
print(res.stdout[3000:])
