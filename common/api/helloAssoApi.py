import requests
from helloasso_api import HaApiV5
from dotenv import load_dotenv
import os
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder, Member
from datetime import datetime


class HelloAssoApi:
    BASE_URL = "https://api.helloasso.com/v5"  


    def __init__(self,):
        load_dotenv()
        client_id = os.getenv("HELLO_ASSO_API_CLIENT_ID")
        client_secret = os.getenv("HELLO_ASSO_API_CLIENT_SECRET")
        
        self.organization_slug = os.getenv("ORGANIZATION_SLUG")
        
        if not client_id or not client_secret or not self.organization_slug:
            raise Exception("missing credentials")
        
        self.hello_asso_api = HaApiV5(
            api_base='api.helloasso.com',
            client_id=client_id,
            client_secret=client_secret,
            timeout=60
        )


    def refresh_membership_forms(self,) -> None:
        url = f"/v5/organizations/{self.organization_slug}/forms"
        params = {
            "formTypes": ["Membership"],
            "states": ["Public", "Private"]
        }
        raw_result = self.hello_asso_api.call(url, method="GET", params=params)
        for i in (raw_result.json()["data"]):
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


    def get_form_orders(self, form: MemberShipForm):
        url = f"/v5/organizations/{self.organization_slug}/forms/{form.form_type}/{form.form_slug}/orders"
        raw_result = self.hello_asso_api.call(url, method="GET")
        for i in raw_result.json()["data"]:
            new_form_order = MemberShipFormOrder(
                order_id = i["id"],
                form = form,
                payer_email = i["payer"]["email"],
                payer_first_name = i["payer"]["firstName"],
                payer_last_name = i["payer"]["lastName"],
                updated_at = i["meta"]["updatedAt"],
                created_at = i["meta"]["createdAt"],
            )
            new_form_order.save()
            self.get_member_registry(new_form_order)

    def refresh_all_membership_forms_registry(self,):
        all_forms = MemberShipForm.objects.all()
        for form in all_forms:
            self.get_form_orders(form)