from django.test import TestCase


####create ad

from otomoto.client import OtomotoClient
# from otomoto.client import OtomotoAuthData
from tyreadderapp.models import Product
from otomoto.models import OtomotoAuthData

auth = OtomotoAuthData.objects.last()
client = OtomotoClient(auth)

product = Product.objects.get(id=1118)  # Select specific product here

# advert_data = client.prepare_advert_data(product)
# print("Prepared advert data:", advert_data)

response = client.create_and_save_advert(product)
print(response)
print(auth)
#---------------------------------------------------
###activate_ad

from otomoto.models import OtomotoAuthData, Product 
from otomoto.client import OtomotoClient  

auth_data = OtomotoAuthData.objects.first()  # or filter by user/email

client = OtomotoClient(auth_data)

access_token = client.get_access_token()

otomoto_advert_id = "6143945226"

response = client.activate_advert(otomoto_advert_id, access_token)

print(response.status_code)
print(response.text)

#---------------------------------------------------
####deactivate

from otomoto.models import OtomotoAuthData 
from otomoto.client import OtomotoClient  


otomoto_advert_id = "6143980444" 
auth_data = OtomotoAuthData.objects.first() 
client = OtomotoClient(auth_data)
access_token = client.get_access_token()
response = client.deactivate_otomoto_advert(otomoto_advert_id, access_token)
print(response.status_code)
print(response.text)

#---------------------------------------------
### delete ad
from otomoto.models import OtomotoAuthData 
from otomoto.client import OtomotoClient
auth_data = OtomotoAuthData.objects.first() 
client = OtomotoClient(auth_data)  
access_token = client.get_access_token()
otomoto_advert_id = "6143973820" 


response = client.delete_advert(otomoto_advert_id, access_token)
print(response.status_code, response.text)

#--------------------------------------------
####get_otomoto_single_advert

from otomoto.models import OtomotoAuthData 
from otomoto.client import OtomotoClient  


otomoto_advert_id = "6143960097" 
auth_data = OtomotoAuthData.objects.first() 
client = OtomotoClient(auth_data)
access_token = client.get_access_token()
response = client.get_otomoto_single_advert(otomoto_advert_id, access_token)
print(response.status_code)
print(response.text)
print(response.json())

#---------------------------------
##get_access_token_test

from otomoto.models import OtomotoAuthData


auth_data = OtomotoAuthData.objects.first()
client = OtomotoClient(auth)
client = OtomotoClient(auth_data=auth_data)




# test get access token

from otomoto.client import OtomotoClient
from otomoto.models import OtomotoAuthData

from django.utils import timezone

# Get or create auth data
auth_data, created = OtomotoAuthData.objects.get_or_create(
    id=1,
    defaults={
        "access_token": "",
        "refresh_token": "",
        "access_token_expired_time": timezone.now(),
        "refresh_token_expired_time": timezone.now()
    }
)

# Initialize client
client = OtomotoClient(auth_data=auth_data)

# Wrap in try/except to see errors
try:
    token = client.get_access_token()
    print("Access Token:", token)
except Exception as e:
    print("Error occurred:", e)


#test authenticate

from otomoto.models import OtomotoAuthData
from otomoto.client import OtomotoClient



# Get the first record, or create one if it doesn't exist
auth_data = OtomotoAuthData.objects.first()
if not auth_data:
    auth_data = OtomotoAuthData.objects.create()

# Initialize client
client = OtomotoClient(auth_data)

# Call authenticate and print the result
access_token = client.authenticate()
print("Access token:", access_token)



#Pair images

from tyreadderapp.models import PairImage, Product, Pair
from otomoto.client.pair.otomoto_pair_ad import OtomotoPairAd

pair = Pair.objects.get(name="219")

ad = OtomotoPairAd()

images = ad.get_images(pair)
print(images)
# print main_img