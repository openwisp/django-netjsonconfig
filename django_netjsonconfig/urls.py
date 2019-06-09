from django.conf.urls import include, url

from . import views
from .api import urls as api

app_name = 'django_netjsonconfig'

urlpatterns = [
    url(r'^api/v1/', include(api)),
    url(r'^netjsonconfig/schema\.json$', views.schema, name='schema'),
]
