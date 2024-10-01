from rest_framework.urls import path
from .apis import OrdersAPIs

urlpatterns = [
    path('', OrdersAPIs.as_view(), name='orders'),
]