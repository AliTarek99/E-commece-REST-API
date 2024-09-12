from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from ..models import Product
from ..serializers import ProductSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework import status


class ProductList(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['price']
    ordering = ['-price']

class ProductAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        if not pk:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        product = Product.objects.filter(pk=pk).first()
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_200_OK)
    
