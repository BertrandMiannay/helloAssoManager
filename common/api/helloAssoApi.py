import requests
from helloasso_api import HaApiV5
from dotenv import load_dotenv
import os
from helloAssoImporter.models import MemberShipForm



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
        


    def refresh_member_ship_forms(self,):
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
                description = i["description"],
                start_date = i["startDate"],
                end_date = i["endDate"],
                updated_at = i["meta"]["updatedAt"],
                created_at = i["meta"]["createdAt"],
            )
            new_form.save()
            

