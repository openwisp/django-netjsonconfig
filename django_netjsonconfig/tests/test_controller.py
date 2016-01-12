from django.test import TestCase
from django.core.urlresolvers import reverse

from django_netjsonconfig.models import Device


class TestController(TestCase):
    """
    tests for django_netjsonconfig.controller
    """
    def _create_device(self):
        d = Device(name='test',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'test'}},
                   key='iaASGWE3fpRX0q44WiaY0rjF8ddQ2f7l')
        d.full_clean()
        d.save()
        return d

    def test_checksum(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.content.decode(), d.checksum)

    def test_checksum_bad_uuid(self):
        d = self._create_device()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:checksum', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_checksum_400(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]))
        self.assertEqual(response.status_code, 400)

    def test_checksum_403(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)

    def test_checksum_405(self):
        d = self._create_device()
        response = self.client.post(reverse('controller:checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)

    def test_download_config(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=test.tar.gz')

    def test_download_config_bad_uuid(self):
        d = self._create_device()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:download_config', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_download_config_400(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]))
        self.assertEqual(response.status_code, 400)

    def test_download_config_403(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)

    def test_download_config_405(self):
        d = self._create_device()
        response = self.client.post(reverse('controller:download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)
