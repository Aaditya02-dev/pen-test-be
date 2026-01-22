"""
Example of how to create tenant-aware models in your application.
This file is for reference only - copy patterns to your actual models.
"""

from django.db import models
from core.models import TenantAwareModel
from core.managers import TenantManager


# Example 1: Simple tenant-aware model
class Project(TenantAwareModel):
    """
    A project that belongs to a tenant.
    The tenant field and timestamps are inherited from TenantAwareModel.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('archived', 'Archived'),
            ('completed', 'Completed'),
        ],
        default='active'
    )
    
    # Add the custom manager for easy tenant filtering
    objects = TenantManager()
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


# Example 2: Model with relationships
class Task(TenantAwareModel):
    """
    A task within a project. Both are tenant-aware.
    """
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('todo', 'To Do'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
        ],
        default='todo'
    )
    due_date = models.DateField(null=True, blank=True)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'tasks'
        ordering = ['due_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.project.name}"
    
    def save(self, *args, **kwargs):
        # Ensure task belongs to same tenant as project
        if self.project and not self.tenant_id:
            self.tenant = self.project.tenant
        super().save(*args, **kwargs)


# Example 3: Usage in views
"""
# In your views.py:

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from .models_example import Project, Task

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_projects(request):
    # Automatically filtered by tenant
    projects = Project.objects.for_tenant(request.tenant).all()
    
    data = [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "created_at": p.created_at.isoformat(),
    } for p in projects]
    
    return JsonResponse({"projects": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_project(request):
    if not request.tenant:
        return JsonResponse({"error": "No tenant"}, status=400)
    
    project = Project.objects.create(
        tenant=request.tenant,
        name=request.data.get("name"),
        description=request.data.get("description", ""),
        status="active"
    )
    
    return JsonResponse({
        "id": project.id,
        "name": project.name,
        "status": project.status
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_tasks(request, project_id):
    # Get project (automatically filtered by tenant)
    try:
        project = Project.objects.for_tenant(request.tenant).get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"error": "Project not found"}, status=404)
    
    # Get tasks for this project
    tasks = Task.objects.for_tenant(request.tenant).filter(project=project)
    
    data = [{
        "id": t.id,
        "title": t.title,
        "status": t.status,
        "assigned_to": t.assigned_to.username if t.assigned_to else None,
        "due_date": t.due_date.isoformat() if t.due_date else None,
    } for t in tasks]
    
    return JsonResponse({"tasks": data})
"""
