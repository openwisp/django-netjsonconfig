import requests
from celery import shared_task
from django.urls import reverse
from six.moves.urllib.parse import urlparse


@shared_task
def subscribe(template_id, import_url, subscriber_url, subscribe=False):
    """
    Send a subscription notification to template designer
    """
    data = {
        'template': template_id,
        'subscribe': subscribe,
        'subscriber': subscriber_url
    }
    parse_url = urlparse(import_url)
    url = '{uri.scheme}://{uri.netloc}'.format(uri=parse_url)
    path = '{0}{1}'.format(url, reverse('api:notify_template'))
    requests.post(path, data=data)


def base_sync_template_content(subscriber_url, template_id):
    """
    synchronize templates of subscribers every midnight
    """
    path = '{0}{1}'.format(subscriber_url, reverse('api:synchronize_template'))
    requests.post(path, data={'template_id': template_id})
