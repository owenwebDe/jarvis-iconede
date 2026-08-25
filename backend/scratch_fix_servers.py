import yaml
import re

with open('fastagent.config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
    
valid_servers = set(config.get('mcp', {}).get('servers', {}).keys())

with open('agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

def replace_servers(match):
    servers_str = match.group(1)
    # Split by comma, clean quotes and spaces
    items = [s.strip() for s in servers_str.split(',') if s.strip()]
    
    valid_items = []
    for item in items:
        # Extract the actual string value (e.g., '"music-playlist"' -> 'music-playlist')
        clean_item = item.strip('\"\'')
        if clean_item in valid_servers or item == '*_MEMORY_SERVERS':
            valid_items.append(item)
            
    return 'servers=[' + ', '.join(valid_items) + ']'

new_content = re.sub(r'servers=\[(.*?)\]', replace_servers, content)

with open('agent.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated agent.py successfully.')
