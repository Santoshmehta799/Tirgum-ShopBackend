# utils.py (or anywhere suitable)
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


def create_otomoto_advert_description(product):
    
        VAT = Decimal("1.23")
        net_price = Decimal(product.net_price)
        gross_price = net_price * VAT
        # gross_price = f"{net_price:.2f} zł brutto"
        
        

        # instance = self
        # p = product  # Use Product model fields
        description = ""
        description += f"Jeśli dzwonisz z pytaniem o oponę podaj nam poniższy nr ID \n\n"
        # description += f"Będziemy również wdzięczni za podanie informacji z jakiego portalu dzwonisz. \n\n"
        description += f"---------------------------- \n"
        description += f"nr ID opony:{product.id}\n"
        description += f"---------------------------- \n"        
        
       
        description += f"WAŻNE.\n"
        description += f"Kupując u nas możesz liczyć na pewną i profesjonalną obsługę.\n"
        description += f"Prowadzimy serwis mobilny, stacjonarny opon ciężarowych.\n"
        description += f"Wszystkie opony są sprawdzane ciśnieniowo oraz wizualnie.\n"
        description += f"Udzielamy gwarancji rozruchowej na 1 mies.\n"
        description += f"Prowadzimy również sprzedaż wysyłkową na paletach.\n"
        description += f"************************************\n"
        
        description += f"Oferujemy na sprzedaż:\n\n"

        description += f"{product.brand} {product.tread}\n\n"
        description += f"Rozmiar {product.size} \n\n"

        # description += f"Data produkcji opony:{instance.dot}r \n\n"

        if product.dot is None or product.dot == 0:
            description += f""
        else:
            description += f"Data produkcji opony: {product.dot}r \n\n"

        # description += f"Głębokość bieżnika to: {product.tread_depth_min} - {product.tread_depth_max}mm \n\n"

        description += f"Głębokość bieżnika w najpłytszym miejscu: {product.tread_depth_min} mm\n\n"
        description += f"Głębokość bieżnika w najgłębszym miejscu: {product.tread_depth_max} mm \n"
        description += f"----------------------------------------------------\n\n"

        # description += f"Oznacza to, że dokonaliśmy pomiaru w kilku przypadkowych miejscach bieżnika\
        #     i wartości powyżej oznaczają najpłytsze miejsce oraz najwyższe."

        description += _(
            "Stopka opony posiada niewielki uszczerbek gumy, powstały podczas montażu opony na felgę. Jest to kosmetyczny ubytek, który w zaden sposób nie wpływa na bezpieczeństwo jazdy czy dalszą eksploatację opony.\n\n") if product.is_tire_bead_damaged else ""
        description += _(
            "Bieżnik opony został profesjonalnie pogłębiony, według zaleceń producenta opon.\n\n") if product.is_incised else ""
        
        # description += _("Opona posiada profesjonalnie wykonaną naprawę na ścianie bocznej. \
        #                 Tego typu naprawy, wykonujemy jedynie jeśli uszkodzenie było nieduże i \
        #                 technologicznie możliwe do naprawy. Dostosowujemy się do zaleceń \
        #                 producentów wkładów naprawczych, które jasno określają, jakiego \n\n") 
                            
        description += _(
                            "Opona ma profesjonalnie wykonaną naprawę boczną. Tego typu naprawy, wykonujemy jedynie jeśli uszkodzenie było nieduże i technologicznie możliwe do naprawy.\n\n" if product.is_side_repair else ''
                        )

        
        description += (
            _("Guma opony jest w niewielkim stopniu sparciała. Takie oznaki eksploatacji są widoczne czasem nawet po 1 roku użytkowania opony i nie wpływają na jej dalszą eksploatację. Przyczyną zazwyczaj są czynniki zewnętrzne takie jak np. Promienie słoneczne, NIE jest to opona uszkodzona.\n\n") if product.is_visible_cracks else ""
        )
        description += _(
            "Opona posiada delikatny ślad po hamowaniu, widoczny w części bieżnika. Jest to nieduży defekt, który nie ma wpływu na dalszą eksploatację.\n\n") if product.is_braked else ""
        description += _(
            "Opona została profesjonalnie naprawiona po “przyhamowaniu”. Widoczny ślad po hamowaniu bądź po zablokowanym hamulcu w naczepie, zostaje nadlany nową gumą oraz zwulkanizowany w autoklawie. Taka metoda naprawy pozwala na dalsze, bezpieczne użytkowanie opony.\n\n") if product.is_braked_repair else ""
        description += (
            _("Opona posiada profesjonalnie wykonaną naprawę w części barku.\n\n") if product.is_shoulder_repair else ""
        )
        description += _(
            "Opona posiada niewielkie “poprawki” kosmetyczne. Nie nazywamy tego naprawą, ponieważ opona nie była uszkodzona. Opona używana czasami ma drobne pęknięcie lub uszczerbek gumy, np. Od kręcenia kołami w miejscu. Tego typu kosmetykę wykonujemy aby klient dostał oponę w 100%%  sprawną, gotową do montażu.\n\n") if product.is_cosmetology else ""
        description += _(
            "Opona jest delikatnie wyząbkowana. Ze względu na to, że jest to wyząbkowanie w niewielkim stopniu, może ona być dalej eksploatowana na osiach napędowych bądź wleczonych.\n\n") if product.is_toothed_out else ""
        description += _("Opona bieżnikowana.") if product.is_retreaded else ""
        description += _(
            "Widoczne są koleiny na krawędziach. Nierówności są małe, dlatego opony w pełni nadają się do dalszej jazdy.\n\n") if product.is_ruts else ""
        description += (
            _("Opona posiada dodatkowy rowek, który został wyżłobiony w bieżniku od ostrego przedmiotu\n\n")
            if product.is_circumventional_cut
            else ""
        )
        
        description += f"Cena opony: {gross_price:.2f} zł brutto\n\n"       
        
        
        # # ✅ Transport price from Product.get_best_pallete_option()
        pallete_data = product.get_best_pallete_option()
        # price_text = "do ustalenia"
        
        if pallete_data and pallete_data.get("transport_price") is not None:
            transport_net = Decimal(pallete_data["transport_price"])
            transport_gross = transport_net * VAT
            description += f"Cena wysyłki paletowej: {transport_gross:.2f} zł brutto\n\n"
        else:
            description += "Cena wysyłki paletowej: do ustalenia\n\n"

        # if pallete_data:
        #     transport_price = pallete_data.get("transport_price")
        #     transport_price = Decimal(transport_price)   
        #     transport_gross_price = transport_price * VAT
        
        #     # Ensure price is numeric
        #     try:
        #         transport_price = f"{transport_price:.2f} zł netto"
        #     except (TypeError, ValueError):
        #         transport_price = "do ustalenia"
            
        
        description += f"* Przy zakupie pełnej palety, wysyłka GRATIS .\n"
        description += f"* Wystawiam fakturę VAT\n\n"
        
        description += f"* Posiadamy duże ilości używanych opon w tym oraz innych rozmiarach. \n\n"
        description += f"* Zapewniamy stałe dostawy i na bieżąco odświeżamy asortyment. \n\n"
        description += f"* Udzielamy miesięczną gwarancję rozruchową na każdą oponę. \n\n"
        description += f"* Każda z Naszych opon jest sprawdzona ciśnieniowo do 10 bar oraz wizualnie. \n\n"
        description += f"* Możliwy montaż mobilnie/ stacjonarnie. \n\n"
        description += f"* Nawiążemy stałą współpracę na korzystnych warunkach! \n\n"      
        
        description += f"Zapraszamy do kontaktu 7.3.3.4.5.6.4.7.4.\n\n"


        description = description.replace("\r\n", "\n")
        return description
