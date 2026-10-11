"""File deletion follows the committing database without damaging other owners."""

import io
from copy import deepcopy

import pytest
from base_feature_app.models import Blog, Product, Sale, SoldProduct
from base_feature_app.tests.factories import (
    BlogFactory,
    ProductFactory,
    SaleFactory,
    SoldProductFactory,
)
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError, connection, connections, transaction
from django.db.models.deletion import ProtectedError
from django_attachments.models import Attachment, Library
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.models import Source, Thumbnail, ThumbnailDimensions
from easy_thumbnails.utils import get_storage_hash
from PIL import Image


@pytest.fixture
def image_attachment(tmp_path, settings, db):
    """Create an image with a real generated thumbnail in disposable storage."""
    settings.MEDIA_ROOT = tmp_path
    buffer = io.BytesIO()
    Image.new('RGB', (20, 20), color=(20, 100, 200)).save(buffer, format='PNG')
    attachment = Attachment.objects.create(
        library=Library.objects.create(title='Commit-controlled files'),
        file=ContentFile(buffer.getvalue(), name='original.png'),
        original_name='original.png', rank=0,
    )
    thumbnail = get_thumbnailer(attachment.file).get_thumbnail({'size': (5, 5)})
    return attachment, thumbnail


@pytest.fixture(params=[(ProductFactory, 'gallery'), (BlogFactory, 'image')], ids=['product', 'blog'])
def owner_factory(request):
    """Factories for both domain owners of the same attachment library."""
    return request.param


@pytest.fixture
def isolated_alias(tmp_path):
    """Create a second SQLite connection with the models needed by this test."""
    alias = 'attachment_isolated'
    database = deepcopy(connections.databases['default'])
    database.update(NAME=str(tmp_path / 'isolated.sqlite3'), ATOMIC_REQUESTS=False)
    isolated_connection = type(connections['default'])(database, alias=alias)
    try:
        isolated_connection.ensure_connection()
        connections.databases[alias] = database
        connections[alias] = isolated_connection
        with isolated_connection.schema_editor() as editor:
            for model in (Library, Attachment, Product, Blog, SoldProduct, Sale, Source, Thumbnail, ThumbnailDimensions):
                editor.create_model(model)
        yield alias
    finally:
        isolated_connection.close()
        try:
            del connections[alias]
        except AttributeError:
            pass
        connections.databases.pop(alias, None)


@pytest.mark.django_db(transaction=True)
def test_exclusive_owner_cleans_files_after_commit(image_attachment, owner_factory):
    """Exclusive originals and thumbnails are removed only after real commit."""
    attachment, thumbnail = image_attachment
    factory, field = owner_factory
    owner = factory(**{field: attachment.library})
    owner_id, library_id, attachment_id = owner.pk, attachment.library_id, attachment.pk
    storage, name = attachment.file.storage, attachment.file.name
    thumbnail_storage, thumbnail_name = thumbnail.storage, thumbnail.name
    with transaction.atomic():
        owner.delete()
        assert not type(owner).objects.filter(pk=owner_id).exists()
        assert storage.exists(name)
        assert thumbnail_storage.exists(thumbnail_name)

    assert not Library.objects.filter(pk=library_id).exists()
    assert not Attachment.objects.filter(pk=attachment_id).exists()
    assert not storage.exists(name)
    assert not thumbnail_storage.exists(thumbnail_name)


@pytest.mark.django_db(transaction=True)
def test_owner_delete_rolls_back_library_failure(image_attachment, owner_factory):
    """A real library DELETE error restores ownership and original file bytes."""
    attachment, thumbnail = image_attachment
    factory, field = owner_factory
    owner = factory(**{field: attachment.library})
    owner_id, library_id, attachment_id = owner.pk, attachment.library_id, attachment.pk
    owner_before = type(owner).objects.values().get(pk=owner_id)
    original = attachment.file.storage.open(attachment.file.name).read()
    thumb_bytes = thumbnail.storage.open(thumbnail.name).read()
    with connection.cursor() as cursor:
        cursor.execute(
            'CREATE TEMP TRIGGER reject_library_cleanup BEFORE DELETE ON django_attachments_library '
            f"WHEN OLD.id = {library_id} BEGIN SELECT RAISE(ABORT, 'library cleanup rejected'); END"
        )
    try:
        with pytest.raises(IntegrityError, match='library cleanup rejected'):
            owner.delete()
    finally:
        with connection.cursor() as cursor:
            cursor.execute('DROP TRIGGER reject_library_cleanup')

    assert type(owner).objects.values().get(pk=owner_id) == owner_before
    assert Attachment.objects.get(pk=attachment_id).library_id == library_id
    assert attachment.file.storage.open(attachment.file.name).read() == original
    assert thumbnail.storage.open(thumbnail.name).read() == thumb_bytes
    assert Thumbnail.objects.filter(name=thumbnail.name).exists()


