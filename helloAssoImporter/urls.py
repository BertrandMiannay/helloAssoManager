from django.urls import path

from . import views

urlpatterns = [
    path("", views.EventFormListView.as_view(), name="inscriptions"),
    path("refresh/", views.refresh_event_forms, name="inscriptions-refresh"),
    path("create/", views.create_event_form, name="event-form-create"),
    path("<str:form_slug>/", views.EventFormDetailView.as_view(), name="event-form-detail"),
]
