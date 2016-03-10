from __future__ import absolute_import, unicode_literals

from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


class JsonSchemaWidget(AdminTextareaWidget):
    """
    JSON Schema Editor widget
    """
    @property
    def media(self):
        js = (
            static('js/jsoneditor/jsoneditor.js'),
            static('js/jsoneditor/widget.js')
        )
        css = {'all': (static('css/jsoneditor/jsoneditor.css'),)}
        return forms.Media(js=js, css=css)

    def render(self, name, value, attrs={}):
        attrs['class'] = 'vLargeTextField jsoneditor-raw'
        html = """
<input class="button json-editor-btn-edit normal-mode" type="button" value="{0}">
<input class="button json-editor-btn-edit advanced-mode" type="button" value="{1}">
<script>django._netjsonconfigSchemaUrl = "{2}";</script>
"""
        html = html.format(_('Normal mode'),
                           _('Advanced mode (raw JSON)'),
                           reverse('netjsonconfig:schema'))
        html += super(JsonSchemaWidget, self).render(name, value, attrs)
        return html
