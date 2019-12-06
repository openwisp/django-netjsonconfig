from ..utils import get_controller_urls
from . import views

app_name = 'django_netjsonconfig'

urlpatterns = get_controller_urls(views)
