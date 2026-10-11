"""Gallery admin routes honor the actual Attachment model permission."""

from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django_attachments.models import Attachment, Library


@pytest.fixture
def attachment_permission(db):
    """Read the real change permission generated for the Attachment content type."""
    content_type = ContentType.objects.get_for_model(Attachment)
    return Permission.objects.get(content_type=content_type, codename='change_attachment')


@pytest.fixture
def attachment_staff(db):
    """Create a real staff account for session-authenticated attachment requests."""
    return get_user_model().objects.create_user(
        email='attachment-staff@example.invalid', password=None, is_staff=True,
    )


@pytest.fixture
def attachment_editor(attachment_staff, attachment_permission):
    """Give an active staff account the actual Attachment change permission."""
    attachment_staff.user_permissions.add(attachment_permission)
    return attachment_staff


@pytest.fixture
def attachment_customer(attachment_permission):
    """Give the same model permission to an active non-staff customer."""
    user = get_user_model().objects.create_user(
        email='attachment-customer@example.invalid', password=None, is_staff=False,
    )
    user.user_permissions.add(attachment_permission)
    return user


@pytest.fixture
def attachment_superuser(attachment_staff):
    """Preserve the active staff account's existing superuser access contract."""
    attachment_staff.is_superuser = True
    attachment_staff.save(update_fields=['is_superuser'])
    return attachment_staff


@pytest.fixture
def preserved_attachment(library):
    """Persist a real attachment whose metadata can be observed over HTTP."""
    return Attachment.objects.create(
        library=library,
        rank=0,
        file=SimpleUploadedFile('preserved.txt', b'original file'),
    )


@pytest.fixture
def attachment_inventory(preserved_attachment):
    """Capture complete existing rows before an unauthorized request."""
    return {
        'libraries': list(Library.objects.values()),
        'attachments': list(Attachment.objects.values()),
    }


def test_staff_can_create_attachment_library(client, attachment_editor):
    """A staff member with the generated permission can persist a new library."""
    client.force_login(attachment_editor)

    response = client.post(reverse('admin:attachments_library_create_api'), {
        'title': 'Authorized library',
    })

    assert response.status_code == 200
    library = Library.objects.get(pk=response.json()['id'])
    assert library.title == 'Authorized library'
    assert Library.objects.count() == 1


@pytest.mark.parametrize('route_name', [
    'admin:attachments_library_edit_api',
    'admin:attachments_gallery_edit_api',
])
def test_staff_can_read_attachment_library(client, attachment_editor, preserved_attachment, route_name):
    """Granted staff receives the existing attachment through each JSON admin route."""
    client.force_login(attachment_editor)
    url = reverse(route_name, args=[preserved_attachment.library_id])

    response = client.get(url, HTTP_ACCEPT='application/json')

    assert response.status_code == 200
    attachments = response.json()['attachments']
    assert len(attachments) == 1
    assert attachments[0]['id'] == preserved_attachment.pk
    assert attachments[0]['name'] == 'preserved.txt'
    assert attachments[0]['filesize'] == 13
    assert attachments[0]['url'] == preserved_attachment.file.url


def test_ungranted_staff_cannot_create_attachment_library(client, attachment_staff, attachment_inventory):
    """Staff status alone cannot create a library or change existing attachments."""
    client.force_login(attachment_staff)

    response = client.post(reverse('admin:attachments_library_create_api'), {
        'title': 'Forbidden library',
    })

    assert response.status_code == 403
    assert list(Library.objects.values()) == attachment_inventory['libraries']
    assert list(Attachment.objects.values()) == attachment_inventory['attachments']


def test_customer_cannot_create_attachment_library(client, attachment_customer, attachment_inventory):
    """The model permission does not allow a non-staff customer to create libraries."""
    client.force_login(attachment_customer)

    response = client.post(reverse('admin:attachments_library_create_api'), {
        'title': 'Forbidden library',
    })

    assert response.status_code == 403
    assert list(Library.objects.values()) == attachment_inventory['libraries']
    assert list(Attachment.objects.values()) == attachment_inventory['attachments']


