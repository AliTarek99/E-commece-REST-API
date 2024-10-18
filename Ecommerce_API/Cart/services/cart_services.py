from products.models import ProductVariant
from ..serializers import CartSerializer
from cart.models import Cart
from rest_framework import status
from django.db import transaction

class CartServices():
    @classmethod
    def add_product_to_cart(cls, request):
        try:
            product = ProductVariant.objects.filter(id=request.data['product_variant']).first()
            if not product:
                error = Exception('Product not found')
                error.status = status.HTTP_404_NOT_FOUND
            with transaction.atomic():
                cart_product = Cart.objects.select_for_update().filter(user=request.user.id, product_variant=request.data['product_variant']).first()
                
                serializer = CartSerializer(cart_product, data={
                        'user': request.user.id,
                        'product_variant': request.data['product_variant'],
                        'quantity': request.data['quantity'] + cart_product.quantity if cart_product else 0,
                    }, context={'user': request.user})
                if not serializer.is_valid():
                    error = Exception(serializer.errors)
                    error.status = status.HTTP_400_BAD_REQUEST
                    raise error
                serializer.save()
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while adding product to cart:", e)
                raise error