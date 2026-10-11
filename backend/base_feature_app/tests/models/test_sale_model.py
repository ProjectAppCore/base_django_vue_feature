"""Exercise sale line ownership and product deletion protection."""

import pytest
from django.db import IntegrityError, connection
from django.db.models.deletion import ProtectedError
from django_attachments.models import Library

from base_feature_app.models import Product, Sale, SoldProduct
from base_feature_app.tests.factories import SaleFactory, SoldProductFactory


@pytest.mark.django_db
class TestSaleModel:
    """Exercise the persisted sale model contract."""

    def test_sale_delete_removes_sold_products(self):
        """Verifies that deleting a Sale cascades to remove its associated SoldProducts."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Product',
            category='Candles',
            sub_category='Modern',
            description='Description',
            price=100,
            gallery=gallery,
        )

        sold = SoldProduct.objects.create(product=product, quantity=1)
        sale = Sale.objects.create(
            email='customer@example.com',
            address='123 Main St',
            city='City',
            state='State',
            postal_code='12345'
        )
        sale.sold_products.add(sold)

        sold_id = sold.id
        sale.delete()

        assert not SoldProduct.objects.filter(id=sold_id).exists()

    def test_sale_creation(self):
        """Persist the supplied sale delivery details."""
        sale = Sale.objects.create(
            email='test@example.com',
            address='456 Oak Avenue',
            city='New York',
            state='NY',
            postal_code='10001'
        )
        
        assert sale.email == 'test@example.com'
        assert sale.address == '456 Oak Avenue'
        assert sale.city == 'New York'
        assert sale.state == 'NY'
        assert sale.postal_code == '10001'

    def test_sale_str_representation(self):
        """Display the buyer email as the sale string representation."""
        sale = Sale.objects.create(
            email='display@example.com',
            address='Address',
            city='City',
            state='State',
            postal_code='12345'
        )
        assert str(sale) == 'display@example.com'

    def test_sale_with_multiple_products(self):
        """Verifies that a Sale can hold multiple SoldProducts and reports the correct count."""
        gallery = Library.objects.create(title='Gallery')
        product1 = Product.objects.create(
            title='Product 1',
            category='C1',
            sub_category='S1',
            description='D1',
            price=100,
            gallery=gallery,
        )
        product2 = Product.objects.create(
            title='Product 2',
            category='C2',
            sub_category='S2',
            description='D2',
            price=200,
            gallery=gallery,
        )

        sold1 = SoldProduct.objects.create(product=product1, quantity=2)
        sold2 = SoldProduct.objects.create(product=product2, quantity=3)
        
        sale = Sale.objects.create(
            email='multi@example.com',
            address='789 Pine St',
            city='Los Angeles',
            state='CA',
            postal_code='90001'
        )
        sale.sold_products.add(sold1, sold2)

        assert sale.sold_products.count() == 2


@pytest.mark.django_db
class TestSoldProductModel:
    """Exercise the persisted sold product model contract."""

    def test_sold_product_creation(self):
        """Verifies that a SoldProduct is created with the correct product reference and quantity."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Product',
            category='Category',
            sub_category='SubCategory',
            description='Description',
            price=150,
            gallery=gallery,
        )

        sold_product = SoldProduct.objects.create(product=product, quantity=5)
        
        assert sold_product.product == product
        assert sold_product.quantity == 5

    def test_sold_product_str_representation(self):
        """Display the product title and sold quantity."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Display Product',
            category='Cat',
            sub_category='Sub',
            description='Desc',
            price=100,
            gallery=gallery,
        )

        sold_product = SoldProduct.objects.create(product=product, quantity=3)
        assert str(sold_product) == 'Display Product (Qty: 3)'

    def test_sold_product_protect_on_product_delete(self):
        """Verifies that attempting to delete a referenced Product raises ProtectedError."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Protected Product',
            category='Cat',
            sub_category='Sub',
            description='Desc',
            price=100,
            gallery=gallery,
        )

        sold_product = SoldProduct.objects.create(product=product, quantity=1)
        
        # Trying to delete product should raise ProtectedError because of PROTECT
        with pytest.raises(ProtectedError):
            product.delete()
        
        # SoldProduct should still exist
        assert SoldProduct.objects.filter(id=sold_product.id).exists()
        assert Product.objects.filter(pk=product.pk, gallery=gallery).exists()
        assert Library.objects.filter(pk=gallery.pk).exists()


@pytest.fixture
def shared_sales(db):
    """Two sales share one line while another line belongs only to the first."""
    selected = SaleFactory()
    retained = SaleFactory()
    shared = SoldProductFactory(quantity=7)
    exclusive = SoldProductFactory(product=shared.product, quantity=3)
    unrelated = SoldProductFactory(product=shared.product, quantity=9)
    selected.sold_products.add(shared, exclusive)
    retained.sold_products.add(shared)
    return selected, retained, shared, exclusive, unrelated


def test_sale_delete_preserves_shared_line(shared_sales):
    """Deleting one sale preserves the other sale's complete shared line."""
    selected, retained, shared, exclusive, unrelated = shared_sales
    selected_id = selected.pk
    retained_before = Sale.objects.values().get(pk=retained.pk)

    result = selected.delete()

    assert result is None
    assert not Sale.objects.filter(pk=selected_id).exists()
    assert Sale.objects.values().get(pk=retained.pk) == retained_before
    assert list(retained.sold_products.values_list('pk', 'product_id', 'quantity')) == [
        (shared.pk, shared.product_id, 7),
    ]
    assert not SoldProduct.objects.filter(pk=exclusive.pk).exists()
    assert SoldProduct.objects.get(pk=unrelated.pk).quantity == 9


def test_sale_delete_cleans_last_shared_line_owner(shared_sales):
    """The shared line is cleaned when its final sale is deleted."""
    selected, retained, shared, exclusive, unrelated = shared_sales
    selected.delete()

    retained.delete()

    assert list(SoldProduct.objects.values_list('pk', 'quantity')) == [(unrelated.pk, 9)]
    assert Sale.objects.count() == 0
    assert Product.objects.filter(pk=shared.product_id).exists()


def test_sale_delete_rolls_back_on_line_cleanup_error(shared_sales):
    """A real DELETE failure restores both the sale and its complete relations."""
    selected, retained, shared, exclusive, unrelated = shared_sales
    sale_rows = list(Sale.objects.order_by('pk').values())
    line_rows = list(SoldProduct.objects.order_by('pk').values())
    links = list(Sale.sold_products.through.objects.order_by('pk').values())
    with connection.cursor() as cursor:
        cursor.execute(
            'CREATE TEMP TRIGGER reject_line_cleanup BEFORE DELETE ON base_feature_app_soldproduct '
            f"WHEN OLD.id = {exclusive.pk} BEGIN SELECT RAISE(ABORT, 'line cleanup rejected'); END"
        )
    try:
        with pytest.raises(IntegrityError, match='line cleanup rejected'):
            selected.delete()
    finally:
        with connection.cursor() as cursor:
            cursor.execute('DROP TRIGGER reject_line_cleanup')

    assert list(Sale.objects.order_by('pk').values()) == sale_rows
    assert list(SoldProduct.objects.order_by('pk').values()) == line_rows
    assert list(Sale.sold_products.through.objects.order_by('pk').values()) == links
