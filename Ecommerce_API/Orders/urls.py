from rest_framework.urls import path
from .apis import OrdersAPIs, PaymentCallbackAPIs

urlpatterns = [
    path('', OrdersAPIs.as_view(), name='orders'),
    path('/payment/callback', PaymentCallbackAPIs.as_view(), name='payment_callback')
]