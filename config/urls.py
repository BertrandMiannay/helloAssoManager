from django.contrib import admin
from django.urls import path, include
from userManagement.views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('invitations/', include('invitations.urls', namespace='invitations')),
    path('inscriptions/', include('helloAssoImporter.urls')),
    path('users/', include('userManagement.urls')),
]
