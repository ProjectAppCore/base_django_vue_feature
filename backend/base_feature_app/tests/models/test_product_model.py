"""Exercise product persistence and shared gallery ownership."""

import io

import pytest
from django.core.files.base import ContentFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django_attachments.models import Attachment, Library
from PIL import Image

from base_feature_app.models import Blog, Product
from base_feature_app.tests.factories import BlogFactory, ProductFactory


def _placeholder_image(name='placeholder.webp'):
    image = Image.new('RGB', (10, 10), color=(240, 240, 240))
    buffer = io.BytesIO()
    image.save(buffer, format='WEBP')
    buffer.seek(0)
    return ContentFile(buffer.read(), name=name)


@pytest.mark.django_db
class TestProductModel:
    """Exercise the persisted product model contract."""

    def test_product_delete_removes_library_and_attachments(self):
        """Verifies that deleting a Product also removes its Gallery Library and all Attachments."""
        gallery = Library.objects.create(title='Product Gallery')
        Attachment.objects.create(library=gallery, file=_placeholder_image(), original_name='placeholder.webp', rank=0)
        product = Product.objects.create(
            title='Test Product',
            category='Candles',
            sub_category='Greek',
            description='Description',
            price=100,
            gallery=gallery,
        )

        gallery_id = gallery.id
        product.delete()

        assert not Library.objects.filter(id=gallery_id).exists()
        assert not Attachment.objects.filter(library_id=gallery_id).exists()

    def test_product_creation(self):
        """Verifies that a Product is created with the correct field values."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Beautiful Candle',
            category='Aesthetic Candles',
            sub_category='Greek Sculptures',
            description='A beautiful Greek sculpture candle',
            price=150,
            gallery=gallery
        )
        
        assert product.title == 'Beautiful Candle'
        assert product.category == 'Aesthetic Candles'
        assert product.sub_category == 'Greek Sculptures'
        assert product.price == 150
        assert product.gallery == gallery

    def test_product_str_representation(self):
        """Display the product title as its string representation."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='My Product',
            category='Decor',
            sub_category='Modern',
            description='Description',
            price=200,
            gallery=gallery
        )
        assert str(product) == 'My Product'

    def test_product_price_validation(self):
        """Persist the supplied product price."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Affordable Product',
            category='Candles',
            sub_category='Modern',
            description='Low price product',
            price=10,
            gallery=gallery
        )
        assert product.price == 10

    def test_product_update(self):
        """Verifies that product fields can be updated and persisted correctly."""
        gallery = Library.objects.create(title='Gallery')
        product = Product.objects.create(
            title='Original Product',
            category='Original Category',
            sub_category='Original Sub',
            description='Original Description',
            price=100,
            gallery=gallery
        )
        
        product.title = 'Updated Product'
        product.price = 250
        product.save()
        
        updated_product = Product.objects.get(id=product.id)
        assert updated_product.title == 'Updated Product'
        assert updated_product.price == 250


@pytest.fixture
def gallery_attachment(tmp_path, settings, db):
    """Create a real image in an isolated media directory."""
    settings.MEDIA_ROOT = tmp_path
    gallery = Library.objects.create(title='Shared product gallery')
    return Attachment.objects.create(
        library=gallery, file=_placeholder_image(), original_name='shared.webp', rank=0,
    )


def test_product_delete_preserves_shared_gallery(gallery_attachment):
    """Another product retains its gallery and original image bytes."""
    attachment = gallery_attachment
    selected = ProductFactory(gallery=attachment.library)
    retained = ProductFactory(gallery=attachment.library)
    retained_before = Product.objects.values().get(pk=retained.pk)
    name, storage = attachment.file.name, attachment.file.storage
    original = storage.open(name).read()
    selected_id = selected.pk

    result = selected.delete()

    assert result is None
    assert not Product.objects.filter(pk=selected_id).exists()
    assert Product.objects.values().get(pk=retained.pk) == retained_before
    assert Attachment.objects.get(pk=attachment.pk).library_id == attachment.library_id
    assert storage.open(name).read() == original


def test_product_delete_preserves_blog_library(gallery_attachment):
    """A blog using the gallery survives deletion of its product."""
    attachment = gallery_attachment
    selected = ProductFactory(gallery=attachment.library)
    retained = BlogFactory(image=attachment.library)
    retained_before = Blog.objects.values().get(pk=retained.pk)
    name, storage = attachment.file.name, attachment.file.storage
    original = storage.open(name).read()

    selected.delete()

    assert Blog.objects.values().get(pk=retained.pk) == retained_before
    assert Library.objects.filter(pk=attachment.library_id).exists()
    assert Attachment.objects.filter(pk=attachment.pk).exists()
    assert storage.open(name).read() == original


def test_product_delete_handles_null_gallery(product, library):
    """A null in-memory gallery cannot cause deletion of an unrelated library."""
    product_id = product.pk
    product.gallery_id = None

    with CaptureQueriesContext(connection) as captured:
        product.delete()

    assert not Product.objects.filter(pk=product_id).exists()
    assert Library.objects.filter(pk=library.pk).exists()
    assert 'django_attachments_library' not in '\n'.join(query['sql'] for query in captured)


def test_product_delete_handles_missing_gallery(product, library):
    """A missing in-memory library reference does not delete another library."""
    product_id = product.pk
    product.gallery_id = library.pk + 10000

    product.delete()

    assert not Product.objects.filter(pk=product_id).exists()
    assert Library.objects.filter(pk=library.pk).exists()
