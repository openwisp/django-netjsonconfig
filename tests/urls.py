from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    # controller URLs
    # used by devices to download/update their configuration
    # keep the namespace argument unchanged
    url(r'^', include('django_netjsonconfig.controller.urls', namespace='controller')),
    # common URLs
    # shared among django-netjsonconfig components
    # keep the namespace argument unchanged
    url(r'^', include('django_netjsonconfig.urls', namespace='netjsonconfig')),
    url(r'^', include('django_x509.urls', namespace='x509')),
]

urlpatterns += staticfiles_urlpatterns()
