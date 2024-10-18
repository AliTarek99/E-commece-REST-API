from django.urls import path
from .apis import CartAPIs

urlpatterns = [
    path('', CartAPIs.as_view(), name="cart-list"),
    path('<int:product_variant>/', CartAPIs.as_view(), name="cart-product"),
]