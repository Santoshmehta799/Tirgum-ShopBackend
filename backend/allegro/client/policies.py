import requests
from django.http import JsonResponse

def fetch_return_policy(access_token):
    url = "https://api.allegro.pl/after-sales-service-conditions/return-policies"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # Pick first policy or filter by name
        policies = data.get("returnPolicies", [])
        if policies:
            return {"id": policies[0]["id"]}
        else:
            return None
    else:
        raise Exception(f"Failed to fetch return policies: {response.status_code}")
        



def fetch_implied_warranties(access_token):
    """
    Fetches Allegro implied warranties and returns the first one as a dict.
    """
    url = "https://api.allegro.pl/after-sales-service-conditions/implied-warranties"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        warranties = data.get("impliedWarranties", [])
        if warranties:
            return {"id": warranties[0]["id"]}
        else:
            return None
    else:
        raise Exception(f"Failed to fetch implied warranties: {response.status_code} {response.text}")
            
        


def fetch_warranties(access_token):
    """
    Fetches Allegro warranties and returns the first one as a dict.
    """
    url = "https://api.allegro.pl/after-sales-service-conditions/warranties"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        warranties = data.get("warranties", [])
        if warranties:
            return {"id": warranties[0]["id"]}
        else:
            return None
    else:
        raise Exception(f"Failed to fetch warranties: {response.status_code} {response.text}")
            



