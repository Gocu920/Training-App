from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from .models import User, Training, TrainingType, Diet

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'surname', 'email')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'surname', 'role', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'name', 'surname', 'email', 'role', 'is_staff')
    search_fields = ('username', 'name', 'surname', 'email')
    ordering = ('username',)

class TrainingAdmin(admin.ModelAdmin):
    list_display = ('training_type', 'date', 'competitor', 'coach', 'gpx_url')
    search_fields = ('training_type__training_type', 'competitor__username', 'coach__username')
    list_filter = ('training_type', 'date', 'coach')

class TrainingTypeAdmin(admin.ModelAdmin):
    list_display = ('training_type',)
    search_fields = ('training_type',)

class DietAdmin(admin.ModelAdmin):
    list_display = ('training_type', 'diet_suggestions')
    search_fields = ('training_type__training_type',)
    list_filter = ('training_type',)

admin.site.register(User, UserAdmin)
admin.site.register(Training, TrainingAdmin)
admin.site.register(TrainingType, TrainingTypeAdmin)
admin.site.register(Diet, DietAdmin)
