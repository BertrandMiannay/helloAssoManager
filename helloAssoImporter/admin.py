from django.contrib import admin

# Register your models here.
from .models import Season, MemberShipForm, MemberShipFormOrder, Member, EventForm, EventFormOrder, EventRegistration
admin.site.register(Season)
admin.site.register(MemberShipForm)
admin.site.register(MemberShipFormOrder)
admin.site.register(EventForm)
admin.site.register(Member)
admin.site.register(EventFormOrder)
admin.site.register(EventRegistration)

