django.jQuery(function($) {
    var overlay = $('.djnjc-overlay'),
        body = $('body'),
        inner = overlay.find('.inner'),
        preview_url = $('.previewlink').attr('data-url');
    var openPreview = function() {
        // gather data to send in POST
        var data = {
            'name': $('#id_name').val(),
            'mac_address': $('#id_mac_address').val(),
            'backend': $('#id_backend').val(),
            'config': $('#id_config').val(),
            'csrfmiddlewaretoken': $('form input[name=csrfmiddlewaretoken]').val(),
            'templates': $('#id_templates').val(),
            'host': $('#id_host').val(),
            'ca': $('#id_ca').val(),
            'cert': $('#id_cert').val(),
            'dh': $('#id_dh').val(),
        },
            $id = $('#id_id'),
            $key = $('#id_key');
        if ($id.length && $key.length) {
            data['id'] = $id.val();
            data['key'] = $key.val();
        }
        // show preview
        $.post(preview_url, data, function(html){
            inner.html($('#content-main div', html).html());
            overlay.show();
            body.css('overflow', 'hidden');
            overlay.find('pre').trigger('click');
            // close preview
            overlay.find('.close').click(function(e){
                e.preventDefault();
                closePreview();
            })
        })
        .error(function(){
            $('#content-main form').trigger('submit');
        })
    };
    var closePreview = function () {
        overlay.hide();
        inner.html('');
        body.attr('style', '');
    }
    $('.previewlink').click(function(e){
        e.preventDefault();
        openPreview();
    });
    $(document).keyup(function(e) {
        // ALT+P
        if (e.altKey && e.which == 80) {
            // unfocus any active input before proceeding
            $(document.activeElement).trigger('blur');
            // wait for JSON editor to update the
            // corresonding raw value before proceding
            setTimeout(openPreview, 15);
        }
        // ESC
        else if (!e.ctrlKey && e.which == 27) {
            closePreview();
        }
    });
});
