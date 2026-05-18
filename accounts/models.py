from django.db import models
from django.contrib.auth.models import User


class Family(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Families'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight'),
        ('muscle', 'Build Muscle'),
        ('health', 'General Health'),
    ]
    DIET_CHOICES = [
        ('none', 'No Restriction'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
        ('gluten_free', 'Gluten Free'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    height_cm = models.FloatField(null=True, blank=True, help_text='Height in centimeters')
    weight_kg = models.FloatField(null=True, blank=True, help_text='Starting weight in kg')
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='health')
    dietary_preference = models.CharField(max_length=20, choices=DIET_CHOICES, default='none')
    medical_notes = models.TextField(blank=True, help_text='Optional: allergies, conditions, etc.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"
