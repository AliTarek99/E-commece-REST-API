from rest_framework.urls import path
from .apis import OrdersAPIs

urlpatterns = [
    path('orders/', OrdersAPIs.as_view(), name='orders'),
]