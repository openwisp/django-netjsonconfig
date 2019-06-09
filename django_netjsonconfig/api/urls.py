from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^search/$',
        views.search_template,
        name='search_template')
]
