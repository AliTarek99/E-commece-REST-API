from django.contrib import admin
from users.models import CustomUser
from orders.admin import OrderInline
from cart.admin import CartInline
from products.admin import ProductInline

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_superuser')
    list_filter = ('is_superuser',)
    search_fields = ('id', 'email')
    ordering = ('id',)
    inlines = [OrderInline, CartInline, ProductInline]
    
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "User"
        model_meta.verbose_name_plural = "Users"
        return super().get_model_perms(request)
    
admin.site.register(CustomUser, CustomUserAdmin)