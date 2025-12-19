from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, TrainingType, Training

class UserRegistrationForm(UserCreationForm):
    name = forms.CharField(required=True, max_length=256)
    surname = forms.CharField(required=True, max_length=256)
    role = forms.ChoiceField(choices=User.ROLA_CHOICES, required=True)
    sport_discipline = forms.CharField(required=False, max_length=256)

    class Meta:
        model = User
        fields = ('username', 'name', 'surname', 'role', 'sport_discipline', 'password1', 'password2')


# class TrainingTypeForm(forms.ModelForm):
#     class Meta:
#         model = TrainingType
#         fields = ['training_type']

class CoachCommentForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['coach_comment']