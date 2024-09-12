from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..models import Cart
from ...Products.models import Product as Prod
from django.db import transaction
from ..serializers import CartSerializer


class CartAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        products = Cart.objects.filter(user_id=request.user.id).select_related('product_id').only('product_id__name', 'product_id__price', 'quantity')
        return Response(products, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CartSerializer(data={
            'user': request.user.id,
            'product': request.data.get('product_id'),
            'quantity': request.data.get('quantity')
        })
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            cart_product = Cart.objects.select_for_update().filter(user_id=request.user.id, product_id=request.data['product_id']).first()
            product = Prod.objects.filter(id=request.data['product_id']).first()
            if not product:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            if cart_product:
                cart_product.quantity = int(request.data['quantity'])
                cart_product.save()
            else:
                Cart.objects.create(user_id=request.user.id, product_id=product, quantity=request.data['quantity'])
            return Response({'message': 'Product added to cart'}, status=status.HTTP_201_CREATED)



    def delete(self, request):
        cart_product = Cart.objects.filter(user_id=request.user.id, product_id=request.data['product_id']).first()
        if not cart_product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        cart_product.delete()
        return Response({'message': 'Product removed from cart'}, status=status.HTTP_200_OK)