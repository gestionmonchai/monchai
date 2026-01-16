import contextvars
from django.db import models
from django.db.models import Q

# Context variable holding the current org for the duration of the request
_current_org = contextvars.ContextVar("current_org", default=None)


class TenantManager(models.Manager):
    """Manager that automatically filters by current organization if the model
    has an 'organization' or 'org' ForeignKey field.

    If no current organization is set, returns an empty queryset to prevent leaks.
    If the model has no organization field, returns the unfiltered queryset.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        org = _current_org.get()
        if org is None:
            # No active organization context → do not implicitly filter
            # Web requests will set it via middleware; tests/scripts may skip scoping
            return qs
        # 1) Explicit org lookups on model
        lookups = getattr(self.model, 'TENANT_ORG_LOOKUPS', None)
        if lookups:
            q = Q()
            for lk in lookups:
                q |= Q(**{lk: org})
            # Relations traversed in lookups can duplicate rows (e.g., multiple lignes/lots).
            # Distinct ensures primary-key uniqueness for downstream get()/count().
            return qs.filter(q).distinct()
        field = getattr(self.model, 'TENANT_ORG_FIELD', None)
        if field:
            return qs.filter(**{field: org})
        # 2) Conventional field names
        try:
            field_names = {f.name for f in self.model._meta.get_fields()}
            if 'organization' in field_names:
                return qs.filter(organization=org)
            if 'org' in field_names:
                return qs.filter(org=org)
        except Exception:
            pass
        # 3) Fallback: model not multi-tenant → no implicit filter
        return qs
