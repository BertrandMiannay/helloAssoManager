from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from common.api.helloAssoApi import HelloAssoApi
from helloAssoImporter.models import MemberShipForm, MemberShipFormOrder
from django.views.generic import ListView


class MemberShipFormListView(LoginRequiredMixin, ListView):
    model = MemberShipForm
    template_name = 'forms.html'


class MemberShipFormOrderListView(LoginRequiredMixin, ListView):
    model = MemberShipFormOrder
    template_name = 'forms.html'


@login_required
def index(request):
    hello_asso_api = HelloAssoApi()
    #hello_asso_api.refresh_membership_forms()
    #hello_asso_api.refresh_all_membership_forms_registry()
    return HttpResponse(f"Hello, world. You're at the polls index.")
