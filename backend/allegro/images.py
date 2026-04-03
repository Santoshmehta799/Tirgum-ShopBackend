import requests

ALLEGRO_CLIENT_ID = "your_client_id"
ALLEGRO_CLIENT_SECRET = "your_client_secret"

# Step 0: Get OAuth token
def get_access_token():
    url = "https://allegro.pl/auth/oauth/token"
    auth = (ALLEGRO_CLIENT_ID, ALLEGRO_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    resp = requests.post(url, auth=auth, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]

# Step 1: Request upload URL from Allegro
def request_upload_url(access_token, filename):
    url = "https://api.allegro.pl/sale/offer-images"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "Content-Type": "application/json"
    }
    data = {"name": filename}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()["url"], resp.json()["id"]

# Step 2: Upload the file to the temporary URL
def upload_image(temp_url, local_path):
    with open(local_path, "rb") as f:
        files = {"file": f}
        resp = requests.post(temp_url, files=files)
        resp.raise_for_status()
    return True

# Step 3: Get final Allegro CDN URL
def get_allegro_cdn_url(image_id):
    # The standard format
    return f"https://a.allegroimg.com/original/{image_id.replace('-', '')}"

# Combined helper
def upload_images_to_allegro(file_paths):
    access_token = get_access_token()
    cdn_urls = []
    for path in file_paths:
        filename = path.split("/")[-1]
        temp_url, image_id = request_upload_url(access_token, filename)
        upload_image(temp_url, path)
        cdn_url = get_allegro_cdn_url(image_id)
        cdn_urls.append(cdn_url)
    return cdn_urls

# Example usage:
local_images = ["tire1.jpg", "tire2.jpg"]
allegro_urls = upload_images_to_allegro(local_images)
print(allegro_urls)