@pytest.mark.parametrize('route_name', [
    'admin:attachments_library_edit_api',
    'admin:attachments_gallery_edit_api',
])
def test_ungranted_staff_cannot_read_attachment_library(client, attachment_staff, attachment_inventory, route_name):
    """Both JSON routes refuse staff lacking the generated model permission."""
    client.force_login(attachment_staff)
    url = reverse(route_name, args=[attachment_inventory['libraries'][0]['id']])

    response = client.get(url, HTTP_ACCEPT='application/json')

    assert response.status_code == 403
    assert list(Library.objects.values()) == attachment_inventory['libraries']
    assert list(Attachment.objects.values()) == attachment_inventory['attachments']


@pytest.mark.parametrize('route_name', [
    'admin:attachments_library_edit_api',
    'admin:attachments_gallery_edit_api',
])
def test_customer_cannot_read_attachment_library(client, attachment_customer, attachment_inventory, route_name):
    """A customer holding the permission still cannot read admin attachment payloads."""
    client.force_login(attachment_customer)
    url = reverse(route_name, args=[attachment_inventory['libraries'][0]['id']])

    response = client.get(url, HTTP_ACCEPT='application/json')

    assert response.status_code == 403
    assert list(Library.objects.values()) == attachment_inventory['libraries']
    assert list(Attachment.objects.values()) == attachment_inventory['attachments']


def test_superuser_can_create_attachment_library(client, attachment_superuser):
    """Existing superuser access continues to persist libraries without explicit grants."""
    client.force_login(attachment_superuser)

    response = client.post(reverse('admin:attachments_library_create_api'), {
        'title': 'Superuser library',
    })

    assert response.status_code == 200
    library = Library.objects.get(pk=response.json()['id'])
    assert library.title == 'Superuser library'
    assert Library.objects.count() == 1


@pytest.mark.parametrize('route_name', [
    'admin:attachments_library_edit_api',
    'admin:attachments_gallery_edit_api',
])
def test_superuser_can_read_attachment_library(client, attachment_superuser, preserved_attachment, route_name):
    """Both attachment JSON routes preserve superuser access."""
    client.force_login(attachment_superuser)
    url = reverse(route_name, args=[preserved_attachment.library_id])

    response = client.get(url, HTTP_ACCEPT='application/json')

    assert response.status_code == 200
    assert response.json()['attachments'][0]['id'] == preserved_attachment.pk
    assert response.json()['attachments'][0]['name'] == 'preserved.txt'


def test_anonymous_cannot_create_attachment_library(client, attachment_inventory):
    """An anonymous creation attempt is redirected to login without persistence."""
    url = reverse('admin:attachments_library_create_api')

    response = client.post(url, {'title': 'Anonymous library'})

    assert response.status_code == 302
    assert parse_qs(urlsplit(response.url).query)['next'] == [url]
    assert list(Library.objects.values()) == attachment_inventory['libraries']
    assert list(Attachment.objects.values()) == attachment_inventory['attachments']


@pytest.mark.parametrize('route_name', [
    'admin:attachments_library_edit_api',
    'admin:attachments_gallery_edit_api',
])
def test_anonymous_cannot_read_attachment_library(client, attachment_inventory, route_name):
    """Anonymous reads redirect to login while preserving attachment inventory."""
    url = reverse(route_name, args=[attachment_inventory['libraries'][0]['id']])

    response = client.get(url, HTTP_ACCEPT='application/json')

    assert response.status_code == 302
    assert parse_qs(urlsplit(response.url).query)['next'] == [url]
    assert list(Library.objects.values()) == attachment_inventory['libraries']
    assert list(Attachment.objects.values()) == attachment_inventory['attachments']
