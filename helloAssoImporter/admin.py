from django.contrib import admin

# Register your models here.
from .models import MemberShipForm, MemberShipFormOrder, Member
admin.site.register(MemberShipForm)
admin.site.register(MemberShipFormOrder)
admin.site.register(Member)