from django.conf.urls import url

from . import views

app_name = 'django_netjsonconfig'

urlpatterns = [
    url(r'^netjsonconfig/schema\.json$', views.schema, name='schema'),
]
