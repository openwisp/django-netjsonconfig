from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

from django_netjsonconfig.models import Config


class TestController(TestCase):
    """
    tests for django_netjsonconfig.controller
    """
    register_url = reverse('controller:register')

    def _create_config(self):
        d = Config(name='test',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'test'}},
                   key='iaASGWE3fpRX0q44WiaY0rjF8ddQ2f7l')
        d.full_clean()
        d.save()
        return d

    def _check_header(self, response):
        self.assertEqual(response['X-Openwisp-Controller'], 'true')

    def test_checksum(self):
        d = self._create_config()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.content.decode(), d.checksum)
        self._check_header(response)

    def test_checksum_bad_uuid(self):
        d = self._create_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:checksum', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_checksum_400(self):
        d = self._create_config()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_checksum_403(self):
        d = self._create_config()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_checksum_405(self):
        d = self._create_config()
        response = self.client.post(reverse('controller:checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)

    def test_download_config(self):
        d = self._create_config()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=test.tar.gz')
        self._check_header(response)

    def test_download_config_bad_uuid(self):
        d = self._create_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:download_config', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_download_config_400(self):
        d = self._create_config()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_download_config_403(self):
        d = self._create_config()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_download_config_405(self):
        d = self._create_config()
        response = self.client.post(reverse('controller:download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)

    def test_register(self):
        response = self.client.post(self.register_url, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': '00:11:22:33:44:55',
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertEqual(response.status_code, 201)
        lines = response.content.decode().split('\n')
        self.assertEqual(lines[0], 'registration-result: success')
        uuid = lines[1].replace('uuid: ', '')
        key = lines[2].replace('key: ', '')
        self.assertEqual(Config.objects.filter(pk=uuid, key=key).count(), 1)
        self._check_header(response)

    def test_register_400(self):
        # missing secret
        response = self.client.post(self.register_url, {
            'name': '00:11:22:33:44:55',
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertContains(response, 'secret', status_code=400)
        # missing name
        response = self.client.post(self.register_url, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertContains(response, 'name', status_code=400)
        # missing backend
        response = self.client.post(self.register_url, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': '00:11:22:33:44:55',
        })
        self.assertContains(response, 'backend', status_code=400)
        self._check_header(response)

    def test_register_403(self):
        # wrong secret
        response = self.client.post(self.register_url, {
            'secret': 'WRONG',
            'name': '00:11:22:33:44:55',
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertContains(response, 'wrong secret', status_code=403)
        # wrong backend
        response = self.client.post(self.register_url, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': '00:11:22:33:44:55',
            'backend': 'wrong'
        })
        self.assertContains(response, 'wrong backend', status_code=403)
        self._check_header(response)

    def test_register_405(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 405)
