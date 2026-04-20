from django.urls import path

from . import views

urlpatterns = [
    path("", views.AdherentListView.as_view(), name="adherents"),
    path("<int:pk>/", views.adherent_detail, name="adherent-detail"),
    path("<int:pk>/formation/<int:cursus_pk>/", views.adherent_formation_save, name="adherent-formation-save"),
]
