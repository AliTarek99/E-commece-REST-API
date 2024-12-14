from django.db.models import F, Prefetch
from cart.models import CartItem, Cart, CartCoupon
from products.models import ProductImages

class CartQueryset:
    @classmethod
    def get_cart(cls, user):
        cart = Cart.objects.filter(user=user).prefetch_related(
            Prefetch(
                'cartitem',
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
                ).distinct()
            ),
            Prefetch( 
                'cartcoupon',
                queryset=CartCoupon.objects.select_related('coupon')
            )
        ).only( 
            'cartcoupon__coupon__code',
            'cartitem__product_variant__price', 
            'cartitem__product_variant__color_id',
            'cartitem__product_variant__size_id', 
            'cartitem__quantity',
            'cartitem__product_variant__parent_id',
            'cartitem__product_variant__parent__name',
            'user_id',
            'cartitem__discount_price',
            'discount_price',
            'total_price'
        )
        return cart