import time
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render

from common.api.helloAssoApi import get_hello_asso_api, HelloAssoApiError
from helloAssoImporter.models import Season, MemberShipForm, MemberShipFormOrder, EventForm, EventRegistration
from django.views.generic import ListView, DetailView
from django.db.models import Count, Q
from userManagement.views import AdminRequiredMixin, admin_required


class EventFormCreateForm(forms.Form):
    title = forms.CharField(label='Titre', max_length=200)
    description = forms.CharField(label='Description courte', required=False, widget=forms.Textarea(attrs={'rows': 3}))
    long_description = forms.CharField(label='Description longue', required=False, widget=forms.Textarea(attrs={'rows': 5}))
    start_date = forms.DateTimeField(label='Date de début', required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_date = forms.DateTimeField(label='Date de fin', required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    place = forms.CharField(label='Lieu', required=False)
    max_entries = forms.IntegerField(label='Nombre max de participants', required=False, min_value=1)


class MemberShipFormListView(AdminRequiredMixin, ListView):
    model = MemberShipForm
    template_name = 'helloAssoImporter/membership_forms.html'
    context_object_name = 'membership_forms'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['seasons'] = Season.objects.all().order_by('-current', 'label')
        ctx['active_tab'] = 'formulaires'
        return ctx


class MemberShipFormOrderListView(LoginRequiredMixin, ListView):
    model = MemberShipFormOrder
    template_name = 'forms.html'


class EventFormListView(LoginRequiredMixin, ListView):
    model = EventForm
    template_name = 'helloAssoImporter/event_forms.html'
    context_object_name = 'event_forms'

    def get_queryset(self):
        return EventForm.objects.annotate(
            registration_count=Count('eventformorder__eventregistration'),
            confirmed_count=Count(
                'eventformorder__eventregistration',
                filter=Q(eventformorder__eventregistration__state=EventRegistration.State.REGISTERED)
            ),
        )


class EventFormDetailView(LoginRequiredMixin, DetailView):
    model = EventForm
    template_name = 'helloAssoImporter/event_form_detail.html'
    context_object_name = 'event_form'
    pk_url_kwarg = 'form_slug'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['registrations'] = EventRegistration.objects.filter(
            order__form=self.object
        ).select_related('order').order_by('state', 'last_name', 'first_name')
        return ctx


def notify_api_error(request, error: HelloAssoApiError):
    messages.error(request, f"Échec du rafraîchissement : {error}")


@admin_required
def season_gestion(request):
    form_data = {}
    if request.method == 'POST':
        label = request.POST.get('label', '').strip()
        if label:
            Season.objects.create(label=label)
            return redirect('saison-gestion')
        form_data = {'label': label}
    seasons = Season.objects.all().order_by('-current', 'label')
    return render(request, 'helloAssoImporter/season_gestion.html', {
        'seasons': seasons,
        'form_data': form_data,
        'active_tab': 'gestion',
    })


@admin_required
def set_current_season(request, pk):
    if request.method == 'POST':
        Season.objects.update(current=False)
        Season.objects.filter(pk=pk).update(current=True)
    return redirect('saison-gestion')


@admin_required
def delete_season(request, pk):
    if request.method == 'POST':
        Season.objects.filter(pk=pk).delete()
    return redirect('saison-gestion')


@admin_required
def formation(request):
    return render(request, 'helloAssoImporter/formation.html', {'active_tab': 'formation'})


@admin_required
def assign_season(request):
    if request.method == 'POST':
        form_slug = request.POST.get('form_slug')
        season_id = request.POST.get('season_id') or None
        try:
            membership_form = MemberShipForm.objects.get(pk=form_slug)
            if season_id and MemberShipForm.objects.filter(season_id=int(season_id)).exclude(pk=form_slug).exists():
                season = Season.objects.get(pk=int(season_id))
                messages.error(request, f"La saison « {season.label} » est déjà associée à un autre formulaire.")
            else:
                membership_form.season_id = int(season_id) if season_id else None
                membership_form.save()
        except MemberShipForm.DoesNotExist:
            pass
    return redirect('saison-formulaires')


@admin_required
def membership_form_detail(request, form_slug):
    membership_form = get_object_or_404(MemberShipForm, pk=form_slug)
    members = None
    if request.method == 'POST':
        api = get_hello_asso_api()
        try:
            members = api.fetch_membership_form_members(membership_form)
        except HelloAssoApiError as e:
            notify_api_error(request, e)
    return render(request, 'helloAssoImporter/membership_form_detail.html', {
        'membership_form': membership_form,
        'members': members,
        'active_tab': 'formulaires',
    })


@admin_required
def refresh_membership_forms(request):
    api = get_hello_asso_api()
    try:
        count = api.refresh_membership_forms()
        messages.success(request, f"{count} formulaire(s) d'adhésion importé(s).")
    except HelloAssoApiError as e:
        notify_api_error(request, e)
    return redirect('saison-formulaires')


@login_required
def create_event_form(request):
    if request.method == 'POST':
        form = EventFormCreateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            api = get_hello_asso_api()
            try:
                api.create_event_form(d)
                messages.success(request, f"Sortie « {d['title']} » créée avec succès.")
                return redirect('inscriptions')
            except HelloAssoApiError as e:
                messages.error(request, f"Échec de la création : {e}")
    else:
        form = EventFormCreateForm()
    return render(request, 'helloAssoImporter/event_form_create.html', {'form': form})


@login_required
def refresh_event_forms(request):
    api = get_hello_asso_api()
    start = time.time()
    try:
        forms_added = api.refresh_event_forms()
    except HelloAssoApiError as e:
        notify_api_error(request, e)
        return redirect('inscriptions')
    registrations_added = 0
    for form in EventForm.objects.all():
        try:
            registrations_added += api.get_event_form_orders(form, since=form.last_registration_updated)
        except HelloAssoApiError as e:
            notify_api_error(request, e)
    elapsed = round(time.time() - start)
    messages.success(request, f"Import terminé. {forms_added} sortie(s) et {registrations_added} inscription(s) créées en {elapsed} seconde(s).")
    return redirect('inscriptions')
