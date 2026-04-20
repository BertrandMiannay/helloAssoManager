from django.urls import path

from . import views

urlpatterns = [
    path("", views.AdherentListView.as_view(), name="adherents"),
    path("<int:pk>/", views.adherent_detail, name="adherent-detail"),
    path("<int:pk>/formation/<int:cursus_pk>/", views.adherent_formation_save, name="adherent-formation-save"),
    path("<int:pk>/formation/<int:cursus_pk>/export/", views.adherent_formation_export, name="adherent-formation-export"),
    path("<int:pk>/evaluation/<int:ev_pk>/delete/", views.adherent_evaluation_delete, name="adherent-evaluation-delete"),
]
