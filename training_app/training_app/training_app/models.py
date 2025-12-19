from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, Group, Permission


class User(AbstractUser):
    ROLA_CHOICES = (
        ('competitor', 'Zawodnik'),
        ('coach', 'Trener'),
    )
    name = models.CharField(_('Imię'), max_length=256, blank=True, null=True)
    surname = models.CharField(_('Nazwisko'), max_length=256, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLA_CHOICES)
    sport_discipline = models.CharField(_('Dyscyplina sportu'), max_length=256, blank=True, null=True)
    user_permissions = models.ManyToManyField(Permission, related_name='training_app_user_permissions')
    competitors = models.ManyToManyField('self', symmetrical=False, related_name='coaches', blank=True)

    def __str__(self):
        return f"{self.name} {self.surname} - {self.get_role_display()}"

    def get_full_name(self) -> str:
        full_name = f"{self.name} {self.surname}"
        return full_name.strip()


class TrainingType(models.Model):
    TRAINING_CHOICES = (
        ('threshold', 'Trening progowy'),
        ('intervals', 'Interwały'),
        ('recovery', 'Trening regeneracyjny'),
        ('functional', 'Trening funkcjonalny'),
        ('strength', 'Trening siłowy'),
        ('general', 'Trening ogólnorozwojowy'),
    )
    training_type = models.CharField(max_length=30, choices=TRAINING_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.get_training_type_display()


class Training(models.Model):
    training_type = models.ForeignKey(TrainingType, on_delete=models.CASCADE, related_name="type_trainings")
    date = models.DateField(_('Data treningu'), blank=True, null=True)
    training_description = models.CharField(_('Opis treningu'), max_length=1000, blank=True, null=True)
    gpx_url = models.URLField(_('Link do pliku GPX'), max_length=200, blank=True, null=True)
    coach = models.ForeignKey(User, on_delete=models.SET_NULL, limit_choices_to={'role': 'coach'}, related_name='coached_trainings', null=True, blank=True)
    competitor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'competitor'}, related_name='participated_trainings')
    feeling = models.TextField(_('Odczucia zawodnika'), blank=True, null=True)
    coach_comment = models.TextField(_('Komentarz trenera'), blank=True, null=True)

    def __str__(self):
        return f"Training on {self.date} - {self.training_type}"


class Diet(models.Model):
    training_type = models.ForeignKey(TrainingType, on_delete=models.CASCADE, related_name='diet_suggestions')
    diet_suggestions = models.TextField(_('Sugestie żywieniowe'), blank=True, null=True)

    def __str__(self):
        return f"Diet for {self.training_type}"
