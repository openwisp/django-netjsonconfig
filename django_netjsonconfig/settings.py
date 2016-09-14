from django.conf import settings

DEFAULT_BACKENDS = [
    ('netjsonconfig.OpenWrt', 'OpenWRT'),
    ('netjsonconfig.OpenWisp', 'OpenWISP'),
]

BACKENDS = DEFAULT_BACKENDS + getattr(settings, 'NETJSONCONFIG_BACKENDS', [])
REGISTRATION_ENABLED = getattr(settings, 'NETJSONCONFIG_REGISTRATION_ENABLED', True)
CONSISTENT_REGISTRATION = getattr(settings, 'NETJSONCONFIG_CONSISTENT_REGISTRATION', True)
SHARED_SECRET = getattr(settings, 'NETJSONCONFIG_SHARED_SECRET', '')
CONTEXT = getattr(settings, 'NETJSONCONFIG_CONTEXT', {})
DEFAULT_BACKEND = getattr(settings, 'NETJSONCONFIG_DEFAULT_BACKEND', DEFAULT_BACKENDS[0][0])

DEFAULT_VPN_BACKENDS = [('django_netjsonconfig.vpn_backends.OpenVpn', 'OpenVPN')]
DEFAULT_VPN_BACKEND = getattr(settings, 'NETJSONCONFIG_DEFAULT_VPN_BACKEND', DEFAULT_VPN_BACKENDS[0][0])
VPN_BACKENDS = DEFAULT_VPN_BACKENDS + getattr(settings, 'NETJSONCONFIG_VPN_BACKENDS', [])
DEFAULT_AUTO_CERT = getattr(settings, 'NETJSONCONFIG_DEFAULT_AUTO_CERT', True)
CERT_PATH = getattr(settings, 'NETJSONCONFIG_CERT_PATH', '/etc/x509')
COMMON_NAME_FORMAT = getattr(settings, 'NETJSONCONFIG_COMMON_NAME_FORMAT', '{mac_address}-{name}')
