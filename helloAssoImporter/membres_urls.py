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
    path('membres/', views.member_list, name='saison-membres'),
    path('membres/doublons/', views.member_duplicates, name='saison-membres-doublons'),
    path('membres/<int:pk>/', views.member_detail, name='saison-membre-detail'),
    path('membres/fusionner/', views.member_merge, name='saison-membres-fusionner'),
    path('<slug:form_slug>/', views.membership_form_detail, name='saison-form-detail'),
]
