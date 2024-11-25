from django.urls import path
from .apis import CartAPIs, RetrieveCartAPIs

urlpatterns = [
    path('list/', RetrieveCartAPIs.as_view(), name="cart-list"),
    path('', CartAPIs.as_view(), name="cart-list"),
    path('<int:product_variant>/', CartAPIs.as_view(), name="cart-product"),
]