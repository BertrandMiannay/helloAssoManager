import logging
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from django.db import transaction
from django.utils import timezone
import helloasso_python
from helloasso_python.api.formulaires_api import FormulairesApi
from helloasso_python.api.commandes_api import CommandesApi
from helloasso_python.api_client import ApiClient
from helloasso_python.exceptions import ApiException
from helloasso_python.models import HelloAssoApiV5ModelsFormsFormQuickCreateRequest, HelloAssoApiV5ModelsCommonPlaceModel
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder, Member, EventForm, EventFormOrder, EventRegistration

logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.helloasso.com/oauth2/token"

# HelloAsso custom field names for membership forms (used as fallbacks / defaults)
FIELD_EMAIL = "Adresse Mail"
FIELD_BIRTHDATE = "Date de naissance"
FIELD_SEX = "Sexe"
FIELD_LICENCE = "Numéro de licence"

# Standardized level fields: maps model field name → French label
# Used by the import logic and the field-mapping UI.
LEVEL_FIELD_LABELS = {
    'dive_level': 'Niveau plongée',
    'dive_teaching_level': 'Encadrement plongée',
    'apnea_level': 'Niveau apnée',
    'apnea_teaching_level': 'Encadrement apnée',
    'underwater_shooting_level': 'Niveau tir sous-marin',
    'underwater_shooting_teaching_level': 'Encadrement tir sous-marin',
}
LEVEL_FIELDS = tuple(LEVEL_FIELD_LABELS)

CONTACT_FIELD_LABELS = {
    'emergency_contact_name': "Contact d'urgence - nom",
    'emergency_contact_phone': "Contact d'urgence - téléphone",
}
CONTACT_FIELDS = tuple(CONTACT_FIELD_LABELS)


def normalize_name(value: str) -> str:
    return value.strip().title()


class HelloAssoApiError(Exception):
    pass


