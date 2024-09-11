from django.urls import path
from .apis import UserAPIs, UserloginAPI, UserRegistrationAPI

urlpatterns = [
    path('', UserAPIs.as_view(), name='user-apis'),
    path('login/', UserloginAPI.as_view(), name='user-login'),
    path('register/', UserRegistrationAPI.as_view(), name='user-register'),
]