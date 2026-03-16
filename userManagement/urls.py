from django.urls import path
from . import views

app_name = 'userManagement'

urlpatterns = [
    path('home/', views.HomeView.as_view(), name='home'),
    path('', views.UserListView.as_view(), name='user_list'),
    path('<int:pk>/role/', views.UserRoleUpdateView.as_view(), name='user_role'),
    path('invite/', views.InviteView.as_view(), name='invite'),
    path('accept/<uuid:token>/', views.AcceptInviteView.as_view(), name='accept_invite'),
    path('<int:pk>/deactivate/', views.UserDeactivateView.as_view(), name='user_deactivate'),
]
