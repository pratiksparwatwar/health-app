from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('tracker/', include('tracker.urls', namespace='tracker')),
    path('assistant/', include('assistant.urls', namespace='assistant')),
    path('', RedirectView.as_view(pattern_name='tracker:dashboard'), name='home'),
]
