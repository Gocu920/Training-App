import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from training_app.models import TrainingType, Training
from faker import Faker

class Command(BaseCommand):
    help = 'Generate data for coaches, competitors, and trainings'

    def random_date(self, start, end):
        """
        This function will return a random datetime between two datetime
        objects.
        """
        delta = end - start
        int_delta = delta.days
        random_day = random.randrange(int_delta)
        return start + timedelta(days=random_day)

    def handle(self, *args, **kwargs):
        User = get_user_model()
        fake = Faker()

        # Tworzenie typów treningów
        training_types = ['threshold', 'intervals', 'recovery', 'functional', 'strength', 'general']
        for t in training_types:
            TrainingType.objects.get_or_create(training_type=t)

        # Definicje trenerów (generowanie realistycznych imion i nazwisk)
        coaches_info = [(fake.unique.user_name(), fake.first_name(), fake.last_name()) for _ in range(3)]

        # Tworzenie trenerów
        coaches = []
        for username, name, surname in coaches_info:
            coach, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'password': 'password',
                    'name': name,
                    'surname': surname,
                    'role': 'coach'
                }
            )
            coaches.append(coach)

        # Linki do plików GPX
        gpx_urls = [
            "https://api.sports-tracker.com/apiserver/v1/workouts/export/AHe6PrQAj2_QhFdybGOwkD8M8-pHst2VHz6j4ARafaOPtIt6xvK6jNqTtnkAjYXEyw==?brand=SUUNTOAPP",
            "https://api.sports-tracker.com/apiserver/v1/workouts/export/AGkEPn_Zibm7jnEWOZHT4AfUtCvEbPRbov7SPeBGyNjvzIpZhFYRPLtLROyjcJBGQw==?brand=SUUNTOAPP",
            "https://api.sports-tracker.com/apiserver/v1/workouts/export/AP21PmECxT-FCzq7D_hRhz1KGALeH1RQ_D6QRcFegByqTmMbMBbX-vOIOwgQSfKARw==?brand=SUUNTOAPP",
            "https://api.sports-tracker.com/apiserver/v1/workouts/export/AF52Y9dGaYPeF4PihWoS_8hKrRBtefOrBXxqtqLnKe47X_TddSsT74iGvnceM6wW3g==?brand=SUUNTOAPP"
        ]

        feeling_choices = {
            '1': 'Bardzo źle',
            '2': 'Źle',
            '3': 'Neutralnie',
            '4': 'Dobrze',
            '5': 'Bardzo dobrze',
            '6': 'Perfekcyjnie'
        }

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = timezone.now()

        # Generowanie zawodników i treningów
        for i in range(1, 31):
            name = fake.first_name()
            surname = fake.last_name()
            competitor = User.objects.create_user(
                username=f'zawodnik{i}',
                password='password',
                name=name,
                surname=surname,
                role='competitor'
            )
            coach = random.choice(coaches)
            coach.competitors.add(competitor)
            # Generowanie 5 treningów dla każdego zawodnika
            for k in range(5):
                training_type = TrainingType.objects.order_by('?').first()
                gpx_url = random.choice(gpx_urls)
                training_date = self.random_date(start_date, end_date)
                feeling_number = str(random.randint(1, 6))
                selected_feeling = feeling_choices.get(feeling_number, 'Neutralnie')
                Training.objects.create(
                    training_type=training_type,
                    date=training_date.date(),
                    training_description=f'Opis treningu {k+1} dla zawodnika {competitor.name} {competitor.surname}',
                    gpx_url=gpx_url,
                    coach=coach,
                    competitor=competitor,
                    feeling=selected_feeling,
                    coach_comment=f'Komentarz trenera {coach.name} {coach.surname} do treningu {k+1}'
                )
            coach.save()

        self.stdout.write(self.style.SUCCESS('Dane zostały wygenerowane.'))
