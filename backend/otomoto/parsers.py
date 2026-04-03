from tyreadderapp.models import Product, Pair
from .models import OtoMotoAdvertData, PairOtoMotoAdvertData


def extract_tire_width(size: str) -> str | None:
    """
    Extracts tyre width from a size string.

    Rules:
    - If size contains "/", tyre width = part before "/"
    - If size does NOT contain "/", tyre width = part before "R"
    - All spaces are removed
    - Output must end with '-mm'
    """
    if not size:
        return None

    size_clean = size.replace(" ", "")  # remove spaces

    if "/" in size_clean:
        width = size_clean.split("/", 1)[0]
    elif "R" in size_clean.upper():
        width = size_clean.upper().split("R", 1)[0]
    else:
        # If nothing matches, treat entire value as width
        width = size_clean

    width = width.strip()

    if not width.isdigit():   # validation (optional)
        return None

    return f"{width}-mm"



def extract_aspect_ratio(size: str) -> str | None:
    """
    Extracts tire profile (height-aspect-ratio) from size.

    Rules:
    - If "/" exists → profile is between "/" and "R"
    - If no "/" → return None
    - Remove spaces
    - Remove "R" and everything after
    """
    if not size:
        return None

    s = size.replace(" ", "")  # normalize

    # If no "/", we do not return profile
    if "/" not in s:
        return None

    # Split at "/"
    after_slash = s.split("/", 1)[1]

    # Remove "R" and everything after
    if "R" in after_slash.upper():
        after_slash = after_slash.upper().split("R", 1)[0]

    profile = after_slash.strip()

    # Optional validation
    if not profile.isdigit():
        return None

    return profile




def extract_rim_diameter(size: str) -> str | None:
    """
    Extracts rim diameter from a tire size string.

    Rules:
    - Remove all spaces
    - Take everything AFTER the first "R"
    - Return as: "felgi-inches-{diameter}"
    - If no R found or invalid value → return None
    """
    if 'R' not in size:
        return None

    try:
        value = float(size.split('R', 1)[1])
    except ValueError:
        return None

    if value >= 22:
        return "felgi-inches-22"
    elif value == 21:
        return "felgi-inches-21"
    elif value == 19.5:
        return "felgi-inches-19-5"
    elif value == 17.5:
        return "felgi-inches-17-5"
    else:
        return None



def extract_tyre_inches(size: str) -> str | None:
    """
    Extracts rim diameter from a tire size string.

    Rules:
    - Remove all spaces
    - Take everything AFTER the first "R"
    - >= 22 → "opony-inches-22"
    - Supported sizes: 16, 16.5, 17, 17.5, 18, 19, 19.5, 20, 21
    - If no R found or invalid value → return None
    """
    size = size.replace(" ", "")

    if "R" not in size:
        return None

    value = size.split("R", 1)[1]

    try:
        inches = float(value)
    except ValueError:
        return None

    if inches >= 22:
        return "opony-inches-22"

    mapping = {
        21.0: "opony-inches-21",
        20.0: "opony-inches-20",
        19.5: "opony-inches-19-5",
        19.0: "opony-inches-19",
        18.0: "opony-inches-18",
        17.5: "opony-inches-17-5",
        17.0: "opony-inches-17",
        16.5: "opony-inches-16-5",
        16.0: "opony-inches-16",
    }

    return mapping.get(inches)


def extract_tyre_profile(size: str) -> str | None:
    """
    Extracts tyre profile from size string.

    Rules:
    - Profile is the part between "/" and "R"
    - Remove spaces
    - Only profiles 40 and 45 are supported
    """
    if not size:
        return None

    s = size.replace(" ", "").upper()

    if "/" not in s or "R" not in s:
        return None

    profile = s.split("/", 1)[1].split("R", 1)[0]

    if not profile.isdigit():
        return None

    mapping = {
        "40": "opony-profile-40",
        "45": "opony-profile-45",
        "50": "opony-profile-50",
        "55": "opony-profile-55",
        "60": "opony-profile-60",
        "65": "opony-profile-65",
        "70": "opony-profile-70",
        "75": "opony-profile-75",
        "80": "opony-profile-80",
        "85": "opony-profile-85",
    }

    return mapping.get(profile)



