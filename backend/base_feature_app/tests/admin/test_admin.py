"""Exercise admin deletion actions and account administration."""

# quality: disable misplaced_file (admin tests live in admin/ subdirectory by design)
import pytest
from base_feature_app.admin import (
    BaseFeatureAdminSite,
    BaseFeatureUserAdmin,
    BlogAdmin,
    ProductAdmin,
    SaleAdmin,
    admin_site,
)
from base_feature_app.models import Blog, Product, Sale, SoldProduct
from base_feature_app.tests.factories import SaleFactory, SoldProductFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django_attachments.models import Library


def _staff_request(db):  # pragma: no cover - trivial helper
    User = get_user_model()
    user = User.objects.create_superuser(email="admin@example.com", password="pass12345")
    factory = RequestFactory()
    request = factory.get("/admin/")
    request.user = user
    return request


def _request_with_messages(user):
    request = RequestFactory().get('/admin/')
    request.user = user
    request.session = {}
    setattr(request, '_messages', FallbackStorage(request))
    return request


def test_blogadmin_delete_queryset_deletes_objects(db):
    """Remove selected blogs through the registered admin implementation."""
    request = _staff_request(db)
    lib = Library.objects.create(title="BLog Lib")
    Blog.objects.create(title="B1", description="D", category="C", image=lib)
    admin = BlogAdmin(Blog, None)

    admin.delete_queryset(request, Blog.objects.all())

    assert Blog.objects.count() == 0


def test_productadmin_delete_queryset_deletes_objects(db):
    """Verifies that ProductAdmin.delete_queryset removes all products from the database."""
    request = _staff_request(db)
    lib = Library.objects.create(title="Prod Lib")
    Product.objects.create(
        title="P1",
        category="C",
        sub_category="S",
        description="D",
        price=10,
        gallery=lib,
    )
    admin = ProductAdmin(Product, None)

    admin.delete_queryset(request, Product.objects.all())

    assert Product.objects.count() == 0


def test_saleadmin_total_products_and_delete_queryset(db):
    """Verifies SaleAdmin total_products count and that delete_queryset cascades to SoldProduct."""
    request = _staff_request(db)
    lib = Library.objects.create(title="Prod Lib 2")
    product = Product.objects.create(
        title="P2",
        category="C",
        sub_category="S",
        description="D",
        price=20,
        gallery=lib,
    )
    sold = SoldProduct.objects.create(product=product, quantity=3)
    sale = Sale.objects.create(
        email="buyer@example.com",
        address="Street 1",
        city="City",
        state="State",
        postal_code="12345",
    )
    sale.sold_products.add(sold)

    admin = SaleAdmin(Sale, None)

    assert admin.total_products(sale) == 1

    admin.delete_queryset(request, Sale.objects.all())

    assert Sale.objects.count() == 0
    assert SoldProduct.objects.count() == 0


def test_saleadmin_delete_selected_preserves_other_sale(client, db):
    """The real admin deletion action preserves another sale's shared line."""
    client.force_login(_staff_request(db).user)
    selected, retained = SaleFactory(), SaleFactory()
    shared = SoldProductFactory(quantity=7)
    exclusive = SoldProductFactory(product=shared.product, quantity=3)
    selected.sold_products.add(shared, exclusive)
    retained.sold_products.add(shared)
    selected_id = selected.pk
    retained_before = Sale.objects.values().get(pk=retained.pk)

    response = client.post('/admin/base_feature_app/sale/', {
        'action': 'delete_selected', '_selected_action': selected_id, 'post': 'yes',
    })

    assert response.status_code == 302
    assert not Sale.objects.filter(pk=selected_id).exists()
    assert Sale.objects.values().get(pk=retained.pk) == retained_before
    assert list(retained.sold_products.values_list('pk', 'quantity')) == [(shared.pk, 7)]
    assert not SoldProduct.objects.filter(pk=exclusive.pk).exists()


