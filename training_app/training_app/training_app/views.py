import requests
import xml.etree.ElementTree as ET
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models import ColumnDataSource, Range1d
import numpy as np
from django.contrib.auth.views import LogoutView
from .forms import UserRegistrationForm
from .models import User, Training, TrainingType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
from django.db.models import Min, Max
from django.shortcuts import render, get_object_or_404
from bokeh.models import HoverTool

class RegisterView(FormView):
    template_name = 'register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Registration successful. You are now registrated.')
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return self.render_to_response(self.get_context_data(form=form))

class LoginView(FormView):
    template_name = 'login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
            if user.role == 'competitor':
                return redirect('zawodnik')
            elif user.role == 'coach':
                return redirect('trener')
        else:
            messages.error(self.request, 'Invalid username or password')
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return self.render_to_response(self.get_context_data(form=form))
    
class CustomLogoutView(LogoutView):
    next_page = 'login'

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

def calculate_time_in_zones(heart_rates, zones_boundaries):
    zone_times = [0] * (len(zones_boundaries) + 1)
    for hr in heart_rates:
        for i, boundary in enumerate(zones_boundaries):
            if hr < boundary:
                zone_times[i] += 1
                break
        else:
            zone_times[-1] += 1
    return zone_times

def create_zone_time_chart(zone_times, zones_boundaries):
    colors = ['blue', 'green', '#FFD700', 'orange', 'red', 'purple']
    zone_labels = ['1', '2', '3', '4', '5']
    
    # sekundy na minuty
    zone_times_in_minutes = [time / 60 for time in zone_times]
    
    source = ColumnDataSource(data=dict(zones=zone_labels, times=zone_times_in_minutes, colors=colors))

    p = figure(x_range=zone_labels, title="Czas spędzony w strefach tętna",height = 400, toolbar_location=None, tools="")
    p.vbar(x='zones', top='times', width=0.9, color='colors', source=source)
    hover = HoverTool(
            tooltips=[
                ("Strefa", "@zones"),
                ("Czas", "@times min"),
            ]
    )
    p.add_tools(hover)

    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.xaxis.axis_label = "Strefy tętna"
    p.yaxis.axis_label = "Czas [min]"

    return p


