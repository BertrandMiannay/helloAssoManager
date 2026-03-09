from django.urls import path

from . import views

urlpatterns = [
    path("", views.EventFormListView.as_view(), name="inscriptions"),
    path("refresh/", views.refresh_event_forms, name="inscriptions-refresh"),
    path("<str:form_slug>/", views.EventFormDetailView.as_view(), name="event-form-detail"),
    path("<str:form_slug>/refresh-orders/", views.refresh_event_form_orders, name="event-form-refresh-orders"),
    path("forms/", views.MemberShipFormListView.as_view()),
    path("orders/", views.MemberShipFormOrderListView.as_view()),
]
