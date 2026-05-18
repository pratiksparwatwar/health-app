from django.contrib import admin
from .models import Family, UserProfile


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'family', 'age', 'gender', 'goal']
    list_filter = ['family', 'goal', 'dietary_preference']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
