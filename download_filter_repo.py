import requests

url = "https://github.com/newren/git-filter-repo/releases/latest/download/git-filter-repo.exe"
response = requests.get(url)

with open("git-filter-repo.exe", "wb") as f:
    f.write(response.content)

print("✅ Download complete!")