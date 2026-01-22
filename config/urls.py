"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("oauth/exchange/", views.oauth_exchange),
    path("auth/me/", views.me),
    path("auth/logout/", views.logout_view),
    path("auth/login/", views.login_api),
    path("auth/register/", views.register),
    path("auth/csrf/", views.get_csrf),
    path("tenant/users/", views.tenant_users),
    path("tenant/invite/", views.invite_user),
    path('upload/', views.upload_file, name='upload_file'),
    path('scan-results/<str:app_id>/', views.get_scan_results, name='get_scan_results'),
    path('scan/', views.start_scan, name='start_scan'),
]
