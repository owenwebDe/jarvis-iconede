import urllib.request
import json
import http.cookiejar
import time

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({'api_key': '9j5WAZ0Tk3AJVvHvFaCpixwXD0jrIOh-GTo3GRp8ySU'}).encode()
)
res = opener.open(req)
csrf = json.loads(res.read().decode())['csrf_token']

def test_query(title, message):
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print(f"Prompt: \"{message}\"")
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/chat',
        headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
        data=json.dumps({'message': message}).encode()
    )
    try:
        t0 = time.time()
        res = opener.open(req)
        dur = time.time() - t0
        data = json.loads(res.read().decode())
        print(f"Status: OK (Duration: {dur:.2f}s)")
        print(f"Target Agent Routed: {data.get('agent_name')}")
        print(f"Token Breakdown: {data.get('tokens')}")
        print(f"Response Snippet: {data.get('response', '')[:220]}...")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"Error: {e}")

test_query('1. Creative Task (Ad Copy & Hooks)', 'Draft a high-converting 3-line hook for SME logistics managers in the UK')
test_query('2. Lead Research Task', 'Find logistics companies in London with fleet sizes over 50')
test_query('3. Jarvis Executive Orchestrator', 'Hello Jarvis, status check for IconEdge Technologies operations')
