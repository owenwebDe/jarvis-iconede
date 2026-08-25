import json
import urllib.request
import urllib.parse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LeadScraperServer")

@mcp.tool()
def scrape_local_leads_without_websites(city: str, bbox: str = "8.9, 7.3, 9.2, 7.6") -> str:
    """
    Scrape real local businesses in a given area (default is Abuja bounding box) that DO NOT have websites,
    but DO have phone numbers.
    Args:
        city: City name (e.g., 'Abuja, Nigeria')
        bbox: Bounding box coordinates (South, West, North, East). Default is Abuja.
    Returns:
        JSON string of leads with name, phone, and category.
    """
    # Overpass API Query
    # The bbox format is usually (south, west, north, east)
    # 8.9 (South), 7.3 (West), 9.2 (North), 7.6 (East) is roughly Abuja
    query = f"""
    [out:json][timeout:60];
    (
      node['shop']({bbox});
      way['shop']({bbox});
      node['amenity'='restaurant']({bbox});
      way['amenity'='restaurant']({bbox});
      node['amenity'='clinic']({bbox});
      way['amenity'='clinic']({bbox});
      node['craft']({bbox});
    );
    out tags;
    """
    url = 'https://overpass-api.de/api/interpreter'
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'IconEdgeLeadGen/1.0'})
    
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            response_data = json.loads(res.read().decode('utf-8'))
            elements = response_data.get('elements', [])
            
            valid_leads = []
            for el in elements:
                tags = el.get('tags', {})
                name = tags.get('name')
                phone = tags.get('phone') or tags.get('contact:phone') or tags.get('contact:mobile')
                website = tags.get('website') or tags.get('contact:website')
                
                # We strictly want leads that have NO website but HAVE a phone number
                if name and phone and not website:
                    # Clean the phone number to E164/international format if possible
                    p = phone.replace(' ', '').replace('-', '')
                    if ';' in p:
                        p = p.split(';')[0]
                    
                    if p.startswith('0'):
                        p = '234' + p[1:]
                    elif p.startswith('+234'):
                        p = p[1:]
                    
                    category = tags.get('shop') or tags.get('amenity') or tags.get('craft', 'business')
                    
                    valid_leads.append({
                        'name': name,
                        'phone': p,
                        'category': category
                    })
            
            # Deduplicate by name and phone
            seen = set()
            unique_leads = []
            for lead in valid_leads:
                key = (lead['name'].lower(), lead['phone'])
                if key not in seen:
                    seen.add(key)
                    unique_leads.append(lead)
            
            return json.dumps({
                "status": "success",
                "total_found": len(unique_leads),
                "leads": unique_leads
            })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    mcp.run()
