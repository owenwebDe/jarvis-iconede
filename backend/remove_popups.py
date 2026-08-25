from bs4 import BeautifulSoup

path = r'c:\Users\Admin\Documents\tech work\javis\new-project\jarvis\backend\templates\pindrop_kit\dashboard.html'

with open(path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

# Remove the location popup
primer = soup.find('div', class_='onboard-primer')
if primer:
    primer.decompose()

# Remove the cookie dialog
cookie_dialog = soup.find('div', attrs={'role': 'dialog', 'aria-label': 'Advertising cookies'})
if cookie_dialog:
    cookie_dialog.decompose()
    
# Remove antigravity-scroll-lock from body if it's there
if soup.body and 'antigravity-scroll-lock' in soup.body.get('class', []):
    soup.body['class'].remove('antigravity-scroll-lock')

with open(path, 'w', encoding='utf-8') as f:
    f.write(str(soup))

print("Popups removed successfully!")
