import requests

# URL of your deployed application (Change this to your Render URL later!)
# Example: URL = "https://gitauditor-xyz.onrender.com/review"
URL = "http://localhost:8000/review"

# The GitHub Pull Request you want to test
PAYLOAD = {
    "github_url": "https://github.com/arko-14/gitauditor/pull/3"
}

print(f"🚀 Sending request to {URL}...")
try:
    response = requests.post(URL, json=PAYLOAD)
    
    if response.status_code == 200:
        print("✅ Success!")
        print("Response Details:")
        print(response.json())
    else:
        print(f"❌ Error! Status Code: {response.status_code}")
        print("Details:", response.text)
        
except requests.exceptions.ConnectionError:
    print(f"❌ Could not connect to {URL}. Make sure your app is running!")
