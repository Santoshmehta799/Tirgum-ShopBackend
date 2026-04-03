from collections import defaultdict
from decimal import Decimal






def aggregate_sizes_from_items(products, stack_max_width=1960):
    size_counts = {}

    for product in products:
        size = product.size
        if not size:
            continue

        width = size.width
        profile = size.profile
        diameter = size.diameter

        if profile is None:
            final_profile_size = width * 0.8 * 2.54
            size_key = f"{width}/80R{diameter}"
        else:
            final_profile_size = width * (profile / 100) * 2.54
            size_key = f"{width}/{profile}R{diameter}"

        final_profile_size = round(final_profile_size, 2)

        if size_key not in size_counts:
            size_counts[size_key] = {
                "quantity": 0,
                "size": size,
                "real_profile_dim": final_profile_size,
                "ofd": size.OFD,
            }

        size_counts[size_key]["quantity"] += 1

    aggregated = []

    for key, data in size_counts.items():
        qty = data["quantity"]
        size = data["size"]

        aggregated.append({
            "size": key,
            "quantity": qty,
            "ofd": data["ofd"],
            "details": size,
            "stack_free_space": max(0, stack_max_width - (qty * size.width)),
            "same_size_stack_additional_qty": max(
                0, getattr(size, "stack_quantity", 0) - qty
            ),
            "real_profile_dim": data["real_profile_dim"],
        })

    return aggregated



# def has_multiple_sizes(aggregated_sizes):
#     size_keys = {
#         f"{p.size.width}/{p.size.profile}R{p.size.diameter}"
#         for p in aggregated_sizes
#     }

#     return len(size_keys) > 1


def calculate_pallets(aggregated_sizes):
    pallets = {
            "half": 0,
            "euro": 0,
            "industrial_m": 0,
            "industrial_d": 0
        }
   

    for size in aggregated_sizes:
        details = size["details"]
        stack_winner = None
        tread_to_y_winner = None
        quantity = size["quantity"]
        

        if details.tread_to_y_winner:
            tread_to_y_winner = details.tread_to_y_winner.lower().replace(' ', '_').lower()
        if details.stack_winner:
                stack_winner = details.stack_winner.lower().replace(' ', '_').lower()
        if size['quantity'] <= details.tread_to_y_quantity:
            if tread_to_y_winner in pallets:
                    pallets[tread_to_y_winner] += details.tread_to_y_quantity
            else:
                    pallets[tread_to_y_winner] = details.tread_to_y_quantity
        else:
            quantity = size['quantity'] - details.tread_to_y_quantity
            if stack_winner in pallets:
                    pallets[stack_winner] += quantity
            else:
                    pallets[stack_winner] = quantity
    print(pallets)
    return pallets


def calculate_shipping_amount(pallets, pallet_queryset):
    """
    pallet_queryset = Pallete.objects.all()
    """

    amount = Decimal("0.00")

    for name, quantity in pallets.items():
        if not name:
            continue

        db_name = name.replace("_", " ")
        pallet = pallet_queryset.filter(name__iexact=db_name).first()

        if pallet and pallet.net_price:
            amount += pallet.net_price * quantity

    return amount
