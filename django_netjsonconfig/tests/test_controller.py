from hashlib import md5
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django_x509.models import Ca

from ..models import Config, Device, Template, Vpn
from . import CreateConfigMixin, CreateTemplateMixin, TestVpnX509Mixin

TEST_MACADDR = '00:11:22:33:44:55'
mac_plus_secret = '%s+%s' % (TEST_MACADDR, settings.NETJSONCONFIG_SHARED_SECRET)
TEST_CONSISTENT_KEY = md5(mac_plus_secret.encode()).hexdigest()
REGISTER_URL = reverse('controller:device_register')


class TestController(CreateConfigMixin, CreateTemplateMixin, TestCase, TestVpnX509Mixin):
    """
    tests for django_netjsonconfig.controller
    """
    config_model = Config
    device_model = Device
    template_model = Template
    ca_model = Ca
    vpn_model = Vpn

    def _check_header(self, response):
        self.assertEqual(response['X-Openwisp-Controller'], 'true')

    def test_device_checksum(self):
        d = self._create_device_config()
        c = d.config
        url = reverse('controller:device_checksum', args=[d.pk])
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

    def test_device_checksum_bad_uuid(self):
        d = self._create_device_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:device_checksum', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_device_checksum_400(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:device_checksum', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_device_checksum_403(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:device_checksum', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_device_checksum_405(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:device_checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)

    def test_device_download_config(self):
        d = self._create_device_config()
        url = reverse('controller:device_download_config', args=[d.pk])
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

    def test_device_download_config_bad_uuid(self):
        d = self._create_device_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.get(reverse('controller:device_download_config', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_device_download_config_400(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:device_download_config', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_device_download_config_403(self):
        d = self._create_device_config()
        path = reverse('controller:device_download_config', args=[d.pk])
        response = self.client.get(path, {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_device_download_config_405(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:device_download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 405)

    def test_vpn_checksum(self):
        v = self._create_vpn()
        url = reverse('controller:vpn_checksum', args=[v.pk])
        response = self.client.get(url, {'key': v.key})
        self.assertEqual(response.content.decode(), v.checksum)
        self._check_header(response)

    def test_vpn_checksum_bad_uuid(self):
        v = self._create_vpn()
        pk = '{}-wrong'.format(v.pk)
        response = self.client.get(reverse('controller:vpn_checksum', args=[pk]), {'key': v.key})
        self.assertEqual(response.status_code, 404)

    def test_vpn_checksum_400(self):
        v = self._create_vpn()
        response = self.client.get(reverse('controller:vpn_checksum', args=[v.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_vpn_checksum_403(self):
        v = self._create_vpn()
        response = self.client.get(reverse('controller:vpn_checksum', args=[v.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_vpn_checksum_405(self):
        v = self._create_vpn()
        response = self.client.post(reverse('controller:vpn_checksum', args=[v.pk]), {'key': v.key})
        self.assertEqual(response.status_code, 405)

    def test_vpn_download_config(self):
        v = self._create_vpn()
        url = reverse('controller:vpn_download_config', args=[v.pk])
        response = self.client.get(url, {'key': v.key})
        self.assertEqual(response['Content-Disposition'], 'attachment; filename=test.tar.gz')
        self._check_header(response)

    def test_vpn_download_config_bad_uuid(self):
        v = self._create_vpn()
        pk = '{}-wrong'.format(v.pk)
        response = self.client.get(reverse('controller:vpn_download_config', args=[pk]), {'key': v.key})
        self.assertEqual(response.status_code, 404)

    def test_vpn_download_config_400(self):
        v = self._create_vpn()
        response = self.client.get(reverse('controller:vpn_download_config', args=[v.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_vpn_download_config_403(self):
        v = self._create_vpn()
        path = reverse('controller:vpn_download_config', args=[v.pk])
        response = self.client.get(path, {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_vpn_download_config_405(self):
        v = self._create_vpn()
        response = self.client.post(reverse('controller:vpn_download_config', args=[v.pk]), {'key': v.key})
        self.assertEqual(response.status_code, 405)

    def test_register(self, **kwargs):
        options = {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'hardware_id': '1234',
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
            'hardware_id': '1234',
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

    def test_device_consistent_registration_existing(self):
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

    def test_device_consistent_registration_exists_no_config(self):
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

    def test_device_registration_update_hw_info(self):
        d = self._create_device_config()
        d.key = TEST_CONSISTENT_KEY
        d.save()
        params = {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'key': TEST_CONSISTENT_KEY,
            'backend': 'netjsonconfig.OpenWrt',
            'model': 'TP-Link TL-WDR4300 v2',
            'os': 'OpenWrt 18.06-SNAPSHOT r7312-e60be11330',
            'system': 'Atheros AR9344 rev 3'
        }
        self.assertNotEqual(d.os, params['os'])
        self.assertNotEqual(d.system, params['system'])
        self.assertNotEqual(d.model, params['model'])
        response = self.client.post(REGISTER_URL, params)
        self.assertEqual(response.status_code, 201)
        d.refresh_from_db()
        self.assertEqual(d.os, params['os'])
        self.assertEqual(d.system, params['system'])
        self.assertEqual(d.model, params['model'])

    def test_device_registration_update_hw_info_no_config(self):
        d = self._create_device()
        d.key = TEST_CONSISTENT_KEY
        d.save()
        params = {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'key': TEST_CONSISTENT_KEY,
            'backend': 'netjsonconfig.OpenWrt',
            'model': 'TP-Link TL-WDR4300 v2',
            'os': 'OpenWrt 18.06-SNAPSHOT r7312-e60be11330',
            'system': 'Atheros AR9344 rev 3'
        }
        self.assertNotEqual(d.os, params['os'])
        self.assertNotEqual(d.system, params['system'])
        self.assertNotEqual(d.model, params['model'])
        response = self.client.post(REGISTER_URL, params)
        self.assertEqual(response.status_code, 201)
        d.refresh_from_db()
        self.assertEqual(d.os, params['os'])
        self.assertEqual(d.system, params['system'])
        self.assertEqual(d.model, params['model'])

    def test_device_report_status_running(self):
        """
        maintained for backward compatibility
        # TODO: remove in stable version 1.0
        """
        d = self._create_device_config()
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'running'})
        self._check_header(response)
        d.config.refresh_from_db()
        self.assertEqual(d.config.status, 'applied')

    def test_device_report_status_applied(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'applied'})
        self._check_header(response)
        d.config.refresh_from_db()
        self.assertEqual(d.config.status, 'applied')

    def test_device_report_status_error(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'error'})
        self._check_header(response)
        d.config.refresh_from_db()
        self.assertEqual(d.config.status, 'error')

    def test_device_report_status_bad_uuid(self):
        d = self._create_device_config()
        pk = '{}-wrong'.format(d.pk)
        response = self.client.post(reverse('controller:device_report_status', args=[pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_device_report_status_400(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]))
        self.assertEqual(response.status_code, 400)
        self._check_header(response)
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]),
                                    {'key': d.key})
        self.assertEqual(response.status_code, 400)
        self._check_header(response)
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]),
                                    {'key': d.key})
        self.assertEqual(response.status_code, 400)
        self._check_header(response)

    def test_device_report_status_403(self):
        d = self._create_device_config()
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]), {'key': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'madeup'})
        self.assertEqual(response.status_code, 403)
        self._check_header(response)

    def test_device_report_status_405(self):
        d = self._create_device_config()
        response = self.client.get(reverse('controller:device_report_status', args=[d.pk]),
                                   {'key': d.key, 'status': 'running'})
        self.assertEqual(response.status_code, 405)

    def test_device_checksum_no_config(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:device_checksum', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_device_download_no_config(self):
        d = self._create_device()
        response = self.client.get(reverse('controller:device_download_config', args=[d.pk]), {'key': d.key})
        self.assertEqual(response.status_code, 404)

    def test_device_report_status_no_config(self):
        d = self._create_device()
        response = self.client.post(reverse('controller:device_report_status', args=[d.pk]),
                                    {'key': d.key, 'status': 'running'})
        self.assertEqual(response.status_code, 404)

    def test_register_failed_rollback(self):
        with patch('django_netjsonconfig.base.config.AbstractConfig.full_clean') as a:
            a.side_effect = ValidationError(dict())
            options = {
                'secret': settings.NETJSONCONFIG_SHARED_SECRET,
                'name': TEST_MACADDR,
                'mac_address': TEST_MACADDR,
                'hardware_id': '1234',
                'backend': 'netjsonconfig.OpenWrt'
            }
            response = self.client.post(REGISTER_URL, options)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(self.device_model.objects.count(), 0)

    @patch('django_netjsonconfig.settings.CONSISTENT_REGISTRATION', False)
    def test_consistent_registration_disabled(self):
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'key': TEST_CONSISTENT_KEY,
            'mac_address': TEST_MACADDR,
            'hardware_id': '1234',
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

    @patch('django_netjsonconfig.settings.REGISTRATION_ENABLED', False)
    def test_registration_disabled(self):
        response = self.client.post(REGISTER_URL, {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'backend': 'netjsonconfig.OpenWrt'
        })
        self.assertEqual(response.status_code, 403)

    @patch('django_netjsonconfig.settings.REGISTRATION_SELF_CREATION', False)
    def test_self_creation_disabled(self):
        options = {
            'secret': settings.NETJSONCONFIG_SHARED_SECRET,
            'name': TEST_MACADDR,
            'mac_address': TEST_MACADDR,
            'hardware_id': '1234',
            'backend': 'netjsonconfig.OpenWrt',
            'key': 'c09164172a9d178735f21d2fd92001fa'
        }
        # first attempt fails because device is not present in DB
        response = self.client.post(REGISTER_URL, options)
        self.assertEqual(response.status_code, 404)
        # once the device is created, everything works normally
        device = self._create_device(name=options['name'],
                                     mac_address=options['mac_address'],
                                     hardware_id=options['hardware_id'])
        self.assertEqual(device.key, options['key'])
        response = self.client.post(REGISTER_URL, options)
        self.assertEqual(response.status_code, 201)
        lines = response.content.decode().split('\n')
        self.assertEqual(lines[0], 'registration-result: success')
        uuid = lines[1].replace('uuid: ', '')
        key = lines[2].replace('key: ', '')
        created = Device.objects.get(pk=uuid)
        self.assertEqual(created.key, key)
        self.assertEqual(created.pk, device.pk)
