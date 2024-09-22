from ..models import Orders, OrdersItems
from cart.models import Cart

class OrdersQueryset:
    @classmethod
    def create_order(self, user):
        cart = Cart.objects.filter(user=user).select_related('product').only('product__price', 'quantity')
        total_price = sum(item.product.price * item.quantity for item in cart)
        order = Orders.objects.create(user=user, total_price=total_price)
        for item in cart:
            OrdersItems.objects.create(order=order, product=item.product, quantity=item.quantity)
        cart.delete()
        return order