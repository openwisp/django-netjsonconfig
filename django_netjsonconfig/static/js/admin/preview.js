django.jQuery(function($) {
    var overlay = $('.djnjc-overlay'),
        body = $('body'),
        inner = overlay.find('.inner'),
        preview_url = $('.previewlink').attr('data-url');
    var openPreview = function() {
        var data = {
            'name': $('#id_name').val(),
            'backend': $('#id_backend').val(),
            'config': $('#id_config').val(),
            'csrfmiddlewaretoken': $('form input[name=csrfmiddlewaretoken]').val(),
            'templates': $('#id_templates').val()
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
        // CTRL+SHIFT+P
        if (e.altKey && e.which == 80) {
            openPreview();
        }
        // ESC
        else if (!e.ctrlKey && e.which == 27) {
            closePreview();
        }
    });
});
