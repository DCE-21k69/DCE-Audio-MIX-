import urllib.request
import json
import sys

CURRENT_VERSION = "1.0.0"
REPO = "DCE-21k69/DCE-Audio-MIX-"

def check_updates():
    try:
        url = f"https://api.github.com/repos/{REPO}/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'DCE-Audio-Mix-Updater'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "").replace("v", "")
            
            if latest_version and latest_version != CURRENT_VERSION:
                print(f"Update available: {latest_version}")
                return data
    except Exception as e:
        print(f"Update check failed: {e}")
    return None

if __name__ == "__main__":
    check_updates()
