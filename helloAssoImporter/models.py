from django.db import models

# Create your models here.
class MemberShipForm(models.Model):
    form_slug = models.CharField(primary_key=True)
    title = models.CharField()
    description = models.CharField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()

    def __str__(self):
        return self.form_slug