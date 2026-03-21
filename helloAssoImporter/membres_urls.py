from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberShipFormListView.as_view(), name='saison-formulaires'),
    path('refresh/', views.refresh_membership_forms, name='saison-refresh'),
    path('assign-season/', views.assign_season, name='saison-assign'),
    path('gestion/', views.season_gestion, name='saison-gestion'),
    path('formation/', views.formation, name='saison-formation'),
    path('set-current/<int:pk>/', views.set_current_season, name='saison-set-current'),
    path('delete/<int:pk>/', views.delete_season, name='saison-delete'),
]
