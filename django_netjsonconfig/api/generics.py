from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response


class BaseTemplateDetailView(RetrieveAPIView):

    def get(self, request, *args, **kwargs):
        key = request.GET.get('key', None)
        opts = {
            'pk': kwargs['uuid'],
            'sharing': 'public'
        }
        if key:
            opts.update({
                'key': key,
                'sharing': 'secret_key'
            })
        template = get_object_or_404(self.template_model, **opts)
        # Setting the models for the serializers. This is done so
        # because this base view will be used by other repos who
        # will define their own concrete models for the serializers
        self.ca_serializer.Meta.model = self.ca_model
        self.cert_serializer.Meta.model = self.cert_model
        self.vpn_serializer.Meta.model = self.vpn_model
        self.template_detail_serializer.Meta.model = self.template_model
        serializer = self.template_detail_serializer(template)
        return Response(serializer.data)


class BaseListTemplateView(ListAPIView):
    """
    List all public templates and also enables
    search/filter of templates by template
    name or template description (des).
    """

    def get_queryset(self):
        name = self.request.GET.get('name', None)
        des = self.request.GET.get('des', None)
        qs = self.queryset.filter(sharing='public')
        if name and des is None:
            qs = qs.filter(name__icontains=name)
        elif des and name is None:
            qs = qs.filter(description__icontains=des)
        else:
            if name is not None and des is not None:
                qs = qs.filter(description__icontains=des,
                               name__icontains=name)
        return qs

    def get(self, request):
        data = self.get_queryset()
        self.list_serializer.Meta.model = self.template_model
        serializer = self.list_serializer(data, many=True)
        return Response(serializer.data)
