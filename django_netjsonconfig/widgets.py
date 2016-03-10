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
        prefix = 'django-netjsonconfig/'
        js = [static('{0}/js/{1}'.format(prefix, f))
              for f in ('jsonschemaeditor.js',
                        'jsonschemaeditor_widget.js')]
        css = {'all': (static('{0}css/jsonschemaeditor.css'.format(prefix)),)}
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
