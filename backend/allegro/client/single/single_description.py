from tyreadderapp.models import Product


def get_product_description(product: Product) -> dict:
    """
    Build a structured JSON description for a product from its fields.
    """

    lines = [
        f"ID opony: {product.id}" if getattr(product, "id_opony", None) else None,
        f"Marka: {product.brand.name}" if getattr(product, "brand", None) else None,
        f"Model: {product.tread.name}" if getattr(product, "tread", None) else None,
        f"Rozmiar: {product.size.size}" if getattr(product, "size", None) else None,
        f"Halo to ja opis",
        # f"Sezon: {product.season}" if getattr(product, "season", None) else None,
        # f"Indeks nośności: {product.load_index}" if getattr(product, "load_index", None) else None,
        # f"Indeks prędkości: {product.speed_index}" if getattr(product, "speed_index", None) else None,
    ]

    # Remove empty lines
    lines = [line for line in lines if line]

    # Bold the ID label
    lines = [line.replace("ID opony:", "<b>ID opony:</b>") for line in lines]

    # Wrap each line in <p>
    content = "".join(f"<p>{line}</p>" for line in lines)

    description_json = {
        "sections": [
            {
                "items": [
                    {
                        "type": "TEXT",
                        "content": content
                    }
                ]
            }
        ]
    }

    return description_json



# b
# i
# u
# br/
# ul
# ol
# li
# p