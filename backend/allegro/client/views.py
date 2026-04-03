from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


from django.http import JsonResponse
import requests
import base64
from django.shortcuts import render

from .client import AllegroClientBase
from .services import AllegroAuthService



def connect_allegro(request):
    client = AllegroClientBase()
    auth_url = (
        f"https://allegro.pl/auth/oauth/authorize?"
        f"response_type=code&client_id={client.CLIENT_ID}&redirect_uri={client.REDIRECT_URI}&prompt=confirm"

    )
    return render(request, "allegro/connect_allegro.html", {"auth_url": auth_url})



def allegro_callback(request):

    error = request.GET.get("error")
    if error:
        return JsonResponse({"error": error}, status=400)

    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No code parameter in URL"}, status=400)

    client = AllegroClientBase()

    headers = client._get_oauth_headers()
    print(headers)

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": client.REDIRECT_URI
    }

    response = requests.post(client.TOKEN_URL, headers=headers, data=data)

    print("Status code:", response.status_code)
    print("Response text:", response.text)

    if response.status_code != 200:
        return JsonResponse({
            "error": "Token exchange failed",
            "status": response.status_code,
            "body": response.text
        }, status=500)

    tokens = response.json()

    AllegroAuthService.save_tokens(tokens)

    return JsonResponse({"status": "connected"})



# def allegro_callback(request):
#     code = request.GET.get("code")
#     if not code:
#         return JsonResponse({"error": "No code parameter in URL"}, status=400)

#     client = AllegroClientBase()

#     headers = client._get_oauth_headers()
#     data = {
#         "grant_type": "authorization_code",
#         "code": code,
#         "redirect_uri": client.REDIRECT_URI
#     }

#     response = requests.post(client.TOKEN_URL, headers=headers, data=data)

#     print("Status code:", response.status_code)
#     print("Response text:", response.text)  # <-- critical for debugging

#     try:
#         tokens = response.json()
#     except Exception as e:
#         print("Failed to parse JSON:", e)
#         return JsonResponse({"error": "Failed to parse token response", "raw": response.text}, status=500)

#     AllegroAuthService.save_tokens(tokens)
#     return JsonResponse({"status": "connected"})


# def allegro_callback(request):
#     """
#     Handles the OAuth 2.0 callback from Allegro after a user authorizes the app.

#     This view is triggered when Allegro redirects the user back to your application
#     after they log in and approve access. It performs the following steps:

#     1. Extracts the `code` parameter from the GET request, which is a temporary
#        authorization code issued by Allegro.
#     2. Initializes an `AllegroClientBase` instance to access client credentials
#        and token URL.
#     3. Encodes the `CLIENT_ID` and `CLIENT_SECRET` in Base64 to create the 
#        required HTTP Basic Authorization header.
#     4. Prepares the POST request payload with:
#        - `grant_type` set to "authorization_code"
#        - the `code` obtained from the query parameters
#        - the `redirect_uri` matching the one registered in Allegro
#     5. Sends a POST request to Allegro's OAuth token endpoint to exchange the
#        authorization code for an access token and refresh token.
#     6. Parses the JSON response containing the tokens.
#     7. Saves the tokens and expiration data in the database using
#        `AllegroAuthService.save_tokens`.
#     8. Returns a JSON response indicating that the connection was successful.

#     Query Parameters:
#     - code (str): The temporary authorization code returned by Allegro.

#     Returns:
#     - JsonResponse: JSON object with a "status" key confirming successful connection.

#     Notes:
#     - The access token allows the server to make authorized API calls on behalf
#       of the user.
#     - The refresh token can be used to obtain a new access token when the current
#       one expires.
#     - This view must be registered as the `redirect_uri` in your Allegro app settings.
#     """

#     code = request.GET.get("code")

#     client = AllegroClientBase()

#     credentials = f"{client.CLIENT_ID}:{client.CLIENT_SECRET}"
#     encoded = base64.b64encode(credentials.encode()).decode()

#     headers = {
#         "Authorization": f"Basic {encoded}",
#         "Content-Type": "application/x-www-form-urlencoded",
#     }

#     data = {
#         "grant_type": "authorization_code",
#         "code": code,
#         "redirect_uri": client.REDIRECT_URI
#     }

#     response = requests.post(client.TOKEN_URL, headers=headers, data=data)

#     tokens = response.json()

#     AllegroAuthService.save_tokens(tokens)

#     return JsonResponse({"status": "connected"})






# from .services import AllegroAuthService

# token = AllegroAuthService.get_valid_access_token()

# headers = {
#     "Authorization": f"Bearer {token}",
#     "Accept": "application/vnd.allegro.public.v1+json"
# }


