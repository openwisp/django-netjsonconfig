from __future__ import absolute_import, unicode_literals

import requests
from celery import shared_task
from django.urls import reverse
from six.moves.urllib.parse import urlparse


@shared_task()
def subscribe_template(template_id, import_url, subscriber_url, is_subscription):
    """
    Send a subscription notification to template designer
    """
    data = {
        'template': template_id,
        'is_subscription': is_subscription,
        'subscriber': subscriber_url
    }
    parse_url = urlparse(import_url)
    url = '{uri.scheme}://{uri.netloc}'.format(uri=parse_url)
    path = '{0}{1}'.format(url, reverse('api:subscribe_template'))
    requests.post(path, data=data)


@shared_task()
def synchronize_templates():
    from .models import TemplateSubscription
    TemplateSubscription.synchronize_templates()
