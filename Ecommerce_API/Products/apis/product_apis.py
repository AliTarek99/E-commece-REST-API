from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from ..models import Product
from ..serializers import OutputProductSerializer, InputProductSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework import status
from shared.services import FileManagment


class ProductList(ListAPIView):
    queryset = Product.objects.filter(visible_in_search=True)
    serializer_class = OutputProductSerializer
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
        product = Product.objects.filter(id=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)


        if product.related_products:
            product_relations = {}
            for product in product['related_products'].all():
                if product['relation'] not in product_relations:
                    product_relations[product['relation']] = {
                        'relation': product['relation'],
                        "products": []
                    }
                product_relations[product['relation']]['products'].append({'name': product['name'], 'id': product['id']})
            product.related_products = product_relations.values()

        serializer = OutputProductSerializer(product)
        return Response(serializer.data)

    def post(self, request):
        request.data['seller'] = request.user.id
        serializer = InputProductSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        urls = FileManagment.save_images(request, 'image')
        
        serializer.validated_data['image'] = urls[0]
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        product = Product.objects.filter(id=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = InputProductSerializer(product, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)

        if request.FILES.get('image'):
            urls = FileManagment.save_images(request, 'image')
            serializer.validated_data['image'] = urls[0]
        serializer.save()
        return Response('product updated.', status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        product = Product.objects.filter(id=pk).first()
        if not product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_200_OK)
    
