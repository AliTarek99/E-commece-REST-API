from django.contrib import admin
from products.models import Product, ProductVariant, ProductImages, Colors, Sizes
from coupons.admin import CouponProductInline

class ColorInline(admin.TabularInline):
    model = Colors
    extra = 0
    readonly_fields = ('id', 'name')
    can_delete = False
    fields = ('id', 'name')
    
class ColorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Color"
        model_meta.verbose_name_plural = "Colors"
        return super().get_model_perms(request)
    
class SizeInline(admin.TabularInline):
    model = Sizes
    extra = 0
    readonly_fields = ('id', 'name')
    can_delete = False
    fields = ('id', 'name')

class SizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Size"
        model_meta.verbose_name_plural = "Sizes"
        return super().get_model_perms(request)

class ProductImagesInline(admin.TabularInline):
    model = ProductImages
    extra = 0
    readonly_fields = ('id', 'url', 'product')
    can_delete = False
    fields = ('id', 'url', 'color', 'product')
    
class ProductImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'product', 'color')
    list_filter = ('product', 'color')
    search_fields = ('product', 'color')
    ordering = ('product', 'color')
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Image"
        model_meta.verbose_name_plural = "Images"
        return super().get_model_perms(request)
    
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    readonly_fields = ('id', 'parent', 'quantity')
    can_delete = False
    fields = ('id', 'parent', 'color', 'size', 'quantity')
    
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'color', 'size', 'quantity', 'price')
    list_filter = ('parent', 'color', 'size', 'quantity')
    search_fields = ('parent', 'color', 'size')
    ordering = ('parent', 'color', 'size', 'quantity')
    # Customizing display names within the admin panel
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Variant"
        model_meta.verbose_name_plural = "Variants"
        return super().get_model_perms(request)
    
class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    readonly_fields = ('id', 'name', 'description', 'max_price', 'min_price', 'seller')
    can_delete = False
    fields = ('id', 'name', 'description', 'max_price', 'min_price', 'seller')
    
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'max_price', 'min_price', 'seller')
    list_filter = ('name', 'description', 'max_price', 'min_price', 'seller', )
    search_fields = ('name', 'price', 'seller', )
    inlines = [ProductVariantInline, ProductImagesInline, CouponProductInline]
    
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(ProductImages, ProductImagesAdmin)
admin.site.register(Colors, ColorAdmin)
admin.site.register(Sizes, SizeAdmin)
