"""Finite entitlement decision; inputs validated by the application adapter."""
def allow(subject_tenant, resource_tenant, active, entitled, enabled):
    return active and subject_tenant == resource_tenant and entitled and enabled
