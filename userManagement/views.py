import uuid

from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, UpdateView, FormView, View, TemplateView
from django.urls import reverse, reverse_lazy
from django import forms

User = get_user_model()


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
    email = forms.EmailField(label='Adresse email')


class AcceptInviteForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur")
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return cleaned_data


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

    def form_valid(self, form):
        email = form.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            form.add_error('email', 'Un utilisateur avec cet email existe déjà.')
            return self.form_invalid(form)

        token = uuid.uuid4()
        invite_url = self.request.build_absolute_uri(
            reverse('userManagement:accept_invite', args=[token])
        )
        User.objects.create(
            username=str(token),
            email=email,
            is_active=False,
            invite_token=token,
            invite_url=invite_url,
        )
        return self.render_to_response(self.get_context_data(
            form=InvitationForm(),
            invitation_url=invite_url,
            invited_email=email,
        ))


class AcceptInviteView(View):
    template_name = 'userManagement/accept_invite.html'

    def get_pending_user(self, token):
        return get_object_or_404(User, invite_token=token, is_active=False)

    def get(self, request, token):
        user = self.get_pending_user(token)
        form = AcceptInviteForm(user=user)
        return render(request, self.template_name, {'form': form, 'email': user.email})

    def post(self, request, token):
        user = self.get_pending_user(token)
        form = AcceptInviteForm(request.POST, user=user)
        if form.is_valid():
            user.username = form.cleaned_data['username']
            user.set_password(form.cleaned_data['password1'])
            user.is_active = True
            user.invite_token = None
            user.invite_url = None
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('/')
        return render(request, self.template_name, {'form': form, 'email': user.email})


class UserDeactivateView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        return redirect('userManagement:user_list')
