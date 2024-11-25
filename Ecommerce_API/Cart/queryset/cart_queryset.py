from django.db.models import F, Prefetch
from cart.models import Cart
from products.models import ProductImages

class CartQueryset:
    @classmethod
    def get_cart_items(cls, user):
        cartItems = Cart.objects.filter(user=user).prefetch_related(
            Prefetch(
                'product_variant__parent__productimages_set', 
                queryset= ProductImages.objects.filter(
                    in_use=True
                )
            )
        ).filter(
            product_variant__parent__productimages__color_id=F('product_variant__color_id')
        ).only( 
            'product_variant__price', 
            'product_variant__color_id',
            'product_variant__size_id', 
            'quantity',
            'product_variant__parent_id',
            'product_variant__parent__name',
            'product_variant__price',
            'user_id',
        ).select_related(
            'product_variant',
            'product_variant__parent'
        ).distinct()
        return cartItems