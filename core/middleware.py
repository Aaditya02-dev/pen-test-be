from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from core.models import Tenant, UserProfile


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to set the current tenant based on:
    1. X-Tenant-ID header
    2. User's associated tenant
    """
    
    def process_request(self, request):
        # Skip tenant check for non-authenticated endpoints
        public_paths = [
            '/auth/login/',
            '/auth/csrf/',
            '/oauth/exchange/',
            '/admin/',
            '/accounts/',
            '/o/',
        ]
        
        # Check if current path is public
        if any(request.path.startswith(path) for path in public_paths):
            request.tenant = None
            return None
        
        tenant = None
        
        # Try to get tenant from header first (useful for API calls)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                pass
        
        # If user is authenticated and no tenant from header, get from user profile
        if not tenant and request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.select_related('tenant').get(user=request.user)
                tenant = user_profile.tenant
            except UserProfile.DoesNotExist:
                pass
        
        # Set tenant on request
        request.tenant = tenant
        
        return None
