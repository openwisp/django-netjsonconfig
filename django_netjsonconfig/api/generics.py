from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.response import Response


class BaseTemplateDetailView(RetrieveAPIView):

    def get_serializer_class(self):
        self.ca_serializer.Meta.model = self.ca_model
        self.cert_serializer.Meta.model = self.cert_model
        self.vpn_serializer.Meta.model = self.vpn_model
        self.template_detail_serializer.Meta.model = self.template_model
        return self.template_detail_serializer

    def get_object(self):
        key = self.request.GET.get('key', None)
        opts = {
            'pk': self.kwargs['pk'],
            'sharing': 'public'
        }
        if key:
            opts.update({
                'key': key,
                'sharing': 'secret_key'
            })
        return get_object_or_404(self.template_model, **opts)


class BaseListTemplateView(ListAPIView):
    """
    List all public templates and also enables
    search/filter of templates by template
    name or template description (des).
    """

    def get_serializer_class(self):
        self.list_template_serializer.Meta.model = self.template_model
        return self.list_template_serializer

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
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data, many=True)
        return Response(serializer.data)


class BaseTemplateSubscriptionView(CreateAPIView):
    """
    Base view to handle template notification
    of templates
    """

    def post(self, request, *args, **kwargs):
        """
        create new notification record if this doesn't exist
        else update the is_subscription field of the existing
        one accordingly
        """
        is_subscription = request.POST.get('is_subscription', False)
        template_pk = request.POST.get('template', None)
        template = self.template_model.objects.get(pk=template_pk)
        options = {
            'template': template,
            'subscriber': request.POST.get('subscriber', None)
        }
        try:
            # update TemplateSubscription for unsubscription
            # and re-subscription
            subscription = self.template_subscription_model.objects.get(**options)
            subscription.is_subscription = is_subscription
            subscription.save()
        except self.template_subscription_model.DoesNotExist:
            # create a new record for new subscription
            options.update({
                'is_subscription': is_subscription
            })
            subscribe = self.template_subscription_model(**options)
            subscribe.full_clean()
            subscribe.save()
        return Response(status=200)


class BaseTemplateSynchronizationView(CreateAPIView):
    """
    synchronize external templates and update last
    sync date
    """

    def post(self, request, *args, **kwargs):
        template_id = request.POST.get('template', None)
        template = self.template_model.objects.get(pk=template_id)
        template.full_clean()
        template.save()
        self.template_subscription_model.subscribe(request, template)
        return Response(status=200)


class BaseSubscriptionCountView(RetrieveAPIView):
    """
    returns the subscription information of a particular
    template.
    """

    def get_serializer_class(self):
        return self.subscription_serializer

    def get_queryset(self):
        template = self.request.GET.get('template', None)
        status = self.request.GET.get('status', None)
        return self.template_subscription_model.objects.filter(template=template, is_subscription=status)

    def get(self, request):
        data = {
            'count': self.get_queryset().count()
        }
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data)
        return Response(serializer.data)
