# from .description import create_allegro_advert_description

# def _allegro_advert_data(product):
#     product_name = product.advert_title
#     description = product.advert_description
#     brand = product.brand.name
#     category_id = "257701"
#     width = product.size.width
#     diameter = float(product.size.diameter)
#     price = float(product.net_price)
#     ean = product.ean
#     stock = 1
#     domain = "tirgumpanel.pl"
    
#     # Get product images
#     product_images = [
#         domain + item.image.url 
#         for item in Image.objects.filter(product=product)[:8]
#     ]

#     # Format description
#     description = description.replace("\r\n", "\n").replace("\r", "\n")
#     paragraphs = description.split("\n")
#     formatted_description = "".join(
#         f"<p>{line.strip()}</p>" 
#         for line in paragraphs 
#         if line.strip()
#     )
#     formatted_description = formatted_description.replace(
#         "ID opony:", "<b>ID opony:</b>"
#     )

#     payload = {
#         "productSet": [{
#             "product": {
#                 "name": product_name,
#                 "category": {
#                     "id": category_id
#                 },
#                 "parameters": [
#                     {
#                         "name": "EAN",
#                         "values": [ean]
#                     },
#                     {
#                         "id": "9300",
#                         "name": "Marka", 
#                         "values": [brand]
#                     },
#                     {
#                         "id": "345",
#                         "name": "Szerokość opony",
#                         "values": [str(width)]  # Convert width to string
#                     },
#                     {
#                         "id": "127088",
#                         "name": "Średnica",
#                         "values": [str(diameter)]  # Convert diameter to string
#                     }
#                 ],
#                 "images": [product_images[0]]  # This should be a list
#             }
#         }],
#         "parameters": [
#             {
#                 "id": "11323",
#                 "name": "Stan",
#                 "valuesIds": ["11323_2"]
#             },
#             {
#                 "id": "128844",
#                 "name": "Liczba opon w ofercie",
#                 "values": ["1 szt."]
#             }
#         ],
#         "images": product_images[1:],  # Additional images
#         "afterSalesServices": {
#             "impliedWarranty": {
#                 "id": "72def2ab-b35e-4ca8-bfc0-cf4bc39cfd56",
#                 "name": "domyślny"
#             },
#             "returnPolicy": {
#                 "id": "7aa7b5c7-4d48-4c50-ab49-f3f7b25aef9e",
#                 "name": "Warunki zwrotu"
#             },
#             "warranty": {
#                 "id": "d40a8bc8-7412-45ce-8c84-4badd12aaac5",
#                 "name": "check this is tril policy"
#             }
#         },
#         "sellingMode": {
#             "price": {
#                 "amount": str(price),  # Convert price to string
#                 "currency": "PLN"
#             }
#         },
#         "stock": {
#             "available": stock
#         },
#         "description": {
#             "sections": [{
#                 "items": [{
#                     "type": "TEXT",
#                     "content": formatted_description
#                 }]
#             }]
#         }
#     }
#     return payload