class ZawodnikView(View):

    def get(self, request):
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        training_type_filter = request.GET.get('training_type_filter')

        athlete_trainings = Training.objects.filter(competitor=request.user).order_by('-date')

        if date_from and date_from.lower() != 'none':
            athlete_trainings = athlete_trainings.filter(date__gte=date_from)
        if date_to and date_to.lower() != 'none':
            athlete_trainings = athlete_trainings.filter(date__lte=date_to)
        if training_type_filter and training_type_filter.lower() != 'none':
            athlete_trainings = athlete_trainings.filter(training_type_id=training_type_filter)

        paginator = Paginator(athlete_trainings, 5)  
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'available_training_types': TrainingType.objects.all(),
            'available_coaches': User.objects.filter(role='coach'),
            'competitor': request.user,
            'athlete_trainings': page_obj,
            'date_from': date_from,
            'date_to': date_to,
            'training_type_filter': training_type_filter
        }

        if 'download_csv' in request.GET:
            return self.generate_csv_report(athlete_trainings, training_type_filter, date_from, date_to)

        return render(request, 'zawodnik.html', context)

    def generate_csv_report(self, athlete_trainings, training_type_filter, date_from, date_to):
        response = HttpResponse(content_type='text/csv; charset=utf-8') 
        filename = 'training_report_'
        response.write('\ufeff'.encode('utf8'))

        if training_type_filter and training_type_filter.lower() != 'none':
            training_type = TrainingType.objects.filter(id=training_type_filter).first()
            if training_type:
                filename += f'{training_type.training_type}_'

        if (date_from and date_from.lower() != 'none') and (date_to and date_to.lower() != 'none'):
            filename += f'{date_from}_{date_to}.csv'
        else:
            min_date = Training.objects.filter(competitor=self.request.user).aggregate(Min('date'))['date__min']
            max_date = Training.objects.filter(competitor=self.request.user).aggregate(Max('date'))['date__max']
            if not date_from or date_from.lower() == 'none':
                date_from = min_date
            if not date_to or date_to.lower() == 'none':
                date_to = max_date
            filename += 'all.csv'

        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Data', 'Rodzaj treningu', 'Opis', 'Link do GPX', 'Odczucia', 'Trener'])

        for training in athlete_trainings:
            writer.writerow([
                training.date,
                training.training_type.training_type if training.training_type else 'Brak',
                training.training_description if training.training_description else '',
                training.gpx_url if training.gpx_url else '',
                training.feeling if training.feeling else '',
                training.coach.get_full_name() if training.coach else 'Brak'
            ])

        return response

    def post(self, request):
        action = request.POST.get('action')
        gpx_url = request.POST.get("gpx_url")
        age = int(request.POST.get("age", 0))
        training_type_id = request.POST.get("training_type")
        feeling_number = request.POST.get("feeling_number")
        feeling_choices = {
            '1': 'Bardzo źle',
            '2': 'Źle',
            '3': 'Neutralnie',
            '4': 'Dobrze',
            '5': 'Bardzo dobrze',
            '6': 'Perfekcyjnie'
        }
        selected_feeling = feeling_choices.get(feeling_number, 'neutral')
        available_training_types = TrainingType.objects.all()
        available_coaches = User.objects.filter(role='coach')
        athlete_trainings = Training.objects.filter(competitor=request.user).order_by('-date')

        if action == 'load':
            response = requests.get(gpx_url)
            if response.status_code == 200:
                gpx_data = response.content
                root = ET.fromstring(gpx_data)
                namespaces = {
                    'gpx': 'http://www.topografix.com/GPX/1/1',
                    'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
                }
                heart_rates = []
                for trkpt in root.findall('.//gpx:trkpt', namespaces):
                    hr = trkpt.find('.//gpxtpx:hr', namespaces)
                    if hr is not None:
                        heart_rates.append(int(hr.text))

                avg_hr = round(sum(heart_rates) / len(heart_rates)) if heart_rates else 0
                actual_max_hr = max(heart_rates) if heart_rates else 0
                request.session['avg_hr'] = avg_hr
                request.session['actual_max_hr'] = actual_max_hr
                request.session['heart_rates'] = heart_rates
                request.session['age'] = age

                time_indices = np.arange(len(heart_rates)) / 60
                max_hr = max(heart_rates) if heart_rates else 0
                min_hr = min(heart_rates) if heart_rates else 0

                y_range = Range1d(start=min_hr, end=max_hr)
                plot_line = figure(title='Tętno w czasie z podziałem na strefy', x_axis_label='Czas[min]', y_axis_label='Tętno [bpm]',
                                   sizing_mode='stretch_width', height=400, y_range=y_range)
                
                hover = HoverTool(
                    tooltips=[
                        ("Czas", "$x{0.2f} min"),
                        ("Tętno", "$y bpm"),
                    ],
                    mode='vline'
                )
                plot_line.add_tools(hover)

                theoretical_max_hr = 200
                start_index = 0
                colors = ['blue', 'green', '#FFD700', 'orange', 'red']
                zones_boundaries = [theoretical_max_hr * 0.6, theoretical_max_hr * 0.7, theoretical_max_hr * 0.8, theoretical_max_hr * 0.9]
                for i, hr in enumerate(heart_rates):
                    zone = next((z for z, boundary in enumerate(zones_boundaries) if hr < boundary), len(zones_boundaries) - 1)
                    if i + 1 == len(heart_rates) or zone != next((z for z, boundary in enumerate(zones_boundaries) if heart_rates[i + 1] < boundary), len(zones_boundaries) - 1):
                        plot_line.line(time_indices[start_index:i + 1], heart_rates[start_index:i + 1], line_width=2, color=colors[zone])
                        start_index = i + 1

                script_line, div_line = components(plot_line)

                zone_times = calculate_time_in_zones(heart_rates, zones_boundaries)
                plot_bar = create_zone_time_chart(zone_times, zones_boundaries)
                script_bar, div_bar = components(plot_bar)

                context = {
                    'max_hr': max_hr,
                    'avg_hr': avg_hr,
                    'actual_max_hr': actual_max_hr,
                    'script_line': script_line,
                    'div_line': div_line,
                    'script_bar': script_bar,
                    'div_bar': div_bar,
                    'zone_times': zone_times,
                    'zones_boundaries': zones_boundaries,
                    'cdn_js': CDN.js_files,
                    'cdn_css': CDN.css_files,
                    'coach': User.objects.get(pk=request.POST.get('coach')) if request.POST.get('coach') else None,
                    'competitor': request.user,
                    'date': request.POST.get("training_date"),
                    'comment': request.POST.get("training_comment"),
                    'gpx_url': gpx_url,
                    'feeling_number': feeling_number,
                    'available_training_types': TrainingType.objects.all(),
                    'available_coaches': User.objects.filter(role='coach'),
                    'athlete_trainings': athlete_trainings,
                }
                if training_type_id:
                    context['training_type'] = TrainingType.objects.get(pk=training_type_id).training_type
                
                paginator = Paginator(athlete_trainings, 5)  
                page_number = request.GET.get('page', 1)
                page_obj = paginator.get_page(page_number)
                context.update({
                    'athlete_trainings': page_obj,
                })
                return render(request, 'zawodnik.html', context)

        elif action == 'save':
            competitor = request.user
            training_type_instance = TrainingType.objects.get(pk=training_type_id) if training_type_id else None
            coach_id = request.POST.get('coach', None)
            coach_instance = User.objects.get(pk=coach_id) if coach_id else None
            

            Training.objects.create(
                training_type=training_type_instance,
                date=request.POST.get("training_date"),
                training_description=request.POST.get("training_comment"),
                coach=coach_instance,
                competitor=competitor,
                gpx_url=gpx_url,
                feeling=selected_feeling
            )
            return redirect('zawodnik') 

        context = {
            'available_training_types': available_training_types,
            'available_coaches': available_coaches,
            'athlete_trainings': athlete_trainings,
            'competitor': request.user,  
        }

        paginator = Paginator(athlete_trainings, 5)  
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        context.update({
            'athlete_trainings': page_obj,
        })

        return render(request, 'zawodnik.html', context)

