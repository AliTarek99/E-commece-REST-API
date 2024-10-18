from cart.models import Cart
from django.contrib import admin
from products.admin import ProductInline

class CartInline(admin.TabularInline):
    model = Cart
    extra = 0
    readonly_fields = ('user', 'product_variant', 'quantity')
    can_delete = False
    fields = ('user', 'product_variant', 'quantity')
    
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_variant', 'quantity',)
    list_filter = ('user', 'product_variant', 'quantity')
    search_fields = ('user', 'product_variant')
    ordering = ('user', 'product_variant')
    search_fields = ('user', 'product_variant')
    
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Cart Item"
        model_meta.verbose_name_plural = "Cart Item"
        return super().get_model_perms(request)
    
admin.site.register(Cart, CartAdmin)