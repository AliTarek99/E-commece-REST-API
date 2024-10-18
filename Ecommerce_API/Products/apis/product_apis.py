from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from ..models import Product, ProductImages, ProductVariant
from ..serializers import OutputProductSerializer, InputProductSerializer, OutputSingleProductSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch


class ProductList(ListAPIView):
    queryset = Product.objects.prefetch_related(Prefetch('productimages_set', queryset=ProductImages.objects.filter(in_use=True).only('url')))
    serializer_class = OutputProductSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['max_price']
    ordering = ['-max_price']

class ProductAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        if not pk:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        product = Product.objects.prefetch_related(
                Prefetch(
                    'productvariant_set', 
                    queryset=ProductVariant.objects.prefetch_related(
                        Prefetch(
                            'productimages_set', 
                            queryset=ProductImages.objects.filter(in_use=True)
                        )
                    )
                )
            ).filter(id=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = OutputSingleProductSerializer(product)
        return Response(serializer.data)

    def post(self, request):
        serializer = InputProductSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('product created successfully.', status=status.HTTP_201_CREATED)
    
    # def put(self, request, pk):
    #     product = Product.objects.filter(id=pk).first()
    #     if not product:
    #         return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
    #     serializer = InputProductSerializer(product, data=request.data, partial=True, context={'request': request})
    #     serializer.is_valid(raise_exception=True)

    #     if request.FILES.get('image'):
    #         urls = FileManagment.save_images(request, 'image')
    #         serializer.validated_data['image'] = urls[0]
    #     serializer.save()
    #     return Response('product updated.', status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        product = Product.objects.filter(id=pk, seller_id=request.user.id).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_200_OK)
    
