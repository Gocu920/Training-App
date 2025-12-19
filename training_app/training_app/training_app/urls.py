from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path
from .views import RegisterView, LoginView, HomeView, ZawodnikView,CustomLogoutView,TrenerView, TrenerTrainingDetailView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('register/', RegisterView.as_view(), name='register'),
    path('', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('home/', HomeView.as_view(), name='home'),
    path('zawodnik/', ZawodnikView.as_view(), name='zawodnik'),
    path('trener/', TrenerView.as_view(), name='trener'),
    path('trener/training/<int:pk>/', TrenerTrainingDetailView.as_view(), name='trener_training_detail'),
    # path('training_type/', TrainingTypeView.as_view(), name='training_type'),
]
