from django.contrib import admin
from orders.models import Orders, OrdersItems

class OrderItemInline(admin.TabularInline):
    model = OrdersItems
    extra = 0
    readonly_fields = ('id', 'order', 'name', 'color', 'size', 'seller', 'quantity', 'price')
    can_delete = False
    fields = ('id', 'order', 'name', 'color', 'size', 'seller', 'quantity', 'price')
    
class OrderInline(admin.TabularInline):
    model = Orders
    extra = 0
    readonly_fields = ('id', 'user', 'created_at', 'total_price', 'address')
    can_delete = False
    fields = ('id', 'user', 'created_at', 'total_price', 'address', 'status')
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_price', 'address', 'status')
    list_filter = ('user', 'created_at', 'total_price', 'address', 'status')
    search_fields = ('user', 'created_at', 'address', 'status')
    ordering = ('user', 'created_at', 'total_price', 'status')
    inlines = [OrderItemInline]
    
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Order"
        model_meta.verbose_name_plural = "Orders"
        return super().get_model_perms(request)
    
    
admin.site.register(Orders, OrderAdmin)