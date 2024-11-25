from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from ..models import Cart
from ..serializers import OutputCartSerializer
from cart.services import CartServices
from cart.queryset import CartQueryset

class RetrieveCartAPIs(ListAPIView):
    serializer_class = OutputCartSerializer
    
    def get_queryset(self):
        return CartQueryset.get_cart_items(self.request.user)
    
    
class CartAPIs(APIView):

    def post(self, request):
        if not request.data.get('product_variant'):
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        if not request.data.get('quantity'):
            return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_item = CartServices.add_product_to_cart(request)
        except Exception as e:
            return Response(str(e), status=e.status if hasattr(e, 'status') else status.HTTP_400_BAD_REQUEST)

        
        return Response({'quantity': cart_item.validated_data['quantity']}, status=status.HTTP_201_CREATED)

    def delete(self, request, product_variant):
        cart_product = Cart.objects.filter(user=request.user.id, product_variant=product_variant).first()
        if not cart_product:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        cart_product.delete()
        return Response('Product removed from cart', status=status.HTTP_200_OK)