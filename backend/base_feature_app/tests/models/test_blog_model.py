"""Exercise blog persistence and shared image ownership."""

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
class TestBlogModel:
    """Exercise the persisted blog model contract."""

    def test_blog_delete_removes_library(self):
        """Remove the library belonging exclusively to the deleted blog."""
        library = Library.objects.create(title='Blog Image')
        Attachment.objects.create(library=library, file=_placeholder_image(), original_name='placeholder.webp', rank=0)
        blog = Blog.objects.create(title='Test Blog', description='Description', category='Technology', image=library)

        library_id = library.id
        blog.delete()

        assert not Library.objects.filter(id=library_id).exists()

    def test_blog_creation(self):
        """Persist the supplied blog attributes."""
        library = Library.objects.create(title='Blog Image')
        blog = Blog.objects.create(
            title='Test Blog',
            description='This is a test blog description',
            category='Technology',
            image=library
        )
        
        assert blog.title == 'Test Blog'
        assert blog.description == 'This is a test blog description'
        assert blog.category == 'Technology'
        assert blog.image == library

    def test_blog_str_representation(self):
        """Display the blog title as its string representation."""
        library = Library.objects.create(title='Blog Image')
        blog = Blog.objects.create(
            title='My Blog Title',
            description='Description',
            category='Health',
            image=library
        )
        assert str(blog) == 'My Blog Title'

    def test_blog_update(self):
        """Verifies that blog fields can be updated and persisted correctly."""
        library = Library.objects.create(title='Original Image')
        blog = Blog.objects.create(
            title='Original Title',
            description='Original Description',
            category='Education',
            image=library
        )
        
        blog.title = 'Updated Title'
        blog.category = 'Technology'
        blog.save()
        
        updated_blog = Blog.objects.get(id=blog.id)
        assert updated_blog.title == 'Updated Title'
        assert updated_blog.category == 'Technology'


def test_blog_delete_preserves_product_gallery(tmp_path, settings, db):
    """A product retains shared image bytes when a blog is deleted."""
    settings.MEDIA_ROOT = tmp_path
    library = Library.objects.create(title='Shared blog image')
    attachment = Attachment.objects.create(
        library=library, file=_placeholder_image(), original_name='shared.webp', rank=0,
    )
    selected = BlogFactory(image=library)
    retained = ProductFactory(gallery=library)
    retained_before = Product.objects.values().get(pk=retained.pk)
    name, storage = attachment.file.name, attachment.file.storage
    original = storage.open(name).read()
    selected_id = selected.pk

    result = selected.delete()

    assert result is None
    assert not Blog.objects.filter(pk=selected_id).exists()
    assert Product.objects.values().get(pk=retained.pk) == retained_before
    assert Attachment.objects.get(pk=attachment.pk).library_id == library.pk
    assert storage.open(name).read() == original


def test_blog_delete_handles_null_image(blog):
    """A null in-memory image reference preserves the existing library."""
    blog_id, library_id = blog.pk, blog.image_id
    blog.image_id = None

    with CaptureQueriesContext(connection) as captured:
        blog.delete()

    assert not Blog.objects.filter(pk=blog_id).exists()
    assert Library.objects.filter(pk=library_id).exists()
    assert 'django_attachments_library' not in '\n'.join(query['sql'] for query in captured)


def test_blog_delete_handles_missing_image(blog):
    """A missing in-memory image reference preserves the existing library."""
    blog_id, library_id = blog.pk, blog.image_id
    blog.image_id = library_id + 10000

    blog.delete()

    assert not Blog.objects.filter(pk=blog_id).exists()
    assert Library.objects.filter(pk=library_id).exists()
