"""Exercise the sale deletion cleanup contract."""

import pytest
from django_attachments.models import Library

from base_feature_app.models import Product, Sale, SoldProduct


@pytest.mark.django_db
def test_sale_delete_also_deletes_sold_products(db):
    """Verifies that deleting a Sale cascades to remove associated SoldProducts."""
    product = Product.objects.create(
        title="P2",
        category="C",
        sub_category="S",
        description="D",
        price=20,
        gallery=Library.objects.create(title="G"),
    )
    sold = SoldProduct.objects.create(product=product, quantity=2)
    sale = Sale.objects.create(
        email="buyer@example.com",
        address="Street 1",
        city="City",
        state="State",
        postal_code="12345",
    )
    sale.sold_products.add(sold)

    sale.delete()

    assert not SoldProduct.objects.filter(id=sold.id).exists()