class TrenerView(View):
    def get(self, request):
        coach = request.user
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        training_type_filter = request.GET.get('training_type_filter')
        competitor_filter = request.GET.get('competitor_filter')

        trainings = Training.objects.filter(coach=coach).order_by('-date')

        if date_from and date_from.lower() != 'none':
            trainings = trainings.filter(date__gte=date_from)
        if date_to and date_to.lower() != 'none':
            trainings = trainings.filter(date__lte=date_to)
        if training_type_filter and training_type_filter.lower() != 'none':
            trainings = trainings.filter(training_type_id=training_type_filter)
        if competitor_filter and competitor_filter.lower() != 'none':
            trainings = trainings.filter(competitor_id=competitor_filter)

        paginator = Paginator(trainings, 5)  
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        available_competitors = User.objects.filter(
            role='competitor',
            participated_trainings__coach=coach
        ).distinct()

        context = {
            'trainings': page_obj,
            'date_from': date_from,
            'date_to': date_to,
            'training_type_filter': training_type_filter,
            'competitor_filter': competitor_filter,
            'available_training_types': TrainingType.objects.all(),
            'available_competitors': available_competitors
        }
        if 'download_csv' in request.GET:
            return self.generate_csv_report(trainings, training_type_filter, date_from, date_to, competitor_filter)

        return render(request, 'trener.html', context)

    def post(self, request):
        training_id = request.POST.get('training_id')
        coach_comment = request.POST.get('coach_comment')
        training = Training.objects.get(id=training_id)
        training.coach_comment = coach_comment
        training.save()
        return redirect('trener')
    
    def generate_csv_report(self, trainings, training_type_filter, date_from, date_to, competitor_filter):
        response = HttpResponse(content_type='text/csv; charset=utf-8') 
        filename = 'training_report_'
        response.write('\ufeff'.encode('utf8'))

        # Dodaj imię i nazwisko zawodnika do nazwy pliku
        if competitor_filter and competitor_filter.lower() != 'none':
            competitor = User.objects.filter(id=competitor_filter).first()
            if competitor:
                filename += f'{competitor.get_full_name()}_'

        # Dodaj zakres dat do nazwy pliku
        if (date_from and date_from.lower() != 'none') and (date_to and date_to.lower() != 'none'):
            filename += f'{date_from}_{date_to}.csv'
        else:
            min_date = trainings.aggregate(Min('date'))['date__min']
            max_date = trainings.aggregate(Max('date'))['date__max']
            if not date_from or date_from.lower() == 'none':
                date_from = min_date
            if not date_to or date_to.lower() == 'none':
                date_to = max_date
            filename += 'all.csv'

        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response,delimiter=';')
        writer.writerow(['Data', 'Rodzaj treningu', 'Opis', 'Link do GPX', 'Odczucia', 'Trener'])

        for training in trainings:
            writer.writerow([
                training.date,
                training.training_type.training_type if training.training_type else 'Brak',
                training.training_description if training.training_description else '',
                training.gpx_url if training.gpx_url else '',
                training.feeling if training.feeling else '',
                training.coach.get_full_name() if training.coach else 'Brak'
            ])

        return response
    
