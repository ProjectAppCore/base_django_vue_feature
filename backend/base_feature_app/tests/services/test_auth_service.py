"""Authentication behavior at the service boundary."""

from unittest.mock import Mock

import pytest

from base_feature_app.models import User
from base_feature_app.services.auth_service import (
    authenticate_google_user,
    authenticate_user,
    register_user,
)

# ===========================================================================
# register_user
# ===========================================================================

@pytest.mark.django_db
def test_register_user_returns_user_with_correct_email():
    """Verify register user returns user with correct email."""
    user = register_user(email='new@example.com', password='strongpass')

    assert user.email == 'new@example.com'
    assert isinstance(user, User)


@pytest.mark.django_db
def test_register_user_stores_first_and_last_name():
    """Verify register user stores first and last name."""
    user = register_user(
        email='named@example.com',
        password='strongpass',
        first_name='Alice',
        last_name='Smith',
    )

    assert user.first_name == 'Alice'
    assert user.last_name == 'Smith'


@pytest.mark.django_db
def test_register_user_hashes_password():
    """Verify register user hashes password."""
    user = register_user(email='hashed@example.com', password='strongpass')

    assert user.password != 'strongpass'
    assert user.check_password('strongpass')


@pytest.mark.django_db
def test_register_user_persists_to_database():
    """Verify register user persists to database."""
    register_user(email='persisted@example.com', password='strongpass')

    assert User.objects.filter(email='persisted@example.com').exists()


@pytest.mark.django_db
def test_register_user_raises_when_password_is_too_short():
    """Verify register user raises when password is too short."""
    with pytest.raises(ValueError, match='Password must be at least 8 characters'):
        register_user(email='short@example.com', password='abc123')

    assert not User.objects.filter(email='short@example.com').exists()


@pytest.mark.django_db
def test_register_user_raises_when_email_already_exists():
    """Verify register user raises when email already exists."""
    User.objects.create_user(email='dup@example.com', password='strongpass')

    with pytest.raises(ValueError, match='User with this email already exists'):
        register_user(email='dup@example.com', password='anotherpass')

    assert User.objects.filter(email='dup@example.com').count() == 1


@pytest.mark.django_db
def test_register_user_does_not_create_user_when_password_too_short():
    """Verify register user does not create user when password too short."""
    with pytest.raises(ValueError, match='Password must be at least 8 characters'):
        register_user(email='nope@example.com', password='short')

    assert not User.objects.filter(email='nope@example.com').exists()


# ===========================================================================
# authenticate_user
# ===========================================================================

@pytest.mark.django_db
def test_authenticate_user_returns_user_with_valid_credentials():
    """Verify authenticate user returns user with valid credentials."""
    User.objects.create_user(email='auth@example.com', password='validpass')

    result = authenticate_user(email='auth@example.com', password='validpass')

    assert result is not None
    assert result.email == 'auth@example.com'


@pytest.mark.django_db
def test_authenticate_user_returns_none_with_wrong_password():
    """Verify authenticate user returns none with wrong password."""
    User.objects.create_user(email='wrong@example.com', password='correctpass')

    result = authenticate_user(email='wrong@example.com', password='wrongpass')

    assert result is None


@pytest.mark.django_db
def test_authenticate_user_returns_none_for_nonexistent_email():
    """Verify authenticate user returns none for nonexistent email."""
    result = authenticate_user(email='ghost@example.com', password='anypass')

    assert result is None


@pytest.mark.django_db
def test_authenticate_user_raises_permission_error_for_disabled_account():
    """Verify authenticate user raises permission error for disabled account."""
    user = User.objects.create_user(email='disabled@example.com', password='validpass')
    user.is_active = False
    user.save()

    with pytest.raises(PermissionError, match='Account is disabled'):
        authenticate_user(email='disabled@example.com', password='validpass')

    user.refresh_from_db()
    assert user.is_active is False


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
@pytest.mark.parametrize('credential', [None, '', '  ', [], {}, 42, True])
def test_google_auth_rejects_empty_credentials(google_verifier, credential):
    """Reject malformed credentials before creating any account."""
    with pytest.raises(ValueError, match='Google token validation failed'):
        authenticate_google_user(credential=credential)

    assert User.objects.count() == 0


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
    {'email': '  ', 'email_verified': True},
    {'email': [], 'email_verified': True},
])
def test_google_auth_rejects_invalid_payload(google_verifier, payload):
    """Reject claims that do not identify a verified email without changing names."""
    user = User.objects.create_user(email='google@example.com', first_name='Original')
    google_verifier.return_value = payload

    with pytest.raises(ValueError, match='Google token validation failed'):
        authenticate_google_user(credential='signed-token')

    user.refresh_from_db()
    assert (user.first_name, user.last_name) == ('Original', '')
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_google_auth_creates_verified_account(google_verifier):
    """Create an account from verified claims after checking the configured audience."""
    google_verifier.return_value['email'] = '  Google@EXAMPLE.COM  '

    user, created = authenticate_google_user(credential='signed-token')

    assert created is True
    assert user.email == 'google@example.com'
    assert User.objects.get(pk=user.pk).first_name == 'Google'
    assert google_verifier.call_args.args[2] == 'client-id'


@pytest.mark.django_db
def test_google_auth_returns_existing_account(google_verifier):
    """Use the existing verified account without creating a duplicate."""
    existing = User.objects.create_user(email='google@example.com')

    user, created = authenticate_google_user(credential='signed-token')

    assert created is False
    assert user.pk == existing.pk
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_google_auth_fills_empty_names(google_verifier):
    """Populate empty profile names from the verified token."""
    existing = User.objects.create_user(email='google@example.com')

    authenticate_google_user(credential='signed-token')

    existing.refresh_from_db()
    assert (existing.first_name, existing.last_name) == ('Google', 'User')


@pytest.mark.django_db
def test_google_auth_preserves_existing_names(google_verifier):
    """Keep names already stored on the verified account."""
    existing = User.objects.create_user(
        email='google@example.com', first_name='Original', last_name='Name',
    )

    authenticate_google_user(credential='signed-token')

    existing.refresh_from_db()
    assert (existing.first_name, existing.last_name) == ('Original', 'Name')


@pytest.mark.django_db
def test_google_auth_rejects_missing_client_id(google_verifier, settings):
    """Fail closed when no application audience is configured."""
    from django.core.exceptions import ImproperlyConfigured
    # quality: disable global_state_mutation (pytest-django restores settings)
    settings.GOOGLE_OAUTH_CLIENT_ID = ''

    with pytest.raises(ImproperlyConfigured, match='Google login is unavailable'):
        authenticate_google_user(credential='signed-token')

    assert User.objects.count() == 0
    google_verifier.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize('failure', [ValueError('Wrong audience'), RuntimeError('Transport failed')])
def test_google_auth_rejects_verification_failure(google_verifier, failure):
    """Reject external verification failures without exposing provider details."""
    google_verifier.side_effect = failure

    with pytest.raises(ValueError, match='Google token validation failed'):
        authenticate_google_user(credential='invalid-token')

    assert User.objects.count() == 0


@pytest.mark.django_db
def test_google_auth_rejects_inactive_account(google_verifier):
    """Reject disabled accounts before modifying their profile."""
    existing = User.objects.create_user(email='google@example.com', is_active=False)

    with pytest.raises(PermissionError, match='Account is disabled'):
        authenticate_google_user(credential='signed-token')

    existing.refresh_from_db()
    assert (existing.first_name, existing.last_name, existing.is_active) == ('', '', False)
    assert User.objects.count() == 1
