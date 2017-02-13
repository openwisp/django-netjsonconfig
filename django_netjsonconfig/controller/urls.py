from . import views
from ..utils import get_controller_urls

urlpatterns = get_controller_urls(views)
