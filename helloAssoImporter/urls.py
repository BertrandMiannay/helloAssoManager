from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("forms/", views.MemberShipFormListView.as_view()),
    path("orders/", views.MemberShipFormOrderListView.as_view())
]