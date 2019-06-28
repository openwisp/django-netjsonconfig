var cleanedData,
    pattern = /^\{\{\s*(\w*)\s*\}\}$/g,
    getContext,
    evaluateVars,
    cleanData;
getContext = function () {
    return document.querySelectorAll("#id_config-0-context, #id_default_values")[0];
};

evaluateVars = function (data, context) {
    if (typeof data === 'object') {
        Object.keys(data).forEach(function (key) {
            data[key] = evaluateVars(data[key], context);
        });
    }
    if (typeof data === 'string') {
        var found_vars = data.match(pattern);
        if (found_vars !== null) {
            found_vars.forEach(function (element) {
                element = element.replace(/^\{\{\s+|\s+\}\}$|^\{\{|\}\}$/g, '');
                if (context.hasOwnProperty(element)) {
                    data = data.replace(pattern, context[element]);
                }
            });
        }
    }
    return data;
};

cleanData = function (data) {
    var json = getContext();
    if (json && data) {
        cleanedData = evaluateVars(data, JSON.parse(json.value));
        return cleanedData;
    } else {
        return data;
    }
};
