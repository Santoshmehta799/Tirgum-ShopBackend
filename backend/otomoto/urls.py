from django.urls import path
from . import views
from .views import  toggle_autorefresh,export_to_olx, sync_ads_view, sync_ad_stats
# from .views import trigger_otomoto_advert_creation
from .client.single.views import active_otomoto,inactive_otomoto, active_single_ad_detail,update_single_ad_detail, create_otomoto_ads,auth_active_otomoto, deactivate_otomoto_ads,activate_otomoto_ads
from .client.pair.views import inactive_otomoto_pairs,active_otomoto_pairs, activate_otomoto_pair_ads, create_otomoto_pair_ads,deactivate_otomoto_pair_ads_manually, prolong_otomoto_pair_ads

app_name = "otomoto"

urlpatterns = [
    #single ads
    path("otomoto-inactive/", inactive_otomoto, name="inactive_otomoto"),
    path("otomoto-active/", active_otomoto, name="active_otomoto"),
    path("activate_otomoto_ads/", activate_otomoto_ads,name="activate_otomoto_ads"),
    path("deactivate_otomoto_ads/", deactivate_otomoto_ads,name="deactivate_otomoto_ads"),
    path(
        "create_otomoto_ad/",create_otomoto_ads, name="create_otomoto_ad"
    ),
    #pair ads
    path("auth-otomoto-active/", auth_active_otomoto, name="auth_active_otomoto"),
    path("inactive_otomoto_pairs/", inactive_otomoto_pairs,name="inactive_otomoto_pairs"),    
    path("active_otomoto_pairs/", active_otomoto_pairs,name="active_otomoto_pairs"),   
    path("activate_otomoto_pair_ads/", activate_otomoto_pair_ads,name="activate_otomoto_pair_ads"),
    path("create_otomoto_pair_ads_manually/", create_otomoto_pair_ads,name="create_otomoto_pair_ads_manually"), 
    path("deactivate_otomoto_pair_ads_manually/", deactivate_otomoto_pair_ads_manually,name="deactivate_otomoto_pair_ads_manually"), 
    path("prolong_otomoto_pair_ads/",prolong_otomoto_pair_ads,name="prolong_otomoto_pair_ads"),
    path("ad-stats/",sync_ad_stats,name="ad-stats"),
    # path("sync-adverts/", views.sync_otomoto_adverts_view, name="sync_adverts"),
    
    #my good function to sync database with otomoto
    path('sync-ads/', sync_ads_view, name='sync_ads'),
    
    
    
    # path("otomoto/create-otomoto-advert", views.trigger_otomoto_advert_creation, name="trigger_otomoto_advert_creation"),
    
    
    
   
    path("toggle_autorefresh/",views.toggle_autorefresh, name="set_autorefresh"),    
    path("olx-export/",views.export_to_olx, name="olx-export"),
    
    
    path(
        "ads/<str:otomoto_advert_id>/",active_single_ad_detail, name="active_single_ad_detail"
    ),
    
    path(
        "update/<str:otomoto_advert_id>/",update_single_ad_detail, name="update_single_ad_detail"
    ),
    
    #TEST
    
     # path('otomoto/create/<int:product_id>/', create_otomoto_advert_view, name='create_otomoto_advert'),
    # path("otomoto/auth/", otomoto_authorize),
    # path("otomoto/callback", otomoto_callback),

    # path("authorize/", views.authorize_otomoto, name="authorize_otomoto"),
    # path("callback/", views.otomoto_callback, name="otomoto_callback"),
    # path("connect_otomoto/", views.connect_otomoto, name="connect_otomoto"),
    # path("profile/", views.profile_otomoto, name="profile_otomoto"), 
    # path("otomoto-active/", views.active_otomoto, name="active_otomoto"),
    # path("refresh_otomoto_ads/", views.refresh_otomoto_ads, name="refresh_otomoto_ads"),
    # path("create_otomoto_ad/", views.create_otomoto_ad, name="create_otomoto_ad"),

]
