from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..models import Cart
from ..serializers import CartSerializer
from cart.services import CartServices

class CartAPIs(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        products = Cart.objects.filter(user=request.user.id).select_related('product').only('product_id__name', 'product_id__price', 'quantity')
        serilaizer = CartSerializer(products, many=True)
        return Response(serilaizer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.data['product']:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            CartServices.add_product_to_cart(request)
        except Exception as e:
            return Response(str(e), status=e.status if hasattr(e, 'status') else status.HTTP_400_BAD_REQUEST)

        
        return Response('cart updated.', status=status.HTTP_201_CREATED)

    def delete(self, request, product):
        cart_product = Cart.objects.filter(user=request.user.id, product=product).first()
        if not cart_product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        cart_product.delete()
        return Response('Product removed from cart', status=status.HTTP_200_OK)