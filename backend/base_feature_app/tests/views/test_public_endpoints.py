"""Tests for guest checkout sale persistence."""

import pytest
from django.urls import reverse
from django_attachments.models import Library
from rest_framework import status

from base_feature_app.models import Blog, Product, Sale, SoldProduct


@pytest.fixture
def library(db):
    """Library."""
    return Library.objects.create(title='Test Library')


@pytest.fixture
def product(db, library):
    """Product."""
    return Product.objects.create(
        title='Test Product',
        category='Test Category',
        sub_category='Test Sub',
        description='Test Description',
        price=100,
        gallery=library,
    )


@pytest.fixture
def blog(db, library):
    """Blog."""
    return Blog.objects.create(
        title='Test Blog',
        description='Test Description',
        category='Test Category',
        image=library,
    )


@pytest.mark.django_db
def test_product_list_success(api_client, product):
    """Test product list success."""
    url = reverse('list-products')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


@pytest.mark.django_db
def test_blog_list_success(api_client, blog):
    """Test blog list success."""
    url = reverse('list-blogs')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


@pytest.mark.django_db
def test_create_sale_validation_error(api_client):
    """Test create sale validation error."""
    url = reverse('create-sale')
    response = api_client.post(url, {}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize('quantity', [1, 2])
def test_create_sale_success(api_client, product, quantity):
    """Persist the exact positive quantity supplied by a guest."""
    url = reverse('create-sale')
    payload = {
        'email': 'buyer@example.com',
        'address': '123 Main St',
        'city': 'City',
        'state': 'State',
        'postal_code': '12345',
        'sold_products': [
            {
                'product_id': product.id,
                'quantity': quantity,
            }
        ],
    }

    response = api_client.post(url, payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['email'] == 'buyer@example.com'
    assert len(data['sold_products']) == 1
    assert data['sold_products'][0]['quantity'] == quantity
    assert Sale.objects.count() == 1
    assert SoldProduct.objects.count() == 1
    sale = Sale.objects.get(pk=data['id'])
    sold_product = sale.sold_products.get()
    assert sold_product.product_id == product.pk
    assert sold_product.quantity == quantity


@pytest.mark.django_db
@pytest.mark.parametrize('quantity', [0, -1])
def test_create_sale_rejects_non_positive_quantity(api_client, product, quantity):
    """Reject the entire guest order when a later line has no positive quantity."""
    existing_sale = Sale.objects.create(
        email='existing@example.com', address='7 Existing St', city='Existing City',
        state='Existing State', postal_code='77777',
    )
    existing_line = SoldProduct.objects.create(product=product, quantity=7)
    existing_sale.sold_products.add(existing_line)
    sales_before = list(Sale.objects.order_by('pk').values())
    lines_before = list(SoldProduct.objects.order_by('pk').values())
    relations_before = list(Sale.sold_products.through.objects.order_by('pk').values())
    payload = {
        'email': 'buyer@example.com', 'address': '123 Main St',
        'city': 'City', 'state': 'State', 'postal_code': '12345',
        'sold_products': [
            {'product_id': product.pk, 'quantity': 2},
            {'product_id': product.pk, 'quantity': quantity},
        ],
    }

    response = api_client.post(reverse('create-sale'), payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['sold_products'] == [
        {}, {'quantity': ['Quantity must be at least 1.']},
    ]
    assert (
        Sale.objects.count(), SoldProduct.objects.count(),
        Sale.sold_products.through.objects.count(),
    ) == (1, 1, 1)
    assert list(Sale.objects.order_by('pk').values()) == sales_before
    assert list(SoldProduct.objects.order_by('pk').values()) == lines_before
    assert list(Sale.sold_products.through.objects.order_by('pk').values()) == relations_before


@pytest.mark.django_db
def test_create_sale_rejects_an_unavailable_product(api_client, product):
    """Test create sale rejects an unavailable product."""
    missing_product_id = product.pk
    product.delete()
    payload = {
        'email': 'buyer@example.com', 'address': '123 Main St',
        'city': 'City', 'state': 'State', 'postal_code': '12345',
        'sold_products': [{'product_id': missing_product_id, 'quantity': 2}],
    }

    response = api_client.post(reverse('create-sale'), payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'product_id' in response.json()['sold_products'][0]
    assert (Sale.objects.count(), SoldProduct.objects.count()) == (0, 0)
