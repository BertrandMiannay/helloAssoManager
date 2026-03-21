from django.urls import path
from . import views

urlpatterns = [
    path('', views.MemberShipFormListView.as_view(), name='saison'),
    path('refresh/', views.refresh_membership_forms, name='saison-refresh'),
]
