from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from .serializers import SearchTemplateSerializer


class BaseSearchTemplate(ListAPIView):
    serializer_class = SearchTemplateSerializer

    def get_queryset(self):
        name = self.request.GET.get('name', None)
        des = self.request.GET.get('des', None)
        temp = self.template_model.filter(sharing='public')
        if name and des is None:
            temp = temp.filter(name__icontains=name)
        elif des and name is None:
            temp = temp.filter(description__icontains=des)
        else:
            if name is not None and des is not None:
                temp = temp.filter(description__icontains=des,
                                   name__icontains=name)
        return temp

    def get(self, request):
        data = self.get_queryset()
        serializer = SearchTemplateSerializer(data, many=True)
        return Response(serializer.data)
