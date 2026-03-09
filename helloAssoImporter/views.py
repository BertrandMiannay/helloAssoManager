from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404

from common.api.helloAssoApi import HelloAssoApi
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder, EventForm, EventRegistration
from django.views.generic import ListView, DetailView
from django.db.models import Count


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


@login_required
def refresh_event_forms(request):
    hello_asso_api = HelloAssoApi()
    hello_asso_api.refresh_event_forms()
    return redirect('inscriptions')


@login_required
def refresh_event_form_orders(request, form_slug):
    form = get_object_or_404(EventForm, pk=form_slug)
    hello_asso_api = HelloAssoApi()
    hello_asso_api.get_event_form_orders(form)
    return redirect('event-form-detail', form_slug=form_slug)
