from django.contrib import admin
from coupons.models import Coupon, CouponRule, CouponProduct, CouponUse

class CouponRuleInline(admin.TabularInline):
    model = CouponRule
    extra = 0

class CouponRuleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'coupon', 
        'coupon',
        'minimum_required_value', 
        'max_uses', 
        'max_uses_per_user', 
        'discount_type', 
        'discount_value', 
        'discount_limit', 
        'coupon_type', 
        'created_at', 
        'expires_at'
    )
    ordering = ('id', 'coupon', 'max_uses_per_user', 'discount_type', 'discount_value', 'discount_limit', 'coupon_type', 'created_at', 'expires_at')
    list_filter = ('coupon',  'discount_type', 'coupon_type', 'created_at', 'expires_at')

class CouponProductInline(admin.TabularInline):
    model = CouponProduct
    extra = 0

class CouponUseInline(admin.TabularInline):
    model = CouponUse
    extra = 0

class CouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'seller', 'uses', 'is_active')
    ordering = ('id', 'uses', 'is_active')
    list_filter = ('seller_id', 'is_active', 'couponrule__discount_type', 'couponrule__coupon_type')
    inlines = [CouponRuleInline, CouponProductInline, CouponUseInline]
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Coupon"
        model_meta.verbose_name_plural = "Coupons"
        return super().get_model_perms(request)

admin.site.register(Coupon, CouponAdmin)
admin.site.register(CouponRule, CouponRuleAdmin)