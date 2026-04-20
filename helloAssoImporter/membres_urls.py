from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberShipFormListView.as_view(), name='saison-formulaires'),
    path('refresh/', views.refresh_membership_forms, name='saison-refresh'),
    path('assign-season/', views.assign_season, name='saison-assign'),
    path('gestion/', views.season_gestion, name='saison-gestion'),
    path('formation/', views.formation_list, name='saison-formation'),
    path('formation/creer/', views.cursus_create, name='saison-cursus-creer'),
    path('formation/<int:pk>/', views.cursus_detail, name='saison-cursus-detail'),
    path('formation/<int:pk>/archiver/', views.cursus_archive, name='saison-cursus-archiver'),
    path('set-current/<int:pk>/', views.set_current_season, name='saison-set-current'),
    path('delete/<int:pk>/', views.delete_season, name='saison-delete'),
    path('membres/', views.member_list, name='saison-membres'),
    path('membres/doublons/', views.member_duplicates, name='saison-membres-doublons'),
    path('membres/<int:pk>/', views.member_detail, name='saison-membre-detail'),
    path('membres/fusionner/', views.member_merge, name='saison-membres-fusionner'),
    path('<slug:form_slug>/', views.membership_form_detail, name='saison-form-detail'),
]
