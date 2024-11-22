from rest_framework import serializers
from shipping.models import City


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name']


class CitySerializer(serializers.ModelSerializer):
    country = CountrySerializer()
    class Meta:
        model = City
        fields = ['id', 'name', 'country', 'shipping_fee']
