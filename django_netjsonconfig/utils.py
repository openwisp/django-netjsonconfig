from django.http import HttpResponse


def send_file(filename, contents):
    response = HttpResponse(contents, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
    return response
