django.jQuery(function($) {
    var type_select = $('#id_type');
        vpn_specific = $('.field-vpn, .field-auto_cert'),
        toggle_vpn_specific = function(){
            if (type_select.val() == 'vpn') {
                vpn_specific.show();
            }
            else{
                vpn_specific.hide();
            }
        };
    type_select.on('change', function(){
        toggle_vpn_specific();
    });
    toggle_vpn_specific();
});
