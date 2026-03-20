import requests
import json
import logging
from pathlib import Path
from helloasso_api import HaApiV5
from dotenv import load_dotenv
from jsonschema import validate, ValidationError
import os
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder, Member, EventForm, EventFormOrder, EventRegistration
from datetime import datetime
import helloasso_python

_schema_dir = Path(__file__).parent
with open(_schema_dir / "event_form_schema.json") as f:
    EVENT_FORM_SCHEMA = json.load(f)
with open(_schema_dir / "membership_form_schema.json") as f:
    MEMBERSHIP_FORM_SCHEMA = json.load(f)
with open(_schema_dir / "event_form_order_schema.json") as f:
    EVENT_FORM_ORDER_SCHEMA = json.load(f)

logger = logging.getLogger(__name__)


class HelloAssoApiError(Exception):
    pass


class HelloAssoApi:
    BASE_URL = "https://api.helloasso.com/v5"  


    def __init__(self,):
        load_dotenv()
        client_id = os.getenv("HELLO_ASSO_API_CLIENT_ID")
        client_secret = os.getenv("HELLO_ASSO_API_CLIENT_SECRET")
        
        self.organization_slug = os.getenv("ORGANIZATION_SLUG")
        
        if not client_id or not client_secret or not self.organization_slug:
            raise Exception("missing credentials")
        
        # LEGACY
        self.hello_asso_api = HaApiV5(
            api_base='api.helloasso.com',
            client_id=client_id,
            client_secret=client_secret,
            timeout=60
        )

        self.token = self.get_access_token(client_id, client_secret)
        self.hello_asso_api_2 = helloasso_python.Configuration(client_id=client_id, client_secret=client_secret)

    def get_access_token(self):
        token = client.fetch_token(token_url, grant_type='client_credentials')
        print("Access Token:", token['access_token'])
        print("Expires In:", token['expires_in'])
        print("Refresh Token:", token['refresh_token'])
        return token

    def refresh_membership_forms(self,) -> None:
        url = f"/v5/organizations/{self.organization_slug}/forms"
        params = {
            "formTypes": ["Membership"],
            "states": ["Public", "Private"]
        }
        raw_result = self.hello_asso_api.call(url, method="GET", params=params)
        for i in self.check_form_data_format(raw_result, MEMBERSHIP_FORM_SCHEMA):
            new_form = MemberShipForm(
                form_slug = i["formSlug"],
                title = i["title"],
                form_type = i["formType"],
                description = i["description"],
                start_date = i["startDate"],
                end_date = i["endDate"],
                updated_at = i["meta"]["updatedAt"],
                created_at = i["meta"]["createdAt"],
            )
            new_form.save()

    def check_form_data_format(self, raw_result, schema: dict) -> list:
        if not raw_result.ok:
            msg = f"Erreur API HelloAsso ({raw_result.status_code})"
            logger.error("%s: %s", msg, raw_result.text)
            raise HelloAssoApiError(msg)
        try:
            body = raw_result.json()
        except ValueError:
            msg = "La réponse de l'API HelloAsso n'est pas un JSON valide"
            logger.error(msg)
            raise HelloAssoApiError(msg)
        try:
            validate(instance=body, schema=schema)
        except ValidationError as e:
            msg = "Le format de la réponse HelloAsso est invalide"
            logger.error("%s: %s", msg, e.message)
            raise HelloAssoApiError(msg)
        return body.get("data", [])

    def refresh_event_forms(self,) -> None:
        url = f"/v5/organizations/{self.organization_slug}/forms"
        params = {
            "formTypes": ["Event"],
            "states": ["Public", "Private"],
            "pageSize": 100
        }
        raw_result = self.hello_asso_api.call(url, method="GET", params=params)
        for i in self.check_form_data_format(raw_result, EVENT_FORM_SCHEMA):
            new_form = EventForm(
                form_slug = i["formSlug"],
                title = i["title"],
                form_type = i["formType"],
                description = i["description"],
                start_date = i["startDate"],
                end_date = i["endDate"],
                last_registration_updated = None,
                updated_at = i["meta"]["updatedAt"],
                created_at = i["meta"]["createdAt"],
            )
            new_form.save()

    def get_member_registry(self, order: MemberShipFormOrder):
        url = f"/v5/orders/{order.order_id}"
        raw_result = self.hello_asso_api.call(url, method="GET")
        for i in raw_result.json()["items"]:
            birthdate = next(
                (field["answer"] for field in i.get("customFields", []) if field.get("name") == "Date de naissance"),
                None  )
            if birthdate:
                birthdate = datetime.strptime(birthdate, "%d/%m/%Y")
            email = next(
                (field["answer"] for field in i.get("customFields", []) if field.get("name") == "Adresse Mail"),
                None  )
            licence_number = next(
                (field["answer"] for field in i.get("customFields", []) if field.get("name") == "Numéro de licence"),
                ''  )
            sex = next(
                (field["answer"] for field in i.get("customFields", []) if field.get("name") == "Sexe"),
                None  )
            new_member = Member(
                member_id = i["id"],
                order = order,
                category = i["name"],
                first_name = i["user"]["firstName"],
                last_name = i["user"]["lastName"],
                birhdate = birthdate,
                licence_number= licence_number,
                sex = sex,
                email = email,
                caci_expiration = None
            )
            new_member.save()


    def get_event_form_orders(self, form: EventForm):
        url = f"/v5/organizations/{self.organization_slug}/forms/{form.form_type}/{form.form_slug}/orders"
        raw_result = self.hello_asso_api.call(url, method="GET")
        for i in self.check_form_data_format(raw_result, EVENT_FORM_ORDER_SCHEMA):
            order, _ = EventFormOrder.objects.get_or_create(
                order_id=i["id"],
                defaults={
                    "form": form,
                    "payer_email": i["payer"]["email"],
                    "payer_first_name": i["payer"]["firstName"],
                    "payer_last_name": i["payer"]["lastName"],
                    "created_at": i["meta"]["createdAt"],
                    "updated_at": i["meta"]["updatedAt"],
                }
            )
            for item in i.get("items", []):
                EventRegistration.objects.get_or_create(
                    item_id=item["id"],
                    defaults={
                        "order": order,
                        "name": item["name"],
                        "first_name": item["user"]["firstName"],
                        "last_name": item["user"]["lastName"],
                    }
                )
        form.last_registration_updated = datetime.now()
        form.save(update_fields=["last_registration_updated"])

    def refresh_all_membership_forms_registry(self,):
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


