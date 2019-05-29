django.jQuery(function ($) {
    'use strict';
    var flag = $('.field-sharing select');
    $('.jsoneditor-wrapper').hide();

    // function for flag_type switcher
    var showFields = function () {
        // define fields for each operation
        var importFields = $('.form-row:not(.field-type, .field-backend, .field-vpn, .field-tags, '+
                                            '.field-auto_cert, .field-config, .field-description, '+
                                            '.field-key, .field-samples)'),
            publicFields = $('.form-row:not(.field-url, .field-config, .field-key)'),
            shareFields = $('.form-row:not(.field-url, .field-config)'),
            privateFields = $('.form-row:not(.field-url, .field-samples, .field-description, '+
                                            '.field-config, .field-key)'),
            allFields = $('.form-row'),
            value = flag.val();
        if (value === 'private') {
            allFields.hide();
            privateFields.show();
        }
        if (value === 'public') {
            allFields.hide();
            publicFields.show();
        }
        if (value === 'secret_key'){
            allFields.hide();
            shareFields.show();
        }
        if (value === 'import') {
            allFields.hide();
            importFields.show();
        }
        if (value === 'import'){
            $('.jsoneditor-wrapper').hide();
        }
        else{
            $('.jsoneditor-wrapper').show();
        }
    };
    showFields();
    flag.on('change', function (e) {
        showFields();
    });
});
