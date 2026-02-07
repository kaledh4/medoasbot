import requests
import os
import urllib.request

fonts = [
    ("https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Bold.ttf", "Tajawal-Bold.ttf"),
    ("https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Regular.ttf", "Tajawal-Regular.ttf")
]

os.makedirs("gateway/static/fonts", exist_ok=True)

for url, filename in fonts:
    output_path = os.path.join("gateway/static/fonts", filename)
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"✅ {filename} downloaded!")
    except Exception as e:
        print(f"❌ Failed to download {filename}: {e}")
