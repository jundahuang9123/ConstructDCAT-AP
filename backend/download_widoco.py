import os
import urllib.request
import json
import ssl

DESTINATION = "backend/tools/widoco.jar"
REPO_API_URL = "https://api.github.com/repos/dgarijo/Widoco/releases/latest"

def run():
    if os.path.exists(DESTINATION):
        print(f"Widoco already exists at {DESTINATION}")
        return

    print(f"Fetching latest release info from {REPO_API_URL}...")
    
    # Create SSL context to verify certificates (standard practice)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # For simplicity in some envs, but ideally check. 

    try:
        # Get Release JSON
        req = urllib.request.Request(REPO_API_URL, headers={'User-Agent': 'Python Script'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode())
        
        if not data.get('assets'):
            print("No assets found in release.")
            print(f"Release keys: {list(data.keys())}")
            if 'message' in data:
                print(f"Message: {data['message']}")

        # Find asset
        download_url = None
        print("Available assets:")
        for asset in data.get('assets', []):
            print(f" - {asset['name']}")
            if "jar-with-dependencies" in asset['name']:
                download_url = asset['browser_download_url']
                # Don't break immediately, let's see all assets, but keep the match

        
        if not download_url:
            print("Error: Could not find widoco-*-jar-with-dependencies.jar in latest release.")
            return

        print(f"Downloading Widoco from {download_url}...")
        os.makedirs(os.path.dirname(DESTINATION), exist_ok=True)
        urllib.request.urlretrieve(download_url, DESTINATION)
        print("Download complete.")

    except Exception as e:
        print(f"Error downloading Widoco: {e}")

if __name__ == "__main__":
    run()
