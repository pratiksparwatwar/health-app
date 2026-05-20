from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import FileResponse, HttpResponse
import os

def service_worker(request):
    # Serve sw.js from static/ with correct MIME type and no-cache header
    # so the browser always picks up updates
    sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'sw.js')
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response

def web_manifest(request):
    manifest_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'manifest.json')
    return FileResponse(open(manifest_path, 'rb'), content_type='application/manifest+json')

def ping(request):
    return HttpResponse('ok', content_type='text/plain')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('tracker/', include('tracker.urls', namespace='tracker')),
    path('assistant/', include('assistant.urls', namespace='assistant')),
    path('ping/', ping, name='ping'),
    path('sw.js', service_worker, name='service_worker'),
    path('manifest.json', web_manifest, name='web_manifest'),
    path('', RedirectView.as_view(pattern_name='tracker:dashboard'), name='home'),
]