def sync_all_active_otomoto_adverts():
    from otomoto.client.otomoto_client import AuthOtomotoClient
    client = AuthOtomotoClient()
    api_adverts_response = client.get_my_adverts()
    
    # Handle response being a dict with "data" key
    if isinstance(api_adverts_response, dict) and "data" in api_adverts_response:
        api_adverts = api_adverts_response["data"]
    else:
        api_adverts = api_adverts_response

    # Make sure we have a list
    if not isinstance(api_adverts, list):
        raise ValueError(f"Unexpected API response: {api_adverts}")

    api_map = {a["id"]: a for a in api_adverts}

    # Pairs
    pair_adverts = PairOtoMotoAdvertData.objects.filter(
        pair__is_otomoto_pair_advert_activated=True,
        otomoto_advert_id__isnull=False
    )
    for advert in pair_adverts:
        api_data = api_map.get(advert.otomoto_advert_id)
        if api_data:
            sync_otomoto_advert(advert, api_data)

    # Singles
    single_adverts = OtoMotoAdvertData.objects.filter(
        product__is_otomoto_advert_activated=True,
        otomoto_advert_id__isnull=False
    )
    for advert in single_adverts:
        api_data = api_map.get(advert.otomoto_advert_id)
        if api_data:
            sync_otomoto_advert(advert, api_data)





# def sync_all_active_otomoto_adverts():
#     from otomoto.client.otomoto_client import AuthOtomotoClient
#     client = AuthOtomotoClient()
#     api_adverts = client.get_my_adverts()  # returns list of dicts
#     api_map = {a["id"]: a for a in api_adverts}

#     # Pairs
#     pair_adverts = PairOtoMotoAdvertData.objects.filter(
#         pair__is_otomoto_pair_advert_activated=True,
#         otomoto_advert_id__isnull=False
#     )
#     for advert in pair_adverts:
#         api_data = api_map.get(advert.otomoto_advert_id)
#         if api_data:
#             sync_otomoto_advert(advert, api_data)

#     # Singles
#     single_adverts = OtoMotoAdvertData.objects.filter(
#         product__is_otomoto_advert_activated=True,
#         otomoto_advert_id__isnull=False
#     )
#     for advert in single_adverts:
#         api_data = api_map.get(advert.otomoto_advert_id)
#         if api_data:
#             sync_otomoto_advert(advert, api_data)
            




from django.utils.dateparse import parse_datetime
from django.utils import timezone

def sync_otomoto_advert(instance, api_data):
    """
    Compare API data with DB instance and update if needed.

    instance: a model instance (PairOtoMotoAdvertData or SingleOtoMotoAdvertData)
    api_data: dict from API containing keys: id, status, valid_to, created_at
    """
    api_status = api_data.get("status")
    api_valid_to = parse_datetime(api_data.get("valid_to"))
    api_created_at = parse_datetime(api_data.get("created_at"))

    # Make datetime aware if naive
    def make_aware_if_needed(dt):
        if dt and timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    api_valid_to = make_aware_if_needed(api_valid_to)
    api_created_at = make_aware_if_needed(api_created_at)

    fields_to_update = []

    # Detect status change
    if api_status != instance.otomoto_advert_status:
        instance.otomoto_advert_status = api_status
        fields_to_update.append("otomoto_advert_status")

    # Detect valid_to change
    if api_valid_to != instance.valid_to:
        instance.valid_to = api_valid_to
        fields_to_update.append("valid_to")

    # Optional: sync created_at if missing
    if api_created_at and not instance.created_at:
        instance.created_at = api_created_at
        fields_to_update.append("created_at")

    if fields_to_update:
        instance.save(update_fields=fields_to_update)

    return fields_to_update




# from django.utils import timezone
# from django.utils.dateparse import parse_datetime


# def sync_advert_instance_from_api(instance, otomoto_client):
#     """
#     Generic sync function for any model that has:
#         - otomoto_advert_id
#         - otomoto_advert_status
#         - valid_to
#         - created_at

#     instance → model instance
#     otomoto_client → Otomoto API service
#     """

#     if not instance.otomoto_advert_id:
#         return None

#     data = otomoto_client.fetch_advert(instance.otomoto_advert_id)
#     if not data:
#         return None

#     api_status = data.get("status")
#     api_valid_to = parse_datetime(data.get("valid_to"))
#     api_created_at = parse_datetime(data.get("created_at"))

#     def make_aware_if_needed(dt):
#         if dt and timezone.is_naive(dt):
#             return timezone.make_aware(
#                 dt, timezone.get_current_timezone()
#             )
#         return dt

#     api_valid_to = make_aware_if_needed(api_valid_to)
#     api_created_at = make_aware_if_needed(api_created_at)

#     fields_to_update = []

#     if api_status != instance.otomoto_advert_status:
#         instance.otomoto_advert_status = api_status
#         fields_to_update.append("otomoto_advert_status")

#     if api_valid_to != instance.valid_to:
#         instance.valid_to = api_valid_to
#         fields_to_update.append("valid_to")

#     if api_created_at and not instance.created_at:
#         instance.created_at = api_created_at
#         fields_to_update.append("created_at")

#     if fields_to_update:
#         instance.save(update_fields=fields_to_update)

#     return {
#         "status": api_status,
#         "valid_to": api_valid_to
#     }