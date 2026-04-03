

# utils.py (or anywhere suitable)
from django.utils.translation import gettext_lazy as _
from tyreadderapp.models import Product, TransportationCost
from decimal import Decimal


def create_otomoto_advert_pair_description(pair):
    products = list(
        Product.objects
        .filter(pair=pair)
        .exclude(status=Product.StatusChoices.SOLD)
    )
   

    VAT = Decimal("1.23")

    net_price = pair.get_pair_advert_price()
    gross_price = net_price * VAT

    transportation_cost = pair.get_pair_best_pallete_option()
    transportation_net_value = transportation_cost.get("price", 0)
    transportation_gross_value = transportation_net_value * VAT

    tyres_and_transportation_net_price = net_price + transportation_net_value
    tyres_and_transportation_gross_price = gross_price + transportation_gross_value
    
    

    if not products:
        return ""

    description = ""
    description += "Drogi kliencie\n\n"
    description += "Dwoniąc podaj nam poniższy nr ID zestawu:\n"
    description += f"-----------------------------------\n"
    description += f"Nr ID zestawu: {pair.get_pair_name()}\n"
    description += f"-----------------------------------\n"

    description += f"W naszej ofercie mamy używany {pair.get_pair_advert_title()}\n\n"

    description += f"WAŻNE.\n"
    description += f"Kupując u nas możesz liczyć na pewną i profesjonalną obsługę.\n"
    description += f"Prowadzimy serwis mobilny, stacjonarny opon ciężarowych.\n"
    description += f"Wszystkie opony są sprawdzane ciśnieniowo oraz wizualnie.\n"
    description += f"Udzielamy gwarancji rozruchowej na 1 mies.\n"
    description += f"Prowadzimy również sprzedaż wysyłkową na paletach.\n"
    description += f"************************************\n"
    description += f"Cena samych opon to:\n"
    description += f"{net_price:.2f} zł netto ({gross_price:.2f} zł brutto) .\n"

    if transportation_net_value > 0:
        description += f"Koszty wysyłki to:\n"
        description += f"{transportation_net_value:.2f} zł netto ({transportation_gross_value:.2f} zł brutto).\n"
        description += (
            f"Całość, czyli cena opon + wysyłka paletowa wynosi "
            f"{tyres_and_transportation_net_price:.2f} zł netto.\n\n"
        )
        description += (
            f"Łącznie do zapłaty z wysyłką: "
            f"{tyres_and_transportation_gross_price:.2f} zł brutto.\n\n"
        )
        description += f"************************************\n"

    description += f"Poniżej znajdziesz dokładny opis każdej opony wchodzącej w skład zestawu.\n\n"
    description += f"Zestaw składa się z {len(products)} opon:\n\n"

    for index, product in enumerate(products, start=1):
        description += f"OPONA {index}\n\n"
        description += f"Marka: {product.brand.name if product.brand else 'Unknown'}\n"
        description += f"Bieżnik: {product.tread.name if product.tread else 'Unknown'}\n"
        description += f"Rozmiar: {product.size or ''}\n"
        description += f"Data produkcji: {product.dot or ''} r.\n"
        description += f"Min. głęb. bieżnika: {product.tread_depth_min or ''} mm\n"
        description += f"Maks. głęb. bieżnika: {product.tread_depth_max or ''} mm\n"
        if product.new_tire_tread_depth:
            description += f"UWAGA: Fabryczna głębokość bieżnika: {product.new_tire_tread_depth} mm.\n"
        if product.new_tire_price:
            description += f"Orientacyjna cena nowej opony: {product.new_tire_price}\n"

        if product.is_retreaded:
                description += "* Opona bieżnikowana.\n\n"

        # description += "Stan techniczny:\n\n"

        if product.is_tire_bead_damaged:
                description += (
                "Stopka opony posiada niewielki uszczerbek gumy, "
                "powstały podczas montażu opony na felgę. "
                "Jest to kosmetyczny ubytek, który w żaden sposób "
                "nie wpływa na bezpieczeństwo jazdy czy dalszą "
                "eksploatację opony.\n\n"
            )

        if product.is_incised:
                description += (
                "Bieżnik opony został profesjonalnie pogłębiony według zaleceń producenta opon.\n\n"
            )

        if product.front_repairs:
                description += f"Naprawy gwoździowe: {product.front_repairs}\n\n"

        # if not product.is_side_repair:
        #     description += "* Bez napraw ścian bocznych.\n\n"

        if product.is_visible_cracks:
                description += (
                "* Guma jest w niewielkim stopniu sparciała. Nie wpływa to na dalszą eksploatację.\n\n"
            )

        if product.is_braked:
                description += (
                "* Posiada delikatny ślad po hamowaniu.\n\n"
            )

        if product.is_braked_repair:
                description += (
                "* Opona została profesjonalnie naprawiona po “przyhamowaniu”.\n\n"
            )

        if product.is_shoulder_repair:
                description += "* Posiada profesjonalnie wykonaną naprawę w części barku.\n\n"

        if product.is_cosmetology:
                description += (
                "* Widoczne niewielkie poprawki kosmetyczne.\n\n"
            )

        if product.is_toothed_out:
                description += (
                "* Widoczne delikatne wyząbkowanie.\n\n"
            )

        if product.is_ruts:
                description += (
                "Widoczne koleiny na krawędziach.\n\n"
            )

        if product.is_circumventional_cut:
                description += (
                "Opona posiada dodatkowy rowek w bieżniku.\n\n"
            )

        description += f"-----------------------------------\n\n"

    # ✅ ONLY CHANGE: return moved OUTSIDE the loop
    
    return description
