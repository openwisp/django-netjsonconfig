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


class OpenVpn(BaseOpenVpn):
    schema = limited_schema
