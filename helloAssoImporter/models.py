from django.db import models


class Season(models.Model):
    label = models.CharField(max_length=20)
    current = models.BooleanField(default=False)

    def __str__(self):
        return self.label

    class Meta:
        verbose_name = 'Saison'
        verbose_name_plural = 'Saisons'


class MemberShipForm(models.Model):
    form_slug = models.CharField(primary_key=True)
    title = models.CharField()
    form_type = models.CharField()
    description = models.CharField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()
    season = models.OneToOneField(Season, null=True, blank=True, on_delete=models.SET_NULL)
    field_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Associe les champs standardisés (définis dans helloAssoApi.LEVEL_FIELD_LABELS) aux noms de champs HelloAsso de ce formulaire.",
    )

    def __str__(self):
        return self.form_slug
    

class EventForm(models.Model):
    form_slug = models.CharField(primary_key=True)
    title = models.CharField()
    form_type = models.CharField()
    description = models.CharField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    last_registration_updated = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()

    def __str__(self):
        return self.form_slug


class EventFormOrder(models.Model):
    order_id = models.IntegerField(primary_key=True)
    form = models.ForeignKey(EventForm, on_delete=models.CASCADE)
    payer_email = models.CharField(null=True)
    payer_first_name = models.CharField(null=True)
    payer_last_name = models.CharField(null=True)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.order_id)


class EventRegistration(models.Model):

    class State(models.TextChoices):
        WAITING = 'Waiting', 'En attente'
        PROCESSED = 'Processed', 'Traité'
        REGISTERED = 'Registered', 'Inscrit'
        DELETED = 'Deleted', 'Supprimé'
        REFUNDED = 'Refunded', 'Remboursé'
        CANCELED = 'Canceled', 'Annulé'
        REFUSED = 'Refused', 'Refusé'
        CONTESTED = 'Contested', 'Contesté'
        ABANDONED = 'Abandoned', 'Abandonné'
        UNKNOWN = 'Unknown', 'Inconnu'

    item_id = models.IntegerField(primary_key=True)
    order = models.ForeignKey(EventFormOrder, on_delete=models.CASCADE)
    name = models.CharField()
    first_name = models.CharField()
    last_name = models.CharField()
    state = models.CharField(max_length=20, choices=State.choices, default=State.UNKNOWN)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Member(models.Model):
    email = models.CharField()
    first_name = models.CharField()
    last_name = models.CharField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'first_name', 'last_name'],
                name='unique_member_identity',
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"


class MemberShipFormOrder(models.Model):
    item_id = models.IntegerField(primary_key=True)
    order_id = models.IntegerField(db_index=True)
    form = models.ForeignKey(MemberShipForm, on_delete=models.CASCADE)
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL)
    payer_email = models.CharField()
    payer_first_name = models.CharField()
    payer_last_name = models.CharField()
    category = models.CharField(null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    licence_number = models.CharField(blank=True, default='')
    sex = models.CharField(null=True, blank=True)
    caci_expiration = models.DateField(null=True, blank=True)
    dive_level = models.CharField(blank=True, default='')
    dive_teaching_level = models.CharField(blank=True, default='')
    apnea_level = models.CharField(blank=True, default='')
    apnea_teaching_level = models.CharField(blank=True, default='')
    underwater_shooting_level = models.CharField(blank=True, default='')
    underwater_shooting_teaching_level = models.CharField(blank=True, default='')
    updated_at = models.DateTimeField()
    created_at = models.DateTimeField()

    def __str__(self):
        return str(self.item_id)