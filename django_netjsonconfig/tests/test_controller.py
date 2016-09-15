from hashlib import md5

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from django_netjsonconfig import settings as app_settings
from django_netjsonconfig.models import Config

TEST_MACADDR = '00:11:22:33:44:55'
mac_plus_secret = '%s+%s' % (TEST_MACADDR, settings.NETJSONCONFIG_SHARED_SECRET)
TEST_CONSISTENT_KEY = md5(mac_plus_secret.encode()).hexdigest()
REGISTER_URL = reverse('controller:register')


class TestController(TestCase):
    """
    tests for django_netjsonconfig.controller
    """
    def _create_config(self):
        d = Config(name='test',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=TEST_MACADDR,
                   config={'general': {'hostname': 'test'}},
                   key='iaASGWE3fpRX0q44WiaY0rjF8ddQ2f7l')
        d.full_clean()
        d.save()
        return d

    def _check_header(self, response):
        self.assertEqual(response['X-Openwisp-Controller'], 'true')

    def test_checksum(self):
        c = self._create_config()
        response = self.client.get(reverse('controller:checksum', args=[c.pk]), {'key': c.key})
        self.assertEqual(response.content.decode(), c.checksum)
        self._check_header(response)
        c.refresh_from_db()
        self.assertIsNotNone(c.last_ip)

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
        c = self._create_config()
        response = self.client.get(reverse('controller:download_config', args=[c.pk]), {'key': c.key})
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=test.tar.gz')
        self._check_header(response)
        c.refresh_from_db()
        self.assertIsNotNone(c.last_ip)

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
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertEqual(response.status_code, 201)
        lines = response.content.decode().split('\n')
        self.assertEqual(lines[0], 'registration-result: success')
        uuid = lines[1].replace('uuid: ', '')
        key = lines[2].replace('key: ', '')
        c = Config.objects.get(pk=uuid, key=key)
        self._check_header(response)
        self.assertIsNotNone(c.last_ip)
        self.assertEqual(c.mac_address, TEST_MACADDR)

    def test_register_400(self):
        # missing secret
        response = self.client.post(REGISTER_URL, {
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertContains(response, 'secret', status_code=400)
        # missing name
        response = self.client.post(REGISTER_URL, {
            'mac_address': TEST_MACADDR,
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertContains(response, 'name', status_code=400)
        # missing backend
        response = self.client.post(REGISTER_URL, {
            'mac_address': TEST_MACADDR,
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
        })
        self.assertContains(response, 'backend', status_code=400)
        # missing mac_address
        response = self.client.post(REGISTER_URL, {
            'backend': 'netjsonconfig.OpenWrt',
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
        })
        self.assertContains(response, 'mac_address', status_code=400)
        self._check_header(response)

    def test_register_failed_creation(self):
        self.test_register()
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertContains(response, 'already exists', status_code=400)

    def test_register_403(self):
        # wrong secret
        response = self.client.post(REGISTER_URL, {
            'secret': 'WRONG',
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertContains(response, 'wrong secret', status_code=403)
        # wrong backend
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'wrong'
        })
        self.assertContains(response, 'wrong backend', status_code=403)
        self._check_header(response)

    def test_register_405(self):
        response = self.client.get(REGISTER_URL)
        self.assertEqual(response.status_code, 405)

    def test_consistent_registration_new(self):
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'key': TEST_CONSISTENT_KEY,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertEqual(response.status_code, 201)
        lines = response.content.decode().split('\n')
        self.assertEqual(lines[0], 'registration-result: success')
        uuid = lines[1].replace('uuid: ', '')
        key = lines[2].replace('key: ', '')
        new = lines[4].replace('is-new: ', '')
        self.assertEqual(new, '1')
        self.assertEqual(key, TEST_CONSISTENT_KEY)
        c = Config.objects.get(pk=uuid, key=TEST_CONSISTENT_KEY)
        self._check_header(response)
        self.assertIsNotNone(c.last_ip)

    def test_consistent_registration_existing(self):
        c = self._create_config()
        c.key = TEST_CONSISTENT_KEY
        c.save()
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'key': TEST_CONSISTENT_KEY,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertEqual(response.status_code, 201)
        lines = response.content.decode().split('\n')
        self.assertEqual(lines[0], 'registration-result: success')
        uuid = lines[1].replace('uuid: ', '')
        key = lines[2].replace('key: ', '')
        hostname = lines[3].replace('hostname: ', '')
        new = lines[4].replace('is-new: ', '')
        self.assertEqual(hostname, c.name)
        self.assertEqual(new, '0')
        c2 = Config.objects.get(pk=uuid, key=key)
        self.assertEqual(c2.id, c.id)
        self.assertEqual(c2.key, c.key)

    def test_report_status_running(self):
        c = self._create_config()
        response = self.client.post(reverse('controller:report_status', args=[c.pk]),
                                    {'key': c.key, 'status': 'running'})
        self._check_header(response)
        c.refresh_from_db()
        self.assertEqual(c.status, 'running')

    def test_report_status_error(self):
        c = self._create_config()
        response = self.client.post(reverse('controller:report_status', args=[c.pk]),
                                    {'key': c.key, 'status': 'error'})
        self._check_header(response)
        c.refresh_from_db()
        self.assertEqual(c.status, 'error')

    def test_report_status_bad_uuid(self):
        c = self._create_config()
        pk = '{}-wrong'.format(c.pk)
        response = self.client.post(reverse('controller:report_status', args=[pk]), {'key': c.key})
        self.assertEqual(response.status_code, 404)

    def test_report_status_400(self):
        c = self._create_config()
        response = self.client.post(reverse('controller:report_status', args=[c.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)
        response = self.client.post(reverse('controller:report_status', args=[c.pk]),
                                    {'key': c.key})
        self.assertEqual(response.status_code, 400)
        self._check_header(response)
        response = self.client.post(reverse('controller:report_status', args=[c.pk]),
                                    {'key': c.key})
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_report_status_403(self):
        c = self._create_config()
        response = self.client.post(reverse('controller:report_status', args=[c.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)
        response = self.client.post(reverse('controller:report_status', args=[c.pk]),
                                    {'key': c.key, 'status': 'madeup'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_report_status_405(self):
        c = self._create_config()
        response = self.client.get(reverse('controller:report_status', args=[c.pk]),
                                   {'key': c.key, 'status': 'running'})
        self.assertEqual(response.status_code, 405)


class TestConsistentRegistrationDisabled(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestConsistentRegistrationDisabled, cls).setUpClass()
        app_settings.CONSISTENT_REGISTRATION = False

    @classmethod
    def tearDownClass(cls):
        super(TestConsistentRegistrationDisabled, cls).tearDownClass()
        app_settings.CONSISTENT_REGISTRATION = True

    def test_consistent_registration_disabled(self):
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'key': TEST_CONSISTENT_KEY,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertEqual(response.status_code, 201)
        lines = response.content.decode().split('\n')
        self.assertEqual(lines[0], 'registration-result: success')
        key = lines[2].replace('key: ', '')
        new = lines[4].replace('is-new: ', '')
        self.assertEqual(new, '1')
        self.assertNotEqual(key, TEST_CONSISTENT_KEY)
        self.assertEqual(Config.objects.filter(key=TEST_CONSISTENT_KEY).count(), 0)
        self.assertEqual(Config.objects.filter(key=key).count(), 1)


class TestRegistrationDisabled(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestRegistrationDisabled, cls).setUpClass()
        app_settings.REGISTRATION_ENABLED = False

    @classmethod
    def tearDownClass(cls):
        super(TestRegistrationDisabled, cls).tearDownClass()
        app_settings.REGISTRATION_ENABLED = True

    def test_register_404(self):
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertEqual(response.status_code, 404)
