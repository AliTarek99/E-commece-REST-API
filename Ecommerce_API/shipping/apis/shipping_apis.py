from rest_framework.generics import ListAPIView
from shipping.models import City
from shipping.serializers import CitySerializer


class CitiesAPIs(ListAPIView):
    queryset = City.objects.select_related('country').all()
    serializer_class = CitySerializer
    lookup_field = 'name'