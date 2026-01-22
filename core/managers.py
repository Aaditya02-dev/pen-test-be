from django.db import models


class TenantManager(models.Manager):
    """
    Custom manager that automatically filters querysets by tenant.
    Usage: MyModel.objects.for_tenant(tenant).all()
    """
    
    def for_tenant(self, tenant):
        """Filter queryset by tenant"""
        if tenant is None:
            return self.none()
        return self.filter(tenant=tenant)
    
    def for_request(self, request):
        """Filter queryset by tenant from request"""
        if not hasattr(request, 'tenant') or request.tenant is None:
            return self.none()
        return self.for_tenant(request.tenant)


class TenantQuerySet(models.QuerySet):
    """Custom queryset for tenant-aware models"""
    
    def for_tenant(self, tenant):
        """Filter queryset by tenant"""
        if tenant is None:
            return self.none()
        return self.filter(tenant=tenant)
