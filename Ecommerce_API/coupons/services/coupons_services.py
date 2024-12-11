from coupons.models import CouponRule
from cart.models import CartItem, Cart, CartCoupon
from django.db import transaction
from orders.services import OrderServicesHelpers

class CouponServices():
    @classmethod
    def apply_coupon(cls, user, coupon):
        products = []
        cart = Cart.objects.filter(user=user).prefetch_related('cartitem').first()
        
        ## Product Coupons
        if coupon.couponrule.coupon_type == CouponRule.COUPON_TYPE_PRODUCT:
            products = CartItem.objects.filter(
                user=user, 
                product_variant__parent__in=coupon.couponproduct.product_id,
            ).select_related('product_variant')
            
            for product in products:
                if coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    value_deducted = min(
                        product.discount_price * (coupon.couponrule.discount_value/100), 
                        coupon.couponrule.discout_limit if coupon.couponrule.discout_limit else 999999
                    )
                    product.discount_price -= value_deducted
                    cart.discount_price -= value_deducted
                elif coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_FIXED:
                    product.discount_price -= coupon.couponrule.discount_value 
                    cart.discount_price -= coupon.couponrule.discount_value
                    
        ## Seller Coupons
        elif coupon.couponrule.coupon_type == CouponRule.COUPON_TYPE_SELLER:
            products = CartItem.objects.filter(
                user=user,
                product_variant__parent__seller=coupon.seller
            ).select_related('product_variant')

            for product in products:
                if coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_PERCENTAGE:
                    value_deducted = min(
                        product.discount_price * (coupon.couponrule.discount_value/100), 
                        coupon.couponrule.discout_limit if coupon.couponrule.discout_limit else 999999
                    )
                    product.discount_price -= value_deducted
                    cart.discount_price -= value_deducted
                elif coupon.couponrule.discount_type == CouponRule.DISCOUNT_TYPE_FIXED:
                    product.discount_price -= coupon.couponrule.discount_value
                    cart.discount_price -= coupon.couponrule.discount_value
                    
        # save cart and used coupons
        with transaction.atomic():
            CartCoupon.objects.create(user=cart, coupon=coupon) 
            result = OrderServicesHelpers.calculate_discount_price(user, cart)
            cart.discount_price = result['discount_price']
            if len(result['expired_coupons']):
                CartCoupon.objects.filter(user=cart, coupon__code__in=result['expired_coupons']).delete()
            
            cart.save()
            
            return {
                'discount_price': cart.discount_price,
                'product_variants': [
                    {
                        'id': product.product_variant.id,
                        'discount_price': product.discount_price
                    } for product in products
                ],
                'expired_coupons': result['expired_coupons']
            } 
            