class HelloAssoApi:

    def __init__(self):
        load_dotenv()
        client_id = os.getenv("HELLO_ASSO_API_CLIENT_ID")
        client_secret = os.getenv("HELLO_ASSO_API_CLIENT_SECRET")
        self.organization_slug = os.getenv("ORGANIZATION_SLUG")

        if not client_id or not client_secret or not self.organization_slug:
            raise Exception("missing credentials")

        access_token = self._fetch_access_token(client_id, client_secret)
        configuration = helloasso_python.Configuration(access_token=access_token)
        api_client = ApiClient(configuration=configuration)
        self._api_client = api_client
        self._client_id = client_id
        self._client_secret = client_secret
        self._formulaires = FormulairesApi(api_client)
        self._commandes = CommandesApi(api_client)

    def _fetch_access_token(self, client_id: str, client_secret: str) -> str:
        response = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=30,
        )
        if not response.ok:
            raise HelloAssoApiError(f"Échec d'authentification HelloAsso ({response.status_code})")
        return response.json()["access_token"]

    def _reauthenticate(self) -> None:
        token = self._fetch_access_token(self._client_id, self._client_secret)
        self._api_client.configuration.access_token = token

    def _call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiException as e:
            if e.status == 401:
                self._reauthenticate()
                try:
                    return fn(*args, **kwargs)
                except ApiException as e2:
                    raise HelloAssoApiError(str(e2)) from e2
            raise HelloAssoApiError(str(e)) from e

    def refresh_membership_forms(self) -> int:
        result = self._call(
            self._formulaires.organizations_organization_slug_forms_get,
            organization_slug=self.organization_slug,
            form_types=["Membership"],
            states=["Public", "Private"],
        )
        new_count = 0
        for i in result.data or []:
            _, created = MemberShipForm.objects.get_or_create(
                form_slug=i.form_slug,
                defaults={
                    "title": i.title,
                    "form_type": i.form_type,
                    "description": i.description,
                    "start_date": i.start_date,
                    "end_date": i.end_date,
                    "updated_at": i.meta.updated_at if i.meta else None,
                    "created_at": i.meta.created_at if i.meta else None,
                }
            )
            if created:
                new_count += 1
        return new_count

    def refresh_event_forms(self) -> int:
        result = self._call(
            self._formulaires.organizations_organization_slug_forms_get,
            organization_slug=self.organization_slug,
            form_types=["Event"],
            states=["Public", "Private"],
            page_size=100,
        )
        new_count = 0
        for i in result.data or []:
            _, created = EventForm.objects.get_or_create(
                form_slug=i.form_slug,
                defaults={
                    "title": i.title,
                    "form_type": i.form_type,
                    "description": i.description,
                    "start_date": i.start_date,
                    "end_date": i.end_date,
                    "last_registration_updated": None,
                    "updated_at": i.meta.updated_at if i.meta else None,
                    "created_at": i.meta.created_at if i.meta else None,
                }
            )
            if created:
                new_count += 1
        return new_count

    def save_membership_form_members(self, form: MemberShipForm) -> tuple[int, int]:
        """Fetch and save members for a membership form.
        Returns (new_members_count, new_orders_count).
        """
        # Fetch all pages first (outside transaction — API calls can't be rolled back)
        pages = []
        continuation_token = None
        while True:
            result = self._call(
                self._commandes.organizations_organization_slug_forms_form_type_form_slug_orders_get,
                organization_slug=self.organization_slug,
                form_slug=form.form_slug,
                form_type=form.form_type,
                page_size=100,
                with_details=True,
                continuation_token=continuation_token,
            )
            pages.append(result.data or [])
            next_token = result.pagination.continuation_token if result.pagination else None
            if not next_token or next_token == continuation_token or not result.data:
                break
            continuation_token = next_token

        new_members = 0
        new_orders = 0
        with transaction.atomic():
            for page in pages:
                for order in page:
                    for item in order.items or []:
                        custom = {f.name.strip(): f.answer for f in (item.custom_fields or [])}

                        email = (custom.get(FIELD_EMAIL) or '').strip().lower()
                        first_name = normalize_name(item.user.first_name if item.user else '')
                        last_name = normalize_name(item.user.last_name if item.user else '')

                        if not email:
                            logger.warning("Item %s skipped: no email", item.id)
                            continue

                        member, member_created = Member.objects.get_or_create(
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                        )
                        if member_created:
                            new_members += 1

                        birthdate_str = custom.get(FIELD_BIRTHDATE)
                        birthdate = None
                        if birthdate_str:
                            try:
                                birthdate = datetime.strptime(birthdate_str, "%d/%m/%Y").date()
                            except ValueError:
                                logger.warning("Invalid birthdate '%s' for item %s", birthdate_str, item.id)

                        if birthdate and member.birthdate != birthdate:
                            member.birthdate = birthdate
                            member.save(update_fields=['birthdate'])

                        level_values = {
                            field: custom.get(form.field_mapping.get(field, ''), '')
                            for field in LEVEL_FIELDS
                        }
                        contact_values = {
                            field: custom.get(form.field_mapping.get(field, ''), '')
                            for field in CONTACT_FIELDS
                        }
                        _, order_created = MemberShipFormOrder.objects.update_or_create(
                            item_id=item.id,
                            defaults={
                                'order_id': order.id,
                                'form': form,
                                'member': member,
                                'payer_email': order.payer.email if order.payer else '',
                                'payer_first_name': order.payer.first_name if order.payer else '',
                                'payer_last_name': order.payer.last_name if order.payer else '',
                                'category': item.name,
                                'birthdate': birthdate,
                                'licence_number': custom.get(FIELD_LICENCE, ''),
                                'sex': custom.get(FIELD_SEX),
                                **level_values,
                                **contact_values,
                                'updated_at': order.meta.updated_at if order.meta else None,
                                'created_at': order.meta.created_at if order.meta else None,
                            }
                        )
                        if order_created:
                            new_orders += 1

        return new_members, new_orders

    def get_event_form_orders(self, form: EventForm, since: datetime | None = None) -> int:
        result = self._call(
            self._commandes.organizations_organization_slug_forms_form_type_form_slug_orders_get,
            organization_slug=self.organization_slug,
            form_slug=form.form_slug,
            form_type=form.form_type,
            var_from=since,
            page_size=100,
        )
        new_registrations = 0
        with transaction.atomic():
            for i in result.data or []:
                order, _ = EventFormOrder.objects.get_or_create(
                    order_id=i.id,
                    defaults={
                        "form": form,
                        "payer_email": i.payer.email if i.payer else None,
                        "payer_first_name": i.payer.first_name if i.payer else None,
                        "payer_last_name": i.payer.last_name if i.payer else None,
                        "created_at": i.meta.created_at if i.meta else None,
                        "updated_at": i.meta.updated_at if i.meta else None,
                    }
                )
                for item in i.items or []:
                    if item.name is None:
                        logger.warning("Skipping item item_id=%s (name is None) for event '%s' (slug=%s) order_id=%s", item.id, form.title, form.form_slug, i.id)
                        continue
                    _, created = EventRegistration.objects.update_or_create(
                        item_id=item.id,
                        defaults={
                            "order": order,
                            "name": item.name,
                            "first_name": item.user.first_name if item.user else None,
                            "last_name": item.user.last_name if item.user else None,
                            "state": item.state if item.state else EventRegistration.State.UNKNOWN,
                        }
                    )
                    if created:
                        new_registrations += 1
            form.last_registration_updated = timezone.now()
            form.save(update_fields=["last_registration_updated"])
        return new_registrations

    def create_event_form(self, data: dict) -> None:
        place = None
        if data.get('place'):
            place = HelloAssoApiV5ModelsCommonPlaceModel(
                address=data['place'],
                country='FRA',
            )
        body = HelloAssoApiV5ModelsFormsFormQuickCreateRequest(
            title=data['title'],
            description=data.get('description') or None,
            long_description=data.get('long_description') or None,
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            max_entries=data.get('max_entries'),
            place=place,
        )
        self._call(
            self._formulaires.organizations_organization_slug_forms_form_type_action_quick_create_post,
            organization_slug=self.organization_slug,
            form_type='Event',
            hello_asso_api_v5_models_forms_form_quick_create_request=body,
        )

    def fetch_membership_form_members(self, form: MemberShipForm) -> list[dict]:
        """Fetch all members for a membership form without saving to DB."""
        members = []
        continuation_token = None
        while True:
            result = self._call(
                self._commandes.organizations_organization_slug_forms_form_type_form_slug_orders_get,
                organization_slug=self.organization_slug,
                form_slug=form.form_slug,
                form_type=form.form_type,
                page_size=100,
                with_details=True,
                continuation_token=continuation_token,
            )
            page_data = result.data or []
            for order in page_data:
                for item in order.items or []:
                    custom = {f.name: f.answer for f in (item.custom_fields or [])}
                    members.append({
                        'id': item.id,
                        'category': item.name,
                        'first_name': item.user.first_name if item.user else None,
                        'last_name': item.user.last_name if item.user else None,
                        'email': custom.get(FIELD_EMAIL),
                        'birthdate': custom.get(FIELD_BIRTHDATE),
                        'sex': custom.get(FIELD_SEX),
                        'licence_number': custom.get(FIELD_LICENCE),
                        'payer_email': order.payer.email if order.payer else None,
                        'custom_fields': custom,
                    })
            next_token = result.pagination.continuation_token if result.pagination else None
            if not next_token or next_token == continuation_token or not page_data:
                break
            continuation_token = next_token
        return members

    def get_available_custom_fields(self, form: MemberShipForm, page_size: int = 20) -> list[str]:
        """Return the unique custom field names found across the first page of orders."""
        result = self._call(
            self._commandes.organizations_organization_slug_forms_form_type_form_slug_orders_get,
            organization_slug=self.organization_slug,
            form_slug=form.form_slug,
            form_type=form.form_type,
            page_size=page_size,
            with_details=True,
        )
        seen: set[str] = set()
        for order in result.data or []:
            for item in order.items or []:
                for f in item.custom_fields or []:
                    seen.add(f.name)
        return list(seen)


_hello_asso_api_instance: HelloAssoApi | None = None


def init_hello_asso_api() -> None:
    global _hello_asso_api_instance
    _hello_asso_api_instance = HelloAssoApi()


def get_hello_asso_api() -> HelloAssoApi:
    if _hello_asso_api_instance is None:
        raise RuntimeError("HelloAssoApi n'a pas été initialisé (appeler init_hello_asso_api() au démarrage)")
    return _hello_asso_api_instance
