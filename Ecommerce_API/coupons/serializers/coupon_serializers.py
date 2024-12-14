from rest_framework import serializers
from coupons.models import Coupon, CouponUse, CouponRule
from django.utils.timezone import now
from django.db.models import Prefetch
from cart.models import CartItem, CartCoupon

class CouponCheckSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8)
    coupon = None
    
    def validate_code(self, code):
        self.coupon = Coupon.objects.filter(
            code=code, 
            is_active=True
        ).select_related('couponrule').prefetch_related(
            Prefetch(
                'couponuse', 
                queryset=CouponUse.objects.filter(user=self.context['request'].user)
            ),
            'couponproduct',
            Prefetch(
                'cartcoupon',
                queryset=CartCoupon.objects.filter(user_id=self.context['request'].user.id)
            )
        ).first()
        
        coupon = self.coupon
        
        if not coupon:
            raise serializers.ValidationError('Invalid coupon code')
        
        if coupon.couponrule.expires_at < now():
            coupon.is_active = False
            coupon.save()
            raise serializers.ValidationError('Coupon has expired')
        
        cart_coupons = coupon.cartcoupon.all()
        if len(cart_coupons):
            raise serializers.ValidationError('Coupon already applied')
        
        user_coupon_use = coupon.couponuse.filter(user=self.context['request'].user).first()
        if (user_coupon_use.uses if user_coupon_use else 0) >= coupon.couponrule.max_uses_per_user:
            raise serializers.ValidationError('Used coupon')
        
        if coupon.couponrule.coupon_type == CouponRule.COUPON_TYPE_SELLER and \
            CartItem.objects.filter(user=self.context['request'].user, product_variant__parent__seller=coupon.seller).exists():
            raise serializers.ValidationError('No product in cart for the applied coupon')
        
        if coupon.couponrule.coupon_type == CouponRule.COUPON_TYPE_PRODUCT and \
            not CartItem.objects.filter(user=self.context['request'].user, product_variant__parent__in=coupon.couponproduct.product_id).exists():
            raise serializers.ValidationError('No product in cart for the applied coupon')
            
        
        