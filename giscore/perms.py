from django.http import HttpResponseForbidden


def enforce_tenant(request, tenant_param: str):
    tenant = request.GET.get("tenant") or request.POST.get("tenant")
    jwt_payload = getattr(request, 'jwt', {}) or {}
    if not tenant:
        tenant = jwt_payload.get('tenant_id')
    if not tenant:
        return None, HttpResponseForbidden("Missing tenant")
    if jwt_payload.get('tenant_id') and jwt_payload.get('tenant_id') != tenant:
        return None, HttpResponseForbidden("Tenant mismatch")
    return tenant, None
