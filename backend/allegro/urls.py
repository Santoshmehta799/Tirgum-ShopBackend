from django.urls import path
from allegro.client.views import allegro_callback, connect_allegro
from allegro.client.single.views import inactive_allegro,upload_images
from allegro.client.single.allegro_single_ad import create_ad
from allegro.client.single.views import active_allegro, delete_draft,update_ads



app_name = 'allegro'

urlpatterns = [
    
    #Szymon
    path('connect_allegro/', connect_allegro, name='connect_allegro'),
    path('callback/', allegro_callback, name='allegro_callback'),
    path('inactive_allegro/', inactive_allegro, name='inactive_allegro'),
    path('upload_images/', upload_images, name='upload_images'),
    path('create_ad/', create_ad, name='create_ad'),
    path('active_allegro/', active_allegro, name='active_allegro'),
    path('delete_draft/', delete_draft, name='delete_draft'),
    path('update_ads/', update_ads, name='update_ads'),
]

    
    
