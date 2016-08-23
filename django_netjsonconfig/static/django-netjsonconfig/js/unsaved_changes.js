(function ($) {
    var form = '#content-main form',
        map_values = function(object) {
            $('input, select, textarea', form).each(function(i, el){
                var field = $(el),
                    name = field.attr('name'),
                    value = field.val();
                // ignore fields that have no name attribute, begin with "_" or "initial-"
                if (!name || name.substr(0, 1) == '_' || name.substr(0, 8) == 'initial-') {
                    return;
                }
                // fix checkbox values inconsistency
                if (field.attr('type') == 'checkbox') {
                    object[name] = field.is(':checked')
                }
                else {
                    object[name] = value;
                }

            });
        };

    var unsaved_changes = function(e) {
        // get current values
        current_values = {}
        map_values(current_values);
        var changed = false,
            message = 'You haven\'t saved your changes yet!';
        if (gettext) { message = gettext(message); }  // i18n if enabled
        // compare initial with current values
        for (name in django._njc_initial_values) {
            // use initial values from initial fields if present
            var initialField = $('#initial-id_' + name),
                initialValue = initialField.length ? initialField.val() : django._njc_initial_values[name];
            // fix checkbox value inconsistency
            if (initialValue == 'True') { initialValue = true }
            else if (initialValue == 'False') { initialValue = false }
            if (initialValue != current_values[name]) {
                changed = true;
                break;
            }
        }
        if (changed) {
            e.returnValue = message;
            return message;
        }
    };

    $(window).load(function(){
        if (!$('.submit-row').length) { return }
        // populate initial map of form values
        django._njc_initial_values = {}
        map_values(django._njc_initial_values);
        // do not perform unsaved_changes if submitting form
        $(form).submit(function() {
            $(window).unbind('beforeunload', unsaved_changes);
        })
        // bind unload event
        $(window).bind('beforeunload', unsaved_changes);
    });
})(django.jQuery);
