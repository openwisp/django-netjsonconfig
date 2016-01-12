from django.conf.urls import url

from . import views
from ..settings import REGISTRATION_ENABLED


urlpatterns = [
    url(r'^controller/checksum/(?P<pk>[^/]+)/$',
        views.checksum,
        name='checksum'),
    url(r'^controller/download-config/(?P<pk>[^/]+)/$',
        views.download_config,
        name='download_config'),
]

if REGISTRATION_ENABLED:
    urlpatterns += [
        url(r'^controller/register/$',
            views.register,
            name='register'),
    ]
