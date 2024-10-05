from ..models import Orders, OrdersItems
from cart.models import Cart
from django.db import transaction

class OrdersServices:
    @classmethod
    def create_order(self, user):
        with transaction.atomic():
            cart = Cart.objects.raw("""
                                    SELECT c.user, c.product_variant, c.quantity, PVS.price, PVS.size, PV.color, PV.id, P.name, P.description, P.seller
                                    FROM Cart AS c 
                                    JOIN Product_Variant_Size AS PVS
                                    ON c.product_variant = PVS.product_variant AND c.size = PVS.size
                                    JOIN Product_Variant AS PV 
                                    ON c.product_variant = PV.id
                                    JOIN Product AS P 
                                    ON PV.parent = P.id
                                    WHERE user_id = %s""", [user.id])
            total_price = sum([item.price * item.quantity for item in cart])
            order = Orders.objects.create(user=user, total_price=total_price)
            
            orderItems = OrdersItems.objects.bulk_create(list(cart))
            order['orderItems'] = orderItems
            cart.delete()
            return order