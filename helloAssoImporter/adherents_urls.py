from django.urls import path

from . import views

urlpatterns = [
    path("", views.AdherentListView.as_view(), name="adherents"),
    path("<int:pk>/", views.adherent_detail, name="adherent-detail"),
]
