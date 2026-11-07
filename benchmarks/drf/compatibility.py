"""Post-hoc compatibility check, excluded from the frozen paired score.

Motivation: historical DRF issue 9299 and revert PR 9332 were inspected after
paired prompts were frozen. This is retrospective reproduction, not discovery.
Execute only inside the Django-configured source sandbox.
"""
from types import SimpleNamespace


def test_anonymous_readonly_preserved():
    from django.contrib.auth.models import AnonymousUser
    from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
    model = SimpleNamespace(_meta=SimpleNamespace(app_label='shadow', model_name='item'))
    view = SimpleNamespace(queryset=SimpleNamespace(model=model))
    for method in ('GET', 'HEAD', 'OPTIONS'):
        request = SimpleNamespace(user=AnonymousUser(), method=method)
        observed = DjangoModelPermissionsOrAnonReadOnly().has_permission(request, view)
        assert observed is True, {'method': method, 'expected': True, 'observed': observed}
