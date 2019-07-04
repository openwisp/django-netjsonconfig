from django_netjsonconfig.utils import get_api_urls

from . import views

app_name = 'django_netjsonconfig'

urlpatterns = get_api_urls(views)
