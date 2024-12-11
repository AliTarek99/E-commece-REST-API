from products.models import ProductVariant
from ..serializers import CartItemSerializer
from cart.models import CartItem, CartCoupon, Cart
from rest_framework import status
from django.db import transaction
from coupons.models import CouponProduct
from django.utils import timezone
from django.db.models import F

class CartServices():
    @classmethod
    def add_product_to_cart(cls, request):
        try:
            product = ProductVariant.objects.filter(id=request.data['product_variant']).first()
            if not product:
                error = Exception('Product not found')
                error.status = status.HTTP_404_NOT_FOUND
                raise error
            with transaction.atomic():
                # lock the cart item
                cart_product = CartItem.objects.select_for_update().filter(
                    user=request.user.id, 
                    product_variant=request.data['product_variant']
                ).first()
                
                #get coupons that apply to this product
                coupons = CartCoupon.objects.filter(
                    user=request.user, 
                    coupon__couponproduct__product=product.parent,
                    coupon__is_active=True,
                    coupon__couponrule__expires_at__gte=timezone.now(),
                    coupon__couponrule__max_uses_per_user__lt=F('coupon__couponuse__uses')
                ).select_related('coupon__couponrule', 'coupon')

                #calculate discount price
                discount_price = product.price
                for coupon in coupons:
                    if coupon.coupon.couponrule.type == 'percentage':
                        discount_price = discount_price - min(
                            (coupon.coupon.couponrule.discount_value * discount_price / 100), 
                            coupon.coupon.couponrule.discount_limit if coupon.coupon.couponrule.discount_limit else 999999
                        )
                    else:
                        discount_price = max(discount_price - coupon.coupon.couponrule.discount_value, 0)
                
                Cart.objects.filter(user=request.user).update(
                    total_price=F('total_price') + product.price, 
                    discount_price=F('discount_price') + discount_price
                )
                
                # update cart item if it exists
                serializer = CartItemSerializer(cart_product, data={
                        'user_id': request.user.id,
                        'quantity': request.data['quantity'] + (cart_product.quantity if cart_product else 0),
                        'discount_price': discount_price
                    }, context={'user': request.user, 'product_variant': product}
                )
                
                if not serializer.is_valid():
                    error = Exception(serializer.errors)
                    error.status = status.HTTP_400_BAD_REQUEST
                    raise error
                serializer.save()
                return serializer
        except Exception as e:
            if hasattr(e, 'status'):
                raise e
            else:
                error = Exception('Something went wrong')
                error.status = status.HTTP_500_INTERNAL_SERVER_ERROR
                print("Error while adding product to cart:", e)
                raise error
            
    @classmethod
    def delete_cart_item(cls, request, product_variant):
        cart_product = CartItem.objects.filter(
            user=request.user.id, 
            product_variant_id=product_variant
        ).select_related('product_variant__parent', 'product_variant').only(
            'user_id',
            'product_variant_id',
            'product_variant__parent_id',
            'product_variant__price'
            'quantity',
            'discount_price'
        ).first()
        
        if not cart_product:
            error = Exception('Product not found')
            error.status = status.HTTP_404_NOT_FOUND
            raise error
            
        cart = Cart.objects.filter(user=request.user).first()
        
        cart.total_price -= cart_product.product_variant.price * cart_product.quantity
        cart.discount_price -= max(cart_product.discount_price * cart_product.quantity, 0)
        cart.save(update_fields=['total_price', 'discount_price'])
        

        cart_product.delete()
        # remove unused coupons
        unused_coupons = CartCoupon.objects.filter(
            user=request.user
        ).exclude(
            coupon__couponproduct__product__productvariant__cartitem__user=request.user
        )
        
        # get sellers that have products in cart
        sellers = [coupon.coupon.seller for coupon in unused_coupons]
        sellers = CartItem.objects.filter(product_variant__parent__seller__in=sellers).values_list('seller_id', flat=True)
        
        unused_coupons.exclude(coupon__seller_id__in=sellers)
        
        unused_coupons.delete()
        return {'total_price': cart.total_price, 'discount_price': cart.discount_price, 'deleted_coupons': unused_coupons}