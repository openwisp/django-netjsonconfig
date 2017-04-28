django.jQuery(function($) {
    var overlay = $('.djnjc-overlay'),
        body = $('body'),
        inner = overlay.find('.inner'),
        preview_url = $('.previewlink').attr('data-url');
    var openPreview = function() {
        var selectors = 'input[type=text], input[type=hidden], select, textarea',
            fields = $(selectors, '#content-main form').not('#id_config_jsoneditor *'),
            $id = $('#id_id')
            data = {};
        // gather data to send in POST
        fields.each(function(i, field){
            var $field = $(field),
                name = $field.attr('name');
            if(!name || name.substr(0, 8) == 'initial-'){ return }
            data[name] = $field.val();
        });
        // add id to POST data
        if ($id.length) { data['id'] = $id.val() }
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
            // rare case, leaving it untranslated for simplicity
            alert('Error while generating preview');
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
