from django.db import models

class MemberShipForm(models.Model):
    form_slug = models.CharField(primary_key=True)
    title = models.CharField()
    form_type = models.CharField()
    description = models.CharField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()

    def __str__(self):
        return self.form_slug
    

class MemberShipFormOrder(models.Model):
    order_id = models.IntegerField(primary_key=True)
    form = models.ForeignKey(MemberShipForm, on_delete=models.CASCADE)
    payer_email = models.CharField()
    payer_first_name = models.CharField()
    payer_last_name = models.CharField()
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()


class Member(models.Model):
    member_id = models.IntegerField(primary_key=True)
    order = models.ForeignKey(MemberShipFormOrder, on_delete=models.CASCADE)
    category = models.CharField()
    first_name = models.CharField()
    last_name = models.CharField()
    birhdate = models.DateField()
    email = models.CharField()
    licence_number = models.CharField(blank=True, default='')
    sex = models.CharField()
    caci_expiration = models.DateField(null=True)