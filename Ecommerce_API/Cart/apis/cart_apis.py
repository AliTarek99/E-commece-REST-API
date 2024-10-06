from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..models import Cart
from ..serializers import CartSerializer, OutputCartSerializer
from cart.services import CartServices
from products.models import ProductVariant, ProductImages, ProductVariantSizes, Product
from django.db.models import Prefetch
from django.contrib.postgres.aggregates import ArrayAgg


class CartAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user_cart_items = Cart.objects.filter(user_id=request.user.id).prefetch_related(
            Prefetch(
                'product_variant', 
                queryset=ProductVariant.objects.prefetch_related(
                    Prefetch('productimages_set', queryset=ProductImages.objects.filter(in_use=True))
                ).only('parent__name', 'parent__seller_id', 'parent__seller__name', 'color', 'productvariantsizes__price')
            )
        ).annotate(
            images=ArrayAgg('product_variant__productimages__url'),
        ).all()
        serializer = OutputCartSerializer(user_cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.data.get('product_variant') or not request.data.get('size'):
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('quantity'):
            return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            CartServices.add_product_to_cart(request)
        except Exception as e:
            return Response(str(e), status=e.status if hasattr(e, 'status') else status.HTTP_400_BAD_REQUEST)

        
        return Response('cart updated.', status=status.HTTP_201_CREATED)

    def delete(self, request, product_variant):
        cart_product = Cart.objects.filter(user=request.user.id, product_variant=product_variant).first()
        if not cart_product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        cart_product.delete()
        return Response('Product removed from cart', status=status.HTTP_200_OK)