import json, base64, urllib.request, urllib.error, subprocess, os

token = subprocess.check_output(['gh', 'auth', 'token']).decode().strip()
repo = "HenrywooChem/ai-transcriber-wx"

def api(method, path, data=None):
    url = f"https://api.github.com/repos/{repo}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"API Error {e.code}: {error_body}")

# Read all files
files = {}
for root, dirs, filenames in os.walk('.'):
    for f in filenames:
        path = os.path.join(root, f)
        if '.git' in path or '__pycache__' in path or path == 'push_to_github.py':
            continue
        rel_path = path[2:] if path.startswith('.\\') else path
        with open(path, 'rb') as fp:
            content = fp.read()
            if content:
                files[rel_path] = base64.b64encode(content).decode('utf-8')
        print(f"Read: {rel_path} ({len(content)} bytes)")

print(f"\nTotal files: {len(files)}")

# Use contents API to create files one by one
for path, content_b64 in files.items():
    try:
        # Decode base64 for the contents API
        content_str = base64.b64encode(base64.b64decode(content_b64)).decode('utf-8')
        api('PUT', f'/contents/{path}', {
            'message': 'Initial commit',
            'content': content_b64
        })
        print(f"Created: {path}")
    except Exception as e:
        print(f"Error creating {path}: {e}")

print(f"\nSuccessfully pushed!")
print(f"Repository: https://github.com/{repo}")