def test_saleadmin_form_offers_previously_linked_line(client, db):
    """The admin permits another sale to select an already linked line."""
    client.force_login(_staff_request(db).user)
    selected, retained = SaleFactory(), SaleFactory()
    shared = SoldProductFactory(quantity=7)
    selected.sold_products.add(shared)

    response = client.get(f'/admin/base_feature_app/sale/{retained.pk}/change/')

    assert response.status_code == 200
    assert response.context['adminform'].form.fields['sold_products'].queryset.get(pk=shared.pk).quantity == 7


@pytest.mark.django_db
def test_custom_admin_site_get_app_list_includes_sections(monkeypatch, db):
    """Verifies that the custom admin site groups models into named management sections."""
    request = _staff_request(db)
    site = BaseFeatureAdminSite(name="myadmin-test")

    # Monkeypatch _build_app_dict so we don't rely on URL reversing
    def fake_build_app_dict(self, req):
        return {
            "base_feature_app": {
                "models": [
                    {"object_name": "User"},
                    {"object_name": "Blog"},
                    {"object_name": "Product"},
                    {"object_name": "Sale"},
                    {"object_name": "SoldProduct"},
                ]
            }
        }

    monkeypatch.setattr(BaseFeatureAdminSite, "_build_app_dict", fake_build_app_dict)

    app_list = site.get_app_list(request)

    # Should group models into custom sections
    section_names = {section["app_label"] for section in app_list}
    assert "user_management" in section_names
    assert "blog_management" in section_names
    assert "product_management" in section_names
    assert "sales_management" in section_names


@pytest.mark.django_db
def test_user_admin_login_as_link_renders_admin_url():
    """Render the target account administration link."""
    User = get_user_model()
    user = User.objects.create_user(email='target@example.com', password='pass12345')
    admin = BaseFeatureUserAdmin(User, admin_site)

    html = admin.login_as_link(user)

    assert 'Login as this user' in html
    assert f'/admin/base_feature_app/user/{user.id}/login_as/' in html


@pytest.mark.django_db
def test_user_admin_login_as_redirects_to_frontend(settings):
    """Redirect account impersonation to the configured frontend."""
    User = get_user_model()
    factory = RequestFactory()
    admin_user = User.objects.create_superuser(email='admin@example.com', password='pass12345')
    target_user = User.objects.create_user(email='target@example.com', password='pass12345')
    request = factory.get('/admin/')
    request.user = admin_user
    settings.FRONTEND_URL = 'http://localhost:3000'

    admin = BaseFeatureUserAdmin(User, admin_site)
    response = admin.login_as_user_view(request, target_user.id)

    assert response.status_code == 302
    assert response['Location'].startswith('http://localhost:3000/admin-login?')
    assert 'access=' in response['Location']
    assert 'refresh=' in response['Location']
    assert 'redirect=%2F' in response['Location']


@pytest.mark.django_db
def test_user_admin_login_as_requires_active_superuser():
    """Reject account impersonation by a regular user."""
    User = get_user_model()
    factory = RequestFactory()
    regular_user = User.objects.create_user(email='user@example.com', password='pass12345')
    target_user = User.objects.create_user(email='target@example.com', password='pass12345')
    request = factory.get('/admin/')
    request.user = regular_user

    admin = BaseFeatureUserAdmin(User, admin_site)

    with pytest.raises(PermissionDenied):
        admin.login_as_user_view(request, target_user.id)


@pytest.mark.django_db
@pytest.mark.parametrize('build_target', [
    pytest.param(
        lambda U: U.objects.create_superuser(email='target@example.com', password='pass12345'),
        id='superuser',
    ),
    pytest.param(
        lambda U: U.objects.create_user(
            email='target@example.com', password='pass12345', is_active=False,
        ),
        id='inactive',
    ),
])
def test_user_admin_login_as_blocks_ineligible_target(build_target):
    """Reject impersonation of an ineligible target account."""
    User = get_user_model()
    admin_user = User.objects.create_superuser(email='admin@example.com', password='pass12345')
    target_user = build_target(User)
    request = _request_with_messages(admin_user)

    admin = BaseFeatureUserAdmin(User, admin_site)
    response = admin.login_as_user_view(request, target_user.id)

    assert response.status_code == 302
    assert 'access=' not in response['Location']
    assert f'/user/{target_user.id}/change/' in response['Location']
