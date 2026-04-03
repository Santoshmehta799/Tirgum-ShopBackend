from tyreadderapp.models import TransportationCost


def half_pal_ultimate_transport_net_price(tyre_qty, pal_cost, fuel_charge):
    if tyre_qty == 1:
        transport_net_price = 66.22

    elif tyre_qty > 1:
        transport_net_price = 77.96
    else:
        transport_net_price = 0.00

    half_pal_ultimate_transport_price = (transport_net_price * fuel_charge) + pal_cost
    return half_pal_ultimate_transport_price


def euro_pal_ultimate_transport_net_price(tyre_qty, pal_cost, fuel_charge):
    if tyre_qty == 1:
        transport_net_price = 87.7
    elif tyre_qty == 2:
        transport_net_price = 107.66
    elif tyre_qty > 2:
        transport_net_price = 118.03
    else:
        transport_net_price = 0.00

    euro_pal_ultimate_transport_price = (transport_net_price * fuel_charge) + pal_cost
    return euro_pal_ultimate_transport_price


def industrial_m_ultimate_transport_net_price(fuel_charge, non_standard_fee):
    transport_net_price = 118.03
    industrial_m_ultimate_transport_price = (transport_net_price * fuel_charge) + non_standard_fee
    return industrial_m_ultimate_transport_price


def industrial_d_ultimate_transport_net_price(fuel_charge, non_standard_fee):
    transport_net_price = 118.03
    industrial_d_ultimate_transport_price = (transport_net_price * fuel_charge) + non_standard_fee
    return industrial_d_ultimate_transport_price


def convert_string(input_string):
    # Check if the input string contains an underscore
    if '_' in input_string:
        # Replace underscores with spaces and convert to uppercase
        return input_string.replace('_', ' ').upper()
    else:
        # Convert the entire string to uppercase if no underscore is found
        return input_string.upper()


def get_transportation_cost(pal_name, weight):
    if weight and pal_name:
        from django.db.models import Min
        if weight < 40:
            from decimal import Decimal
            # Get the smallest kg greater than or equal to the given weight
            nearest_weight = TransportationCost.objects.filter(
                pallet__name__icontains=pal_name,  # Filter based on pallet name
            ).aggregate(min_kg=Min('kg'))['min_kg']  # Get the minimum kg value
            weight = Decimal(nearest_weight)
        pal_name = convert_string(pal_name)
        # Get the smallest kg greater than or equal to the given weight
        nearest_kg = TransportationCost.objects.filter(
            pallet__name__icontains=pal_name,  # Filter based on pallet name
            kg__gte=weight  # Get objects where kg is greater than or equal to self.weight
        ).aggregate(min_kg=Min('kg'))['min_kg']  # Get the minimum kg value
        # If a nearest kg is found, filter objects by that kg
        if nearest_kg:
            objects = TransportationCost.objects.filter(
                pallet__name__icontains=pal_name,
                kg=nearest_kg  # Only select objects with the nearest kg
            )

            # Check if objects exist
            if objects.exists():
                # Get the minimum price from the filtered objects
                min_price = objects.aggregate(min_price=Min('price'))['min_price']
                # Get the object with the minimum price
                min_price_object = objects.filter(price=min_price).first()
                return min_price, min_price_object.company.company_name
    return 0, None


def get_transportation_discount(pal_name, weight):
    if weight and pal_name:
        from django.db.models import Min
        if weight < 40:
            from decimal import Decimal
            # Get the smallest kg greater than or equal to the given weight
            nearest_weight = TransportationCost.objects.filter(
                pallet__name__icontains=pal_name,  # Filter based on pallet name
            ).aggregate(min_kg=Min('kg'))['min_kg']  # Get the minimum kg value
            weight = Decimal(nearest_weight)
        pal_name = convert_string(pal_name)
        # Get the smallest kg greater than or equal to the given weight
        nearest_kg = TransportationCost.objects.filter(
            pallet__name__icontains=pal_name,  # Filter based on pallet name
            kg__gte=weight  # Get objects where kg is greater than or equal to self.weight
        ).aggregate(min_kg=Min('kg'))['min_kg']  # Get the minimum kg value
        # If a nearest kg is found, filter objects by that kg
        if nearest_kg:
            objects = TransportationCost.objects.filter(
                pallet__name__icontains=pal_name,
                kg=nearest_kg  # Only select objects with the nearest kg
            )

            # Check if objects exist
            if objects.exists():
                # Get the minimum price from the filtered objects
                min_price = objects.aggregate(min_price=Min('price'))['min_price']
                # Get the object with the minimum price
                min_price_object = objects.filter(price=min_price).first()
                return min_price_object.pal_discounted_price
    return 0.0


def get_palletes(full_pal_qty, full_pall_name, remaining_pal_qty, remaining_pall_name):
    pallets = {
        "half": 0,
        "euro": 0,
        "industrial_m": 0,
        "industrial_d": 0
    }
    if full_pall_name:
        pallets[full_pall_name] += full_pal_qty
    if remaining_pall_name:
        pallets[remaining_pall_name] += remaining_pal_qty
    return pallets


def determine_packing(quantity, tread_to_y_quantity, tread_to_x_quantity, stack_quantity):
    options = {
        "tread_to_y": tread_to_y_quantity,
        "tread_to_x": tread_to_x_quantity,
        "stack": stack_quantity
    }
    if quantity <= tread_to_y_quantity:
        closest_option = 'tread_to_y'
    elif quantity <= tread_to_x_quantity and quantity > tread_to_y_quantity:
        closest_option = 'tread_to_x'
    elif quantity > tread_to_x_quantity and quantity <= stack_quantity:
        closest_option = 'stack'
    else:
        closest_option = ''
    # closest_option = min(options, key=lambda k: abs(quantity - options[k]))
    return closest_option