class TrenerTrainingDetailView(View):
    def get(self, request, pk):
        return self.render_training_detail(request, pk)

    def post(self, request, pk):
        training = get_object_or_404(Training, pk=pk)
        comment_text = request.POST.get('coach_comment')
        if comment_text:
            training.coach_comment = comment_text
            training.save()
        return self.render_training_detail(request, pk)

    def render_training_detail(self, request, pk):
        training = get_object_or_404(Training, pk=pk)
        response = requests.get(training.gpx_url)
        if response.status_code == 200:
            gpx_data = response.content
            root = ET.fromstring(gpx_data)
            namespaces = {
                'gpx': 'http://www.topografix.com/GPX/1/1',
                'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
            }
            heart_rates = []
            for trkpt in root.findall('.//gpx:trkpt', namespaces):
                hr = trkpt.find('.//gpxtpx:hr', namespaces)
                if hr is not None:
                    heart_rates.append(int(hr.text))

            avg_hr = round(sum(heart_rates) / len(heart_rates)) if heart_rates else 0
            actual_max_hr = max(heart_rates) if heart_rates else 0

            time_indices = np.arange(len(heart_rates)) / 60
            max_hr = max(heart_rates) if heart_rates else 0
            min_hr = min(heart_rates) if heart_rates else 0

            y_range = Range1d(start=min_hr, end=max_hr)
            plot_line = figure(title='Tętno w czasie z podziałem na strefy', x_axis_label='Czas[min]', y_axis_label='Tętno [bpm]',
                               sizing_mode='stretch_width', height=400, y_range=y_range)
            hover = HoverTool(
            tooltips=[
                ("Czas", "$x{0.2f} min"),
                ("Tętno", "$y bpm"),
            ],
            mode='vline'
            )
            plot_line.add_tools(hover)

            theoretical_max_hr = 200
            start_index = 0
            colors = ['blue', 'green', '#FFD700', 'orange', 'red']
            zones_boundaries = [theoretical_max_hr * 0.6, theoretical_max_hr * 0.7, theoretical_max_hr * 0.8, theoretical_max_hr * 0.9]
            for i, hr in enumerate(heart_rates):
                zone = next((z for z, boundary in enumerate(zones_boundaries) if hr < boundary), len(zones_boundaries) - 1)
                if i + 1 == len(heart_rates) or zone != next((z for z, boundary in enumerate(zones_boundaries) if heart_rates[i + 1] < boundary), len(zones_boundaries) - 1):
                    plot_line.line(time_indices[start_index:i + 1], heart_rates[start_index:i + 1], line_width=2, color=colors[zone])
                    start_index = i + 1

            script_line, div_line = components(plot_line)

            zone_times = self.calculate_time_in_zones(heart_rates, zones_boundaries)
            plot_bar = self.create_zone_time_chart(zone_times, zones_boundaries)
            script_bar, div_bar = components(plot_bar)

            context = {
                'max_hr': max_hr,
                'avg_hr': avg_hr,
                'actual_max_hr': actual_max_hr,
                'script_line': script_line,
                'div_line': div_line,
                'script_bar': script_bar,
                'div_bar': div_bar,
                'zone_times': zone_times,
                'zones_boundaries': zones_boundaries,
                'training': training,
                'cdn_js': CDN.js_files,
                'cdn_css': CDN.css_files
            }

            return render(request, 'trener_training_detail.html', context)

        return redirect('trener')

    def calculate_time_in_zones(self, heart_rates, zones_boundaries):
        zone_times = [0] * (len(zones_boundaries) + 1)
        for hr in heart_rates:
            for i, boundary in enumerate(zones_boundaries):
                if hr < boundary:
                    zone_times[i] += 1
                    break
            else:
                zone_times[-1] += 1
        return zone_times

    def create_zone_time_chart(self, zone_times, zones_boundaries):
        colors = ['blue', 'green', '#FFD700', 'orange', 'red', 'purple']
        zone_labels = ['1', '2', '3', '4', '5']
        zone_times_in_minutes = [time / 60 for time in zone_times]
        source = ColumnDataSource(data=dict(zones=zone_labels, times=zone_times_in_minutes, colors=colors))

        p = figure(x_range=zone_labels, title="Czas spędzony w strefach tętna", height=400,sizing_mode='stretch_width', toolbar_location=None, tools="")
        p.vbar(x='zones', top='times', width=0.9, color='colors', source=source)
        hover = HoverTool(
            tooltips=[
                ("Strefa", "@zones"),
                ("Czas", "@times min"),
            ]
        )
        p.add_tools(hover)

        p.xgrid.grid_line_color = None
        p.y_range.start = 0
        p.xaxis.axis_label = "Strefy tętna"
        p.yaxis.axis_label = "Czas [s]"

        return p
    
# class TrainingTypeView(FormView):
#     template_name = 'zawodnik.html'
#     form_class = TrainingTypeForm
#     success_url = reverse_lazy('zawodnik')

#     def form_valid(self, form):
#         form.save()
#         return super().form_valid(form)
