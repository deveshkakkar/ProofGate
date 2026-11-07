"""Collect real permission-method outputs; run only in the source namespace.

No reference outputs or allowed-change policy are provided to this process.
The trusted host owns comparison and inventory validation.
"""
import json
import sys
from types import SimpleNamespace
from django.conf import settings

if not settings.configured:
    settings.configure(INSTALLED_APPS=[], USE_I18N=False)
from rest_framework.permissions import DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly

CLASSES = {'model': DjangoModelPermissions, 'model_or_anon': DjangoModelPermissionsOrAnonReadOnly}
inputs = json.load(sys.stdin)
outputs = []
for row in inputs:
    granted = {'shadow.' + action + '_item' for action in ('view', 'change', 'add', 'delete')
               if row['can_' + action]}
    user = SimpleNamespace(is_authenticated=row['authenticated'],
                           has_perms=lambda names: all(name in granted for name in names))
    model = SimpleNamespace(_meta=SimpleNamespace(app_label='shadow', model_name='item'))
    view = SimpleNamespace(queryset=SimpleNamespace(model=model))
    request = SimpleNamespace(user=user, method=row['method'])
    try:
        value = CLASSES[row['permission_class']]().has_permission(request, view)
        output = {'kind': 'return', 'value': value}
    except Exception as exc:
        output = {'kind': 'raise', 'type': type(exc).__module__ + '.' + type(exc).__qualname__}
    outputs.append({'input': row, 'output': output})
print(json.dumps(outputs, allow_nan=False))
