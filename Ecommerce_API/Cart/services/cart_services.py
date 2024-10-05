from products.models import ProductVariantSizes
from ..serializers import CartSerializer
from cart.models import Cart
from rest_framework import status
from django.db import transaction

class CartServices():
    @classmethod
    def add_product_to_cart(cls, request):
        try:
            product = ProductVariantSizes.objects.filter(size=request.data['size'], product_variant=request.data['product_variant']).select_related('product_varaint').first()
            if not product:
                error = Exception('Product not found')
                error.status = status.HTTP_404_NOT_FOUND
            with transaction.atomic():
                cart_product = Cart.objects.select_for_update().filter(user=request.user.id, product_variant=request.data['product_variant'], size=request.data['size']).first()
                serializer = CartSerializer(cart_product, data={
                        'user': request.user.id,
                        'product_varaint': ProductVariantSizes.objects.filter(id=request.data['product']).only('id').first().id,
                        'quantity': request.data['quantity'],
                        'size': request.data['size'],
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
                raise error