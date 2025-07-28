from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from common.api.helloAssoApi import HelloAssoApi
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder
from django.views.generic import ListView

class MemberShipFormListView(ListView):
    model = MemberShipForm
    template_name = 'forms.html'

class MemberShipFormOrderListView(ListView):
    model = MemberShipFormOrder
    template_name = 'forms.html'

def index(request):
    hello_asso_api = HelloAssoApi()
    hello_asso_api.refresh_membership_forms()
    hello_asso_api.refresh_all_membership_forms_registry()
    return HttpResponse(f"Hello, world. You're at the polls index.")