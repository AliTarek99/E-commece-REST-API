from django.urls import path
from shipping.apis import CitiesAPIs

urlpatterns = [
    path('cities/', CitiesAPIs.as_view(), name='cities'),
]