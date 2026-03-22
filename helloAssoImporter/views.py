import time
from itertools import groupby as itertools_groupby
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from common.api.helloAssoApi import get_hello_asso_api, HelloAssoApiError, FIELD_EMAIL, FIELD_BIRTHDATE, FIELD_SEX, FIELD_LICENCE
from helloAssoImporter.models import Season, MemberShipForm, MemberShipFormOrder, Member, EventForm, EventRegistration
from django.views.generic import ListView, DetailView
from django.db.models import Count, Q
from django.core.cache import cache
from userManagement.views import AdminRequiredMixin, admin_required, ClubStaffRequiredMixin, club_staff_required


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


class EventFormListView(ClubStaffRequiredMixin, ListView):
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


class EventFormDetailView(ClubStaffRequiredMixin, DetailView):
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
    if request.method == 'POST':
        api = get_hello_asso_api()
        try:
            new_members, new_orders = api.save_membership_form_members(membership_form)
            messages.success(request, f"Import terminé : {new_members} nouveau(x) membre(s), {new_orders} inscription(s) créée(s).")
        except HelloAssoApiError as e:
            notify_api_error(request, e)
    orders = MemberShipFormOrder.objects.filter(form=membership_form).select_related('member').order_by('member__last_name', 'member__first_name')
    return render(request, 'helloAssoImporter/membership_form_detail.html', {
        'membership_form': membership_form,
        'orders': orders,
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


@admin_required
def member_list(request):
    seasons = Season.objects.order_by('-current', 'label')
    season_id = request.GET.get('season')
    members = Member.objects.prefetch_related('membershipformorder_set__form__season').order_by('last_name', 'first_name')
    if season_id:
        members = members.filter(membershipformorder__form__season_id=season_id)
    members = list(members)
    duplicate_count = (
        Member.objects.values('first_name', 'last_name')
        .annotate(n=Count('id')).filter(n__gt=1).count()
    )
    return render(request, 'helloAssoImporter/member_list.html', {
        'members': members,
        'members_count': len(members),
        'seasons': seasons,
        'current_season_id': season_id,
        'duplicate_count': duplicate_count,
        'active_tab': 'membres',
    })


@admin_required
def member_duplicates(request):
    duplicate_pairs = list(
        Member.objects.values('first_name', 'last_name')
        .annotate(n=Count('id')).filter(n__gt=1)
        .values_list('first_name', 'last_name')
    )
    groups = []
    if duplicate_pairs:
        q = Q()
        for fn, ln in duplicate_pairs:
            q |= Q(first_name=fn, last_name=ln)
        all_members = (
            Member.objects.filter(q)
            .prefetch_related('membershipformorder_set__form__season')
            .order_by('last_name', 'first_name')
        )
        groups = [
            list(group)
            for _, group in itertools_groupby(all_members, key=lambda m: (m.last_name, m.first_name))
        ]
    return render(request, 'helloAssoImporter/member_duplicates.html', {
        'groups': groups,
        'active_tab': 'membres',
    })


@admin_required
def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    orders = MemberShipFormOrder.objects.filter(member=member).select_related('form__season').order_by('form__start_date')
    query = request.GET.get('q', '').strip()
    candidates = []
    if query:
        candidates = (
            Member.objects
            .filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
            .exclude(pk=pk)
            .prefetch_related('membershipformorder_set__form__season')
        )
    return render(request, 'helloAssoImporter/member_detail.html', {
        'member': member,
        'orders': orders,
        'query': query,
        'candidates': candidates,
        'active_tab': 'membres',
    })


@admin_required
def member_merge(request):
    if request.method != 'POST':
        return redirect('saison-membres-doublons')

    keep_id = request.POST.get('keep_id')
    merge_ids = request.POST.getlist('merge_ids')

    if not keep_id or not merge_ids:
        messages.error(request, "Données de fusion invalides.")
        return redirect('saison-membres-doublons')

    try:
        with transaction.atomic():
            keep = Member.objects.get(pk=keep_id)
            to_merge = list(Member.objects.filter(pk__in=merge_ids))
            existing_form_ids = set(
                MemberShipFormOrder.objects.filter(member=keep).values_list('form_id', flat=True)
            )
            to_update = []
            for source in to_merge:
                for order in source.membershipformorder_set.all():
                    if order.form_id not in existing_form_ids:
                        order.member = keep
                        to_update.append(order)
                        existing_form_ids.add(order.form_id)
            if to_update:
                MemberShipFormOrder.objects.bulk_update(to_update, ['member'])
            for source in to_merge:
                source.delete()
            reassigned = len(to_update)
        messages.success(request, f"Fusion effectuée : {keep.first_name} {keep.last_name} conservé, {reassigned} inscription(s) réassignée(s).")
    except Member.DoesNotExist:
        messages.error(request, "Membre introuvable.")

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('saison-membres-doublons')


@club_staff_required
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


_REFRESH_COOLDOWN_KEY = 'event_refresh_cooldown'
_REFRESH_COOLDOWN_SECONDS = 60


@club_staff_required
def refresh_event_forms(request):
    if cache.get(_REFRESH_COOLDOWN_KEY):
        messages.warning(request, "Rafraîchissement déjà effectué récemment. Veuillez patienter 1 minute.")
        return redirect('inscriptions')
    cache.set(_REFRESH_COOLDOWN_KEY, True, _REFRESH_COOLDOWN_SECONDS)
    api = get_hello_asso_api()
    start = time.time()
    try:
        forms_added = api.refresh_event_forms()
    except HelloAssoApiError as e:
        cache.delete(_REFRESH_COOLDOWN_KEY)
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
