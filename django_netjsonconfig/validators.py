from django.core.validators import RegexValidator, _lazy_re_compile
from django.utils.translation import ugettext_lazy as _

key_validator = RegexValidator(
    _lazy_re_compile('^[^\s/\.]+$'),
    message=_('Key must not contain spaces, dots or slashes.'),
    code='invalid',
)

mac_address_validator = RegexValidator(
    _lazy_re_compile('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'),
    message=_('Must be a valid mac address.'),
    code='invalid',
)
