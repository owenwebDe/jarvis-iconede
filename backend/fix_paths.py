import os

kit_dir = r'c:\Users\Admin\Documents\tech work\javis\new-project\jarvis\backend\templates\pindrop_kit'

for file_name in ['index.html', 'dashboard.html']:
    path = os.path.join(kit_dir, file_name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace absolute root paths with relative paths
        content = content.replace('href="/_next/', 'href="./_next/')
        content = content.replace('src="/_next/', 'src="./_next/')
        content = content.replace('srcset="/_next/', 'srcset="./_next/')
        # also handle cases where srcset has multiple URLs
        content = content.replace(', /_next/', ', ./_next/')
        content = content.replace('href="/favicon.ico', 'href="./favicon.ico')
        content = content.replace('href="/icon.png', 'href="./icon.png')
        content = content.replace('href="/apple-icon.png', 'href="./apple-icon.png')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated paths in {file_name}')
