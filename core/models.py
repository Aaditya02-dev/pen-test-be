from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Tenant(models.Model):
    """Represents an organization/company in the system"""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Settings
    max_users = models.IntegerField(default=10)
    
    class Meta:
        db_table = 'tenants'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Extends the User model to include tenant relationship"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(
        max_length=20, 
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
        ],
        default='member'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        unique_together = [['user', 'tenant']]
    
    def __str__(self):
        return f"{self.user.username} - {self.tenant.name}"


# Base model for tenant-aware models
class TenantAwareModel(models.Model):
    """Abstract base class for all models that should be tenant-aware"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='%(class)s_set')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
