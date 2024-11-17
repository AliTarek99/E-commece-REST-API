from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, DestroyAPIView
from rest_framework.views import APIView
from ..models import Product, ProductImages, ProductVariant
from ..serializers import InputProductSerializer, OutputProductSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch
from products.permissions import IsSellerOfTheProduct


class ProductRetrievalAPIs(ListAPIView, RetrieveAPIView):
    serializer_class = OutputProductSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['max_price']
    ordering = ['-max_price']
    lookup_field = 'id'
    def get_queryset(self):
        return Product.objects.only('id', 'name', 'description', 'max_price', 'min_price', 'quantity', 'seller').prefetch_related(
            Prefetch('productimages_set', queryset=ProductImages.objects.filter(in_use=True).only('url', 'color', 'product', 'default'), to_attr='filtered_images')
        ).prefetch_related(
            Prefetch('productvariant_set', queryset=ProductVariant.objects.filter(quantity__gt=0).only('id', 'color_id', 'size_id', 'price', 'quantity', 'parent'), to_attr='filtered_variants')
        ).select_related('seller')

    def get(self, request, *args, **kwargs):
        if 'id' in self.kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)
    
    
class ProductCreateView(CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = InputProductSerializer
    
class ProductDeleteView(DestroyAPIView):
    queryset = Product.objects.all()
    lookup_field = 'id'
    permission_classes = [IsSellerOfTheProduct]