@pytest.mark.django_db(transaction=True)
def test_outer_rollback_preserves_attachment_files(image_attachment):
    """Rollback after a successful nested delete restores rows and both files."""
    attachment, thumbnail = image_attachment
    product = ProductFactory(gallery=attachment.library)
    product_id, attachment_id = product.pk, attachment.pk
    product_before = Product.objects.values().get(pk=product_id)
    original = attachment.file.storage.open(attachment.file.name).read()
    thumb_bytes = thumbnail.storage.open(thumbnail.name).read()

    def abort_after_delete():
        with transaction.atomic():
            product.delete()
            raise ValueError('abort outer transaction')

    with pytest.raises(ValueError, match='abort outer transaction'):
        abort_after_delete()

    assert Product.objects.values().get(pk=product_id) == product_before
    assert Attachment.objects.get(pk=attachment_id).library_id == attachment.library_id
    assert attachment.file.storage.open(attachment.file.name).read() == original
    assert thumbnail.storage.open(thumbnail.name).read() == thumb_bytes


@pytest.mark.django_db(transaction=True)
def test_protected_product_preserves_image_bytes(image_attachment):
    """PROTECT leaves the sold product's original and thumbnail unchanged."""
    attachment, thumbnail = image_attachment
    product = ProductFactory(gallery=attachment.library)
    line = SoldProductFactory(product=product, quantity=7)
    product_before = Product.objects.values().get(pk=product.pk)
    original = attachment.file.storage.open(attachment.file.name).read()
    thumb_bytes = thumbnail.storage.open(thumbnail.name).read()

    with pytest.raises(ProtectedError):
        product.delete()

    assert Product.objects.values().get(pk=product.pk) == product_before
    assert SoldProduct.objects.get(pk=line.pk).quantity == 7
    assert Attachment.objects.get(pk=attachment.pk).library_id == attachment.library_id
    assert attachment.file.storage.open(attachment.file.name).read() == original
    assert thumbnail.storage.open(thumbnail.name).read() == thumb_bytes


@pytest.mark.django_db(transaction=True)
def test_cleanup_captures_original_destination(image_attachment, tmp_path):
    """Mutating a FieldFile after deletion cannot redirect the captured cleanup."""
    attachment, thumbnail = image_attachment
    field_file = attachment.file
    storage, original_name = field_file.storage, field_file.name
    other_storage = FileSystemStorage(location=tmp_path / 'other-storage')
    other_name = other_storage.save('unrelated.txt', ContentFile(b'keep other storage'))
    sentinel = storage.save('unrelated.txt', ContentFile(b'keep original storage'))
    with transaction.atomic():
        attachment.delete()
        field_file.name = other_name
        field_file.storage = other_storage

    assert not storage.exists(original_name)
    assert not thumbnail.storage.exists(thumbnail.name)
    assert other_storage.open(other_name).read() == b'keep other storage'
    assert storage.open(sentinel).read() == b'keep original storage'


@pytest.mark.django_db(transaction=True)
def test_storage_failure_keeps_sql_committed(image_attachment, monkeypatch, caplog):
    """An original-file storage failure leaves committed SQL and pending bytes."""
    attachment, thumbnail = image_attachment
    product = ProductFactory(gallery=attachment.library)
    product_id, library_id, attachment_id = product.pk, attachment.library_id, attachment.pk
    storage, name = attachment.file.storage, attachment.file.name
    original = storage.open(name).read()

    def unavailable_storage(filename):
        raise OSError('storage unavailable')

    delete_file = storage.delete

    def delete_with_original_failure(filename):
        return {name: unavailable_storage}.get(filename, delete_file)(filename)

    monkeypatch.setattr(storage, 'delete', delete_with_original_failure)
    product.delete()

    assert not Product.objects.filter(pk=product_id).exists()
    assert not Library.objects.filter(pk=library_id).exists()
    assert not Attachment.objects.filter(pk=attachment_id).exists()
    assert storage.open(name).read() == original
    assert f'File not deleted: {name}' in caplog.text


