from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('api/org/', include('apps.organizations.urls')),
    path('api/jobs/', include('apps.jobs.urls')),
    path('api/applications/', include('apps.applications.urls')),
    path('api/interviews/', include('apps.interviews.urls')),
    path('api/', include('apps.evaluations.urls')),
    path('api/', include('apps.hiring.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/reports/', include('apps.analytics.report_urls')),
    path('api/billing/', include('apps.billing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler500 = 'config.exceptions.json_server_error'
