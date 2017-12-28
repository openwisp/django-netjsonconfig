from . import views
from ..utils import get_controller_urls

app_name = 'django_netjsonconfig'

urlpatterns = get_controller_urls(views)
