

# # utils.py (or anywhere suitable)
# from django.utils.translation import gettext_lazy as _
# from tyreadderapp.models import Product, TransportationCost
# from decimal import Decimal


# # 
# def create_allegro_advert_pair_description(pair):
#     products = list(
#         Product.objects
#         .filter(pair=pair)
#         .exclude(status=Product.StatusChoices.SOLD)
        
#     )
#     VAT = Decimal("1.23")
#     #tyres
#     net_price = pair.get_pair_advert_price()
#     gross_price = net_price * VAT
#   # Assuming 23% VAT
    
#     transportation_cost = pair.get_pair_best_pallete_option()
#     #transportation
#     transportation_net_value = transportation_cost.get("price", 0)  # numeric
#     transportation_gross_value = transportation_net_value * VAT  # Assuming 23% VAT

#     tyres_and_transportation_net_price = net_price + transportation_net_value
    
    
    
#     tyres_and_transportation_gross_price = gross_price + transportation_gross_value   

    
#     if not products:
#         return ""

#     description = ""
#     description += "Drogi kliencie\n\n"
#     # description += "Ogłoszenie dotyczy sprzedaży zestawu opon używanych.\n\n"
#     description += "Dwoniąc podaj nam poniższy nr ID zestawu:\n"
#     description += f"-----------------------------------\n"
#     description += f"Nr ID zestawu: {pair.get_pair_name()}\n"
#     description += f"-----------------------------------\n"
    
    
#     description += f"W naszej ofercie mamy używany {pair.get_pair_advert_title()}\n\n" 
       
#     description += f"WAŻNE.\n"
#     description += f"Kupując u nas możesz liczyć na pewną i profesjonalną obsługę.\n"
#     description += f"Prowadzimy serwis mobilny, stacjonarny opon ciężarowych.\n"
#     description += f"Wszystkie opony są sprawdzane ciśnieniowo oraz wizualnie.\n"
#     description += f"Udzielamy gwarancji rozruchowej na 1 mies.\n"
#     description += f"Prowadzimy również sprzedaż wysyłkową na paletach.\n"
#     description += f"************************************\n"
#     description += f"Cena samych opon to:\n"
#     description += f"{net_price:.2f} zł netto ({gross_price:.2f} zł brutto) .\n"
#     if transportation_net_value > 0:
#         description += f"Koszty wysyłki to:\n"
#         description += f"{transportation_net_value:.2f} zł netto ({transportation_gross_value:.2f} zł brutto).\n"
#         description += f"Całość, czyli cena opon + wysyłka paletowa wynosi {tyres_and_transportation_net_price:.2f} zł netto.\n\n"
#         description += f"Łącznie do zapłaty z wysyłką: {tyres_and_transportation_gross_price:.2f} zł brutto.\n\n"
#         description += f"************************************\n"


        
    
#     description += f"Poniżej znajdziesz dokładny opis każdej opony wchodzącej w skład zestawu.\n\n"
    
#     description += f"Zestaw składa się z {len(products)} opon:\n\n"

#     for index, product in enumerate(products, start=1):
#         description += f"OPONA {index}\n\n"
#         description += f"Marka: {product.brand.name if product.brand else 'Unknown'}\n"
#         description += f"Bieżnik: {product.tread.name if product.tread else 'Unknown'}\n"
#         description += f"Rozmiar: {product.size or ''}\n"
#         description += f"Data produkcji: {product.dot or ''} r.\n"
#         description += f"Min. głęb. bieżnika: {product.tread_depth_min or ''} mm\n"
#         description += f"Maks. głęb. bieżnika: {product.tread_depth_max or ''} mm\n"
#         if not product.is_retreaded:
#                 description += (
#                         f"* Opona bieżnikowana.\n\n"
#         )
        
#         description += "Stan techniczny:\n\n"
        
#         if product.is_tire_bead_damaged:
#             description += (
#                 "Stopka opony posiada niewielki uszczerbek gumy, "
#                 "powstały podczas montażu opony na felgę."
#                 "Jest to kosmetyczny ubytek, który w żaden sposób "
#                 "nie wpływa na bezpieczeństwo jazdy czy dalszą "
#                 "eksploatację opony.\n\n"
#             )
#         if product.is_incised:
#             description += (
#                 "Bieżnik opony został profesjonalnie pogłębiony, według zaleceń producenta opon.\n\n"
#             )
            
#         if product.front_repairs:
#                 description += (
#                         f"Naprawy gwoździowe: {product.front_repairs}\n\n"
#         )
#         if not product.is_side_repair:
#                 description += (
#                         f"* Bez napraw ścian bocznych.\n\n"
#         )
#         if not product.is_visible_cracks:
#                 description += (
#                         f"* Guma jest w niewielkim stopniu sparciała. Takie oznaki eksploatacji są widoczne czasem nawet po 1 roku użytkowania opony i nie wpływają na jej dalszą eksploatację. Przyczyną zazwyczaj są czynniki zewnętrzne takie jak np. Promienie słoneczne, NIE jest to opona uszkodzona.\n\n"
#         )
#         if not product.is_braked:
#                 description += (
#                         f"* Posiada delikatny ślad po hamowaniu, widoczny w części bieżnika. Jest to nieduży defekt, który nie ma wpływu na dalszą eksploatację.\n\n"
#         )
#         if not product.is_braked_repair:
#                 description += (
#                         f"* Opona została profesjonalnie naprawiona po “przyhamowaniu”. Widoczny ślad po hamowaniu bądź po zablokowanym hamulcu w naczepie, zostaje nadlany nową gumą oraz zwulkanizowany w autoklawie. Taka metoda naprawy pozwala na dalsze, bezpieczne użytkowanie opony.\n\n"
#         )
#         if not product.is_shoulder_repair:
#                 description += (
#                         f"* Posiada profesjonalnie wykonaną naprawę w części barku.\n\n"
#         )
#         if not product.is_cosmetology:
#                 description += (
#                         f"* Widoczne niewielkie “poprawki” kosmetyczne. Nie nazywamy tego naprawą, ponieważ opona nie była uszkodzona. Opona używana czasami ma drobne pęknięcie lub uszczerbek gumy, np. Od kręcenia kołami w miejscu. Tego typu kosmetykę wykonujemy aby klient dostał oponę w 100 sprawną, gotową do montażu.\n\n"
#         )
#         if not product.is_toothed_out:
#                 description += (
#                         f"* Widoczne delikatnie wyząbkowanie. Ze względu na to, że jest to wyząbkowanie w niewielkim stopniu, może ona być dalej eksploatowana na osiach napędowych bądź wleczonych.\n\n"
#         )
        
#         if not product.is_ruts:
#                 description += (
#                         f"Widoczne koleiny na krawędziach. Nierówności są małe, dlatego opony w pełni nadają się do dalszej jazdy.\n\n"
#         )
#         if not product.is_circumventional_cut:
#                 description += (
#                         f"Opona posiada dodatkowy rowek, który został wyżłobiony w bieżniku od ostrego przedmiotu.\n\n"
#                         )
                
#         description += f"-----------------------------------\n\n"
#         # description += f"Serdecznie zapraszam\n"
#         # description += f"Mateusz\n"
#         return description

       
        
        
       
