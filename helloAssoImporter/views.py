from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from common.api.helloAssoApi import HelloAssoApi

def index(request):
    hello_asso_api = HelloAssoApi()
    hello_asso_api.refresh_member_ship_forms()
    return HttpResponse(f"Hello, world. You're at the polls index.")