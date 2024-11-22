from django.contrib import admin

from shipping.models import City, Country

class CityInline(admin.TabularInline):
    model = City
    readonly_fields = ('id', )
    fields = ('id', 'name', 'shipping_fee')
    

class CoutryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_filter = ('name', 'id')
    search_fields = ('name', ' id')
    inlines = [CityInline]
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "Country"
        model_meta.verbose_name_plural = "Countries"
        return super().get_model_perms(request)


class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country', 'shipping_fee')
    list_filter = ('name', 'country', 'shipping_fee')
    search_fields = ('name', 'country', 'shipping_fee')
    def get_model_perms(self, request):
        # Use this method to control the name of the model in the admin panel
        model_meta = self.model._meta
        model_meta.verbose_name = "City"
        model_meta.verbose_name_plural = "Cities"
        return super().get_model_perms(request)
    

admin.site.register(City, CityAdmin)
admin.site.register(Country, CoutryAdmin)