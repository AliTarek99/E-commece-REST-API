from django.urls import path
from .apis import UserAPIs, UserloginAPI, UserRegistrationAPI, UserAddressesListAPI, UserAddressesAPIs

urlpatterns = [
    path('', UserAPIs.as_view(), name='user-apis'),
    path('login/', UserloginAPI.as_view(), name='user-login'),
    path('register/', UserRegistrationAPI.as_view(), name='user-register'),
    path('address-list/', UserAddressesListAPI.as_view(), name='user-addresses'),
    path('address/', UserAddressesAPIs.as_view(), name='user-addresses-create'),
]