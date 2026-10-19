class Cart:
    """سلة المشتريات — وحدة لكل مطعم، محفوظة فالsession."""

    def __init__(self, request, restaurant):
        self.session = request.session
        self.restaurant = restaurant
        self.key = f"cart_{restaurant.id}"
        self.data = self.session.get(self.key, {})

    # حد أقصى للكمية لكل منتج — حماية من الطلبات غير المعقولة
    MAX_QTY_PER_PRODUCT = 20

    def add(self, product_id, quantity=1):
        product_key = str(product_id)
        new_qty = self.data.get(product_key, 0) + quantity
        self.data[product_key] = min(new_qty, self.MAX_QTY_PER_PRODUCT)
        self.save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self.save()

    def save(self):
        self.session[self.key] = self.data
        self.session.modified = True

    def clear(self):
        self.session.pop(self.key, None)
        self.data = {}
        self.session.modified = True

    def lines(self):
        from apps.menu.models import Product

        products = Product.objects.filter(
            id__in=self.data.keys(),
            restaurant=self.restaurant,
            is_available=True,
        )
        product_map = {str(product.id): product for product in products}
        result = []
        for product_id, quantity in self.data.items():
            product = product_map.get(product_id)
            if product and isinstance(quantity, int) and quantity > 0:
                result.append(
                    {
                        "product": product,
                        "quantity": quantity,
                        "line_total": product.price * quantity,
                    }
                )
        return result

    @property
    def total(self):
        return sum((line["line_total"] for line in self.lines()), start=0)

    def __len__(self):
        return sum(
            quantity
            for quantity in self.data.values()
            if isinstance(quantity, int) and quantity > 0
        )
