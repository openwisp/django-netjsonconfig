from ..models import Template
from .generics import BaseSearchTemplate


class SearchTemplate(BaseSearchTemplate):
    template_model = Template


search_template = SearchTemplate.as_view()