@pytest.mark.django_db(databases='__all__', transaction=True)
def test_owner_delete_uses_emitting_database(isolated_alias, owner_factory):
    """Deleting an owner in a second database preserves the default controls."""
    factory, field = owner_factory
    control = factory()
    default_before = type(control).objects.values().get(pk=control.pk)
    library = Library.objects.using(isolated_alias).create(title='Isolated library')
    selected = factory.build(**{field: library})
    selected.save(using=isolated_alias)
    selected_id, library_id = selected.pk, library.pk

    result = selected.delete(using=isolated_alias)

    assert result is None
    assert not type(selected).objects.using(isolated_alias).filter(pk=selected_id).exists()
    assert not Library.objects.using(isolated_alias).filter(pk=library_id).exists()
    assert type(control).objects.values().get(pk=control.pk) == default_before
    assert Library.objects.filter(pk=getattr(control, f'{field}_id')).exists()


@pytest.mark.django_db(databases='__all__', transaction=True)
def test_sale_delete_uses_emitting_database(isolated_alias):
    """Sale cleanup in the second database cannot delete a default sale's line."""
    control = SaleFactory()
    control_line = SoldProductFactory(quantity=7)
    control.sold_products.add(control_line)
    library = Library.objects.using(isolated_alias).create(title='Isolated sale library')
    product = ProductFactory.build(gallery=library)
    product.save(using=isolated_alias)
    selected = SaleFactory.build()
    selected.save(using=isolated_alias)
    line = SoldProduct.objects.using(isolated_alias).create(product=product, quantity=3)
    selected.sold_products.add(line)
    selected_id = selected.pk

    result = selected.delete()

    assert result is None
    assert not Sale.objects.using(isolated_alias).filter(pk=selected_id).exists()
    assert not SoldProduct.objects.using(isolated_alias).filter(pk=line.pk).exists()
    assert list(control.sold_products.values_list('pk', 'quantity')) == [(control_line.pk, 7)]


@pytest.mark.django_db(databases='__all__', transaction=True)
def test_attachment_cleanup_waits_for_emitting_alias(isolated_alias, image_attachment, tmp_path):
    """Committing default cannot run a callback belonging to the second alias."""
    control, control_thumbnail = image_attachment
    control_before = Attachment.objects.values().get(pk=control.pk)
    control_bytes = (
        control.file.storage.open(control.file.name).read(),
        control_thumbnail.storage.open(control_thumbnail.name).read(),
    )
    library = Library.objects.using(isolated_alias).create(title='Alias image')
    attachment = Attachment.objects.using(isolated_alias).create(
        library=library, original_name='isolated.txt', rank=0,
        file=ContentFile(b'alias bytes', name='isolated.txt'),
    )
    storage = attachment.file.storage
    name = attachment.file.name
    thumbnail_storage = control_thumbnail.storage
    thumbnail_name = thumbnail_storage.save(
        'isolated-thumbnail.jpg', ContentFile(thumbnail_storage.open(control_thumbnail.name).read()),
    )
    source = Source.objects.using(isolated_alias).create(
        name=name, storage_hash=get_storage_hash(storage),
    )
    alias_thumbnail = Thumbnail.objects.using(isolated_alias).create(
        source=source, name=thumbnail_name, storage_hash=get_storage_hash(thumbnail_storage),
    )
    control_metadata = Thumbnail.objects.values().get(name=control_thumbnail.name)
    with transaction.atomic(using=isolated_alias):
        attachment.delete(using=isolated_alias)
        with transaction.atomic(using='default'):
            SaleFactory()
        assert storage.open(name).read() == b'alias bytes'
        assert thumbnail_storage.exists(thumbnail_name)

    assert (storage.exists(name), thumbnail_storage.exists(thumbnail_name)) == (False, False)
    assert not Thumbnail.objects.using(isolated_alias).filter(pk=alias_thumbnail.pk).exists()
    assert Thumbnail.objects.values().get(pk=control_metadata['id']) == control_metadata
    assert Attachment.objects.values().get(pk=control.pk) == control_before
    assert (
        control.file.storage.open(control.file.name).read(),
        control_thumbnail.storage.open(control_thumbnail.name).read(),
    ) == control_bytes
