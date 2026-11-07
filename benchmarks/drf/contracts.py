"""Frozen replay checks: execute only inside the external source sandbox.

Requirements were researched with historical outcomes known. These checks are
not evidence of blind requirements discovery or full application correctness.
"""
import itertools
import os
from types import SimpleNamespace

CASE = os.environ.get('PROOFGATE_CASE')
if CASE not in ('or_composition', 'model_permissions', 'renderer_boundary'):
    raise ValueError('explicit supported PROOFGATE_CASE is required')


def test_or_contract():
    if CASE != 'or_composition':
        return
    from rest_framework import permissions
    for ar, ao, br, bo in itertools.product((False, True), repeat=4):
        class A(permissions.BasePermission):
            def has_permission(self, request, view):
                return ar
            def has_object_permission(self, request, view, obj):
                return ao
        class B(permissions.BasePermission):
            def has_permission(self, request, view):
                return br
            def has_object_permission(self, request, view, obj):
                return bo
        composed = (A | B)()
        observed = bool(composed.has_permission(None, None) and
                        composed.has_object_permission(None, None, None))
        expected = (ar and ao) or (br and bo)
        assert observed is expected, {'input': (ar, ao, br, bo),
                                      'expected': expected, 'observed': observed}


def test_model_permissions_contract():
    if CASE != 'model_permissions':
        return
    from rest_framework import permissions
    model = SimpleNamespace(_meta=SimpleNamespace(app_label='shadow', model_name='item'))
    view = SimpleNamespace(queryset=SimpleNamespace(model=model))
    for authenticated, bits, method in itertools.product(
            (False, True), itertools.product((False, True), repeat=4),
            ('GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'PATCH', 'DELETE')):
        can_view, can_change, can_add, can_delete = bits
        granted = {f'shadow.{name}_item' for name, allowed in
                   zip(('view', 'change', 'add', 'delete'), bits) if allowed}
        user = SimpleNamespace(is_authenticated=authenticated,
                               has_perms=lambda perms: all(p in granted for p in perms))
        request = SimpleNamespace(user=user, method=method)
        required = {'GET': can_view or can_change, 'HEAD': can_view,
                    'OPTIONS': True, 'POST': can_add, 'PUT': can_change,
                    'PATCH': can_change, 'DELETE': can_delete}[method]
        expected = authenticated and required
        observed = bool(permissions.DjangoModelPermissions().has_permission(request, view))
        assert observed is expected, {'input': (authenticated, bits, method),
                                      'expected': expected, 'observed': observed}


def test_renderer_boundary_contract():
    if CASE != 'renderer_boundary':
        return
    from rest_framework import exceptions, serializers
    from rest_framework.renderers import BrowsableAPIRenderer
    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory
    class Serializer(serializers.Serializer):
        name = serializers.CharField()
    for method, allowed, view_grant, object_grant in itertools.product(
            ('OPTIONS', 'DELETE', 'PUT', 'PATCH'), (False, True), (False, True), (False, True)):
        calls = []
        class View:
            allowed_methods = [method] if allowed else []
            def check_permissions(self, request):
                calls.append('view')
                if not view_grant:
                    raise exceptions.PermissionDenied()
            def check_object_permissions(self, request, obj):
                calls.append('object')
                if not object_grant:
                    raise exceptions.PermissionDenied()
        request = Request(APIRequestFactory().get('/'))
        serializer = Serializer(instance=SimpleNamespace(name='demo'))
        result = BrowsableAPIRenderer().get_rendered_html_form(
            serializer.data, View(), method, request)
        expected_calls = [] if not allowed else ['view']
        if allowed and view_grant and method != 'OPTIONS':
            expected_calls.append('object')
        expected_result = True if allowed and view_grant and (
            method == 'OPTIONS' or method == 'DELETE' and object_grant) else None
        assert calls == expected_calls and result is expected_result, {
            'input': (method, allowed, view_grant, object_grant),
            'expected': (expected_calls, expected_result), 'observed': (calls, result)}
