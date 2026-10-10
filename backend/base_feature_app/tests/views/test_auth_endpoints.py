"""Authentication behavior at the API boundary."""

import logging
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_requires_email_and_password(mock_captcha, api_client):
    """Verify sign up requires email and password."""
    url = reverse('sign_up')
    response = api_client.post(url, {}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_rejects_short_password(mock_captcha, api_client):
    """Verify sign up rejects short password."""
    url = reverse('sign_up')
    response = api_client.post(
        url,
        {'email': 'short@example.com', 'password': '123'},
        format='json',
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_rejects_existing_email(mock_captcha, api_client):
    """Verify sign up rejects existing email."""
    User = get_user_model()
    User.objects.create_user(email='exists@example.com', password='pass12345')

    url = reverse('sign_up')
    response = api_client.post(
        url,
        {'email': 'exists@example.com', 'password': 'pass12345'},
        format='json',
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_success(mock_captcha, api_client):
    """Verifies that a valid sign_up request creates a user and returns access and refresh tokens."""
    url = reverse('sign_up')
    response = api_client.post(
        url,
        {
            'email': 'new@example.com',
            'password': 'pass12345',
            'first_name': 'New',
            'last_name': 'User',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['user']['email'] == 'new@example.com'
    assert 'access' in data
    assert 'refresh' in data


@pytest.fixture
def rejected_auth_insert(db):
    """Reject only the scratch identity through SQLite's real persistence boundary."""
    table = connection.ops.quote_name(get_user_model()._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TEMP TRIGGER reject_auth_user_insert
            BEFORE INSERT ON {table}
            WHEN NEW.email = 'blocked-auth@example.invalid'
            BEGIN
                SELECT RAISE(ABORT, 'private-persistence-detail');
            END;
        """)
    try:
        yield 'blocked-auth@example.invalid'
    finally:
        with connection.cursor() as cursor:
            cursor.execute('DROP TRIGGER reject_auth_user_insert')


@pytest.mark.django_db
@patch('base_feature_app.views.captcha_views.requests.post')
def test_sign_up_returns_safe_server_error_on_persistence_failure(
    mock_captcha_http, api_client, admin_user, rejected_auth_insert, settings, caplog,
):
    """A real rejected insert produces a sanitized server error without changing accounts."""
    User = get_user_model()
    before = list(User.objects.values())
    # quality: disable global_state_mutation (pytest-django restores settings)
    settings.RECAPTCHA_SECRET_KEY = 'synthetic-private-captcha-secret'
    mock_captcha_http.return_value.json.return_value = {'success': True}
    caplog.set_level(logging.ERROR, logger='base_feature_app.views.auth')

    # The trigger predates this savepoint; the caught IntegrityError rolls it back on exit.
    with transaction.atomic():
        response = api_client.post(reverse('sign_up'), {
            'email': rejected_auth_insert,
            'password': 'synthetic-private-password',
            'captcha_token': 'synthetic-private-captcha-token',
        }, format='json')

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'error': 'An unexpected authentication error occurred.'}
    assert list(User.objects.values()) == before
    records = [record for record in caplog.records if record.name == 'base_feature_app.views.auth']
    assert len(records) == 1
    record = records[0]
    assert {
        'level': record.levelno, 'template': record.msg,
        'args': record.args, 'message': record.getMessage(),
        'exc_info': record.exc_info, 'stack_info': record.stack_info,
    } == {
        'level': logging.ERROR,
        'template': 'Unexpected authentication failure: operation=%s exception_type=%s',
        'args': ('sign_up', 'IntegrityError'),
        'message': 'Unexpected authentication failure: operation=sign_up exception_type=IntegrityError',
        'exc_info': None, 'stack_info': None,
    }
    safe_output = response.content.decode() + caplog.text
    private_markers = [
        rejected_auth_insert, admin_user.email, 'private-persistence-detail',
        'synthetic-private-password', 'synthetic-private-captcha-token',
        'synthetic-private-captcha-secret',
    ]
    assert [marker for marker in private_markers if marker in safe_output] == []


@pytest.mark.django_db
def test_google_login_returns_safe_server_error_on_persistence_failure(
    api_client, admin_user, rejected_auth_insert, google_verifier, caplog,
):
    """A real Google account insert failure exposes only the safe server error."""
    User = get_user_model()
    before = list(User.objects.values())
    google_verifier.return_value = {
        'email': rejected_auth_insert,
        'email_verified': True,
        'given_name': 'Synthetic',
        'family_name': 'Private',
    }
    caplog.set_level(logging.ERROR, logger='base_feature_app.views.auth')

    with transaction.atomic():
        response = api_client.post(reverse('google_login'), {
            'credential': 'synthetic-private-google-credential',
        }, format='json')

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {'error': 'An unexpected authentication error occurred.'}
    assert list(User.objects.values()) == before
    records = [record for record in caplog.records if record.name == 'base_feature_app.views.auth']
    assert len(records) == 1
    record = records[0]
    assert {
        'level': record.levelno, 'template': record.msg,
        'args': record.args, 'message': record.getMessage(),
        'exc_info': record.exc_info, 'stack_info': record.stack_info,
    } == {
        'level': logging.ERROR,
        'template': 'Unexpected authentication failure: operation=%s exception_type=%s',
        'args': ('google_login', 'IntegrityError'),
        'message': 'Unexpected authentication failure: operation=google_login exception_type=IntegrityError',
        'exc_info': None, 'stack_info': None,
    }
    safe_output = response.content.decode() + caplog.text
    private_markers = [
        rejected_auth_insert, admin_user.email, 'private-persistence-detail',
        'synthetic-private-google-credential', 'Synthetic', 'Private',
    ]
    assert [marker for marker in private_markers if marker in safe_output] == []


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_requires_email_and_password(mock_captcha, api_client):
    """Verify sign in requires email and password."""
    url = reverse('sign_in')
    response = api_client.post(url, {}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_invalid_credentials(mock_captcha, api_client):
    """Verify sign in invalid credentials."""
    url = reverse('sign_in')
    response = api_client.post(
        url,
        {'email': 'missing@example.com', 'password': 'pass12345'},
        format='json',
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_disabled_account(mock_captcha, api_client):
    """Verify sign in disabled account."""
    User = get_user_model()
    user = User.objects.create_user(email='disabled@example.com', password='pass12345')
    user.is_active = False
    user.save(update_fields=['is_active'])

    url = reverse('sign_in')
    response = api_client.post(
        url,
        {'email': 'disabled@example.com', 'password': 'pass12345'},
        format='json',
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_success(mock_captcha, api_client):
    """Verifies that valid credentials return HTTP 200 with user info and JWT tokens."""
    User = get_user_model()
    User.objects.create_user(email='login@example.com', password='pass12345')

    url = reverse('sign_in')
    response = api_client.post(
        url,
        {'email': 'login@example.com', 'password': 'pass12345'},
        format='json',
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['user']['email'] == 'login@example.com'
    assert 'access' in data
    assert 'refresh' in data


@pytest.mark.django_db
def test_validate_token_unauthenticated(api_client):
    """Verify validate token unauthenticated."""
    url = reverse('validate_token')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_validate_token_authenticated(api_client):
    """Verify validate token authenticated."""
    User = get_user_model()
    user = User.objects.create_user(email='val@example.com', password='pass12345')

    api_client.force_authenticate(user=user)
    url = reverse('validate_token')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['valid'] is True
    assert data['user']['email'] == 'val@example.com'


@pytest.mark.django_db
def test_validate_token_returns_valid_false_for_anonymous_user(api_client, monkeypatch):
    """Verify validate token returns valid false for anonymous user."""
    from rest_framework.permissions import AllowAny

    from base_feature_app.views.auth import validate_token

    monkeypatch.setattr(validate_token.cls, 'permission_classes', [AllowAny])

    url = reverse('validate_token')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'valid': False}


@pytest.fixture
def google_verifier(settings, monkeypatch):
    """Replace the external Google verifier with verified identity claims."""
    # quality: disable global_state_mutation (pytest-django restores settings)
    settings.GOOGLE_OAUTH_CLIENT_ID = 'client-id'
    verifier = Mock(return_value={
        'email': 'google@example.com',
        'email_verified': True,
        'given_name': 'Google',
        'family_name': 'User',
    })
    monkeypatch.setattr(
        'base_feature_app.services.auth_service.id_token.verify_oauth2_token',
        verifier,
    )
    return verifier


@pytest.mark.django_db
@pytest.mark.parametrize('credential', [None, '', '  ', [], {}, 42])
def test_google_login_rejects_empty_credentials(api_client, google_verifier, credential):
    """Malformed credentials return a generic rejection without creating accounts."""
    response = api_client.post(reverse('google_login'), {'credential': credential}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'error': 'Google token validation failed'}
    assert get_user_model().objects.count() == 0


@pytest.mark.django_db
def test_google_login_rejects_email_only_impersonation(api_client, google_verifier):
    """An anonymous email-only request cannot modify or authenticate a staff account."""
    user = get_user_model().objects.create_user(email='staff@example.com', is_staff=True)

    response = api_client.post(reverse('google_login'), {
        'email': user.email, 'given_name': 'Attacker', 'family_name': 'Changed',
    }, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'error': 'Google token validation failed'}
    user.refresh_from_db()
    assert (user.first_name, user.last_name, user.is_staff) == ('', '', True)
    assert get_user_model().objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize('payload', [
    None,
    [],
    {'email': 'google@example.com'},
    {
        'email': 'google@example.com', 'email_verified': False,
        'given_name': 'Attacker', 'family_name': 'Changed',
    },
    {'email': 'google@example.com', 'email_verified': 'true'},
    {'email': 'google@example.com', 'email_verified': 1},
    {'email_verified': True},
    {'email': '', 'email_verified': True},
    {'email': {}, 'email_verified': True},
])
def test_google_login_rejects_invalid_payload(api_client, google_verifier, payload):
    """Invalid verified claims cannot fall back to the email in the request."""
    user = get_user_model().objects.create_user(email='google@example.com', first_name='Original')
    google_verifier.return_value = payload

    response = api_client.post(reverse('google_login'), {
        'credential': 'signed-token', 'email': user.email, 'given_name': 'Attacker',
    }, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'error': 'Google token validation failed'}
    user.refresh_from_db()
    assert (user.first_name, user.last_name) == ('Original', '')
    assert get_user_model().objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize('failure', [ValueError('Wrong audience'), RuntimeError('Transport failed')])
def test_google_login_rejects_verification_failure(api_client, google_verifier, failure):
    """Provider rejection or transport failure cannot create an authenticated session."""
    google_verifier.side_effect = failure

    response = api_client.post(reverse('google_login'), {'credential': 'invalid'}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'error': 'Google token validation failed'}
    assert get_user_model().objects.count() == 0


@pytest.mark.django_db
def test_google_login_requires_configured_audience(api_client, google_verifier, settings):
    """Missing backend client ID disables Google login without a tokeninfo fallback."""
    # quality: disable global_state_mutation (pytest-django restores settings)
    settings.GOOGLE_OAUTH_CLIENT_ID = ''

    response = api_client.post(reverse('google_login'), {'credential': 'signed-token'}, format='json')

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {'error': 'Google login is unavailable'}
    assert get_user_model().objects.count() == 0
    google_verifier.assert_not_called()


@pytest.mark.django_db
def test_google_login_rejects_inactive_account(api_client, google_verifier):
    """A valid Google token cannot reactivate or change a disabled local account."""
    user = get_user_model().objects.create_user(email='google@example.com', is_active=False)

    response = api_client.post(reverse('google_login'), {'credential': 'signed-token'}, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {'error': 'Account is disabled'}
    user.refresh_from_db()
    assert (user.first_name, user.last_name, user.is_active) == ('', '', False)
    assert get_user_model().objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize('body_email', ['staff@example.com', [], {}, 42])
def test_google_login_uses_verified_identity(api_client, google_verifier, body_email):
    """Tokens identify the signed account even when the request names a different user."""
    from rest_framework_simplejwt.tokens import AccessToken
    rightful = get_user_model().objects.create_user(email='google@example.com')
    victim = get_user_model().objects.create_user(email='staff@example.com', is_staff=True)

    response = api_client.post(reverse('google_login'), {
        'credential': 'signed-token', 'email': body_email,
    }, format='json')

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert (data['user']['id'], data['created']) == (rightful.pk, False)
    assert AccessToken(data['access'])['user_id'] == str(rightful.pk)
    api_client.credentials(HTTP_AUTHORIZATION='Bearer ' + data['access'])
    assert api_client.get(reverse('validate_token')).json()['user']['id'] == rightful.pk
    victim.refresh_from_db()
    assert (victim.first_name, victim.last_name, victim.is_staff) == ('', '', True)
    assert get_user_model().objects.count() == 2


@pytest.mark.django_db
def test_google_login_accepts_id_token_alias(api_client, google_verifier):
    """The legacy id_token key retains the successful token response contract."""
    from rest_framework_simplejwt.tokens import RefreshToken

    response = api_client.post(reverse('google_login'), {'id_token': 'signed-token'}, format='json')

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert set(data) == {'user', 'access', 'refresh', 'created'}
    assert data['created'] is True
    assert RefreshToken(data['refresh'])['user_id'] == str(data['user']['id'])
    assert get_user_model().objects.get(pk=data['user']['id']).email == 'google@example.com'
