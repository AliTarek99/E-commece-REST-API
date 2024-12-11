from django.db.models import F, Prefetch
from cart.models import CartItem, Cart
from products.models import ProductImages

class CartQueryset:
    @classmethod
    def get_cart(cls, user):
        cart = Cart.objects.filter(user=user).prefetch_related(
            Prefetch(
                'user__cartitem_set',
                queryset=CartItem.objects.prefetch_related(
                    Prefetch(
                        'product_variant__parent__productimages_set', 
                        queryset= ProductImages.objects.filter(
                            in_use=True
                        )
                    )
                ).filter(
                    product_variant__parent__productimages__color_id=F('product_variant__color_id')
                ).select_related(
                    'product_variant',
                    'product_variant__parent'
                )
            ),
            'user__cartcoupon_set'
        ).only( 
            'user__cartitem__product_variant__price', 
            'user__cartitem__product_variant__color_id',
            'user__cartitem__product_variant__size_id', 
            'user__cartitem__quantity',
            'user__cartitem__product_variant__parent_id',
            'user__cartitem__product_variant__parent__name',
            'user_id',
            'user__cartitem__discount_price',
            'discount_price',
            'total_price'
        )
        return cart