from hashlib import md5

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from . import CreateConfigMixin, CreateTemplateMixin
from .. import settings as app_settings
from ..models import Config, Device, Template

TEST_MACADDR = '00:11:22:33:44:55'
mac_plus_secret = '%s+%s' % (TEST_MACADDR, settings.NETJSONCONFIG_SHARED_SECRET)
TEST_CONSISTENT_KEY = md5(mac_plus_secret.encode()).hexdigest()
REGISTER_URL = reverse('controller:register')


class TestController(CreateConfigMixin, CreateTemplateMixin, TestCase):
    """
    tests for django_netjsonconfig.controller
    """
    config_model = Config
    device_model = Device
    template_model = Template

    def _check_header(self, response):
        self.assertEqual(response['X-Openwisp-Controller'], 'true')

    def test_checksum(self):
        d = self._create_device_config()
        c = d.config
        url = reverse('controller:checksum', args=[d.pk])
        response = self.client.get(url, {'key': d.key, 'management_ip': '10.0.0.2'})
        self.assertEqual(response.content.decode(), c.checksum)
        self._check_header(response)
        d.refresh_from_db()
        self.assertIsNotNone(d.last_ip)
        self.assertEqual(d.management_ip, '10.0.0.2')
        # repeat without management_ip
        response = self.client.get(url, {'key': d.key})
        d.refresh_from_db()
        self.assertIsNotNone(d.last_ip)
        self.assertIsNone(d.management_ip)

    def test_checksum_bad_uuid(self):
        d = self._create_device_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:checksum', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_checksum_400(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_checksum_403(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_checksum_405(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)

    def test_download_config(self):
        d = self._create_device_config()
        url = reverse('controller:download_config', args=[d.pk])
        response = self.client.get(url, {'key': d.key, 'management_ip': '10.0.0.2'})
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=test.tar.gz')
        self._check_header(response)
        d.refresh_from_db()
        self.assertIsNotNone(d.last_ip)
        self.assertEqual(d.management_ip, '10.0.0.2')
        # repeat without management_ip
        response = self.client.get(url, {'key': d.key})
        d.refresh_from_db()
        self.assertIsNotNone(d.last_ip)
        self.assertIsNone(d.management_ip)

    def test_download_config_bad_uuid(self):
        d = self._create_device_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:download_config', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_download_config_400(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_download_config_403(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_download_config_405(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)

    def test_register(self, **kwargs):
        options = {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        }
        options.update(kwargs)
        response = self.client.post(REGISTER_URL, options)
        self.assertEqual(response.status_code, 201)
        lines = response.content.decode().split('\n')
        self.assertEqual(lines[0], 'registration-result: success')
        uuid = lines[1].replace('uuid: ', '')
        key = lines[2].replace('key: ', '')
        d = Device.objects.get(pk=uuid)
        self._check_header(response)
        self.assertEqual(d.key, key)
        self.assertIsNotNone(d.last_ip)
        self.assertEqual(d.mac_address, TEST_MACADDR)
        if 'management_ip' not in kwargs:
            self.assertIsNone(d.management_ip)
        else:
            self.assertEqual(d.management_ip, kwargs['management_ip'])
        return d

    def test_register_with_management_ip(self):
        self.test_register(management_ip='10.0.0.2')

    def test_register_template_tags(self):
        mesh_protocol = self._create_template(name='mesh protocol')
        mesh_protocol.tags.add('mesh')
        mesh_interface = self._create_template(name='mesh interface')
        mesh_interface.tags.add('mesh')
        rome = self._create_template(name='rome')
        rome.tags.add('rome')
        c = self.test_register(tags='mesh rome').config
        for t in [mesh_protocol, mesh_interface, rome]:
            self.assertEqual(c.templates.filter(name=t.name).count(), 1)

    def test_register_device_info(self):
        device_model = 'TP-Link TL-WDR4300 v1'
        os = 'LEDE Reboot 17.01-SNAPSHOT r3270-09a8183'
        system = 'Atheros AR9344 rev 2'
        d = self.test_register(model=device_model, os=os, system=system)
        self.assertEqual(d.model, device_model)
        self.assertEqual(d.os, os)
        self.assertEqual(d.system, system)

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

    def test_register_failed_creation_wrong_backend(self):
        self.test_register()
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.CLEARLYWRONG'
        })
        self.assertContains(response, 'backend', status_code=403)

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
        d = Device.objects.get(pk=uuid)
        self._check_header(response)
        self.assertEqual(d.key, TEST_CONSISTENT_KEY)
        self.assertIsNotNone(d.last_ip)

    def test_consistent_registration_existing(self):
        d = self._create_device_config()
        d.key = TEST_CONSISTENT_KEY
        d.save()
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
        self.assertEqual(hostname, d.name)
        self.assertEqual(new, '0')
        count = Device.objects.filter(pk=uuid, key=key, name=hostname).count()
        self.assertEqual(count, 1)

    def test_consistent_registration_exists_no_config(self):
        d = self._create_device()
        d.key = TEST_CONSISTENT_KEY
        d.save()
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
        self.assertEqual(hostname, d.name)
        self.assertEqual(new, '0')
        count = Device.objects.filter(pk=uuid, key=key, name=hostname).count()
        self.assertEqual(count, 1)
        d.refresh_from_db()
        self.assertIsNotNone(d.config)

    def test_report_status_running(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'running'})
        self._check_header(response)
        d.config.refresh_from_db()
        self.assertEqual(d.config.status, 'running')

    def test_report_status_error(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'error'})
        self._check_header(response)
        d.config.refresh_from_db()
        self.assertEqual(d.config.status, 'error')

    def test_report_status_bad_uuid(self):
        d = self._create_device_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.post(reverse('controller:report_status', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_report_status_400(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:report_status', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)
        response = self.client.post(reverse('controller:report_status', args=[d.pk]),
                                    {'key': d.key})
        self.assertEqual(response.status_code, 400)
        self._check_header(response)
        response = self.client.post(reverse('controller:report_status', args=[d.pk]),
                                    {'key': d.key})
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_report_status_403(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:report_status', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)
        response = self.client.post(reverse('controller:report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'madeup'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_report_status_405(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:report_status', args=[d.pk]),
                                   {'key': d.key, 'status': 'running'})
        self.assertEqual(response.status_code, 405)

    def test_checksum_no_config(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_download_no_config(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_report_status_no_config(self):
        d = self._create_device()
        response = self.client.post(reverse('controller:report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'running'})
        self.assertEqual(response.status_code, 404)


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
        self.assertEqual(Device.objects.filter(key=TEST_CONSISTENT_KEY).count(), 0)
        self.assertEqual(Device.objects.filter(key=key).count(), 1)


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
