from django.contrib import admin
from django.urls import path
# from tyreadderapp.views import to_pdf
from olx.views import olx_advert_sync, addpair_olx_bulk
from tyreadderapp import views
from .views import DeleteImageView, DownloadListView, TreadListView, TyreSearchView, UpdateImageView, SingleTreadCreateView, bulk_create_otomoto_ads, update_product_status,modify_pair_image_view,generate_main_pair_image, create_missing_pairs,create_pdf_offer
from .views import shutdown_server
# from .views import ProductView, ThankYouView

app_name = 'tyreadderapp'

urlpatterns = [

    # path("add-products", views.AddTyreView.as_view(), name="products"),
    path("thank-you", views.ThankYouView.as_view(), name="thank-you"),
    path("login", views.login, name="login"),
    path('shutdown/', shutdown_server),
    # path("logout",views.logout(), name="logout"),
    # path("dashboard",views.dashboard(), name="dashboard")
    path("main", views.Main.as_view(), name="main"),
    # path("add-brand", views.AddBrand.as_view(), name="add-brand"),
    # path("addtread", views.AddTread.as_view(), name="add-brand"),
    
    # path("load_treads/",views.load_treads, name = "load_cities"),
         
    path("form", views.tyre_form, name="form"),   
      
    
    # path("labels_to_pdf", views.labels_to_pdf, name="labels_to_pdf"),
    path("single_label/<int:pk>", views.single_label, name="single_label"),  

    path("product_cards_pdf", views.product_cards_pdf, name="product_cards_pdf"),  
    path("product_card_pdf/<int:pk>", views.product_card_pdf, name="product_card_pdf"),

    #products for sale
    path("workspace", views.workspace, name="workspace"),
    path("shop", views.shop, name="shop"),
    # path("sold", views.sold_products, name="shop"),
    

    path("shop/<int:pk>", views.SingleProductView.as_view(), name = "product-detail"),
    path('shop/<int:pk>/edit', views.SingleProductEditView.as_view(), name='edit-detail'),
    path("shop/<int:pk>/delete", views.SingleProductDeleteView.as_view(), name ="delete-detail"),

    path("pair_search", views.pair_search, name="pair_search"),


    path("statistics", views.statistics, name="statistics"),
    path("distinct_treads", views.distinct_treads, name="distinct-treads"),
    path("staff_login", views.stafflogin, name="stafflogin"),
    path("test", views.Test.as_view(), name="test"),
    path("treads",views.getTreads, name = "treads"),
    path("downloads",views.DownloadListView.as_view(), name = "downloads"),
    path("imports",views.ImportView.as_view(), name = "imports"),
    path("add-product-images/<int:product_id>", views.add_product_images,name="add-product-images"),
    path("pairadverts",views.pairadverts, name = "pairadverts"),
    path("add-tread",views.SingleTreadCreateView.as_view(), name = "add-tread"),
    path('addpair-olx-bulk/', addpair_olx_bulk, name='addpair_olx_bulk'),

    # image update delete
    path('delete-image/<int:image_id>/', DeleteImageView.as_view(), name='delete_image'),
    path('update-image/<int:image_id>/', UpdateImageView.as_view(), name='update_image'),

    # form page url
    path('product/',views.tyre_product_view, name="tyre_product_view"),
    path('product/<int:pk>/update/',views.tyre_product_edit_view, name="edit_product"),
    path('product/<int:pk>/delete/', views.tyre_product_delete_view, name='delete_product'),

    # label 
    path('select/multiple_product_label', views.selected_label, name="selected_label"),
    path('select/multiple_label_printout', views.multiple_label_printout, name="multiple_label_printout"),
    
    path('single_label/<str:ids>', views.select_single_label, name="select_single_label"),
    path('process_selected_products', views.process_selected_products, name="process_selected_products"),

    # search functionality tyre tread' and 'tyre class
    path('api/tyre_search/tread/tyre_class/', TyreSearchView.as_view(), name="tyre_search"),
    path('api/treads/', TreadListView.as_view(), name='tread-list'),

    # fetch tread according brand
    path('ajax/load-treads/', views.load_treads, name='ajax_load_treads'),

    # sync olx advert status
    path('olx_advert_sync/', olx_advert_sync, name='olx_advert_sync'),

    path('add-image/', views.add_pair_image, name='add_pair_image'),
    path('image-update/',views.image_update,name='image-update'),

    path('filter-to-add/', views.filter_to_add, name='filter_to_add'),
    path('filter-on-sale/', views.filter_on_sale, name='filter_on_sale'),
    path('filter-to-sold/', views.filter_to_sold, name='filter_to_sold'),
    path('update_status/<int:product_id>/', views.update_product_status, name='update_product_status'),
    path('bulk_update_status/', views.bulk_update_status, name='bulk_update_status'),

    # temperory url to updarte eans
    path("load-ean-data/", views.load_ean_data, name="load_ean_data"),

    

    path('api/tyre-by-size/', views.get_tires_by_size, name='tires_by_size'),

    path('merge-pair-images/', views.merge_pair_images, name='merge_pair_images'),

    path('payu-payment-dashboard/', views.payu_payment_dashboard, name="payu_payment_dashboard" ),
    path('payments/<int:order_id>/', views.payment_detail_view, name='payment_detail'),
    path('payment-dashboard/',views.payment_dashboard,name='payment_dashboard'),

    path('similar-tread-dashboard/', views.similar_tread_dashboard, name='similar_tread_dashboard'),
    path('get-treads/<int:brand_id>/', views.get_treads, name='get_treads'),
    path('prospects_for_pairs/', views.prospects_for_pairs, name='prospects_for_pairs'),
    path('tread_depths_combinations/', views.product_tread_depth_combinations, name='tread_depths_combinations'),
    
    
    path('ean_combinations/', views.product_ean_combinations, name='ean_combinations'),
   
   #warehouses 
    path('warehouses/', views.warehouse_list_view, name='warehouse_list'),
    path('warehouses/<int:warehouse_id>/', views.warehouse_detail_view, name='warehouse_detail'),
    path('assign_location/', views.assign_product_location_view, name='assign_product_location'),
    path('ajax/load-location-data/', views.load_location_data, name='ajax_load_location_data'),
    path('create_staple/', views.create_staple_view, name='create_staple'),
    path('delete-staple/<int:pk>/', views.delete_staple_view, name='delete-staple'),
    
    path('order/<int:order_id>/print/', views.print_order_pdf, name='print_order_pdf'),
    path("bulk_create_otomoto_ads/", views.bulk_create_otomoto_ads, name="bulk_create_otomoto_ads"),

    
    path("update-items-status/", update_product_status, name="update-items-status"),    
    # path("update-order-status/<int:order_id>/", views.update_order_status, name="update_order_status")

    path("modify-pair-image/", modify_pair_image_view, name="modify-pair-image"),
    
    
    path("generate-pair-main-image/", generate_main_pair_image, name="generate_main_pair_image"),
    
    # path(
    #     'pairs/generate-main-image/',
    #     views.generate_main_pair_image,
    #     name='generate_main_pair_image'
    # ),
    path(
        "create_missing_pairs/",create_missing_pairs, name="create_missing_pairs"),
    
    path("create-pdf-offer/", create_pdf_offer, name="create_pdf_offer"),
    
       
    
]
