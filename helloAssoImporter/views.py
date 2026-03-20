import time
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render

from common.api.helloAssoApi import get_hello_asso_api, HelloAssoApiError
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder, EventForm, EventRegistration
from django.views.generic import ListView, DetailView
from django.db.models import Count


class EventFormCreateForm(forms.Form):
    title = forms.CharField(label='Titre', max_length=200)
    description = forms.CharField(label='Description courte', required=False, widget=forms.Textarea(attrs={'rows': 3}))
    long_description = forms.CharField(label='Description longue', required=False, widget=forms.Textarea(attrs={'rows': 5}))
    start_date = forms.DateTimeField(label='Date de début', required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_date = forms.DateTimeField(label='Date de fin', required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    place = forms.CharField(label='Lieu', required=False)
    max_entries = forms.IntegerField(label='Nombre max de participants', required=False, min_value=1)


class MemberShipFormListView(LoginRequiredMixin, ListView):
    model = MemberShipForm
    template_name = 'forms.html'


class MemberShipFormOrderListView(LoginRequiredMixin, ListView):
    model = MemberShipFormOrder
    template_name = 'forms.html'


class EventFormListView(LoginRequiredMixin, ListView):
    model = EventForm
    template_name = 'helloAssoImporter/event_forms.html'
    context_object_name = 'event_forms'

    def get_queryset(self):
        return EventForm.objects.annotate(
            registration_count=Count('eventformorder__eventregistration')
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
        ).select_related('order')
        return ctx


def notify_api_error(request, error: HelloAssoApiError):
    messages.error(request, f"Échec du rafraîchissement : {error}")


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
