"""Independent request-boundary obligations for frozen DRF QUERY proposal.

Test client requests stay in-process; session/permission state uses SQLite.
Force-authenticated permission cases are separate from real session/CSRF cases.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import path
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import (
    DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView


class SessionEcho(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'count': get_user_model().objects.count()})

    post = get
    query = get


class ModelEcho(SessionEcho):
    authentication_classes = [BasicAuthentication]
    permission_classes = [DjangoModelPermissions]
    queryset = get_user_model().objects.all()


class ReadOnlyEcho(ModelEcho):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class ExplicitQueryPermissions(DjangoModelPermissionsOrAnonReadOnly):
    perms_map = dict(DjangoModelPermissions.perms_map, QUERY=['auth.view_user'])


class ExplicitQueryEcho(ModelEcho):
    permission_classes = [ExplicitQueryPermissions]


class LegacyPermissionMap(DjangoModelPermissions):
    perms_map = {key: value for key, value in DjangoModelPermissions.perms_map.items() if key != 'QUERY'}


class LegacyMapEcho(ModelEcho):
    permission_classes = [LegacyPermissionMap]


urlpatterns = [path('session/', SessionEcho.as_view()), path('model/', ModelEcho.as_view()),
               path('readonly/', ReadOnlyEcho.as_view()), path('explicit/', ExplicitQueryEcho.as_view()),
               path('legacy-map/', LegacyMapEcho.as_view())]
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def urls():
    with override_settings(ROOT_URLCONF=__name__, ALLOWED_HOSTS=['testserver']):
        yield


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username='shadow-user')


def query(client, url):
    return client.generic('QUERY', url, data='{}', content_type='application/json')


def test_existing_session_get_without_csrf_is_allowed(user):
    client = APIClient(enforce_csrf_checks=True);client.force_login(user)
    assert client.get('/session/').status_code == 200


def test_existing_session_post_without_csrf_is_denied(user):
    client = APIClient(enforce_csrf_checks=True);client.force_login(user)
    assert client.post('/session/', {}, format='json').status_code == 403


def test_query_session_without_csrf_is_allowed_and_does_not_add_users(user):
    client = APIClient(enforce_csrf_checks=True);client.force_login(user)
    before = get_user_model().objects.count()
    response = query(client, '/session/')
    assert response.status_code == 200
    assert response.data['count'] == before
    assert get_user_model().objects.count() == before


def test_query_authenticated_model_access_needs_no_default_model_grant(user):
    client = APIClient();client.force_authenticate(user)
    assert query(client, '/model/').status_code == 200


def test_query_anonymous_readonly_access():
    assert query(APIClient(), '/readonly/').status_code == 200


def test_query_explicit_permission_denies_anonymous():
    assert query(APIClient(), '/explicit/').status_code == 401


def test_query_explicit_permission_denies_user_without_database_grant(user):
    client = APIClient();client.force_authenticate(user)
    assert query(client, '/explicit/').status_code == 403


def test_query_explicit_permission_accepts_user_with_database_grant(user):
    user.user_permissions.add(Permission.objects.get(codename='view_user', content_type__app_label='auth'))
    client = APIClient();client.force_authenticate(user)
    assert query(client, '/explicit/').status_code == 200


def test_legacy_permission_map_without_query_returns_405(user):
    client = APIClient();client.force_authenticate(user)
    assert query(client, '/legacy-map/').status_code == 405
