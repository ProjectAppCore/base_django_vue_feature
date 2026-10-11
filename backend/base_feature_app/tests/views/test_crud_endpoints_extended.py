"""Extended CRUD endpoint tests: auth guards, 404 paths and serializer contracts."""
import pytest
from django.urls import reverse
from django_attachments.models import Library
from rest_framework import status

from base_feature_app.models import Product


@pytest.fixture
def staff_client(admin_client):
    """Alias for admin_client to preserve test semantics."""
    return admin_client


# ---------------------------------------------------------------------------
# Blog CRUD — atomic tests
# ---------------------------------------------------------------------------

@pytest.fixture
def created_blog(staff_client):
    """Blog created via API, returns (staff_client, blog_id)."""
    library = Library.objects.create(title='Blog Library')
    url = reverse('create-blog')
    response = staff_client.post(
        url,
        {'title': 'New Blog', 'description': 'Desc', 'category': 'Cat', 'image': library.id},
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    return staff_client, response.json()['id']


@pytest.mark.django_db
def test_blog_create_returns_201_for_staff(staff_client):
    """Blog create returns 201 for staff."""
    library = Library.objects.create(title='Blog Library Create')
    url = reverse('create-blog')
    response = staff_client.post(
        url,
        {'title': 'New Blog', 'description': 'Desc', 'category': 'Cat', 'image': library.id},
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['title'] == 'New Blog'


@pytest.mark.django_db
def test_blog_retrieve_returns_200_for_staff(created_blog):
    """Blog retrieve returns 200 for staff."""
    client, blog_id = created_blog
    url = reverse('retrieve-blog', kwargs={'blog_id': blog_id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_blog_patch_returns_200_for_staff(created_blog):
    """Blog patch returns 200 for staff."""
    client, blog_id = created_blog
    url = reverse('update-blog', kwargs={'blog_id': blog_id})
    response = client.patch(url, {'title': 'Updated Title'}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['title'] == 'Updated Title'


@pytest.mark.django_db
def test_blog_delete_returns_204_for_staff(created_blog):
    """Blog delete returns 204 for staff."""
    client, blog_id = created_blog
    url = reverse('delete-blog', kwargs={'blog_id': blog_id})
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_blog_returns_404_after_delete(created_blog):
    """Blog returns 404 after delete."""
    client, blog_id = created_blog
    delete_url = reverse('delete-blog', kwargs={'blog_id': blog_id})
    retrieve_url = reverse('retrieve-blog', kwargs={'blog_id': blog_id})
    client.delete(delete_url)
    response = client.get(retrieve_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_blog_retrieve_returns_404_when_not_found(staff_client):
    """Blog retrieve returns 404 when not found."""
    url = reverse('retrieve-blog', kwargs={'blog_id': 999999})
    response = staff_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_blog_create_invalid_payload_returns_400(staff_client):
    """Blog create invalid payload returns 400."""
    url = reverse('create-blog')
    response = staff_client.post(url, {}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_blog_create_rejects_unauthenticated(api_client):
    """Blog create rejects unauthenticated."""
    url = reverse('create-blog')
    response = api_client.post(url, {'title': 'X', 'description': 'D', 'category': 'C'}, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Product CRUD — atomic tests
# ---------------------------------------------------------------------------

@pytest.fixture
def created_product(staff_client):
    """Product created via API, returns (staff_client, product_id, library_id)."""
    library = Library.objects.create(title='Product Library')
    url = reverse('create-product')
    response = staff_client.post(
        url,
        {
            'title': 'New Product',
            'category': 'Cat',
            'sub_category': 'Sub',
            'description': 'Desc',
            'price': 123,
            'gallery': library.id,
        },
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    return staff_client, response.json()['id'], library.id


@pytest.mark.django_db
def test_product_create_returns_201_for_staff(staff_client):
    """Product create returns 201 for staff."""
    library = Library.objects.create(title='Product Library Create')
    url = reverse('create-product')
    response = staff_client.post(
        url,
        {'title': 'New P', 'category': 'Cat', 'sub_category': 'Sub', 'description': 'D', 'price': 50, 'gallery': library.id},
        format='json',
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['title'] == 'New P'


@pytest.mark.django_db
def test_product_retrieve_returns_200_for_staff(created_product):
    """Product retrieve returns 200 for staff."""
    client, product_id, _ = created_product
    url = reverse('retrieve-product', kwargs={'product_id': product_id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_product_put_returns_200_for_staff(created_product):
    """Product put returns 200 for staff."""
    client, product_id, library_id = created_product
    url = reverse('update-product', kwargs={'product_id': product_id})
    response = client.put(
        url,
        {'title': 'Updated', 'category': 'Cat', 'sub_category': 'Sub', 'description': 'D', 'price': 222, 'gallery': library_id},
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK
    assert float(response.json()['price']) == 222.0


@pytest.mark.django_db
def test_product_delete_returns_204_for_staff(created_product):
    """Product delete returns 204 for staff."""
    client, product_id, _ = created_product
    url = reverse('delete-product', kwargs={'product_id': product_id})
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.fixture
def products_sharing_gallery(staff_client):
    """Two products reference the same library through real CRUD requests."""
    library = Library.objects.create(title='Shared API gallery')
    payload = {
        'title': 'Shared first', 'category': 'Cat', 'sub_category': 'Sub',
        'description': 'Shared description', 'price': 50, 'gallery': library.pk,
    }
    first = staff_client.post(reverse('create-product'), payload, format='json')
    second = staff_client.post(
        reverse('create-product'), {**payload, 'title': 'Shared second'}, format='json',
    )
    assert (first.status_code, second.status_code) == (201, 201)
    return first.json()['id'], second.json()['id'], library.pk


@pytest.mark.django_db
def test_product_delete_preserves_other_api_product(staff_client, products_sharing_gallery):
    """Deleting one API product leaves the other product retrievable unchanged."""
    first_id, retained_id, library_id = products_sharing_gallery
    retained_before = Product.objects.values().get(pk=retained_id)

    response = staff_client.delete(reverse('delete-product', kwargs={'product_id': first_id}))
    retained_response = staff_client.get(reverse('retrieve-product', kwargs={'product_id': retained_id}))

    assert response.status_code == 204
    assert not Product.objects.filter(pk=first_id).exists()
    assert retained_response.status_code == 200
    assert retained_response.json()['title'] == 'Shared second'
    assert Product.objects.values().get(pk=retained_id) == retained_before
    assert Library.objects.filter(pk=library_id).exists()


@pytest.mark.django_db
def test_product_retrieve_returns_404_when_not_found(staff_client):
    """Product retrieve returns 404 when not found."""
    url = reverse('retrieve-product', kwargs={'product_id': 999999})
    response = staff_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_product_create_invalid_payload_returns_400(staff_client):
    """Product create invalid payload returns 400."""
    url = reverse('create-product')
    response = staff_client.post(url, {}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_product_create_rejects_unauthenticated(api_client):
    """Product create rejects unauthenticated."""
    url = reverse('create-product')
    response = api_client.post(url, {'title': 'X', 'category': 'C', 'sub_category': 'S', 'description': 'D', 'price': 1}, format='json')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# User CRUD — atomic tests
# ---------------------------------------------------------------------------

_NEW_USER_PAYLOAD = {
    'email': 'created@example.com',
    'password': 'pass12345',
    'first_name': 'Created',
    'last_name': 'User',
    'phone': '123',
    'role': 'customer',
    'is_active': True,
    'is_staff': False,
}


@pytest.fixture
def created_user_via_api(staff_client):
    """User created via admin API, returns (staff_client, user_id)."""
    url = reverse('create-user')
    response = staff_client.post(url, _NEW_USER_PAYLOAD, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    return staff_client, response.json()['id']


@pytest.mark.django_db
def test_user_create_returns_201_for_staff(staff_client):
    """User create returns 201 for staff."""
    url = reverse('create-user')
    response = staff_client.post(url, _NEW_USER_PAYLOAD, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()['email'] == 'created@example.com'


@pytest.mark.django_db
def test_user_retrieve_returns_200_for_staff(created_user_via_api):
    """User retrieve returns 200 for staff."""
    client, user_id = created_user_via_api
    url = reverse('retrieve-user', kwargs={'user_id': user_id})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_patch_returns_200_for_staff(created_user_via_api):
    """User patch returns 200 for staff."""
    client, user_id = created_user_via_api
    url = reverse('update-user', kwargs={'user_id': user_id})
    response = client.patch(url, {'first_name': 'Updated'}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['first_name'] == 'Updated'


@pytest.mark.django_db
def test_user_delete_returns_204_for_staff(created_user_via_api):
    """User delete returns 204 for staff."""
    client, user_id = created_user_via_api
    url = reverse('delete-user', kwargs={'user_id': user_id})
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_user_returns_404_after_delete(created_user_via_api):
    """User returns 404 after delete."""
    client, user_id = created_user_via_api
    delete_url = reverse('delete-user', kwargs={'user_id': user_id})
    retrieve_url = reverse('retrieve-user', kwargs={'user_id': user_id})
    client.delete(delete_url)
    response = client.get(retrieve_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_user_create_invalid_payload_returns_400(staff_client):
    """User create invalid payload returns 400."""
    url = reverse('create-user')
    response = staff_client.post(url, {}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_delete_rejects_unauthenticated(api_client, user):
    """User delete rejects unauthenticated."""
    url = reverse('delete-user', kwargs={'user_id': user.id})
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Sale list/detail — atomic tests
# ---------------------------------------------------------------------------

@pytest.fixture
def sale_in_db(db, product):
    """Sale created directly in DB via the create-sale API."""
    from base_feature_app.models import Sale, SoldProduct
    sold = SoldProduct.objects.create(product=product, quantity=2)
    sale = Sale.objects.create(
        email='buyer@example.com',
        address='Street 1',
        city='City',
        state='State',
        postal_code='12345',
    )
    sale.sold_products.add(sold)
    return sale


@pytest.mark.django_db
def test_sale_list_returns_200_for_staff(staff_client, sale_in_db):
    """Sale list returns 200 for staff."""
    url = reverse('list-sales')
    response = staff_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_sale_retrieve_returns_200_for_staff(staff_client, sale_in_db):
    """Sale retrieve returns 200 for staff."""
    url = reverse('retrieve-sale', kwargs={'sale_id': sale_in_db.id})
    response = staff_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_sale_retrieve_returns_404_when_not_found(staff_client):
    """Sale retrieve returns 404 when not found."""
    url = reverse('retrieve-sale', kwargs={'sale_id': 999999})
    response = staff_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Missing 404 paths — update and delete with non-existent IDs
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_blog_update_returns_404_when_not_found(staff_client):
    """Blog update returns 404 when not found."""
    url = reverse('update-blog', kwargs={'blog_id': 999999})
    response = staff_client.patch(url, {'title': 'X'}, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_blog_delete_returns_404_when_not_found(staff_client):
    """Blog delete returns 404 when not found."""
    url = reverse('delete-blog', kwargs={'blog_id': 999999})
    response = staff_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_product_update_returns_404_when_not_found(staff_client):
    """Product update returns 404 when not found."""
    url = reverse('update-product', kwargs={'product_id': 999999})
    response = staff_client.patch(url, {'title': 'X'}, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_product_delete_returns_404_when_not_found(staff_client):
    """Product delete returns 404 when not found."""
    url = reverse('delete-product', kwargs={'product_id': 999999})
    response = staff_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_user_update_returns_404_when_not_found(staff_client):
    """User update returns 404 when not found."""
    url = reverse('update-user', kwargs={'user_id': 999999})
    response = staff_client.patch(url, {'first_name': 'X'}, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_user_delete_returns_404_when_not_found(staff_client):
    """User delete returns 404 when not found."""
    url = reverse('delete-user', kwargs={'user_id': 999999})
    response = staff_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
