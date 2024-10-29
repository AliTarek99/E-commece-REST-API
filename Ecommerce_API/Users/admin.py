from django.contrib import admin
from users.models import CustomUser, Address
from orders.admin import OrderInline
from cart.admin import CartInline
from products.admin import ProductInline

class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'city', 'street', 'country', 'building_no', 'apartment_no')
    list_filter = ('user', 'city', 'street', 'country', 'building_no', 'apartment_no')
    search_fields = ('user', 'city', 'street', 'country', 'building_no', 'apartment_no')

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    readonly_fields = ('id', 'user')
    fields = ('id', 'user', 'city', 'street', 'country', 'building_no', 'apartment_no')

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_superuser')
    list_filter = ('is_superuser',)
    search_fields = ('id', 'email')
    ordering = ('id',)
    inlines = [OrderInline, CartInline, ProductInline, AddressInline]
    
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "User"
        model_meta.verbose_name_plural = "Users"
        return super().get_model_perms(request)
    
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Address, AddressAdmin)