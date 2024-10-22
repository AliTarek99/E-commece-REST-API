from rest_framework import permissions

class IsSellerOfTheProduct(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.seller == request.user