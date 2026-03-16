from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, FormView, View, TemplateView
from django.urls import reverse_lazy
from django import forms
from invitations.utils import get_invitation_model

User = get_user_model()
Invitation = get_invitation_model()


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        is_admin = self.request.user.groups.filter(name='admin').exists()
        ctx['apps'] = [

            {
                'title': 'Utilisateurs',
                'description': 'Gérer les comptes, les rôles et les invitations.',
                'url': '/users/',
                'visible': is_admin,
            },
            {
                'title': 'Inscriptions',
                'description': "Consulter les formulaires d'adhésion et les membres importés depuis HelloAsso.",
                'url': '/inscriptions/',
                'visible': True,
            }
        ]
        return ctx


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow access only to users in the 'admin' group."""

    def test_func(self):
        return self.request.user.groups.filter(name='admin').exists()


class UserRoleForm(forms.Form):
    role = forms.ChoiceField(choices=[
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    ])


class InvitationForm(forms.Form):
    email = forms.EmailField(label='Email address')


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'userManagement/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.prefetch_related('groups').order_by('username')


class UserRoleUpdateView(AdminRequiredMixin, FormView):
    template_name = 'userManagement/user_role_form.html'
    form_class = UserRoleForm
    success_url = reverse_lazy('userManagement:user_list')

    def get_target_user(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['target_user'] = self.get_target_user()
        return ctx

    def form_valid(self, form):
        user = self.get_target_user()
        user.groups.clear()
        group = Group.objects.get(name=form.cleaned_data['role'])
        user.groups.add(group)
        return super().form_valid(form)


class InviteView(AdminRequiredMixin, FormView):
    template_name = 'userManagement/invite.html'
    form_class = InvitationForm
    success_url = reverse_lazy('userManagement:user_list')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        invitation = Invitation.create(email, inviter=self.request.user)
        invitation.send_invitation(self.request)
        return super().form_valid(form)


class UserDeactivateView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        return redirect('userManagement:user_list')
