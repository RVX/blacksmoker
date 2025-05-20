import requests

token = "8c8bf9a0-4d10-49f3-bfcd-70dfc3344faa"
url = "https://data.oceannetworks.ca/api/deployments"
params = {
    "method": "get",
    "token": token,
    "locationCode": "BACND",
    "deviceCategoryCode": "HYDROPHONE"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
try:
    r = requests.get(url, params=params, timeout=30, headers=headers)
    print("Status code:", r.status_code)
    print("First 500 chars of response:", r.text[:500])
except Exception as e:
    print("Error:", e)