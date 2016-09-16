from copy import deepcopy

from netjsonconfig import OpenVpn as BaseOpenVpn

# adapt OpenVPN schema in order to limit it to 1 item only
limited_schema = deepcopy(BaseOpenVpn.schema)
limited_schema['properties']['openvpn'].update({
    "additionalItems": False,
    "minItems": 1,
    "maxItems": 1
})
# server mode only
limited_schema['properties']['openvpn']['items'].update({
    "oneOf": [{"$ref": "#/definitions/server"}]
})

# default values for ca, cert and key
limited_schema['definitions']['tunnel']['properties']['ca']['default'] = 'ca.pem'
limited_schema['definitions']['tunnel']['properties']['cert']['default'] = 'cert.pem'
limited_schema['definitions']['tunnel']['properties']['key']['default'] = 'key.pem'
limited_schema['properties']['files']['default'] = [
    {
        "path": "ca.pem",
        "mode": "0644",
        "contents": "{{ ca }}"
    },
    {
        "path": "cert.pem",
        "mode": "0644",
        "contents": "{{ cert }}"
    },
    {
        "path": "key.pem",
        "mode": "0644",
        "contents": "{{ key }}"
    }
]


class OpenVpn(BaseOpenVpn):
    schema = limited_schema
