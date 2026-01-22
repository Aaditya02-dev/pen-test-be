# Multi-Tenant Implementation Guide

## Overview
This application now uses a **shared database with tenant column** approach for multi-tenancy. Each tenant (organization/company) shares the same database, but data is isolated using tenant IDs.

## Architecture

### Models

#### Tenant Model
- Represents an organization/company
- Fields: `name`, `slug`, `domain`, `max_users`, `is_active`
- Each tenant is completely isolated from others

#### UserProfile Model
- Links Django Users to Tenants
- A user can belong to multiple tenants
- Fields: `user`, `tenant`, `role` (owner/admin/member)
- Unique constraint on (user, tenant)

#### TenantAwareModel (Abstract Base Class)
- Use this as base class for any model that should be tenant-specific
- Automatically includes `tenant` foreign key
- Example:
```python
from core.models import TenantAwareModel

class Project(TenantAwareModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    # tenant field is automatically added
```

### Middleware

**TenantMiddleware** automatically sets `request.tenant` based on:
1. `X-Tenant-ID` header (for API calls)
2. Authenticated user's associated tenant

Public endpoints (login, register, oauth) skip tenant requirement.

### Managers

**TenantManager** provides convenient filtering:
```python
# In your views
projects = Project.objects.for_tenant(request.tenant).all()
# or
projects = Project.objects.for_request(request).all()
```

## API Endpoints

### Authentication

#### POST /auth/register/
Register a new user and create a tenant
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "username",
  "tenant_name": "My Company"
}
```

Response:
```json
{
  "status": "ok",
  "user": {
    "id": 1,
    "username": "username",
    "email": "user@example.com"
  },
  "tenant": {
    "id": 1,
    "name": "My Company",
    "slug": "my-company",
    "role": "owner"
  }
}
```

#### POST /auth/login/
Login existing user
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response includes tenant information:
```json
{
  "status": "ok",
  "user": {...},
  "tenant": {
    "id": 1,
    "name": "My Company",
    "slug": "my-company",
    "role": "owner"
  }
}
```

#### GET /auth/me/
Get current user info including tenant
```json
{
  "username": "username",
  "id": 1,
  "email": "user@example.com",
  "tenant": {
    "id": 1,
    "name": "My Company",
    "slug": "my-company",
    "role": "owner"
  }
}
```

### Tenant Management

#### GET /tenant/users/
Get all users in current tenant (requires authentication)

#### POST /tenant/invite/
Invite user to tenant (admin/owner only)
```json
{
  "email": "newuser@example.com",
  "role": "member"  // or "admin"
}
```

## Usage Examples

### Creating Tenant-Aware Models

```python
from core.models import TenantAwareModel
from core.managers import TenantManager

class Project(TenantAwareModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'projects'
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
```

### Views with Tenant Filtering

```python
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_projects(request):
    if not request.tenant:
        return JsonResponse({"error": "No tenant"}, status=400)
    
    # Automatic tenant filtering
    projects = Project.objects.for_tenant(request.tenant).all()
    
    data = [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
    } for p in projects]
    
    return JsonResponse({"projects": data})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_project(request):
    if not request.tenant:
        return JsonResponse({"error": "No tenant"}, status=400)
    
    # Create with tenant automatically
    project = Project.objects.create(
        tenant=request.tenant,
        name=request.data.get("name"),
        description=request.data.get("description")
    )
    
    return JsonResponse({"id": project.id, "name": project.name})
```

### Frontend Integration

When making API calls, include the tenant ID in headers (optional, auto-detected from user):
```javascript
fetch('http://localhost:8000/api/projects/', {
  headers: {
    'X-Tenant-ID': '1',
    'Authorization': 'Bearer <token>',
  },
  credentials: 'include'
})
```

## Roles

- **Owner**: Created the tenant, full control
- **Admin**: Can invite users, manage tenant settings
- **Member**: Standard user access

## Data Isolation

All tenant-aware models automatically filter by tenant:
- Users in Tenant A cannot see Tenant B's data
- Queries are automatically scoped to the current tenant
- Foreign keys maintain referential integrity within tenants

## Migration Guide for Existing Models

To make an existing model tenant-aware:

1. Inherit from `TenantAwareModel`:
```python
from core.models import TenantAwareModel

class YourModel(TenantAwareModel):  # instead of models.Model
    # your fields
    pass
```

2. Add the manager:
```python
from core.managers import TenantManager

class YourModel(TenantAwareModel):
    # your fields
    objects = TenantManager()
```

3. Create and run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Update views to use tenant filtering:
```python
YourModel.objects.for_tenant(request.tenant).all()
```

## Security Considerations

1. **Always verify tenant access** - Middleware handles this automatically
2. **Use tenant filtering** - Always filter queries by tenant
3. **Role-based access** - Check user role before sensitive operations
4. **Input validation** - Validate tenant IDs in headers/requests
5. **Audit logging** - Consider adding audit trails for tenant operations

## Testing

Create test fixtures for multiple tenants:
```python
def test_tenant_isolation():
    tenant1 = Tenant.objects.create(name="Company A", slug="company-a")
    tenant2 = Tenant.objects.create(name="Company B", slug="company-b")
    
    project1 = Project.objects.create(tenant=tenant1, name="Project A")
    project2 = Project.objects.create(tenant=tenant2, name="Project B")
    
    # Verify isolation
    assert Project.objects.for_tenant(tenant1).count() == 1
    assert Project.objects.for_tenant(tenant2).count() == 1
```

## Admin Panel

Access Django admin at `/admin/` to manage:
- Tenants
- User Profiles
- Tenant-User associations

Super users can see all tenants and switch between them.
