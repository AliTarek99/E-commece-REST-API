from cart.models import CartItem, Cart, CartCoupon
from django.contrib import admin

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('user', 'product_variant', 'discount_price')
    fields = ('user', 'product_variant', 'quantity', 'discount_price')
    
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_variant', 'quantity', 'discount_price')
    list_filter = ('user', 'product_variant', 'quantity')
    search_fields = ('user', 'product_variant')
    ordering = ('user', 'product_variant', 'discount_price')
    search_fields = ('user', 'product_variant')
    
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Cart Item"
        model_meta.verbose_name_plural = "Cart Item"
        return super().get_model_perms(request)
    
class CartCouponInline(admin.TabularInline):
    model = CartCoupon
    extra = 0
    fields = ('coupon',)
    
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'discount_price')
    list_filter = ('user', 'total_price', 'discount_price')
    search_fields = ('user', 'total_price', 'discount_price')
    ordering = ('user', 'total_price', 'discount_price')
    inlines = [CartItemInline, CartCouponInline]
    
class CartInline(admin.TabularInline):
    model = Cart
    extra = 0
    readonly_fields = ('user', 'total_price', 'discount_price')
    
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Cart, CartAdmin)