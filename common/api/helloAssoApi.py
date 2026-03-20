import logging
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import helloasso_python
from helloasso_python.api.formulaires_api import FormulairesApi
from helloasso_python.api.commandes_api import CommandesApi
from helloasso_python.api_client import ApiClient
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder, Member, EventForm, EventFormOrder, EventRegistration

logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.helloasso.com/oauth2/token"


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

    def refresh_membership_forms(self) -> None:
        result = self._formulaires.organizations_organization_slug_forms_get(
            organization_slug=self.organization_slug,
            form_types=["Membership"],
            states=["Public", "Private"],
        )
        for i in result.data or []:
            new_form = MemberShipForm(
                form_slug=i.form_slug,
                title=i.title,
                form_type=i.form_type,
                description=i.description,
                start_date=i.start_date,
                end_date=i.end_date,
                updated_at=i.meta.updated_at if i.meta else None,
                created_at=i.meta.created_at if i.meta else None,
            )
            new_form.save()

    def refresh_event_forms(self) -> int:
        result = self._formulaires.organizations_organization_slug_forms_get(
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

    def get_member_registry(self, order: MemberShipFormOrder) -> None:
        result = self._commandes.orders_order_id_get(order_id=order.order_id)
        for i in result.items or []:
            custom = {f.name: f.answer for f in (i.custom_fields or [])}
            birthdate = custom.get("Date de naissance")
            if birthdate:
                birthdate = datetime.strptime(birthdate, "%d/%m/%Y")
            new_member = Member(
                member_id=i.id,
                order=order,
                category=i.name,
                first_name=i.user.first_name if i.user else None,
                last_name=i.user.last_name if i.user else None,
                birhdate=birthdate,
                licence_number=custom.get("Numéro de licence", ""),
                sex=custom.get("Sexe"),
                email=custom.get("Adresse Mail"),
                caci_expiration=None,
            )
            new_member.save()

    def get_event_form_orders(self, form: EventForm, since: datetime | None = None) -> int:
        result = self._commandes.organizations_organization_slug_forms_form_type_form_slug_orders_get(
            organization_slug=self.organization_slug,
            form_slug=form.form_slug,
            form_type=form.form_type,
            var_from=since,
        )
        new_registrations = 0
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
                _, created = EventRegistration.objects.get_or_create(
                    item_id=item.id,
                    defaults={
                        "order": order,
                        "name": item.name,
                        "first_name": item.user.first_name if item.user else None,
                        "last_name": item.user.last_name if item.user else None,
                    }
                )
                if created:
                    new_registrations += 1
        form.last_registration_updated = datetime.now()
        form.save(update_fields=["last_registration_updated"])
        return new_registrations

    def refresh_all_membership_forms_registry(self) -> None:
        all_forms = MemberShipForm.objects.all()
        for form in all_forms:
            self.get_form_orders(form)


_hello_asso_api_instance: HelloAssoApi | None = None


def init_hello_asso_api() -> None:
    global _hello_asso_api_instance
    _hello_asso_api_instance = HelloAssoApi()


def get_hello_asso_api() -> HelloAssoApi:
    if _hello_asso_api_instance is None:
        raise RuntimeError("HelloAssoApi n'a pas été initialisé (appeler init_hello_asso_api() au démarrage)")
    return _hello_asso_api_instance
