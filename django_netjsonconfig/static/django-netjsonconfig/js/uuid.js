django.jQuery(function($) {
    var p = $('.field-id p'),
        value = p.text();
    p.html('<input readonly id="id_id" type="text" class="vTextField readonly" value="'+ value +'">');
    var id = $('#id_id');
    id.click(function(){
        $(this).select()
    });
});
