"""Tests for guest checkout sale persistence."""

import pytest
from django.db import IntegrityError
from django_attachments.models import Library
from rest_framework.exceptions import ValidationError

from base_feature_app.models import Product, Sale, SoldProduct
from base_feature_app.serializers.sale import SaleSerializer
from base_feature_app.serializers.sale_detail import SaleDetailSerializer
from base_feature_app.serializers.sale_list import SaleListSerializer


@pytest.mark.django_db
class TestSaleSerializer:
    """Cover sale creation and product reference validation."""

    def test_sale_serializer_creates_sold_products(self):
        """Verifies that SaleSerializer creates a Sale with the correct SoldProduct count and quantity."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Product 1',
            category='C',
            sub_category='S',
            description='D',
            price=100,
            gallery=gallery,
        )

        payload = {
            'email': 'customer@example.com',
            'address': '123 Main St',
            'city': 'City',
            'state': 'State',
            'postal_code': '12345',
            'sold_products': [{'product_id': product.id, 'quantity': 2}],
        }

        serializer = SaleSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        sale = serializer.save()

        assert sale.sold_products.count() == 1
        assert sale.sold_products.first().quantity == 2
        assert sale.email == 'customer@example.com'

    def test_sale_serializer_multiple_products(self):
        """Verifies that SaleSerializer creates a Sale with multiple SoldProducts."""
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

        payload = {
            'email': 'multi@example.com',
            'address': '456 Oak Ave',
            'city': 'Town',
            'state': 'State',
            'postal_code': '67890',
            'sold_products': [
                {'product_id': product1.id, 'quantity': 3},
                {'product_id': product2.id, 'quantity': 1}
            ],
        }

        serializer = SaleSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        sale = serializer.save()

        assert sale.sold_products.count() == 2

    def test_sale_serializer_invalid_product_id(self):
        """Reject an unavailable product before creating a sale."""
        payload = {
            'email': 'test@example.com',
            'address': 'Address',
            'city': 'City',
            'state': 'State',
            'postal_code': '12345',
            'sold_products': [{'product_id': 99999, 'quantity': 1}],
        }

        serializer = SaleSerializer(data=payload)
        assert serializer.is_valid() is False
        assert 'product_id' in serializer.errors['sold_products'][0]
        assert (Sale.objects.count(), SoldProduct.objects.count()) == (0, 0)


@pytest.mark.django_db
class TestSaleListSerializer:
    """Cover the public sale list representation."""

    def test_sale_list_serializer_fields(self):
        """Verifies that SaleListSerializer outputs the expected email, city, and postal_code fields."""
        gallery = Library.objects.create(title='Gallery')
        Product.objects.create(
            title='Product',
            category='C',
            sub_category='S',
            description='D',
            price=100,
            gallery=gallery,
        )
        sale = Sale.objects.create(
            email='list@example.com',
            address='789 Pine St',
            city='Village',
            state='State',
            postal_code='11111'
        )

        serializer = SaleListSerializer(sale)
        data = serializer.data

        assert data['email'] == 'list@example.com'
        assert data['city'] == 'Village'
        assert data['postal_code'] == '11111'


@pytest.mark.django_db
class TestSaleDetailSerializer:
    """Cover nested products in a sale detail representation."""

    def test_sale_detail_serializer_includes_sold_products(self):
        """Verifies that SaleDetailSerializer includes nested sold_products with correct quantity."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Product',
            category='C',
            sub_category='S',
            description='D',
            price=100,
            gallery=gallery,
        )
        
        payload = {
            'email': 'detail@example.com',
            'address': '321 Elm St',
            'city': 'Metro',
            'state': 'State',
            'postal_code': '22222',
            'sold_products': [{'product_id': product.id, 'quantity': 5}],
        }

        sale_serializer = SaleSerializer(data=payload)
        assert sale_serializer.is_valid()
        sale = sale_serializer.save()

        detail_serializer = SaleDetailSerializer(sale)
        data = detail_serializer.data

        assert data['email'] == 'detail@example.com'
        assert len(data['sold_products']) == 1
        assert data['sold_products'][0]['quantity'] == 5


@pytest.fixture
def checkout_products(db):
    """Checkout products."""
    gallery = Library.objects.create(title='Checkout gallery')
    return [
        Product.objects.create(
            title=title, category='C', sub_category='S', description='D',
            price=100, gallery=gallery,
        )
        for title in ('First checkout product', 'Second checkout product')
    ]


def checkout_payload(products):
    """Checkout payload."""
    return {
        'email': 'buyer@example.com', 'address': '123 Main St',
        'city': 'City', 'state': 'State', 'postal_code': '12345',
        'sold_products': [
            {'product_id': product.pk, 'quantity': 2} for product in products
        ],
    }


@pytest.mark.django_db
def test_sale_rolls_back_when_a_validated_product_disappears(checkout_products):
    """Test sale rolls back when a validated product disappears."""
    serializer = SaleSerializer(data=checkout_payload(checkout_products))
    assert serializer.is_valid(), serializer.errors
    checkout_products[1].delete()

    with pytest.raises(ValidationError, match='Product is no longer available'):
        serializer.save()

    assert (
        Sale.objects.count(), SoldProduct.objects.count(),
        Sale.sold_products.through.objects.count(),
    ) == (0, 0, 0)


@pytest.mark.django_db
def test_sale_rolls_back_on_a_line_database_failure(checkout_products):
    """Test sale rolls back on a line database failure."""
    serializer = SaleSerializer(data=checkout_payload(checkout_products))
    assert serializer.is_valid(), serializer.errors
    # Exercise a real NOT NULL failure after the first line has been saved.
    serializer.validated_data['sold_products'][1]['quantity'] = None

    with pytest.raises(IntegrityError):
        serializer.save()

    assert (
        Sale.objects.count(), SoldProduct.objects.count(),
        Sale.sold_products.through.objects.count(),
    ) == (0, 0, 0)
